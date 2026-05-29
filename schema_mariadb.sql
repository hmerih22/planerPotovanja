CREATE TABLE IF NOT EXISTS countries (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS travel_options (
    id INT AUTO_INCREMENT PRIMARY KEY,
    country_id INT NOT NULL,
    mode VARCHAR(50) NOT NULL,
    label VARCHAR(100) NOT NULL,
    month INT NULL,
    cost_eur DECIMAL(10,2) NOT NULL,
    price_scope VARCHAR(50) NOT NULL,
    source_note TEXT NULL,
    FOREIGN KEY (country_id) REFERENCES countries(id)
);

CREATE TABLE IF NOT EXISTS lodging_rates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    country_id INT NOT NULL,
    persons INT NOT NULL,
    nightly_cost_eur DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (country_id) REFERENCES countries(id)
);

CREATE TABLE IF NOT EXISTS local_transport_costs (
    country_id INT PRIMARY KEY,
    bus_daily_eur DECIMAL(10,2) NULL,
    tram_daily_eur DECIMAL(10,2) NULL,
    metro_daily_eur DECIMAL(10,2) NULL,
    train_daily_eur DECIMAL(10,2) NULL,
    taxi_10km_eur DECIMAL(10,2) NULL,
    rental_car_daily_eur DECIMAL(10,2) NULL,
    bike_daily_eur DECIMAL(10,2) NULL,
    walkability_score DECIMAL(4,2) NULL,
    FOREIGN KEY (country_id) REFERENCES countries(id)
);

CREATE TABLE IF NOT EXISTS activity_costs (
    country_id INT PRIMARY KEY,
    culture_daily_eur DECIMAL(10,2) NOT NULL,
    nature_daily_eur DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (country_id) REFERENCES countries(id)
);

CREATE TABLE IF NOT EXISTS food_costs (
    country_id INT PRIMARY KEY,
    restaurant_daily_eur DECIMAL(10,2) NOT NULL,
    fastfood_daily_eur DECIMAL(10,2) NOT NULL,
    grocery_daily_eur DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (country_id) REFERENCES countries(id)
);

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    email VARCHAR(180) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS trip_requests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    days INT NOT NULL,
    nights INT NOT NULL,
    persons INT NOT NULL,
    month INT NOT NULL,
    preference VARCHAR(50) NOT NULL,
    food_style VARCHAR(50) NOT NULL,
    travel_mode VARCHAR(50) NOT NULL,
    local_transport_mode VARCHAR(50) NOT NULL,
    budget_eur DECIMAL(10,2) NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS trip_recommendations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    request_id INT NOT NULL,
    rank INT NOT NULL,
    country_id INT NOT NULL,
    total_cost_eur DECIMAL(10,2) NOT NULL,
    budget_delta_eur DECIMAL(10,2) NULL,
    travel_label VARCHAR(100) NOT NULL,
    local_transport_label VARCHAR(100) NOT NULL,
    components_json TEXT NOT NULL,
    FOREIGN KEY (request_id) REFERENCES trip_requests(id),
    FOREIGN KEY (country_id) REFERENCES countries(id)
);