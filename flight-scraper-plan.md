# Flight Scraper — Project Plan

## Overview

A Python script that scrapes Expedia.com for flight prices between Chicago O'Hare (ORD) and New York City (JFK, LGA, EWR), runs on a cron schedule, and determines the best rate by comparing all trip structures: round-trip tickets vs. two separate one-way tickets, including mixed-airport combinations.

**Key question the algorithm answers:** Is buying a round-trip ticket cheaper than combining two one-way tickets — and does flying into one NYC airport and out of another save money?

---

## Scope (v1)

- Origin: Chicago O'Hare (ORD)
- Destinations: JFK, LGA, EWR (all NYC-area airports)
- Trip types: round-trip, one-way outbound, one-way return
- Algorithm: price + stop-penalty scoring across all 12 candidate combinations
- Storage: SQLite for historical run data
- Output: ranked report printed to console + saved to log
- Scheduler: macOS crontab

**Out of scope for v1:** email notifications, price threshold alerts, UI, hotel/car bundling.

---

## The Algorithm

### Candidate Trip Structures

For any travel window (depart `D1`, return `D2`), there are 12 candidates:

```
Round-Trips (3):
  ORD ↔ JFK
  ORD ↔ LGA
  ORD ↔ EWR

Two One-Ways — same airport (3):
  [ORD→JFK] + [JFK→ORD]
  [ORD→LGA] + [LGA→ORD]
  [ORD→EWR] + [EWR→ORD]

Two One-Ways — mixed airports (6):
  [ORD→JFK] + [LGA→ORD]
  [ORD→JFK] + [EWR→ORD]
  [ORD→LGA] + [JFK→ORD]
  [ORD→LGA] + [EWR→ORD]
  [ORD→EWR] + [JFK→ORD]
  [ORD→EWR] + [LGA→ORD]
```

### Scoring Formula

```
score = price_usd + (stops_penalty × total_stops)
```

- `stops_penalty` = $25/stop (configurable in `config.py`)
- Duration penalty is available but off by default
- Lower score = better deal
- Candidates ranked ascending by score

### Scraping Sessions Per Run

| # | Type | Route |
|---|------|-------|
| 1 | Round-trip | ORD ↔ JFK |
| 2 | Round-trip | ORD ↔ LGA |
| 3 | Round-trip | ORD ↔ EWR |
| 4 | One-way outbound | ORD → JFK |
| 5 | One-way outbound | ORD → LGA |
| 6 | One-way outbound | ORD → EWR |
| 7 | One-way return | JFK/LGA/EWR → ORD |

7 sessions total per run. Sessions run sequentially with randomized delays to reduce bot detection risk.

---

## Data Model

### Flight Dict (in-memory)

```python
{
    "origin":           str,   # "ORD"
    "destination":      str,   # "JFK"
    "date":             str,   # "YYYY-MM-DD"
    "return_date":      str,   # "YYYY-MM-DD" or None
    "trip_type":        str,   # "round-trip" | "one-way"
    "airline":          str,
    "price_usd":        float,
    "stops":            int,
    "duration_mins":    int,
    "departure_time":   str,   # "HH:MM"
    "arrival_time":     str,   # "HH:MM"
    "scraped_at":       str    # ISO timestamp
}
```

### SQLite Schema

```sql
CREATE TABLE flights (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    scraped_at      TEXT NOT NULL,
    origin          TEXT NOT NULL,
    destination     TEXT NOT NULL,
    date            TEXT NOT NULL,
    return_date     TEXT,
    trip_type       TEXT NOT NULL,
    airline         TEXT,
    price_usd       REAL,
    stops           INTEGER,
    duration_mins   INTEGER,
    departure_time  TEXT,
    arrival_time    TEXT,
    raw_json        TEXT
);

CREATE TABLE runs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    run_at          TEXT NOT NULL,
    depart_date     TEXT NOT NULL,
    return_date     TEXT NOT NULL,
    winner_type     TEXT,
    winner_price    REAL,
    winner_json     TEXT
);
```

---

## Sample Output

```
=== Flight Price Report: ORD → NYC ===
Depart: 2026-06-15  |  Return: 2026-06-20
Scraped: 2026-05-12 10:04:21
──────────────────────────────────────────────────────────────────
RANK  TYPE            ROUTE              PRICE    STOPS  SCORE
 #1   Two one-ways    ORD→EWR / JFK→ORD  $312.00    1   $337.00
 #2   Round-trip      ORD↔LGA            $329.00    0   $329.00
 #3   Two one-ways    ORD→JFK / JFK→ORD  $341.00    0   $341.00
 #4   Round-trip      ORD↔JFK            $359.00    1   $384.00
──────────────────────────────────────────────────────────────────

WINNER: Two one-ways
  Outbound : Spirit  ORD→EWR  $149.00  1 stop   6h 10m
  Return   : JetBlue JFK→ORD  $163.00  0 stops  2h 55m
  Total    : $312.00
  vs Best RT: $329.00 (United ORD↔LGA, nonstop)
  Savings  : $17.00 buying two one-ways

  Note: Arrive EWR, depart from JFK — different NYC airports.
```

---

## File Structure

```
flight-scraper/
├── flight-scraper-plan.md   # this file
├── config.py                # origin, destinations, dates, penalty weights
├── parser.py                # DOM HTML → list[Flight dict]
├── scraper.py               # Playwright browser session for one search
├── price_optimizer.py       # Core algorithm: combos, scoring, ranking
├── storage.py               # SQLite read/write
├── run.py                   # Orchestrator: runs all 7 sessions → report
├── requirements.txt         # Python dependencies
├── run.sh                   # Shell wrapper for cron
├── logs/
│   └── scraper.log
└── data/
    └── flights.db
```

---

## Build Order

| Step | File | Purpose |
|------|------|---------|
| 1 | `config.py` | Route config, date params, penalty weights |
| 2 | `parser.py` | HTML → Flight dicts (unit-testable, no browser needed) |
| 3 | `price_optimizer.py` | Full ranking algorithm |
| 4 | `storage.py` | SQLite schema + insert/query helpers |
| 5 | `scraper.py` | Playwright session for one Expedia search |
| 6 | `run.py` | Orchestrates all 7 sessions + prints report |
| 7 | `requirements.txt` + `run.sh` | Dependencies + cron shell wrapper |

---

## Dependencies

```
playwright          # Browser automation
playwright-stealth  # Reduce bot detection
```

Install:
```bash
pip install playwright playwright-stealth
playwright install chromium
```

---

## Cron Setup (macOS)

Edit crontab with `crontab -e`, add:

```bash
# Run every 4 hours
0 */4 * * * cd /Users/alexdelgado/flight-scraper && bash run.sh >> logs/scraper.log 2>&1
```

---

## Important Notes

1. **Expedia ToS:** Automated scraping may violate Expedia's Terms of Service. Use for personal research only. An alternative is the [Amadeus Flights API](https://developers.amadeus.com/) (free tier available), which is legal and stable.
2. **Bot detection:** Expedia uses Cloudflare and dynamic JavaScript. `playwright-stealth` reduces detection risk but is not a guarantee. If blocked, sessions will fail gracefully and log the error.
3. **Mixed-airport combos:** A mixed-airport result is only actionable if traveling within NYC between the two airports is acceptable (e.g., EWR→JFK costs ~$20–40 by transit/rideshare). The algorithm does not yet factor in inter-airport transfer cost — noted as a v2 enhancement.
