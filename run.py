"""
Flight price optimizer — Google Flights via SerpAPI.

Usage:
    python run.py --from ORD --to JFK --depart 2026-06-15 --return 2026-06-20
    python run.py --from ORD --to NYC --depart 2026-06-15 --return 2026-06-20
    python run.py --from ORD --to caribbean --depart 2026-06-15 --return 2026-06-22
    python run.py --from DFW --to CUN --depart 2026-07-04
    python run.py --list-airports

Setup:
    export SERPAPI_KEY="your_key_here"
    pip install -r requirements.txt
"""

import argparse
import logging
import sys
from config import cfg
from airports import resolve, region_label, list_airports
from api_client import search
from price_optimizer import build_candidates, analyze, format_report
from storage import init_db, save_flights, save_run

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(cfg.log_path),
    ],
)
logger = logging.getLogger(__name__)


def parse_args():
    p = argparse.ArgumentParser(
        description="Flight price optimizer — finds the best rate across all trip structures.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  python run.py --from ORD --to NYC --depart 2026-06-15 --return 2026-06-20\n"
            "  python run.py --from ORD --to caribbean --depart 2026-06-15 --return 2026-06-22\n"
            "  python run.py --from DFW --to CUN --depart 2026-07-04\n"
            "  python run.py --list-airports\n"
        ),
    )
    p.add_argument("--from",    dest="origin",      required=False,
                   help="Origin airport code or city (e.g. ORD, Chicago)")
    p.add_argument("--to",      dest="destination", required=False,
                   help="Destination code, metro alias, city, or region (e.g. JFK, NYC, caribbean)")
    p.add_argument("--depart",  dest="depart_date", required=False,
                   help="Departure date YYYY-MM-DD")
    p.add_argument("--return",  dest="return_date", required=False, default=None,
                   help="Return date YYYY-MM-DD (omit for one-way only search)")
    p.add_argument("--max-destinations", dest="max_destinations", type=int,
                   default=cfg.max_destinations,
                   help=f"Cap how many destination airports to search (default: {cfg.max_destinations})")
    p.add_argument("--list-airports", action="store_true",
                   help="Print all supported airports and exit")
    return p.parse_args()


def run(origin: str, destinations: list, depart_date: str,
        return_date: str | None, dest_query: str) -> None:
    """
    Orchestrate all API sessions for the given origin → destinations combination.

    Sessions per destination airport:
      - 1 round-trip search      (if return_date provided)
      - 1 one-way outbound search
      - 1 one-way return search  (if return_date provided)

    Total sessions = len(destinations) × 2 or × 3 depending on trip type.
    """
    logger.info(
        "=== Run started: %s → %s (%d airports) depart=%s return=%s ===",
        origin, dest_query, len(destinations), depart_date, return_date or "one-way",
    )
    init_db()

    round_trips: list = []
    outbound_one_ways: list = []
    return_one_ways: list = []
    session_hits = {"round_trip": 0, "outbound": 0, "return": 0}
    total_sessions = len(destinations) * (3 if return_date else 1)

    for airport in destinations:
        # Round-trip (only when return date provided)
        if return_date:
            flights = search(origin=origin, destination=airport,
                             depart_date=depart_date, trip_type="round-trip",
                             return_date=return_date)
            if flights:
                session_hits["round_trip"] += 1
            round_trips.extend(flights[:cfg.results_per_search])
            save_flights(flights[:cfg.results_per_search])

        # One-way outbound
        flights = search(origin=origin, destination=airport,
                         depart_date=depart_date, trip_type="one-way")
        if flights:
            session_hits["outbound"] += 1
        outbound_one_ways.extend(flights[:cfg.results_per_search])
        save_flights(flights[:cfg.results_per_search])

        # One-way return (only when return date provided)
        if return_date:
            flights = search(origin=airport, destination=origin,
                             depart_date=return_date, trip_type="one-way")
            if flights:
                session_hits["return"] += 1
            return_one_ways.extend(flights[:cfg.results_per_search])
            save_flights(flights[:cfg.results_per_search])

    # --- Dead scrape detector ---
    total_hits = sum(session_hits.values())
    if total_hits == 0:
        logger.error(
            "SCRAPER_FAILED: All %d sessions returned 0 results. "
            "Check SERPAPI_KEY and account quota.",
            total_sessions,
        )
        print(
            "\n[SCRAPER_FAILED] No flight data returned from any session.\n"
            "  Possible causes:\n"
            "    1. SERPAPI_KEY is missing or invalid\n"
            "    2. Monthly API quota exhausted\n"
            "    3. No flights exist for this route/date combination\n"
            "  Check logs for details."
        )
        sys.exit(1)

    if total_hits < total_sessions:
        failed = total_sessions - total_hits
        logger.warning(
            "Partial results: %d/%d sessions returned data. "
            "Hits — RT: %d/%d, Outbound: %d/%d, Return: %d/%d",
            total_hits, total_sessions,
            session_hits["round_trip"], len(destinations),
            session_hits["outbound"],   len(destinations),
            session_hits["return"],     len(destinations) if return_date else 0,
        )
        print(
            f"\n[WARNING] {failed} of {total_sessions} sessions returned no data. "
            "Results may be incomplete."
        )

    # --- Algorithm ---
    candidates = build_candidates(round_trips, outbound_one_ways, return_one_ways)
    result = analyze(candidates)

    # --- Persist ---
    save_run(depart_date, return_date or "", result)

    # --- Report ---
    origin_label = origin
    dest_display = region_label(destinations) if len(destinations) > 1 else (
        region_label([destinations[0]]) if destinations else dest_query
    )
    report = format_report(result, depart_date, return_date or "one-way",
                           origin_label=origin_label, dest_label=dest_display)
    print(report)

    if result["winner"]:
        logger.info(
            "Run complete. Winner: %s @ $%.2f (effective)",
            result["winner"]["type"],
            result["winner"]["effective_price"],
        )


if __name__ == "__main__":
    args = parse_args()

    if args.list_airports:
        print(list_airports())
        sys.exit(0)

    # Validate required args when not listing airports
    missing = [f for f, v in [("--from", args.origin), ("--to", args.destination),
                               ("--depart", args.depart_date)] if not v]
    if missing:
        print(f"Error: {', '.join(missing)} {'is' if len(missing)==1 else 'are'} required.\n")
        print("  python run.py --from ORD --to NYC --depart 2026-06-15 --return 2026-06-20")
        print("  python run.py --list-airports")
        sys.exit(1)

    # Resolve origin (must be a single airport)
    try:
        origin_codes = resolve(args.origin)
    except ValueError as e:
        print(f"Error in --from: {e}")
        sys.exit(1)

    if len(origin_codes) > 1:
        print(
            f"Error: --from must resolve to a single airport. "
            f"'{args.origin}' matched {origin_codes}. "
            f"Pick one (e.g. --from {origin_codes[0]})."
        )
        sys.exit(1)
    origin = origin_codes[0]

    # Resolve destinations (can be multiple)
    try:
        destinations = resolve(args.destination)
    except ValueError as e:
        print(f"Error in --to: {e}")
        sys.exit(1)

    # Warn + cap if destination count is large
    if len(destinations) > args.max_destinations:
        print(
            f"[INFO] '{args.destination}' resolved to {len(destinations)} airports. "
            f"Capping at {args.max_destinations} (use --max-destinations N to override). "
            f"Each destination uses 3 API calls."
        )
        destinations = destinations[:args.max_destinations]

    api_calls = len(destinations) * (3 if args.return_date else 1)
    if api_calls > 20:
        print(
            f"[INFO] This run will use {api_calls} SerpAPI calls "
            f"({len(destinations)} destinations × {'3' if args.return_date else '1'} searches each)."
        )

    # Guard: origin must not appear in destinations
    if origin in destinations:
        destinations = [d for d in destinations if d != origin]
        if not destinations:
            print(f"Error: origin ({origin}) and destination resolved to the same airport.")
            sys.exit(1)
        logger.warning("Removed origin %s from destination list.", origin)

    run(
        origin=origin,
        destinations=destinations,
        depart_date=args.depart_date,
        return_date=args.return_date,
        dest_query=args.destination,
    )
