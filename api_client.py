"""
Google Flights data via SerpAPI.

SerpAPI's `google_flights` engine queries Google Flights and returns clean JSON
including taxes and fees — more accurate than Expedia's pre-tax listings.

Requires:
    pip install google-search-results
    export SERPAPI_KEY="your_key_here"

Free tier: 100 searches/month
Basic plan: $50/month for 5,000 searches
  → 1 run/day × 9 sessions = ~270/month (Basic plan needed for daily use)
  → On-demand / weekly runs fit within the free tier.

SerpAPI docs: https://serpapi.com/google-flights-api
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional
from config import cfg

logger = logging.getLogger(__name__)

# SerpAPI trip type codes
_ROUND_TRIP = "1"
_ONE_WAY = "2"


def search(
    origin: str,
    destination: str,
    depart_date: str,
    trip_type: str = "round-trip",
    return_date: Optional[str] = None,
) -> List[dict]:
    """
    Query Google Flights via SerpAPI for one route + date combination.

    Args:
        origin:       IATA code e.g. "ORD"
        destination:  IATA code e.g. "JFK"
        depart_date:  "YYYY-MM-DD"
        trip_type:    "round-trip" or "one-way"
        return_date:  "YYYY-MM-DD" (required for round-trip)

    Returns:
        List of Flight dicts sorted by price ascending.
        Returns [] on API error or missing key — caller checks for empty result.
    """
    if not cfg.serpapi_key:
        logger.error(
            "SERPAPI_KEY is not set. Export it: export SERPAPI_KEY='your_key'"
        )
        return []

    try:
        from serpapi import GoogleSearch
    except ImportError:
        logger.error(
            "google-search-results not installed. Run: pip install google-search-results"
        )
        return []

    params = {
        "engine":         "google_flights",
        "departure_id":   origin,
        "arrival_id":     destination,
        "outbound_date":  depart_date,
        "type":           _ROUND_TRIP if trip_type == "round-trip" else _ONE_WAY,
        "adults":         "1",
        "currency":       "USD",
        "hl":             "en",
        "api_key":        cfg.serpapi_key,
    }

    if trip_type == "round-trip" and return_date:
        params["return_date"] = return_date

    logger.info(
        "SerpAPI request: %s → %s (%s) on %s", origin, destination, trip_type, depart_date
    )

    try:
        results = GoogleSearch(params).get_dict()
    except Exception as exc:
        logger.error("SerpAPI error on %s→%s: %s", origin, destination, exc)
        return []

    if "error" in results:
        logger.error("SerpAPI returned error for %s→%s: %s", origin, destination, results["error"])
        return []

    raw_flights = results.get("best_flights", []) + results.get("other_flights", [])
    flights = [
        _parse_flight(f, origin, destination, trip_type, depart_date, return_date)
        for f in raw_flights
    ]
    flights = [f for f in flights if f is not None]
    flights.sort(key=lambda f: f["price_usd"])

    logger.info("SerpAPI returned %d flights for %s→%s", len(flights), origin, destination)
    return flights[:cfg.results_per_search]


def _parse_flight(
    raw: dict,
    origin: str,
    destination: str,
    trip_type: str,
    date: str,
    return_date: Optional[str],
) -> Optional[dict]:
    """Convert one SerpAPI flight result dict into a Flight dict."""
    price = raw.get("price")
    if price is None:
        return None

    segments = raw.get("flights", [])
    if not segments:
        return None

    # Stops = number of segments minus 1 (layovers between segments)
    stops = max(len(segments) - 1, len(raw.get("layovers", [])))

    # Primary airline = first segment's carrier
    airline = segments[0].get("airline", "Unknown")

    # Departure time from first segment; arrival from last
    dep_raw = segments[0].get("departure_airport", {}).get("time", "")
    arr_raw = segments[-1].get("arrival_airport", {}).get("time", "")
    departure_time = _normalize_time(dep_raw)
    arrival_time = _normalize_time(arr_raw)

    # SerpAPI provides total_duration in minutes
    duration_mins = raw.get("total_duration")

    return {
        "origin":         origin,
        "destination":    destination,
        "date":           date,
        "return_date":    return_date,
        "trip_type":      trip_type,
        "airline":        airline,
        "price_usd":      float(price),
        "stops":          stops,
        "duration_mins":  duration_mins,
        "departure_time": departure_time,
        "arrival_time":   arrival_time,
        "scraped_at":     datetime.now(timezone.utc).isoformat(),
        "source":         "google_flights",
    }


def _normalize_time(raw: str) -> Optional[str]:
    """Convert '8:00 AM', '11:30 PM' to 'HH:MM' 24h. Returns None if unparseable."""
    if not raw:
        return None
    raw = raw.strip().upper()
    for fmt in ("%I:%M %p", "%I:%M%p", "%H:%M"):
        try:
            return datetime.strptime(raw, fmt).strftime("%H:%M")
        except ValueError:
            continue
    return None
