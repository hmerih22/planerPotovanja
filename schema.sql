PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS trip_recommendations;
DROP TABLE IF EXISTS trip_requests;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS food_costs;
DROP TABLE IF EXISTS activity_costs;
DROP TABLE IF EXISTS local_transport_costs;
DROP TABLE IF EXISTS lodging_rates;
DROP TABLE IF EXISTS travel_options;
DROP TABLE IF EXISTS countries;

CREATE TABLE countries (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE travel_options (
    id INTEGER PRIMARY KEY,
    country_id INTEGER NOT NULL REFERENCES countries(id) ON DELETE CASCADE,
    mode TEXT NOT NULL,
    label TEXT NOT NULL,
    month INTEGER CHECK (month IS NULL OR month BETWEEN 1 AND 12),
    cost_eur REAL NOT NULL CHECK (cost_eur >= 0),
    price_scope TEXT NOT NULL CHECK (price_scope IN ('person', 'group')),
    source_note TEXT
);

CREATE INDEX idx_travel_options_country ON travel_options(country_id);
CREATE INDEX idx_travel_options_mode_month ON travel_options(mode, month);

CREATE TABLE lodging_rates (
    id INTEGER PRIMARY KEY,
    country_id INTEGER NOT NULL REFERENCES countries(id) ON DELETE CASCADE,
    persons INTEGER NOT NULL CHECK (persons BETWEEN 1 AND 5),
    nightly_cost_eur REAL NOT NULL CHECK (nightly_cost_eur >= 0),
    UNIQUE (country_id, persons)
);

CREATE TABLE local_transport_costs (
    country_id INTEGER PRIMARY KEY REFERENCES countries(id) ON DELETE CASCADE,
    bus_daily_eur REAL,
    tram_daily_eur REAL,
    metro_daily_eur REAL,
    train_daily_eur REAL,
    taxi_10km_eur REAL,
    rental_car_daily_eur REAL,
    bike_daily_eur REAL,
    walkability_score REAL CHECK (walkability_score IS NULL OR walkability_score BETWEEN 1 AND 5)
);

CREATE TABLE activity_costs (
    country_id INTEGER PRIMARY KEY REFERENCES countries(id) ON DELETE CASCADE,
    culture_daily_eur REAL NOT NULL CHECK (culture_daily_eur >= 0),
    nature_daily_eur REAL NOT NULL CHECK (nature_daily_eur >= 0)
);

CREATE TABLE food_costs (
    country_id INTEGER PRIMARY KEY REFERENCES countries(id) ON DELETE CASCADE,
    restaurant_daily_eur REAL NOT NULL CHECK (restaurant_daily_eur >= 0),
    fastfood_daily_eur REAL NOT NULL CHECK (fastfood_daily_eur >= 0),
    grocery_daily_eur REAL NOT NULL CHECK (grocery_daily_eur >= 0)
);

CREATE TABLE trip_requests (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    days INTEGER NOT NULL,
    nights INTEGER NOT NULL,
    persons INTEGER NOT NULL,
    month INTEGER NOT NULL,
    preference TEXT NOT NULL,
    food_style TEXT NOT NULL,
    travel_mode TEXT NOT NULL,
    local_transport_mode TEXT NOT NULL,
    budget_eur REAL
);

CREATE TABLE trip_recommendations (
    id INTEGER PRIMARY KEY,
    request_id INTEGER NOT NULL REFERENCES trip_requests(id) ON DELETE CASCADE,
    rank INTEGER NOT NULL,
    country_id INTEGER NOT NULL REFERENCES countries(id) ON DELETE CASCADE,
    total_cost_eur REAL NOT NULL,
    budget_delta_eur REAL,
    travel_label TEXT NOT NULL,
    local_transport_label TEXT NOT NULL,
    components_json TEXT NOT NULL
);
