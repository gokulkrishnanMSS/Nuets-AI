-- Schema for the Nuets Food AI Service.
-- Runs once, on first start of an empty data volume.

-- Nutrition lookup table, populated by load_to_postgres.py from the ingredient CSV.
CREATE TABLE IF NOT EXISTS nutrition_data (
    id              SERIAL PRIMARY KEY,
    ingredient      TEXT UNIQUE,
    calories_kcal   REAL,
    protein_g       REAL,
    fat_g           REAL,
    carbs_g         REAL,
    fiber_g         REAL,
    sugar_g         REAL,
    calcium_mg      REAL,
    iron_mg         REAL,
    sodium_mg       REAL,
    potassium_mg    REAL,
    vitamin_c_mg    REAL,
    cholesterol_mg  REAL
);

-- fetch_nutrition() matches with ILIKE '%ingredient%'; this index keeps that
-- lookup fast once the table grows. pg_trgm ships with the official image.
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE INDEX IF NOT EXISTS nutrition_data_ingredient_trgm_idx
    ON nutrition_data USING gin (ingredient gin_trgm_ops);

-- Scan history written by FoodService.save_scan_result().
CREATE TABLE IF NOT EXISTS scan_results (
    id             SERIAL PRIMARY KEY,
    result         TEXT,
    ingredients    JSONB,
    nutrition_info JSONB,
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- /food/scans orders by created_at DESC.
CREATE INDEX IF NOT EXISTS scan_results_created_at_idx
    ON scan_results (created_at DESC);
