"""
Extracts structured Flight dicts from Expedia search result HTML.
All functions are pure (no browser dependency) — pass raw HTML strings.
"""

import re
from datetime import datetime, timezone
from typing import List, Optional
from bs4 import BeautifulSoup


Flight = dict  # type alias for clarity


def parse_duration(text: str) -> Optional[int]:
    """Convert '2h 55m' or '6h 10m' to total minutes. Returns None if unparseable."""
    match = re.search(r"(?:(\d+)h)?\s*(?:(\d+)m)?", text.strip())
    if not match:
        return None
    hours = int(match.group(1) or 0)
    mins = int(match.group(2) or 0)
    total = hours * 60 + mins
    return total if total > 0 else None


def parse_price(text: str) -> Optional[float]:
    """Convert '$189', '1,234', or '$1,234.56' to float. Returns None if unparseable."""
    cleaned = re.sub(r"[^\d.]", "", text)
    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_stops(text: str) -> int:
    """Convert 'Nonstop', '1 stop', '2 stops' to int."""
    text = text.strip().lower()
    if "nonstop" in text or "direct" in text:
        return 0
    match = re.search(r"(\d+)\s*stop", text)
    return int(match.group(1)) if match else 0


def parse_time(text: str) -> Optional[str]:
    """Normalize time strings like '7:00 AM', '09:22' to 'HH:MM' 24h format."""
    text = text.strip().upper()
    for fmt in ("%I:%M %p", "%I:%M%p", "%H:%M"):
        try:
            return datetime.strptime(text, fmt).strftime("%H:%M")
        except ValueError:
            continue
    return None


def parse_flight_cards(html: str, origin: str, destination: str,
                        trip_type: str, date: str,
                        return_date: Optional[str] = None) -> List[Flight]:
    """
    Parse all flight result cards from an Expedia search results page.

    Expedia renders results as <div> cards. This targets the data attributes
    and text patterns present in their current DOM structure.

    Args:
        html:         Raw HTML of the Expedia results page.
        origin:       e.g. "ORD"
        destination:  e.g. "JFK"
        trip_type:    "round-trip" or "one-way"
        date:         Departure date "YYYY-MM-DD"
        return_date:  Return date "YYYY-MM-DD" (round-trip only)

    Returns:
        List of Flight dicts, sorted by price ascending.
    """
    soup = BeautifulSoup(html, "html.parser")
    flights: List[Flight] = []
    scraped_at = datetime.now(timezone.utc).isoformat()

    # Expedia wraps each result in a section with data-test-id="offer-listing"
    # or inside li elements under the results list. We cast a wide net.
    cards = (
        soup.find_all("div", {"data-test-id": "offer-listing"})
        or soup.find_all("li", class_=re.compile(r"uitk-layout-grid-item"))
        or soup.find_all("div", class_=re.compile(r"flight-module"))
    )

    for card in cards:
        flight = _extract_card(card, origin, destination, trip_type,
                               date, return_date, scraped_at)
        if flight:
            flights.append(flight)

    flights.sort(key=lambda f: f["price_usd"] or float("inf"))
    return flights


def _extract_card(card, origin: str, destination: str, trip_type: str,
                  date: str, return_date: Optional[str], scraped_at: str) -> Optional[Flight]:
    """Extract one Flight dict from a single result card element."""
    text = card.get_text(separator=" ", strip=True)

    # Price — look for dollar amounts
    price_el = (
        card.find(attrs={"data-test-id": re.compile(r"price")})
        or card.find(class_=re.compile(r"price"))
        or card.find(string=re.compile(r"\$\d"))
    )
    price_text = price_el.get_text() if hasattr(price_el, "get_text") else str(price_el or "")
    price = parse_price(price_text)
    if price is None:
        # Fall back: scan all text for first dollar amount
        match = re.search(r"\$[\d,]+(?:\.\d{2})?", text)
        price = parse_price(match.group(0)) if match else None

    if not price:
        return None  # skip cards with no parseable price

    # Airline
    airline_el = (
        card.find(attrs={"data-test-id": re.compile(r"airline|carrier")})
        or card.find(class_=re.compile(r"airline|carrier"))
    )
    airline = airline_el.get_text(strip=True) if airline_el else _extract_airline_from_text(text)

    # Duration
    duration_el = card.find(string=re.compile(r"\d+h\s*\d*m?", re.I))
    duration_text = duration_el.strip() if duration_el else ""
    duration_mins = parse_duration(duration_text)

    # Stops
    stops_el = card.find(string=re.compile(r"nonstop|\d+\s*stop", re.I))
    stops_text = stops_el.strip() if stops_el else ""
    stops = parse_stops(stops_text)

    # Departure and arrival times
    times = re.findall(r"\b\d{1,2}:\d{2}\s*(?:AM|PM)?\b", text, re.I)
    departure_time = parse_time(times[0]) if len(times) > 0 else None
    arrival_time = parse_time(times[1]) if len(times) > 1 else None

    return {
        "origin": origin,
        "destination": destination,
        "date": date,
        "return_date": return_date,
        "trip_type": trip_type,
        "airline": airline,
        "price_usd": price,
        "stops": stops,
        "duration_mins": duration_mins,
        "departure_time": departure_time,
        "arrival_time": arrival_time,
        "scraped_at": scraped_at,
    }


def _extract_airline_from_text(text: str) -> Optional[str]:
    """Best-effort airline name extraction from card text."""
    known = [
        "United", "American", "Delta", "Southwest", "JetBlue",
        "Spirit", "Frontier", "Alaska", "Sun Country", "Breeze",
    ]
    for name in known:
        if name.lower() in text.lower():
            return name
    return None
