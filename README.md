# Flight Price Optimizer

Finds the best rate for a flight by comparing every trip structure — round-trip tickets vs. two separate one-way tickets — across all relevant airports for your destination. Uses **Google Flights data via SerpAPI**, factors in airline baggage fees so the comparison reflects what you actually pay, and prints a **direct booking link** to Google Flights for each winning leg.

---

## How It Works

For any origin → destination pair the script runs up to three searches per destination airport:

1. **Round-trip** — one ticket covering both legs
2. **One-way outbound** — origin → destination
3. **One-way return** — destination → origin

It then builds every combination of outbound + return one-ways (including mixed-airport combos, e.g. fly into JFK, leave from LGA) and scores each candidate on **effective price** — listed fare plus any carry-on or checked bag fees for that airline. The lowest-scoring candidate wins, and the report prints a direct Google Flights booking link for each winning leg.

### Example output

```
=== Chicago (ORD) → New York (NYC) ===
Depart: 2026-06-15  |  Return: 2026-06-20
Fetched: 2026-06-01 14:22:10 UTC  |  Source: Google Flights (SerpAPI)
Baggage: carry-on fees included in effective price
────────────────────────────────────────────────────────────────────────
RANK  TYPE            ROUTE                   EFF.PRICE    BAGS  STOPS     SCORE
────────────────────────────────────────────────────────────────────────
 #1    two-one-ways    ORD→EWR / JFK→ORD         $312.00   incl.      0   $312.00
 #2    round-trip      ORD↔LGA                   $329.00   incl.      0   $329.00
 #3    two-one-ways    ORD→JFK / JFK→ORD         $341.00   incl.      0   $341.00
────────────────────────────────────────────────────────────────────────

WINNER: Two one-ways
  Outbound : United        ORD→EWR  $ 149.00  0 stops  2h 20m
  Return   : JetBlue       JFK→ORD  $ 163.00  0 stops  2h 55m
  Listed   : $312.00
  Effective: $312.00  ← what you pay
  vs Best round-trip: $329.00 (ORD↔LGA)
  Savings  : $17.00 (effective price)

  Note: Arrive EWR, depart from JFK — different airports.

  Book outbound → https://www.google.com/travel/flights?tfs=<token>
  Book return   → https://www.google.com/travel/flights?tfs=<token>
```

---

## Booking a Flight

At the end of every report, the winner section includes a direct link to Google Flights:

- **Round-trip winner** — one `Book now` link covering both legs
- **Two one-ways winner** — separate `Book outbound` and `Book return` links, each opening the exact flight on Google Flights

Links are generated from the `booking_token` (round-trips) or `departure_token` (one-ways) returned by SerpAPI. If a token is unavailable, the report falls back to a generic `google.com/flights` link.

> Prices on Google Flights are live — the fare shown in the report may differ slightly by the time you click through. Book promptly once you find a good rate.

---

## Requirements

- Python 3.11+
- [SerpAPI account](https://serpapi.com/) — free tier includes 100 searches/month; Basic plan ($50/mo) covers daily use (~270 searches/month)

---

## Installation

```bash
git clone https://github.com/alxdelgado/flight-scraper.git
cd flight-scraper

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

---

## Configuration

### 1. Set your SerpAPI key

Copy the example env file and add your key:

```bash
cp .env.example .env
```

Edit `.env`:

```
SERPAPI_KEY=your_actual_key_here
```

The key is loaded automatically on every run. Never commit `.env` — it is listed in `.gitignore`.

### 2. Tune scoring (optional)

Edit `config.py` to adjust:

| Setting | Default | Description |
|---|---|---|
| `stops_penalty_usd` | `$25` | Dollar penalty added per stop when ranking |
| `duration_penalty_usd` | `$0` | Dollar penalty per hour of travel (off by default) |
| `carry_on_bag` | `True` | Include carry-on fees in effective price |
| `checked_bag` | `False` | Include checked bag fees in effective price |
| `results_per_search` | `5` | Max results to pull per API call |
| `max_destinations` | `10` | Cap on destination airports before warning |

---

## Usage

```bash
python run.py --from <ORIGIN> --to <DESTINATION> --depart <DATE> [--return <DATE>]
```

### Arguments

| Argument | Required | Description |
|---|---|---|
| `--from` | Yes | Origin airport code or city name (resolves to a single airport) |
| `--to` | Yes | Destination — IATA code, metro alias, city name, or region name |
| `--depart` | Yes | Departure date in `YYYY-MM-DD` format |
| `--return` | No | Return date in `YYYY-MM-DD` format. Omit for one-way searches only |
| `--max-destinations` | No | Override the destination airport cap (default: 10) |
| `--list-airports` | No | Print all supported airports, metro codes, and region names, then exit |

### Destination formats

| Input | Resolves to | Sessions |
|---|---|---|
| `JFK` | Single airport | 3 |
| `NYC` | JFK, LGA, EWR | 9 |
| `Caribbean` | 42 airports (capped at 10 by default) | 30 |
| `Miami` | MIA, FLL, PBI | 9 |
| `Canada` | 16 airports (capped at 10 by default) | 30 |

---

## Examples

### Single airport, round-trip
```bash
python run.py --from ORD --to JFK --depart 2026-06-15 --return 2026-06-20
```

### Metro area — compares all NYC airports and mixed combos
```bash
python run.py --from ORD --to NYC --depart 2026-06-15 --return 2026-06-20
```

### City name
```bash
python run.py --from "Chicago" --to "Miami" --depart 2026-07-04 --return 2026-07-11
```

### International — Mexico
```bash
python run.py --from DFW --to CUN --depart 2026-07-04 --return 2026-07-11
```

### Region — Caribbean (top 10 airports by registry order)
```bash
python run.py --from MIA --to caribbean --depart 2026-12-20 --return 2026-12-27
```

### Region — expand cap to search all Caribbean airports
```bash
python run.py --from MIA --to caribbean --depart 2026-12-20 --return 2026-12-27 --max-destinations 42
```

### One-way only (no return date)
```bash
python run.py --from ORD --to LAX --depart 2026-06-15
```

### Canada
```bash
python run.py --from SEA --to canada --depart 2026-08-01 --return 2026-08-10
```

### List all supported airports, metro codes, and regions
```bash
python run.py --list-airports
```

---

## Scheduling (macOS cron)

Run automatically every 4 hours:

```bash
crontab -e
```

Add:

```
0 */4 * * * cd /path/to/flight-scraper && bash run.sh >> logs/scraper.log 2>&1
```

Results are stored in `data/flights.db` (SQLite) so every run's winner is saved for later comparison.

---

## Deploying to Render (hosted API)

The FastAPI backend can be deployed to Render's free tier in under 10 minutes using the included `render.yaml` Blueprint. This is required for the iOS app.

### Prerequisites

- [Render account](https://render.com) (free)
- GitHub repo connected to Render (fork or push `alxdelgado/flight-scraper`)
- SerpAPI key

### Steps

**1. Create a new Blueprint deployment**

Go to [dashboard.render.com](https://dashboard.render.com) → **New** → **Blueprint** → connect the `flight-scraper` repo. Render reads `render.yaml` and provisions both resources:

| Resource | Plan | Cost |
|---|---|---|
| `flight-price-optimizer` (web service) | Free | $0 |
| `flight-optimizer-db` (PostgreSQL) | Free | $0 |

**2. Set your SerpAPI key**

After the first deploy completes, go to:  
**Dashboard → flight-price-optimizer → Environment → Add environment variable**

```
Key:   SERPAPI_KEY
Value: your_actual_serpapi_key
```

Click **Save** — Render redeploys automatically.

**3. Verify the deployment**

```bash
curl https://flight-price-optimizer.onrender.com/health
# {"status":"ok","db":"ok","version":"1.0.0"}
```

**4. Test a search**

```bash
curl -X POST https://flight-price-optimizer.onrender.com/search \
  -H "Content-Type: application/json" \
  -d '{"origin":"ORD","destination":"NYC","depart_date":"2026-06-15","return_date":"2026-06-20"}'
# {"search_id":"...","status":"running","total_sessions":9}
```

### Free tier notes

- **Cold starts:** The free web service sleeps after 15 minutes of inactivity and takes ~30 seconds to wake. This is acceptable since searches take 2–5 minutes regardless.
- **PostgreSQL expiry:** Render free PostgreSQL databases expire after **90 days**. Before expiry, upgrade to the $7/month Starter plan or export and reimport the data.
- **Keep-warm option:** Use [UptimeRobot](https://uptimerobot.com) (free) to ping `/health` every 10 minutes and prevent cold starts.

---

## Supported Regions

| Region name | Airports | Countries |
|---|---|---|
| `northeast` | 20 | US |
| `southeast` | 24 | US |
| `midwest` | 22 | US |
| `southwest` | 18 | US |
| `west` | 31 | US |
| `canada` | 16 | Canada |
| `mexico` | 20 | Mexico |
| `puerto_rico` | 6 | US territory |
| `caribbean` | 42 | Bahamas, Jamaica, Cuba, DR, Haiti, USVI, Lesser Antilles, ABC islands |

Metro aliases: `NYC`, `CHI`, `LA`, `SF`, `DC`, `DAL`, `HOU`, `MIA`, `ORL`, `TOR`, `MTL`, `VAN`

---

## Project Structure

```
flight-scraper/
├── .env                  # Your SerpAPI key (never committed)
├── .env.example          # Safe template — commit this
├── .gitignore
├── README.md
├── requirements.txt
├── run.py                # Entry point — CLI args, orchestration
├── run.sh                # Shell wrapper for cron
├── airports.py           # 199-airport registry + resolve()
├── api_client.py         # Google Flights via SerpAPI
├── config.py             # Scoring, baggage fees, API settings
├── flight_parser.py      # HTML → Flight dict (Expedia fallback parser)
├── price_optimizer.py    # Core algorithm — scoring, ranking, report
├── scraper.py            # Playwright browser scraper (Expedia fallback)
├── storage.py            # SQLite persistence
├── data/
│   └── flights.db        # Run history (auto-created)
└── logs/
    └── scraper.log       # Run logs (auto-created)
```

---

## Notes

- **Google Flights prices include taxes and fees** — SerpAPI returns post-tax totals, which are more accurate than most travel site listings.
- **Baggage fees** are applied per airline per leg. Budget carriers (Spirit, Frontier) are automatically penalized when `carry_on_bag = True`, preventing misleadingly cheap results.
- **Mixed-airport combos** (e.g., fly into EWR, return from JFK) are flagged in the report. Factor in ground transfer costs (~$20–$50) before booking.
- **SerpAPI free tier** (100 searches/month) covers roughly one run per week for a 3-airport destination like NYC. For daily use, the Basic plan ($50/month) is needed.
