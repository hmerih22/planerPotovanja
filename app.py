from __future__ import annotations

import json
import os
from functools import wraps
from pathlib import Path

from flask import Flask, flash, g, redirect, render_template, request, session, url_for

from travel_planner.auth import authenticate_user, create_user, get_user
from travel_planner.db import (
    DEFAULT_DB_PATH,
    database_ready,
    ensure_auth_schema,
    get_connection,
)
from travel_planner.importer import import_workbook
from travel_planner.planner import (
    FOOD_STYLES,
    LOCAL_TRANSPORT_MODES,
    MONTHS,
    PREFERENCES,
    TRAVEL_MODES,
    build_recommendations,
    config_summary,
    parse_trip_config,
    save_trip_request,
)


def ensure_application_database(app: Flask) -> None:
    workbook_path = Path(app.root_path) / "data" / "raw" / "travel_data.xlsx"
    if not database_ready():
        import_workbook(workbook_path, DEFAULT_DB_PATH)
    ensure_auth_schema()


def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("login"))
        return view(**kwargs)

    return wrapped_view


def load_selected_trip(request_id: int, rank: int, user_id: int):
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT
                tr.id AS request_id,
                rec.rank,
                c.name AS country,
                rec.total_cost_eur,
                rec.budget_delta_eur,
                rec.travel_label,
                rec.local_transport_label,
                rec.components_json
            FROM trip_recommendations AS rec
            JOIN trip_requests AS tr ON tr.id = rec.request_id
            JOIN countries AS c ON c.id = rec.country_id
            WHERE rec.request_id = ? AND rec.rank = ? AND tr.user_id = ?
            """,
            (request_id, rank, user_id),
        ).fetchone()

    if row is None:
        return None

    trip = dict(row)
    trip["components"] = json.loads(trip["components_json"])
    return trip


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get(
        "SECRET_KEY", "local-travel-planner-dev-secret"
    )

    @app.before_request
    def load_logged_in_user():
        ensure_application_database(app)
        g.user = get_user(session.get("user_id"))

    @app.template_filter("eur")
    def eur(value: float | None) -> str:
        if value is None:
            return "—"
        return f"{value:,.0f} €".replace(",", ".")

    @app.route("/")
    @login_required
    def index():
        return render_template(
            "index.html",
            months=MONTHS,
            preferences=PREFERENCES,
            food_styles=FOOD_STYLES,
            travel_modes=TRAVEL_MODES,
            local_transport_modes=LOCAL_TRANSPORT_MODES,
        )

    @app.route("/registracija", methods=("GET", "POST"))
    def register():
        if g.user is not None:
            return redirect(url_for("index"))

        if request.method == "POST":
            password = request.form.get("password", "")
            password_confirm = request.form.get("password_confirm", "")
            if password != password_confirm:
                flash("Gesli se ne ujemata.", "error")
            else:
                ok, message = create_user(
                    request.form.get("name", ""),
                    request.form.get("email", ""),
                    password,
                )
                flash(message, "success" if ok else "error")
                if ok:
                    return redirect(url_for("login"))

        return render_template("register.html")

    @app.route("/prijava", methods=("GET", "POST"))
    def login():
        if g.user is not None:
            return redirect(url_for("index"))

        if request.method == "POST":
            user = authenticate_user(
                request.form.get("email", ""),
                request.form.get("password", ""),
            )
            if user is None:
                flash("Email ali geslo ni pravilno.", "error")
            else:
                session.clear()
                session["user_id"] = user["id"]
                return redirect(url_for("index"))

        return render_template("login.html")

    @app.post("/odjava")
    def logout():
        session.clear()
        return redirect(url_for("login"))

    @app.post("/plan")
    @login_required
    def plan():
        config = parse_trip_config(request.form)
        recommendations = build_recommendations(config, limit=3)
        request_id = save_trip_request(config, recommendations, user_id=g.user["id"])
        return render_template(
            "results.html",
            request_id=request_id,
            summary=config_summary(config),
            recommendations=recommendations,
        )

    @app.get("/potovanje/<int:request_id>/<int:rank>")
    @login_required
    def selected_trip(request_id: int, rank: int):
        trip = load_selected_trip(request_id, rank, g.user["id"])
        if trip is None:
            flash("Izbranega potovanja ni bilo mogoče najti.", "error")
            return redirect(url_for("index"))
        return render_template("selected_trip.html", trip=trip)

    @app.post("/refresh-data")
    @login_required
    def refresh_data():
        import_workbook(Path(app.root_path) / "data" / "raw" / "travel_data.xlsx", DEFAULT_DB_PATH)
        ensure_auth_schema()
        return redirect(url_for("index"))

    return app


app = create_app()


if __name__ == "__main__":
    app.run(
    host=os.environ.get("FLASK_HOST", "127.0.0.1"),
    port=int(os.environ.get("FLASK_PORT", "5000")),
    debug=os.environ.get("FLASK_DEBUG", "1") == "1",
)
