from __future__ import annotations

import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
DEFAULT_DB_PATH = DATA_DIR / "travel_model.sqlite3"
SCHEMA_PATH = BASE_DIR / "schema.sql"


def get_connection(db_path: Path | str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_database(db_path: Path | str = DEFAULT_DB_PATH) -> None:
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    with get_connection(db_path) as conn:
        conn.executescript(schema)


def ensure_auth_schema(db_path: Path | str = DEFAULT_DB_PATH) -> None:
    with get_connection(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        trip_request_columns = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(trip_requests)").fetchall()
        }
        if trip_request_columns and "user_id" not in trip_request_columns:
            conn.execute(
                "ALTER TABLE trip_requests ADD COLUMN user_id INTEGER REFERENCES users(id) ON DELETE SET NULL"
            )


def database_ready(db_path: Path | str = DEFAULT_DB_PATH) -> bool:
    path = Path(db_path)
    if not path.exists():
        return False
    try:
        with get_connection(path) as conn:
            row = conn.execute("SELECT COUNT(*) AS count FROM countries").fetchone()
            return bool(row and row["count"])
    except sqlite3.Error:
        return False


def table_counts(db_path: Path | str = DEFAULT_DB_PATH) -> dict[str, int]:
    tables = [
        "countries",
        "travel_options",
        "lodging_rates",
        "local_transport_costs",
        "activity_costs",
        "food_costs",
        "trip_requests",
    ]
    with get_connection(db_path) as conn:
        return {
            table: conn.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()["count"]
            for table in tables
        }
