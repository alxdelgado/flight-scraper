"""
Core best-rate algorithm.

Given lists of scraped flights (round-trips + one-ways), builds all 12 candidate
trip structures, scores them, and returns a ranked list with a clear winner.

Entirely pure — no I/O, no browser dependency. Easy to unit-test.
"""

from datetime import datetime, timezone
from typing import List, Optional
from config import cfg


Flight = dict
Candidate = dict


def baggage_cost(airline: Optional[str], legs: int = 1) -> float:
    """
    Return the total baggage fee for a given airline and number of one-way legs.

    Uses cfg.carry_on_bag and cfg.checked_bag to determine which fees apply.
    Unknown airlines default to $0 (conservative — avoids false penalties).

    Args:
        airline: Airline name string (matches keys in cfg.baggage_fees).
        legs:    1 for one-way, 2 for round-trip.
    """
    if not airline:
        return 0.0
    fee = cfg.baggage_fees.get(airline)
    if fee is None:
        return 0.0
    total = 0.0
    if cfg.carry_on_bag:
        total += fee.carry_on * legs
    if cfg.checked_bag:
        total += fee.checked * legs
    return round(total, 2)


def score(effective_price: float, stops: int, duration_mins: Optional[int]) -> float:
    """
    Lower is better. Operates on effective_price (listed + baggage fees).
    Adds a dollar penalty per stop and optionally per hour of total travel.
    """
    s = effective_price + (stops * cfg.stops_penalty_usd)
    if cfg.duration_penalty_usd > 0 and duration_mins:
        s += (duration_mins / 60) * cfg.duration_penalty_usd
    return round(s, 2)


def _best(flights: List[Flight], dest: Optional[str] = None,
          origin: Optional[str] = None) -> Optional[Flight]:
    """Return the cheapest flight matching optional origin/dest filter."""
    pool = flights
    if dest:
        pool = [f for f in pool if f["destination"] == dest]
    if origin:
        pool = [f for f in pool if f["origin"] == origin]
    if not pool:
        return None
    return min(pool, key=lambda f: f["price_usd"] or float("inf"))


def build_candidates(
    round_trips: List[Flight],
    outbound_one_ways: List[Flight],
    return_one_ways: List[Flight],
) -> List[Candidate]:
    """
    Build all 12 candidate structures, score each one on effective price
    (listed price + applicable baggage fees), and return sorted best-first.

    Candidate shape:
    {
        "type":             "round-trip" | "two-one-ways",
        "outbound":         Flight,
        "return":           Flight | None,
        "listed_price":     float,   # raw price from Google Flights
        "baggage_cost":     float,   # total bag fees for this candidate
        "effective_price":  float,   # listed + baggage (what you'll actually pay)
        "total_stops":      int,
        "total_duration":   int | None,
        "score":            float,
        "airports_match":   bool,
        "label":            str,
    }
    """
    candidates: List[Candidate] = []

    # Derive destination airport codes directly from flight data so this
    # function works for any origin/destination pair without config changes.
    dest_airports: List[str] = list(dict.fromkeys(
        f["destination"] for f in (round_trips + outbound_one_ways) if f
    ))
    return_airports: List[str] = list(dict.fromkeys(
        f["origin"] for f in return_one_ways if f
    ))

    # --- Round-trips (one candidate per destination airport) ---
    for airport in dest_airports:
        flight = _best(round_trips, dest=airport)
        if not flight:
            continue
        origin = flight["origin"]
        total_stops = flight["stops"]
        duration = flight["duration_mins"]
        total_duration = (duration * 2) if duration else None
        bags = baggage_cost(flight.get("airline"), legs=2)
        listed = flight["price_usd"]
        effective = round(listed + bags, 2)
        candidates.append({
            "type":            "round-trip",
            "outbound":        flight,
            "return":          None,
            "listed_price":    listed,
            "baggage_cost":    bags,
            "effective_price": effective,
            "total_stops":     total_stops,
            "total_duration":  total_duration,
            "score":           score(effective, total_stops, total_duration),
            "airports_match":  True,
            "label":           f"{origin}↔{airport}",
        })

    # --- Two one-ways: best-per-airport outbound × best-per-airport return ---
    best_outbound = {ap: _best(outbound_one_ways, dest=ap) for ap in dest_airports}
    best_return = {ap: _best(return_one_ways, origin=ap) for ap in return_airports}

    for ob_airport, ob in best_outbound.items():
        if not ob:
            continue
        for ret_airport, ret in best_return.items():
            if not ret:
                continue
            combined_listed = ob["price_usd"] + ret["price_usd"]
            combined_stops = ob["stops"] + ret["stops"]
            combined_duration = (
                ob["duration_mins"] + ret["duration_mins"]
                if ob["duration_mins"] and ret["duration_mins"]
                else None
            )
            # Baggage fees are per one-way leg; each ticket is 1 leg
            ob_bags = baggage_cost(ob.get("airline"), legs=1)
            ret_bags = baggage_cost(ret.get("airline"), legs=1)
            combined_bags = round(ob_bags + ret_bags, 2)
            combined_effective = round(combined_listed + combined_bags, 2)

            airports_match = ob_airport == ret_airport
            ob_origin = ob["origin"]
            ret_dest  = ret["destination"]
            label = f"{ob_origin}→{ob_airport} / {ret_airport}→{ret_dest}"

            candidates.append({
                "type":            "two-one-ways",
                "outbound":        ob,
                "return":          ret,
                "listed_price":    round(combined_listed, 2),
                "baggage_cost":    combined_bags,
                "effective_price": combined_effective,
                "total_stops":     combined_stops,
                "total_duration":  combined_duration,
                "score":           score(combined_effective, combined_stops, combined_duration),
                "airports_match":  airports_match,
                "label":           label,
            })

    candidates.sort(key=lambda c: c["score"])
    return candidates


def best_round_trip(candidates: List[Candidate]) -> Optional[Candidate]:
    rts = [c for c in candidates if c["type"] == "round-trip"]
    return rts[0] if rts else None


def best_two_one_ways(candidates: List[Candidate]) -> Optional[Candidate]:
    ows = [c for c in candidates if c["type"] == "two-one-ways"]
    return ows[0] if ows else None


def analyze(candidates: List[Candidate]) -> dict:
    """
    Compare best RT vs best two-OW on effective price (listed + baggage).

    savings is a raw effective-price delta so the number reflects actual
    out-of-pocket dollars saved, not the score/stop-penalty adjustment.

    Returns:
    {
        "winner":       Candidate,
        "best_rt":      Candidate | None,
        "best_two_ow":  Candidate | None,
        "savings":      float,   # effective price of loser minus winner (>= 0)
        "savings_vs":   str,     # "round-trip" | "two-one-ways"
        "ranked":       List[Candidate]
    }
    """
    if not candidates:
        return {"winner": None, "best_rt": None, "best_two_ow": None,
                "savings": 0.0, "savings_vs": "", "ranked": []}

    winner = candidates[0]
    best_rt = best_round_trip(candidates)
    best_ow = best_two_one_ways(candidates)

    if best_rt and best_ow:
        if winner["type"] == "round-trip":
            savings = round(max(best_ow["effective_price"] - best_rt["effective_price"], 0.0), 2)
            savings_vs = "two-one-ways"
        else:
            savings = round(max(best_rt["effective_price"] - best_ow["effective_price"], 0.0), 2)
            savings_vs = "round-trip"
    else:
        savings = 0.0
        savings_vs = ""

    return {
        "winner":      winner,
        "best_rt":     best_rt,
        "best_two_ow": best_ow,
        "savings":     savings,
        "savings_vs":  savings_vs,
        "ranked":      candidates,
    }


def format_report(result: dict, depart_date: str, return_date: str,
                  origin_label: str = "", dest_label: str = "") -> str:
    """Render the analysis dict as a human-readable console report."""
    bags_active = cfg.carry_on_bag or cfg.checked_bag
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    ranked = result["ranked"]
    winner = result["winner"]

    price_col = "EFF.PRICE" if bags_active else "PRICE"
    route_title = f"{origin_label} → {dest_label}" if origin_label and dest_label else "Flight Price Report"

    lines = [
        "",
        f"=== {route_title} ===",
        f"Depart: {depart_date}  |  Return: {return_date}",
        f"Fetched: {now}  |  Source: Google Flights (SerpAPI)",
    ]
    if bags_active:
        bag_types = []
        if cfg.carry_on_bag:
            bag_types.append("carry-on")
        if cfg.checked_bag:
            bag_types.append("checked bag")
        lines.append(f"Baggage: {', '.join(bag_types)} fees included in effective price")
    lines += [
        "─" * 72,
        f"{'RANK':<5} {'TYPE':<15} {'ROUTE':<22} {price_col:>10}  {'BAGS':>6}  {'STOPS':>5}  {'SCORE':>8}",
        "─" * 72,
    ]

    for i, c in enumerate(ranked[:10], start=1):
        eff_str = f"${c['effective_price']:,.2f}"
        bags_str = f"${c['baggage_cost']:,.0f}" if c["baggage_cost"] > 0 else "incl."
        score_str = f"${c['score']:,.2f}"
        stops_str = str(c["total_stops"])
        lines.append(
            f" #{i:<4} {c['type']:<15} {c['label']:<22} {eff_str:>10}  {bags_str:>6}  "
            f"{stops_str:>5}  {score_str:>8}"
        )

    lines.append("─" * 72)

    if winner:
        lines.append("")
        winner_label = "WINNER: " + ("Round-trip" if winner["type"] == "round-trip" else "Two one-ways")
        lines.append(winner_label)

        ob = winner["outbound"]
        lines.append(
            f"  Outbound : {ob.get('airline', '?'):<12}  {ob['origin']}→{ob['destination']}  "
            f"${ob['price_usd']:>7,.2f}  {ob['stops']} stop{'s' if ob['stops'] != 1 else ''}  "
            f"{_fmt_duration(ob.get('duration_mins'))}"
        )

        if winner["type"] == "two-one-ways":
            ret = winner["return"]
            lines.append(
                f"  Return   : {ret.get('airline', '?'):<12}  {ret['origin']}→{ret['destination']}  "
                f"${ret['price_usd']:>7,.2f}  {ret['stops']} stop{'s' if ret['stops'] != 1 else ''}  "
                f"{_fmt_duration(ret.get('duration_mins'))}"
            )
            lines.append(f"  Listed   : ${winner['listed_price']:,.2f}")
        else:
            lines.append(f"  Listed   : ${winner['listed_price']:,.2f}")

        if winner["baggage_cost"] > 0:
            lines.append(f"  Bags     : +${winner['baggage_cost']:,.2f}")
        lines.append(f"  Effective: ${winner['effective_price']:,.2f}  ← what you pay")

        vs = result["savings_vs"]
        opp = result["best_two_ow"] if vs == "two-one-ways" else result["best_rt"]
        if opp and result["savings"] > 0:
            opp_label = "two one-ways" if vs == "two-one-ways" else "round-trip"
            lines.append(
                f"  vs Best {opp_label}: ${opp['effective_price']:,.2f} ({opp['label']})"
            )
            lines.append(f"  Savings  : ${result['savings']:,.2f} (effective price)")
        elif opp:
            lines.append("  (Winner chosen by score; effective prices are close)")

        if winner["type"] == "two-one-ways" and not winner["airports_match"]:
            ob_dest = winner["outbound"]["destination"]
            ret_orig = winner["return"]["origin"]
            lines.append(
                f"\n  Note: Arrive {ob_dest}, depart from {ret_orig} — different airports."
            )

        # Booking links
        lines.append("")
        if winner["type"] == "round-trip":
            url = ob.get("booking_url")
            if url:
                lines.append(f"  Book now  → {url}")
            else:
                lines.append("  Book on Google Flights: https://www.google.com/flights")
        else:
            ret = winner["return"]
            ob_url  = ob.get("booking_url")
            ret_url = ret.get("booking_url")
            if ob_url:
                lines.append(f"  Book outbound → {ob_url}")
            if ret_url:
                lines.append(f"  Book return   → {ret_url}")
            if not ob_url and not ret_url:
                lines.append("  Book on Google Flights: https://www.google.com/flights")

    lines.append("")
    return "\n".join(lines)


def _fmt_duration(mins: Optional[int]) -> str:
    if not mins:
        return "--"
    h, m = divmod(mins, 60)
    return f"{h}h {m:02d}m"
