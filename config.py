import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict

# Load .env from the project root (the directory this file lives in).
# Has no effect if python-dotenv is not installed or .env doesn't exist.
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass


@dataclass
class BaggageFee:
    carry_on: float   # USD, one-way
    checked: float    # USD, one-way


@dataclass
class Config:
    # Scoring penalties (dollar value added per unit — lower score = better)
    stops_penalty_usd: float = 25.0    # per stop
    duration_penalty_usd: float = 0.0  # per hour of total travel (off by default)

    # Baggage — set to True to include fees in effective price
    carry_on_bag: bool = True
    checked_bag: bool = False

    # Per-airline baggage fees (one-way rates; round-trip doubles automatically).
    # Fees reflect 2026 standard rates for one carry-on or one checked bag.
    baggage_fees: Dict[str, BaggageFee] = field(default_factory=lambda: {
        "Spirit":      BaggageFee(carry_on=79.00, checked=49.00),
        "Frontier":    BaggageFee(carry_on=69.00, checked=49.00),
        "Breeze":      BaggageFee(carry_on=45.00, checked=35.00),
        "Sun Country": BaggageFee(carry_on=35.00, checked=35.00),
        "Allegiant":   BaggageFee(carry_on=50.00, checked=50.00),
        # Mainline carriers include carry-on; checked bag fees below
        "United":      BaggageFee(carry_on=0.00, checked=40.00),
        "American":    BaggageFee(carry_on=0.00, checked=40.00),
        "Delta":       BaggageFee(carry_on=0.00, checked=35.00),
        "JetBlue":     BaggageFee(carry_on=0.00, checked=35.00),
        "Alaska":      BaggageFee(carry_on=0.00, checked=35.00),
        "Southwest":   BaggageFee(carry_on=0.00, checked=0.00),
    })

    # Google Flights via SerpAPI — set SERPAPI_KEY env var or override here
    serpapi_key: str = field(default_factory=lambda: os.getenv("SERPAPI_KEY", ""))
    results_per_search: int = 5

    # Warn when destination airport count exceeds this threshold
    # (each additional destination = 3 more API calls per run)
    max_destinations: int = 10

    # Paths
    db_path: str = "data/flights.db"
    log_path: str = "logs/scraper.log"


# Module-level singleton — import this everywhere
cfg = Config()
