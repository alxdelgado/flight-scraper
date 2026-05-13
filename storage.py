"""
Persistence layer — PostgreSQL in production, SQLite for local development.

Backend selection:
  DATABASE_URL set  → psycopg2 / PostgreSQL (Render production)
  DATABASE_URL unset → sqlite3 (local dev, no setup required)

All public functions accept and return plain Python dicts.
"""

import json
import logging
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Generator, List, Optional

from config import cfg

logger = logging.getLogger(__name__)

_DATABASE_URL: str = os.getenv("DATABASE_URL", "")
_POSTGRES: bool = bool(_DATABASE_URL)

if _POSTGRES:
    logger.info("Storage backend: PostgreSQL")
else:
    logger.info("Storage backend: SQLite (%s)", cfg.db_path)


# ---------------------------------------------------------------------------
# SQL dialect helpers
# ---------------------------------------------------------------------------

def _p(key: str) -> str:
    """Named parameter placeholder for the active backend."""
    return f"%({key})s" if _POSTGRES else f":{key}"


def _pos() -> str:
    """Positional parameter placeholder for the active backend."""
    return "%s" if _POSTGRES else "?"


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

_ID_COL = "SERIAL PRIMARY KEY" if _POSTGRES else "INTEGER PRIMARY KEY AUTOINCREMENT"

_FLIGHTS_DDL = f"""
    CREATE TABLE IF NOT EXISTS flights (
        id              {_ID_COL},
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
    )
"""

_RUNS_DDL = f"""
    CREATE TABLE IF NOT EXISTS runs (
        id              {_ID_COL},
        run_at          TEXT NOT NULL,
        depart_date     TEXT NOT NULL,
        return_date     TEXT NOT NULL,
        winner_type     TEXT,
        winner_price    REAL,
        winner_json     TEXT
    )
"""


# ---------------------------------------------------------------------------
# Connection context manager
# ---------------------------------------------------------------------------

@contextmanager
def _cursor() -> Generator:
    """
    Yield a cursor for the active backend.
    Commits on clean exit, rolls back on exception, always closes connection.
    """
    if _POSTGRES:
        try:
            import psycopg2
            import psycopg2.extras
        except ImportError:
            raise RuntimeError(
                "psycopg2-binary is required for PostgreSQL. "
                "Run: pip install psycopg2-binary"
            )
        conn = psycopg2.connect(_DATABASE_URL,
                                cursor_factory=psycopg2.extras.RealDictCursor)
        cur = conn.cursor()
        try:
            yield cur
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()
    else:
        conn = sqlite3.connect(cfg.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        try:
            yield cur
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()


def _to_dict(row) -> dict:
    """Normalise a row from either backend into a plain dict."""
    if row is None:
        return {}
    if isinstance(row, dict):
        return row
    return dict(row)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def init_db() -> None:
    """Create tables if they don't exist."""
    with _cursor() as cur:
        cur.execute(_FLIGHTS_DDL)
        cur.execute(_RUNS_DDL)


def save_flights(flights: List[dict]) -> None:
    """Bulk-insert a list of Flight dicts."""
    if not flights:
        return
    sql = f"""
        INSERT INTO flights
            (scraped_at, origin, destination, date, return_date, trip_type,
             airline, price_usd, stops, duration_mins,
             departure_time, arrival_time, raw_json)
        VALUES
            ({_p('scraped_at')}, {_p('origin')}, {_p('destination')}, {_p('date')},
             {_p('return_date')}, {_p('trip_type')}, {_p('airline')}, {_p('price_usd')},
             {_p('stops')}, {_p('duration_mins')}, {_p('departure_time')},
             {_p('arrival_time')}, {_p('raw_json')})
    """
    with _cursor() as cur:
        cur.executemany(sql, [_serialize(f) for f in flights])


def save_run(depart_date: str, return_date: str, analysis: dict) -> None:
    """Record the winner from one full orchestration run."""
    winner = analysis.get("winner")
    sql = f"""
        INSERT INTO runs
            (run_at, depart_date, return_date, winner_type, winner_price, winner_json)
        VALUES
            ({_pos()}, {_pos()}, {_pos()}, {_pos()}, {_pos()}, {_pos()})
    """
    with _cursor() as cur:
        cur.execute(sql, (
            datetime.now(timezone.utc).isoformat(),
            depart_date,
            return_date,
            winner["type"] if winner else None,
            winner.get("effective_price") if winner else None,
            json.dumps(winner, default=str) if winner else None,
        ))


def lowest_price_seen(origin: str, destination: str,
                      depart_date: str, trip_type: str) -> Optional[float]:
    """Return the all-time lowest scraped price for a specific route + date."""
    sql = f"""
        SELECT MIN(price_usd) AS low
        FROM flights
        WHERE origin = {_pos()} AND destination = {_pos()}
          AND date = {_pos()} AND trip_type = {_pos()}
    """
    with _cursor() as cur:
        cur.execute(sql, (origin, destination, depart_date, trip_type))
        row = cur.fetchone()
        return _to_dict(row).get("low") if row else None


def recent_runs(limit: int = 10) -> List[dict]:
    """Fetch the most recent run summaries."""
    sql = f"SELECT * FROM runs ORDER BY run_at DESC LIMIT {_pos()}"
    with _cursor() as cur:
        cur.execute(sql, (limit,))
        return [_to_dict(r) for r in cur.fetchall()]


def _serialize(flight: dict) -> dict:
    """Add raw_json field before inserting."""
    out = dict(flight)
    out["raw_json"] = json.dumps(flight, default=str)
    return out
