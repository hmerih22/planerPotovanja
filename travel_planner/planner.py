from __future__ import annotations

import json
import math
from dataclasses import dataclass
from typing import Any

from travel_planner.db import get_connection

MONTHS = [
    ("1", "Januar"),
    ("2", "Februar"),
    ("3", "Marec"),
    ("4", "April"),
    ("5", "Maj"),
    ("6", "Junij"),
    ("7", "Julij"),
    ("8", "Avgust"),
    ("9", "September"),
    ("10", "Oktober"),
    ("11", "November"),
    ("12", "December"),
]

PREFERENCES = [
    ("balanced", "Uravnoteženo"),
    ("culture", "Kultura"),
    ("nature", "Narava"),
]

FOOD_STYLES = [
    ("mixed", "Mešano"),
    ("restaurant", "Restavracije"),
    ("fastfood", "Fast food"),
    ("grocery", "Trgovine"),
]

TRAVEL_MODES = [
    ("cheapest", "Najcenejša pot"),
    ("flight_ljubljana", "Letalo iz Ljubljane"),
    ("flight_zagreb", "Letalo iz Zagreba"),
    ("road", "Cestni prevoz"),
    ("train", "Vlak"),
    ("bus", "Avtobus"),
]

LOCAL_TRANSPORT_MODES = [
    ("cheapest", "Najcenejši lokalni prevoz"),
    ("public", "Javni prevoz"),
    ("walk", "Peš"),
    ("bike", "Kolo / e-kolo"),
    ("car", "Najem avta"),
    ("taxi", "Taxi"),
]

MODEL_WEIGHTS = [
    ("travel", "Pot do destinacije", 25),
    ("lodging", "Prenočišča", 25),
    ("food", "Prehrana", 15),
    ("activities", "Aktivnosti", 20),
    ("local_transport", "Lokalni prevoz", 10),
    ("budget", "Proračun", 30),
]


CRITERION_WEIGHTS = {
    "budget": 0.80,
    "travel": 0.05,
    "lodging": 0.05,
    "food": 0.04,
    "activities": 0.04,
    "local_transport": 0.02,
}


@dataclass(frozen=True)
class TripConfig:
    days: int
    nights: int
    persons: int
    month: int
    preference: str
    food_style: str
    travel_mode: str
    local_transport_mode: str
    budget_eur: float | None
    weights: dict[str, float]


def choice_label(choices: list[tuple[str, str]], value: str | int) -> str:
    value = str(value)
    return next((label for key, label in choices if key == value), value)


def parse_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def parse_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(str(value).replace(",", "."))
    except ValueError:
        return None


def clamp(number: int, lower: int, upper: int) -> int:
    return max(lower, min(upper, number))


def parse_weights(form: Any) -> dict[str, float]:
    weights: dict[str, float] = {}
    for key, _label, default in MODEL_WEIGHTS:
        value = parse_float(form.get(f"weight_{key}"))
        if value is None:
            value = float(default)
        weights[key] = float(max(0, min(100, value)))

    if not any(weights.values()):
        return {key: float(default) for key, _label, default in MODEL_WEIGHTS}
    return weights


def parse_trip_config(form: Any) -> TripConfig:
    days = clamp(parse_int(form.get("days"), 4), 1, 30)
    persons = clamp(parse_int(form.get("persons"), 2), 1, 5)
    month = clamp(parse_int(form.get("month"), 6), 1, 12)
    nights = max(days - 1, 1)

    preference = form.get("preference", "balanced")
    if preference not in dict(PREFERENCES):
        preference = "balanced"

    food_style = form.get("food_style", "mixed")
    if food_style not in dict(FOOD_STYLES):
        food_style = "mixed"

    travel_mode = form.get("travel_mode", "cheapest")
    if travel_mode not in dict(TRAVEL_MODES):
        travel_mode = "cheapest"

    local_transport_mode = form.get("local_transport_mode", "cheapest")
    if local_transport_mode not in dict(LOCAL_TRANSPORT_MODES):
        local_transport_mode = "cheapest"

    budget = parse_float(form.get("budget_eur"))
    if budget is not None and budget <= 0:
        budget = None

    return TripConfig(
        days=days,
        nights=nights,
        persons=persons,
        month=month,
        preference=preference,
        food_style=food_style,
        travel_mode=travel_mode,
        local_transport_mode=local_transport_mode,
        budget_eur=budget,
        weights=parse_weights(form),
    )


def food_daily_cost(food: dict[str, Any], style: str) -> tuple[float, str]:
    if style == "restaurant":
        return float(food["restaurant_daily_eur"]), "Restavracije"
    if style == "fastfood":
        return float(food["fastfood_daily_eur"]), "Fast food"
    if style == "grocery":
        return float(food["grocery_daily_eur"]), "Trgovine"
    mixed = (
        float(food["restaurant_daily_eur"]) * 0.4
        + float(food["fastfood_daily_eur"]) * 0.35
        + float(food["grocery_daily_eur"]) * 0.25
    )
    return mixed, "Mešano"


def activity_daily_cost(activity: dict[str, Any], preference: str) -> tuple[float, str]:
    culture = float(activity["culture_daily_eur"])
    nature = float(activity["nature_daily_eur"])
    if preference == "culture":
        return culture, "Kulturne aktivnosti"
    if preference == "nature":
        return nature, "Naravne aktivnosti"
    return (culture + nature) / 2, "Uravnotežene aktivnosti"


def travel_option_total(option: dict[str, Any], persons: int) -> float:
    multiplier = persons if option["price_scope"] == "person" else 1
    return float(option["cost_eur"]) * multiplier


def choose_travel_option(
    options: list[dict[str, Any]], config: TripConfig
) -> dict[str, Any] | None:
    candidates: list[dict[str, Any]] = []
    for option in options:
        if config.travel_mode != "cheapest" and option["mode"] != config.travel_mode:
            continue
        if option["month"] is not None and int(option["month"]) != config.month:
            continue

        candidates.append(
            {
                "mode": option["mode"],
                "label": option["label"],
                "cost": travel_option_total(option, config.persons),
                "source_note": option["source_note"],
            }
        )

    if not candidates:
        return None
    return min(candidates, key=lambda item: item["cost"])


def local_transport_candidates(
    transport: dict[str, Any], persons: int, days: int
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    public_values = [
        transport.get("bus_daily_eur"),
        transport.get("tram_daily_eur"),
        transport.get("metro_daily_eur"),
        transport.get("train_daily_eur"),
    ]
    available_public = [float(value) for value in public_values if value is not None]
    if available_public:
        candidates.append(
            {
                "mode": "public",
                "label": "Javni prevoz",
                "cost": min(available_public) * persons * days,
                "score_penalty": 0,
            }
        )

    if transport.get("bike_daily_eur") is not None:
        candidates.append(
            {
                "mode": "bike",
                "label": "Kolo / e-kolo",
                "cost": float(transport["bike_daily_eur"]) * persons * days,
                "score_penalty": 0,
            }
        )

    if transport.get("rental_car_daily_eur") is not None:
        candidates.append(
            {
                "mode": "car",
                "label": "Najem avta",
                "cost": float(transport["rental_car_daily_eur"]) * days,
                "score_penalty": 0,
            }
        )

    if transport.get("taxi_10km_eur") is not None:
        candidates.append(
            {
                "mode": "taxi",
                "label": "Taxi",
                "cost": float(transport["taxi_10km_eur"]) * 2 * days,
                "score_penalty": 0,
            }
        )

    walkability = transport.get("walkability_score")
    if walkability is not None:
        score = float(walkability)
        penalty = max(0.0, 4 - score) * 25
        candidates.append(
            {
                "mode": "walk",
                "label": f"Peš, ocena {score:g}/5",
                "cost": 0.0,
                "score_penalty": penalty,
            }
        )

    return candidates


def choose_local_transport(
    transport: dict[str, Any], config: TripConfig
) -> dict[str, Any] | None:
    candidates = local_transport_candidates(transport, config.persons, config.days)
    if config.local_transport_mode != "cheapest":
        candidates = [
            item for item in candidates if item["mode"] == config.local_transport_mode
        ]
    else:
        paid = [item for item in candidates if item["mode"] != "walk"]
        candidates = paid or candidates

    if not candidates:
        return None
    return min(candidates, key=lambda item: item["cost"] + item["score_penalty"])


def load_country_inputs(conn) -> list[dict[str, Any]]:
    countries = conn.execute("SELECT id, name FROM countries ORDER BY name").fetchall()
    output: list[dict[str, Any]] = []

    for country in countries:
        country_id = country["id"]
        lodging_rows = conn.execute(
            "SELECT persons, nightly_cost_eur FROM lodging_rates WHERE country_id = ?",
            (country_id,),
        ).fetchall()
        lodging = {row["persons"]: float(row["nightly_cost_eur"]) for row in lodging_rows}

        food = conn.execute(
            "SELECT * FROM food_costs WHERE country_id = ?", (country_id,)
        ).fetchone()
        activity = conn.execute(
            "SELECT * FROM activity_costs WHERE country_id = ?", (country_id,)
        ).fetchone()
        transport = conn.execute(
            "SELECT * FROM local_transport_costs WHERE country_id = ?", (country_id,)
        ).fetchone()
        travel_options = conn.execute(
            "SELECT * FROM travel_options WHERE country_id = ?", (country_id,)
        ).fetchall()

        if not (lodging and food and activity and transport and travel_options):
            continue

        output.append(
            {
                "id": country_id,
                "name": country["name"],
                "lodging": lodging,
                "food": dict(food),
                "activity": dict(activity),
                "transport": dict(transport),
                "travel_options": [dict(row) for row in travel_options],
            }
        )

    return output


def _build_recommendations_legacy(config: TripConfig, limit: int = 3) -> list[dict[str, Any]]:
    with get_connection() as conn:
        country_inputs = load_country_inputs(conn)

    recommendations: list[dict[str, Any]] = []
    for item in country_inputs:
        nightly_rate = item["lodging"].get(config.persons)
        travel = choose_travel_option(item["travel_options"], config)
        local_transport = choose_local_transport(item["transport"], config)
        if nightly_rate is None or travel is None or local_transport is None:
            continue

        lodging_total = float(nightly_rate) * config.nights
        food_daily, food_label = food_daily_cost(item["food"], config.food_style)
        food_total = food_daily * config.persons * config.days
        activity_daily, activity_label = activity_daily_cost(
            item["activity"], config.preference
        )
        activity_total = activity_daily * config.persons * config.days
        local_transport_total = float(local_transport["cost"])
        travel_total = float(travel["cost"])
        total = (
            travel_total
            + lodging_total
            + food_total
            + activity_total
            + local_transport_total
        )
        budget_delta = None
        if config.budget_eur is not None:
            budget_delta = config.budget_eur - total

        score = total + float(local_transport.get("score_penalty", 0))

        components = {
            "Pot do destinacije": travel_total,
            "Prenočišča": lodging_total,
            "Prehrana": food_total,
            "Aktivnosti": activity_total,
            "Lokalni prevoz": local_transport_total,
        }

        recommendations.append(
            {
                "country_id": item["id"],
                "country": item["name"],
                "total": total,
                "score": score,
                "budget_delta": budget_delta,
                "travel_label": travel["label"],
                "travel_source": travel["source_note"],
                "local_transport_label": local_transport["label"],
                "food_label": food_label,
                "activity_label": activity_label,
                "components": components,
            }
        )

    selected = select_recommendations(recommendations, config, limit)
    for index, row in enumerate(selected, start=1):
        row["rank"] = index
    return selected


def _select_recommendations_legacy(
    recommendations: list[dict[str, Any]], config: TripConfig, limit: int
) -> list[dict[str, Any]]:
    if config.budget_eur is None:
        return sorted(recommendations, key=lambda row: row["score"])[:limit]

    over_budget = [
        row
        for row in recommendations
        if row["budget_delta"] is not None and row["budget_delta"] < 0
    ]
    if over_budget:
        return sorted(
            over_budget,
            key=lambda row: (abs(row["budget_delta"]), row["score"]),
        )[:limit]

    return sorted(
        recommendations,
        key=lambda row: (
            row["budget_delta"] if row["budget_delta"] is not None else float("inf"),
            row["score"],
        ),
    )[:limit]


def normalize(value: float, minimum: float, maximum: float) -> float:
    if maximum == minimum:
        return 0.0
    return (value - minimum) / (maximum - minimum)


def active_model_weights(config: TripConfig) -> dict[str, float]:
    weights = dict(config.weights)
    if config.budget_eur is None:
        weights["budget"] = 0.0

    if not any(weights.values()):
        weights = {key: float(default) for key, _label, default in MODEL_WEIGHTS}
        if config.budget_eur is None:
            weights["budget"] = 0.0
    return weights


def apply_weighted_model_scores(
    recommendations: list[dict[str, Any]], config: TripConfig
) -> None:
    if not recommendations:
        return

    component_keys = ["travel", "lodging", "food", "activities", "local_transport"]
    ranges = {}
    for key in component_keys:
        values = [row["component_values"][key] for row in recommendations]
        ranges[key] = (min(values), max(values))

    budget_penalties = []
    for row in recommendations:
        if config.budget_eur:
            penalty = max(0.0, row["total"] - config.budget_eur) / config.budget_eur
        else:
            penalty = 0.0
        row["budget_penalty"] = penalty
        budget_penalties.append(penalty)

    ranges["budget"] = (min(budget_penalties), max(budget_penalties))
    weights = active_model_weights(config)
    total_weight = sum(weights.values()) or 1.0
    labels = {key: label for key, label, _default in MODEL_WEIGHTS}

    for row in recommendations:
        normalized = {}
        for key in component_keys:
            minimum, maximum = ranges[key]
            normalized[key] = normalize(row["component_values"][key], minimum, maximum)

        minimum, maximum = ranges["budget"]
        normalized["budget"] = normalize(row["budget_penalty"], minimum, maximum)

        weighted_terms = []
        score = 0.0
        for key, weight in weights.items():
            normalized_value = normalized.get(key, 0.0)
            contribution = weight * normalized_value / total_weight
            score += contribution
            weighted_terms.append(
                {
                    "key": key,
                    "label": labels[key],
                    "weight": weight,
                    "normalized": normalized_value,
                    "contribution": contribution,
                }
            )

        row["model_score"] = score * 100
        row["normalized_scores"] = normalized
        row["weighted_terms"] = weighted_terms


def apply_price_criterion_scores(
    recommendations: list[dict[str, Any]], config: TripConfig
) -> None:
    if not recommendations:
        return

    totals = [row["total"] for row in recommendations]
    minimum_total = min(totals)
    maximum_total = max(totals)
    component_keys = ["travel", "lodging", "food", "activities", "local_transport"]
    component_ranges = {}
    for key in component_keys:
        values = [row["component_values"][key] for row in recommendations]
        component_ranges[key] = (min(values), max(values))

    for row in recommendations:
        if config.budget_eur:
            over_budget = max(0.0, row["total"] - config.budget_eur)
            under_budget = max(0.0, config.budget_eur - row["total"])
            budget_criterion = (2 * over_budget + under_budget) / config.budget_eur
            distance = abs(row["total"] - config.budget_eur)
            row["criterion_distance"] = distance
            row["criterion_label"] = (
                f"(2 * max(0, {row['total']:.0f} - {config.budget_eur:.0f}) "
                f"+ max(0, {config.budget_eur:.0f} - {row['total']:.0f})) / {config.budget_eur:.0f}"
            )
        else:
            budget_criterion = normalize(row["total"], minimum_total, maximum_total)
            row["criterion_distance"] = row["total"] - minimum_total
            row["criterion_label"] = "normaliziran skupni strošek"


        component_criteria = {}
        for key in component_keys:
            minimum, maximum = component_ranges[key]
            component_criteria[key] = normalize(
                row["component_values"][key], minimum, maximum
            )

        criterion = CRITERION_WEIGHTS["budget"] * budget_criterion
        weighted_terms = [
            {
                "key": "budget",
                "label": "Proračun",
                "weight": CRITERION_WEIGHTS["budget"],
                "normalized": budget_criterion,
                "contribution": CRITERION_WEIGHTS["budget"] * budget_criterion,
            }
        ]
        labels = {
            "travel": "Pot",
            "lodging": "Prenočišča",
            "food": "Prehrana",
            "activities": "Aktivnosti",
            "local_transport": "Lokalni prevoz",
        }
        for key in component_keys:
            contribution = CRITERION_WEIGHTS[key] * component_criteria[key]
            criterion += contribution
            weighted_terms.append(
                {
                    "key": key,
                    "label": labels[key],
                    "weight": CRITERION_WEIGHTS[key],
                    "normalized": component_criteria[key],
                    "contribution": contribution,
                }
            )

        row["model_score"] = criterion * 100
        row["criterion_value"] = criterion
        row["budget_criterion"] = budget_criterion
        row["component_criteria"] = component_criteria
        row["weighted_terms"] = weighted_terms


def select_recommendations(
    recommendations: list[dict[str, Any]], config: TripConfig, limit: int
) -> list[dict[str, Any]]:
    return sorted(
        recommendations,
        key=lambda row: (row.get("model_score", row["score"]), row["total"]),
    )[:limit]


def build_recommendations(config: TripConfig, limit: int = 3) -> list[dict[str, Any]]:
    with get_connection() as conn:
        country_inputs = load_country_inputs(conn)

    recommendations: list[dict[str, Any]] = []
    for item in country_inputs:
        nightly_rate = item["lodging"].get(config.persons)
        travel = choose_travel_option(item["travel_options"], config)
        local_transport = choose_local_transport(item["transport"], config)
        if nightly_rate is None or travel is None or local_transport is None:
            continue

        lodging_total = float(nightly_rate) * config.nights
        food_daily, food_label = food_daily_cost(item["food"], config.food_style)
        food_total = food_daily * config.persons * config.days
        activity_daily, activity_label = activity_daily_cost(
            item["activity"], config.preference
        )
        activity_total = activity_daily * config.persons * config.days
        local_transport_total = float(local_transport["cost"])
        travel_total = float(travel["cost"])
        total = (
            travel_total
            + lodging_total
            + food_total
            + activity_total
            + local_transport_total
        )
        budget_delta = None
        if config.budget_eur is not None:
            budget_delta = config.budget_eur - total

        component_values = {
            "travel": travel_total,
            "lodging": lodging_total,
            "food": food_total,
            "activities": activity_total,
            "local_transport": local_transport_total,
        }
        components = {
            "Pot do destinacije": travel_total,
            "Prenočišča": lodging_total,
            "Prehrana": food_total,
            "Aktivnosti": activity_total,
            "Lokalni prevoz": local_transport_total,
        }

        recommendations.append(
            {
                "country_id": item["id"],
                "country": item["name"],
                "total": total,
                "score": total + float(local_transport.get("score_penalty", 0)),
                "budget_delta": budget_delta,
                "travel_label": travel["label"],
                "travel_source": travel["source_note"],
                "local_transport_label": local_transport["label"],
                "food_label": food_label,
                "activity_label": activity_label,
                "components": components,
                "component_values": component_values,
            }
        )

    apply_price_criterion_scores(recommendations, config)
    selected = select_recommendations(recommendations, config, limit)
    for index, row in enumerate(selected, start=1):
        row["rank"] = index
    return selected


def save_trip_request(
    config: TripConfig, recommendations: list[dict[str, Any]], user_id: int | None = None
) -> int:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO trip_requests (
                days,
                nights,
                persons,
                user_id,
                month,
                preference,
                food_style,
                travel_mode,
                local_transport_mode,
                budget_eur
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                config.days,
                config.nights,
                config.persons,
                user_id,
                config.month,
                config.preference,
                config.food_style,
                config.travel_mode,
                config.local_transport_mode,
                config.budget_eur,
            ),
        )
        request_id = int(cursor.lastrowid)

        for row in recommendations:
            conn.execute(
                """
                INSERT INTO trip_recommendations (
                    request_id,
                    rank,
                    country_id,
                    total_cost_eur,
                    budget_delta_eur,
                    travel_label,
                    local_transport_label,
                    components_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    request_id,
                    row["rank"],
                    row["country_id"],
                    row["total"],
                    row["budget_delta"],
                    row["travel_label"],
                    row["local_transport_label"],
                    json.dumps(row["components"], ensure_ascii=False),
                ),
            )

        conn.commit()
        return request_id


def config_summary(config: TripConfig) -> dict[str, str]:
    return {
        "Dni": str(config.days),
        "Noči": str(config.nights),
        "Oseb": str(config.persons),
        "Mesec": choice_label(MONTHS, config.month),
        "Preference": choice_label(PREFERENCES, config.preference),
        "Prehrana": choice_label(FOOD_STYLES, config.food_style),
        "Pot": choice_label(TRAVEL_MODES, config.travel_mode),
        "Lokalni prevoz": choice_label(
            LOCAL_TRANSPORT_MODES, config.local_transport_mode
        ),
        "Proračun": "" if config.budget_eur is None else f"{math.ceil(config.budget_eur)} €",
    }
