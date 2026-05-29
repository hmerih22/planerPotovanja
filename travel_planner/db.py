from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any

import pymysql
from pymysql.cursors import DictCursor

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
DEFAULT_DB_PATH = DATA_DIR / "travel_model.sqlite3"
SCHEMA_PATH = BASE_DIR / "schema.sql"


def use_mariadb() -> bool:
    return bool(os.getenv("DB_HOST"))


def translate_sql(sql: str) -> str:
    if use_mariadb():
        return sql.replace("?", "%s")
    return sql


class MariaDBConnection:
    def __init__(self) -> None:
        self.connection = pymysql.connect(
            host=os.getenv("DB_HOST", "db"),
            port=int(os.getenv("DB_PORT", "3306")),
            user=os.getenv("DB_USER", "travel_user"),
            password=os.getenv("DB_PASSWORD", "travel_password"),
            database=os.getenv("DB_NAME", "travel_planner"),
            cursorclass=DictCursor,
            autocommit=False,
        )

    def execute(self, sql: str, params: tuple[Any, ...] | list[Any] = ()) -> Any:
        cursor = self.connection.cursor()
        cursor.execute(translate_sql(sql), params)
        return cursor

    def executemany(self, sql: str, params: list[tuple[Any, ...]]) -> Any:
        cursor = self.connection.cursor()
        cursor.executemany(translate_sql(sql), params)
        return cursor

    def commit(self) -> None:
        self.connection.commit()

    def rollback(self) -> None:
        self.connection.rollback()

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> "MariaDBConnection":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        if exc_type is None:
            self.commit()
        else:
            self.rollback()
        self.close()


def get_connection(db_path: Path | str = DEFAULT_DB_PATH):
    if use_mariadb():
        return MariaDBConnection()

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_database(db_path: Path | str = DEFAULT_DB_PATH) -> None:
    if use_mariadb():
        return

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

        if use_mariadb():
            return

        trip_request_columns = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(trip_requests)").fetchall()
        }
        if trip_request_columns and "user_id" not in trip_request_columns:
            conn.execute(
                "ALTER TABLE trip_requests ADD COLUMN user_id INTEGER REFERENCES users(id) ON DELETE SET NULL"
            )


def database_ready(db_path: Path | str = DEFAULT_DB_PATH) -> bool:
    try:
        with get_connection(db_path) as conn:
            row = conn.execute("SELECT COUNT(*) AS count FROM countries").fetchone()
            return bool(row and row["count"])
    except Exception:
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