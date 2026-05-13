"""
SQLite persistence layer.
Creates the schema on first use. All functions accept/return plain dicts.
"""

import json
import sqlite3
from datetime import datetime
from typing import List, Optional
from config import cfg


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(cfg.db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create tables if they don't exist."""
    with _connect() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS flights (
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

            CREATE TABLE IF NOT EXISTS runs (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                run_at          TEXT NOT NULL,
                depart_date     TEXT NOT NULL,
                return_date     TEXT NOT NULL,
                winner_type     TEXT,
                winner_price    REAL,
                winner_json     TEXT
            );
        """)


def save_flights(flights: List[dict]) -> None:
    """Bulk-insert a list of Flight dicts."""
    if not flights:
        return
    with _connect() as conn:
        conn.executemany(
            """
            INSERT INTO flights
                (scraped_at, origin, destination, date, return_date, trip_type,
                 airline, price_usd, stops, duration_mins,
                 departure_time, arrival_time, raw_json)
            VALUES
                (:scraped_at, :origin, :destination, :date, :return_date, :trip_type,
                 :airline, :price_usd, :stops, :duration_mins,
                 :departure_time, :arrival_time, :raw_json)
            """,
            [_serialize(f) for f in flights],
        )


def save_run(depart_date: str, return_date: str, analysis: dict) -> None:
    """Record the winner from one full orchestration run."""
    winner = analysis.get("winner")
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO runs (run_at, depart_date, return_date, winner_type, winner_price, winner_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.utcnow().isoformat(),
                depart_date,
                return_date,
                winner["type"] if winner else None,
                winner["total_price"] if winner else None,
                json.dumps(winner, default=str) if winner else None,
            ),
        )


def lowest_price_seen(origin: str, destination: str,
                       depart_date: str, trip_type: str) -> Optional[float]:
    """Return the all-time lowest scraped price for a specific route + date."""
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT MIN(price_usd) AS low
            FROM flights
            WHERE origin = ? AND destination = ? AND date = ? AND trip_type = ?
            """,
            (origin, destination, depart_date, trip_type),
        ).fetchone()
        return row["low"] if row else None


def recent_runs(limit: int = 10) -> List[dict]:
    """Fetch the most recent run summaries."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM runs ORDER BY run_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


def _serialize(flight: dict) -> dict:
    """Add raw_json field before inserting."""
    out = dict(flight)
    out["raw_json"] = json.dumps(flight, default=str)
    return out
