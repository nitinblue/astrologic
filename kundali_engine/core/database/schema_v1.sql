-- Person / Trader profile
CREATE TABLE IF NOT EXISTS person (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    dob TEXT NOT NULL,
    tob TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    timezone TEXT DEFAULT 'UTC'
);

-- Natal planetary placements
CREATE TABLE IF NOT EXISTS natal_planet (
    person_id INTEGER NOT NULL,
    planet TEXT NOT NULL,
    sign TEXT NOT NULL,
    house INTEGER NOT NULL,
    strength REAL DEFAULT 1.0,
    PRIMARY KEY (person_id, planet),
    FOREIGN KEY (person_id) REFERENCES person(id)
);

-- Dasha periods
CREATE TABLE IF NOT EXISTS dasha (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id INTEGER NOT NULL,
    level TEXT CHECK(level IN ('maha','antar','pratyantar')),
    planet TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    FOREIGN KEY (person_id) REFERENCES person(id)
);

-- Cached daily astro regime (VERY IMPORTANT for backtesting)
CREATE TABLE IF NOT EXISTS astro_regime_snapshot (
    person_id INTEGER,
    date TEXT,
    directional_bias TEXT,
    volatility_bias TEXT,
    risk_multiplier REAL,
    allowed_strategies TEXT,
    favored_sectors TEXT,
    explanation TEXT,
    PRIMARY KEY (person_id, date)
);
