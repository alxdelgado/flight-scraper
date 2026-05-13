"""
FastAPI server — wraps the flight-scraper engine as a REST API.

Endpoints:
  POST /search          → start async search, returns search_id
  GET  /search/{id}     → poll status + results
  GET  /airports        → resolve airport query
  GET  /history         → recent search winners
  GET  /health          → Render health check (DB connectivity)

Run locally:
    uvicorn server:app --reload --port 8000

Render start command (set in render.yaml):
    uvicorn server:app --host 0.0.0.0 --port $PORT
"""

import logging
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator

from airports import resolve, AIRPORTS
from api_client import search as api_search
from config import cfg
from price_optimizer import build_candidates, analyze
from storage import init_db, save_flights, save_run, recent_runs

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Flight Price Optimizer",
    description="Finds the best rate across all trip structures.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# In-memory search state — keyed by search_id.
# Replaced by a DB-backed table in a future iteration.
_searches: dict = {}

# Thread pool for running blocking SerpAPI calls without blocking the event loop.
_executor = ThreadPoolExecutor(max_workers=4)


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class SearchRequest(BaseModel):
    origin: str
    destination: str
    depart_date: str
    return_date: Optional[str] = None
    max_destinations: int = cfg.max_destinations

    @field_validator("origin", "destination")
    @classmethod
    def strip_and_upper(cls, v: str) -> str:
        return v.strip()

    @field_validator("depart_date", "return_date")
    @classmethod
    def validate_date(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Date must be YYYY-MM-DD")
        return v


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

@app.on_event("startup")
def on_startup() -> None:
    init_db()
    logger.info("Database initialised.")


# ---------------------------------------------------------------------------
# POST /search
# ---------------------------------------------------------------------------

@app.post("/search", status_code=202)
async def create_search(req: SearchRequest) -> dict:
    """
    Kick off an async flight search. Returns a search_id immediately.
    Poll GET /search/{search_id} for status and results.
    """
    # Resolve origin — must be a single airport
    try:
        origin_codes = resolve(req.origin)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"origin: {e}")

    if len(origin_codes) > 1:
        raise HTTPException(
            status_code=422,
            detail=f"origin '{req.origin}' matched multiple airports: {origin_codes}. "
                   f"Use a single IATA code (e.g. {origin_codes[0]}).",
        )
    origin = origin_codes[0]

    # Resolve destinations
    try:
        destinations = resolve(req.destination)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"destination: {e}")

    # Cap destinations
    if len(destinations) > req.max_destinations:
        destinations = destinations[:req.max_destinations]

    # Remove origin from destinations if present
    destinations = [d for d in destinations if d != origin]
    if not destinations:
        raise HTTPException(
            status_code=422,
            detail="No valid destination airports after resolving query.",
        )

    total_sessions = len(destinations) * (3 if req.return_date else 1)
    search_id = str(uuid.uuid4())
    _searches[search_id] = {
        "search_id":           search_id,
        "status":              "running",
        "origin":              origin,
        "destination":         req.destination,
        "depart_date":         req.depart_date,
        "return_date":         req.return_date,
        "completed_sessions":  0,
        "total_sessions":      total_sessions,
        "winner":              None,
        "ranked":              None,
        "error":               None,
        "started_at":          datetime.now(timezone.utc).isoformat(),
    }

    # Run the search in a thread so the event loop stays free
    import asyncio
    asyncio.create_task(
        run_in_threadpool(
            _run_search, search_id, origin, destinations,
            req.depart_date, req.return_date,
        )
    )

    return {
        "search_id":      search_id,
        "status":         "running",
        "total_sessions": total_sessions,
    }


# ---------------------------------------------------------------------------
# GET /search/{search_id}
# ---------------------------------------------------------------------------

@app.get("/search/{search_id}")
async def get_search(search_id: str) -> dict:
    """Poll for search status. Returns partial progress while running, full results when complete."""
    state = _searches.get(search_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Search not found.")
    return state


# ---------------------------------------------------------------------------
# GET /airports
# ---------------------------------------------------------------------------

@app.get("/airports")
async def get_airports(q: Optional[str] = None) -> dict:
    """
    Resolve an airport query string to a list of Airport objects.
    If q is omitted, returns all airports grouped by region.
    """
    if not q:
        grouped: dict = {}
        for iata, ap in AIRPORTS.items():
            grouped.setdefault(ap.region, []).append(_airport_dict(iata, ap))
        return {"grouped": grouped}

    try:
        codes = resolve(q)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return {
        "query":    q,
        "airports": [_airport_dict(c, AIRPORTS[c]) for c in codes if c in AIRPORTS],
    }


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------

@app.get("/health")
async def health_check() -> dict:
    """
    Render health check endpoint. Returns 200 when the service is up.
    Attempts a lightweight DB query to surface connectivity issues early.
    """
    db_status = "ok"
    try:
        await run_in_threadpool(recent_runs, 1)
    except Exception as exc:
        logger.warning("Health check DB query failed: %s", exc)
        db_status = "error"

    return {
        "status":  "ok" if db_status == "ok" else "degraded",
        "db":      db_status,
        "version": "1.0.0",
    }


# ---------------------------------------------------------------------------
# GET /history
# ---------------------------------------------------------------------------

@app.get("/history")
async def get_history(limit: int = 20) -> dict:
    """Return the most recent search winners from the database."""
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=422, detail="limit must be between 1 and 100.")
    runs = recent_runs(limit)
    return {"runs": runs}


# ---------------------------------------------------------------------------
# Background search worker
# ---------------------------------------------------------------------------

def _run_search(
    search_id: str,
    origin: str,
    destinations: list,
    depart_date: str,
    return_date: Optional[str],
) -> None:
    """
    Blocking function — runs in a thread via run_in_threadpool.
    Executes all SerpAPI sessions and updates _searches[search_id] in place.
    """
    state = _searches[search_id]
    round_trips: list = []
    outbound_one_ways: list = []
    return_one_ways: list = []

    try:
        for airport in destinations:
            if return_date:
                flights = api_search(origin=origin, destination=airport,
                                     depart_date=depart_date, trip_type="round-trip",
                                     return_date=return_date)
                round_trips.extend(flights[:cfg.results_per_search])
                save_flights(flights[:cfg.results_per_search])
                state["completed_sessions"] += 1

            flights = api_search(origin=origin, destination=airport,
                                 depart_date=depart_date, trip_type="one-way")
            outbound_one_ways.extend(flights[:cfg.results_per_search])
            save_flights(flights[:cfg.results_per_search])
            state["completed_sessions"] += 1

            if return_date:
                flights = api_search(origin=airport, destination=origin,
                                     depart_date=return_date, trip_type="one-way")
                return_one_ways.extend(flights[:cfg.results_per_search])
                save_flights(flights[:cfg.results_per_search])
                state["completed_sessions"] += 1

        candidates = build_candidates(round_trips, outbound_one_ways, return_one_ways)
        result = analyze(candidates)
        save_run(depart_date, return_date or "", result)

        state["status"] = "complete"
        state["winner"] = _serialise_candidate(result.get("winner"))
        state["ranked"] = [_serialise_candidate(c) for c in result.get("ranked", [])[:10]]

    except Exception as exc:
        logger.exception("Search %s failed: %s", search_id, exc)
        state["status"] = "failed"
        state["error"] = str(exc)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _airport_dict(iata: str, ap) -> dict:
    return {
        "iata":             iata,
        "name":             ap.name,
        "city":             ap.city,
        "subdivision":      ap.subdivision,
        "country":          ap.country,
        "region":           ap.region,
        "is_international": ap.is_international,
    }


def _serialise_candidate(c: Optional[dict]) -> Optional[dict]:
    """Strip non-JSON-serialisable keys before sending over the wire."""
    if c is None:
        return None
    return {
        "type":             c.get("type"),
        "label":            c.get("label"),
        "listed_price":     c.get("listed_price"),
        "baggage_cost":     c.get("baggage_cost"),
        "effective_price":  c.get("effective_price"),
        "total_stops":      c.get("total_stops"),
        "total_duration":   c.get("total_duration"),
        "score":            c.get("score"),
        "airports_match":   c.get("airports_match"),
        "outbound":         _serialise_flight(c.get("outbound")),
        "return":           _serialise_flight(c.get("return")),
        "savings":          None,   # populated at top level from analyze()
        "savings_vs":       None,
    }


def _serialise_flight(f: Optional[dict]) -> Optional[dict]:
    if f is None:
        return None
    return {
        "origin":         f.get("origin"),
        "destination":    f.get("destination"),
        "date":           f.get("date"),
        "return_date":    f.get("return_date"),
        "trip_type":      f.get("trip_type"),
        "airline":        f.get("airline"),
        "price_usd":      f.get("price_usd"),
        "stops":          f.get("stops"),
        "duration_mins":  f.get("duration_mins"),
        "departure_time": f.get("departure_time"),
        "arrival_time":   f.get("arrival_time"),
        "booking_url":    f.get("booking_url"),
    }
