from __future__ import annotations

import sqlite3
from typing import Any

from werkzeug.security import check_password_hash, generate_password_hash

from travel_planner.db import ensure_auth_schema, get_connection


def normalize_email(email: str) -> str:
    return email.strip().lower()


def create_user(name: str, email: str, password: str) -> tuple[bool, str]:
    name = name.strip()
    email = normalize_email(email)

    if len(name) < 2:
        return False, "Ime naj ima vsaj 2 znaka."
    if "@" not in email or "." not in email:
        return False, "Vpiši veljaven email."
    if len(password) < 6:
        return False, "Geslo naj ima vsaj 6 znakov."

    ensure_auth_schema()
    try:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO users (name, email, password_hash)
                VALUES (?, ?, ?)
                """,
                (name, email, generate_password_hash(password)),
            )
        return True, "Račun je ustvarjen. Zdaj se lahko prijaviš."
    except sqlite3.IntegrityError:
        return False, "Ta email je že registriran."


def authenticate_user(email: str, password: str) -> dict[str, Any] | None:
    ensure_auth_schema()
    with get_connection() as conn:
        user = conn.execute(
            "SELECT id, name, email, password_hash FROM users WHERE email = ?",
            (normalize_email(email),),
        ).fetchone()

    if user and check_password_hash(user["password_hash"], password):
        return {"id": user["id"], "name": user["name"], "email": user["email"]}
    return None


def get_user(user_id: int | None) -> dict[str, Any] | None:
    if user_id is None:
        return None
    ensure_auth_schema()
    with get_connection() as conn:
        user = conn.execute(
            "SELECT id, name, email FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
    return dict(user) if user else None
