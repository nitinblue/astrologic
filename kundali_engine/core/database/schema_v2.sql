-- =============================================================================
-- AstroLogic Database Schema v2
-- 39 tables across 7 categories
-- =============================================================================
-- Design: TEXT keys for planet/sign names, composite natural PKs,
--         JSON in TEXT columns for variable-length lists,
--         self-referencing FK for dasha hierarchy
-- =============================================================================

-- =============================================
-- CATEGORY 1: STATIC REFERENCE (15 tables)
-- Seeded once from Vedic Astrology classical texts
-- =============================================

-- 1. ref_sign: 12 zodiac signs
CREATE TABLE IF NOT EXISTS ref_sign (
    name        TEXT PRIMARY KEY,       -- 'Aries', 'Taurus', ...
    sign_number INTEGER NOT NULL UNIQUE,-- 1-12
    sanskrit    TEXT NOT NULL,
    symbol      TEXT,
    element     TEXT NOT NULL CHECK(element IN ('Fire','Earth','Air','Water')),
    modality    TEXT NOT NULL CHECK(modality IN ('Cardinal','Fixed','Mutable')),
    ruler       TEXT NOT NULL,          -- planet name
    gender      TEXT NOT NULL CHECK(gender IN ('Male','Female')),
    nature      TEXT NOT NULL CHECK(nature IN ('Cruel','Gentle')),
    degree_start REAL NOT NULL,         -- 0, 30, 60, ...
    degree_end  REAL NOT NULL           -- 30, 60, 90, ...
);

-- 2. ref_planet: 9 Vedic planets (grahas)
CREATE TABLE IF NOT EXISTS ref_planet (
    name            TEXT PRIMARY KEY,   -- 'Sun', 'Moon', ...
    sanskrit        TEXT NOT NULL,
    symbol          TEXT,
    nature          TEXT NOT NULL CHECK(nature IN ('Benefic','Malefic','Neutral')),
    gender          TEXT CHECK(gender IN ('Male','Female','Neutral')),
    element         TEXT,
    dasha_years     REAL NOT NULL,      -- Vimshottari duration
    avg_daily_motion REAL,              -- degrees/day
    naisargika_bala REAL,               -- natural strength (Shadbala component)
    dig_bala_house  INTEGER             -- house of max directional strength (1-12)
);

-- 3. ref_nakshatra: 27 lunar mansions
CREATE TABLE IF NOT EXISTS ref_nakshatra (
    name            TEXT PRIMARY KEY,   -- 'Ashwini', 'Bharani', ...
    nakshatra_number INTEGER NOT NULL UNIQUE, -- 1-27
    degree_start    REAL NOT NULL,      -- absolute sidereal degrees
    degree_end      REAL NOT NULL,
    ruler           TEXT NOT NULL,       -- dasha ruler planet
    deity           TEXT,
    nature          TEXT,
    signs           TEXT                -- JSON array of sign(s) it spans
);

-- 4. ref_dignity: exaltation and debilitation per planet
CREATE TABLE IF NOT EXISTS ref_dignity (
    planet          TEXT NOT NULL,
    dignity_type    TEXT NOT NULL CHECK(dignity_type IN ('exaltation','debilitation')),
    sign            TEXT NOT NULL,
    exact_degree    REAL,               -- NULL for Rahu/Ketu
    PRIMARY KEY (planet, dignity_type)
);

-- 5. ref_moolatrikona: moolatrikona sign + degree range per planet
CREATE TABLE IF NOT EXISTS ref_moolatrikona (
    planet          TEXT PRIMARY KEY,
    sign            TEXT NOT NULL,
    degree_start    REAL NOT NULL,
    degree_end      REAL NOT NULL
);

-- 6. ref_ownership: planet → sign ownership mapping
CREATE TABLE IF NOT EXISTS ref_ownership (
    sign            TEXT PRIMARY KEY,
    ruler           TEXT NOT NULL        -- planet that owns this sign
);

-- 7. ref_natural_relationship: 9x9 grid of naisargika relationships
CREATE TABLE IF NOT EXISTS ref_natural_relationship (
    planet          TEXT NOT NULL,
    other_planet    TEXT NOT NULL,
    relationship    TEXT NOT NULL CHECK(relationship IN ('Friend','Neutral','Enemy')),
    PRIMARY KEY (planet, other_planet)
);

-- 8. ref_aspect_rule: aspect offsets per planet
CREATE TABLE IF NOT EXISTS ref_aspect_rule (
    planet          TEXT NOT NULL,
    aspect_offset   INTEGER NOT NULL,   -- house distance (e.g. 7, 4, 8)
    strength        REAL NOT NULL DEFAULT 1.0, -- aspect strength (0.0-1.0)
    PRIMARY KEY (planet, aspect_offset)
);

-- 9. ref_house: house significations and group flags
CREATE TABLE IF NOT EXISTS ref_house (
    house_number    INTEGER PRIMARY KEY, -- 1-12
    sanskrit_name   TEXT NOT NULL,
    english_name    TEXT NOT NULL,
    core_domain     TEXT NOT NULL,
    is_kendra       INTEGER NOT NULL DEFAULT 0,  -- 1,4,7,10
    is_trikona      INTEGER NOT NULL DEFAULT 0,  -- 1,5,9
    is_upachaya     INTEGER NOT NULL DEFAULT 0,  -- 3,6,10,11
    is_dusthana     INTEGER NOT NULL DEFAULT 0,  -- 6,8,12
    is_maraka       INTEGER NOT NULL DEFAULT 0,  -- 2,7
    domain_group    TEXT CHECK(domain_group IN ('Dharma','Artha','Kama','Moksha'))
);

-- 10. ref_dasha_sequence: Vimshottari order + durations
CREATE TABLE IF NOT EXISTS ref_dasha_sequence (
    sequence_order  INTEGER PRIMARY KEY, -- 1-9
    planet          TEXT NOT NULL UNIQUE,
    years           REAL NOT NULL
);

-- 11. ref_ashtakavarga_rule: bindu contribution rules per contributor
CREATE TABLE IF NOT EXISTS ref_ashtakavarga_rule (
    contributor     TEXT PRIMARY KEY,    -- 'Sun','Moon',...,'Lagna'
    bindu_houses    TEXT NOT NULL        -- JSON array of house offsets
);

-- 12. ref_combustion_range: combustion degree thresholds
CREATE TABLE IF NOT EXISTS ref_combustion_range (
    planet          TEXT PRIMARY KEY,
    normal_range    REAL NOT NULL,       -- degrees from Sun
    retrograde_range REAL               -- different range when retrograde (NULL if same)
);

-- 13. ref_planet_sector: planet → market sector mapping
CREATE TABLE IF NOT EXISTS ref_planet_sector (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    planet          TEXT NOT NULL,
    sector          TEXT NOT NULL,
    affinity        TEXT DEFAULT 'primary' CHECK(affinity IN ('primary','secondary'))
);

-- 14. ref_planet_commodity: planet → commodity mapping
CREATE TABLE IF NOT EXISTS ref_planet_commodity (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    planet          TEXT NOT NULL,
    commodity       TEXT NOT NULL,
    affinity        TEXT DEFAULT 'primary' CHECK(affinity IN ('primary','secondary'))
);

-- 15. ref_strategy_class: trading strategy classification
CREATE TABLE IF NOT EXISTS ref_strategy_class (
    name            TEXT PRIMARY KEY,    -- 'momentum', 'mean_reversion', ...
    description     TEXT,
    favorable_planets TEXT,              -- JSON array
    unfavorable_planets TEXT             -- JSON array
);

-- =============================================
-- CATEGORY 2: PER-PERSON NATAL (11 tables)
-- Computed once from birth data, cached permanently
-- =============================================

-- 1. person (enhanced from v1)
CREATE TABLE IF NOT EXISTS person (
    id              INTEGER PRIMARY KEY,
    name            TEXT NOT NULL,
    dob             TEXT NOT NULL,       -- YYYY-MM-DD
    tob             TEXT NOT NULL,       -- HH:MM
    latitude        REAL NOT NULL,
    longitude       REAL NOT NULL,
    timezone        TEXT DEFAULT 'UTC',
    place_name      TEXT,
    ayanamsa        TEXT DEFAULT 'Lahiri',
    lagna_sign      TEXT,
    lagna_degree    REAL
);

-- 2. natal_planet (enhanced from v1)
CREATE TABLE IF NOT EXISTS natal_planet (
    person_id           INTEGER NOT NULL,
    planet              TEXT NOT NULL,
    sign                TEXT NOT NULL,
    house               INTEGER NOT NULL,
    sidereal_longitude  REAL,           -- absolute sidereal degrees (0-360)
    degree_in_sign      REAL,           -- degrees within current sign (0-30)
    nakshatra           TEXT,
    nakshatra_pada      INTEGER CHECK(nakshatra_pada BETWEEN 1 AND 4),
    is_retrograde       INTEGER DEFAULT 0,
    is_combust          INTEGER DEFAULT 0,
    dignity             TEXT,           -- 'exalted','moolatrikona','own','friendly','neutral','enemy','debilitated'
    speed               REAL,           -- degrees/day at birth
    strength            REAL DEFAULT 1.0, -- backward compat; replaced by shadbala
    PRIMARY KEY (person_id, planet),
    FOREIGN KEY (person_id) REFERENCES person(id)
);

-- 3. natal_house_lord: house → sign → lord → lord's house
CREATE TABLE IF NOT EXISTS natal_house_lord (
    person_id       INTEGER NOT NULL,
    house_number    INTEGER NOT NULL CHECK(house_number BETWEEN 1 AND 12),
    sign            TEXT NOT NULL,
    lord            TEXT NOT NULL,       -- planet ruling this sign
    lord_house      INTEGER,            -- house where the lord sits
    PRIMARY KEY (person_id, house_number),
    FOREIGN KEY (person_id) REFERENCES person(id)
);

-- 4. natal_aspect: all aspects between planets
CREATE TABLE IF NOT EXISTS natal_aspect (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id       INTEGER NOT NULL,
    aspecting_planet TEXT NOT NULL,
    aspected_planet TEXT NOT NULL,
    aspect_type     TEXT,               -- 'conjunction','opposition','special'
    aspect_offset   INTEGER,            -- house distance
    strength        REAL DEFAULT 1.0,
    FOREIGN KEY (person_id) REFERENCES person(id)
);

-- 5. natal_compound_relationship: 5-fold relationships (panchadha)
CREATE TABLE IF NOT EXISTS natal_compound_relationship (
    person_id           INTEGER NOT NULL,
    planet              TEXT NOT NULL,
    other_planet        TEXT NOT NULL,
    natural_relation    TEXT NOT NULL,   -- 'Friend','Neutral','Enemy'
    temporal_relation   TEXT NOT NULL,   -- 'Friend','Enemy'
    compound_relation   TEXT NOT NULL,   -- 'BestFriend','Friend','Neutral','Enemy','BitterEnemy'
    PRIMARY KEY (person_id, planet, other_planet),
    FOREIGN KEY (person_id) REFERENCES person(id)
);

-- 6. natal_yoga: detected yogas
CREATE TABLE IF NOT EXISTS natal_yoga (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id           INTEGER NOT NULL,
    yoga_name           TEXT NOT NULL,
    yoga_type           TEXT,           -- 'mahapurusha','raja','dhana','negative','other'
    participating_planets TEXT,         -- JSON array
    strength            REAL DEFAULT 1.0,
    description         TEXT,
    FOREIGN KEY (person_id) REFERENCES person(id)
);

-- 7. natal_bav: bhinnaashtakavarga (7 planets x 12 signs = 84 per person)
CREATE TABLE IF NOT EXISTS natal_bav (
    person_id       INTEGER NOT NULL,
    planet          TEXT NOT NULL,       -- the planet whose BAV we're computing
    sign            TEXT NOT NULL,       -- the sign
    bindus          INTEGER NOT NULL CHECK(bindus BETWEEN 0 AND 8),
    PRIMARY KEY (person_id, planet, sign),
    FOREIGN KEY (person_id) REFERENCES person(id)
);

-- 8. natal_sav: sarvashtakavarga (totals per sign, 12 per person)
CREATE TABLE IF NOT EXISTS natal_sav (
    person_id       INTEGER NOT NULL,
    sign            TEXT NOT NULL,
    total_bindus    INTEGER NOT NULL CHECK(total_bindus BETWEEN 0 AND 56),
    PRIMARY KEY (person_id, sign),
    FOREIGN KEY (person_id) REFERENCES person(id)
);

-- 9. natal_varga: divisional chart positions
CREATE TABLE IF NOT EXISTS natal_varga (
    person_id       INTEGER NOT NULL,
    planet          TEXT NOT NULL,
    varga_type      TEXT NOT NULL,       -- 'D-9','D-10','D-2', etc.
    varga_sign      TEXT NOT NULL,
    is_vargottama   INTEGER DEFAULT 0,   -- same sign in D-1 and this varga
    PRIMARY KEY (person_id, planet, varga_type),
    FOREIGN KEY (person_id) REFERENCES person(id)
);

-- 10. natal_shadbala: six-fold strength scores
CREATE TABLE IF NOT EXISTS natal_shadbala (
    person_id       INTEGER NOT NULL,
    planet          TEXT NOT NULL,
    sthana_bala     REAL,               -- positional strength
    dig_bala        REAL,               -- directional strength
    kala_bala       REAL,               -- temporal strength
    chesta_bala     REAL,               -- motional strength
    naisargika_bala REAL,               -- natural strength
    drik_bala       REAL,               -- aspectual strength
    total_shadbala  REAL,               -- sum of all six
    is_strong       INTEGER DEFAULT 0,  -- meets minimum threshold
    PRIMARY KEY (person_id, planet),
    FOREIGN KEY (person_id) REFERENCES person(id)
);

-- 11. dasha: full hierarchy with parent reference
CREATE TABLE IF NOT EXISTS dasha (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id       INTEGER NOT NULL,
    level           TEXT NOT NULL CHECK(level IN ('maha','antar','pratyantar')),
    planet          TEXT NOT NULL,
    start_date      TEXT NOT NULL,       -- YYYY-MM-DD
    end_date        TEXT NOT NULL,       -- YYYY-MM-DD
    parent_dasha_id INTEGER,            -- self-referencing FK for hierarchy
    FOREIGN KEY (person_id) REFERENCES person(id),
    FOREIGN KEY (parent_dasha_id) REFERENCES dasha(id)
);

-- =============================================
-- CATEGORY 3: TRANSIT / DAILY (4 tables)
-- Ephemeris feed, daily or batch
-- =============================================

-- 1. transit_position: current sidereal positions
CREATE TABLE IF NOT EXISTS transit_position (
    date                TEXT NOT NULL,   -- YYYY-MM-DD
    planet              TEXT NOT NULL,
    sidereal_longitude  REAL NOT NULL,
    sign                TEXT NOT NULL,
    degree_in_sign      REAL,
    nakshatra           TEXT,
    nakshatra_pada      INTEGER,
    is_retrograde       INTEGER DEFAULT 0,
    speed               REAL,
    PRIMARY KEY (date, planet)
);

-- 2. transit_event: retrogrades, eclipses, planetary wars, ingresses
CREATE TABLE IF NOT EXISTS transit_event (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    date            TEXT NOT NULL,
    event_type      TEXT NOT NULL,       -- 'retrograde_start','retrograde_end','eclipse_solar','eclipse_lunar','planetary_war','ingress'
    planet          TEXT,
    description     TEXT,
    from_sign       TEXT,               -- for ingress events
    to_sign         TEXT                -- for ingress events
);

-- 3. transit_score: per-person transit scoring
CREATE TABLE IF NOT EXISTS transit_score (
    person_id       INTEGER NOT NULL,
    date            TEXT NOT NULL,
    planet          TEXT NOT NULL,       -- the transiting planet
    transit_sign    TEXT NOT NULL,
    bav_score       INTEGER,            -- BAV lookup for this planet in transit sign
    dignity_score   REAL,               -- dignity of transiting planet
    aspect_score    REAL,               -- aspects to natal planets
    composite_score REAL,               -- weighted combination
    PRIMARY KEY (person_id, date, planet),
    FOREIGN KEY (person_id) REFERENCES person(id)
);

-- 4. sade_sati_period: Saturn's 7.5-year transit phases
CREATE TABLE IF NOT EXISTS sade_sati_period (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id       INTEGER NOT NULL,
    phase           INTEGER NOT NULL CHECK(phase IN (1,2,3)), -- 12th, 1st, 2nd from Moon
    start_date      TEXT NOT NULL,
    end_date        TEXT NOT NULL,
    saturn_sign     TEXT NOT NULL,
    moon_sign       TEXT NOT NULL,
    FOREIGN KEY (person_id) REFERENCES person(id)
);

-- =============================================
-- CATEGORY 4: OUTPUT / CACHE (2 tables)
-- =============================================

-- 1. astro_regime_snapshot (enhanced from v1)
CREATE TABLE IF NOT EXISTS astro_regime_snapshot (
    person_id       INTEGER NOT NULL,
    date            TEXT NOT NULL,
    directional_bias TEXT,
    volatility_bias TEXT,
    risk_multiplier REAL,
    allowed_strategies TEXT,            -- JSON array
    favored_sectors TEXT,               -- JSON array
    explanation     TEXT,
    dasha_context   TEXT,               -- JSON: current maha/antar/pratyantar lords
    transit_context TEXT,               -- JSON: key transit summary
    composite_score REAL,               -- overall daily score (-10 to +10)
    PRIMARY KEY (person_id, date),
    FOREIGN KEY (person_id) REFERENCES person(id)
);

-- 2. daily_recommendation: per-category daily guidance
CREATE TABLE IF NOT EXISTS daily_recommendation (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id       INTEGER NOT NULL,
    date            TEXT NOT NULL,
    category        TEXT NOT NULL,       -- 'career','wealth','health','trading','relationships','spirituality'
    action_type     TEXT NOT NULL CHECK(action_type IN ('do','avoid')),
    recommendation  TEXT NOT NULL,
    confidence      REAL,               -- 0.0-1.0
    source_factors  TEXT,               -- JSON: what drove this recommendation
    FOREIGN KEY (person_id) REFERENCES person(id)
);

-- =============================================
-- CATEGORY 5: ENTITY / FINANCIAL (2 tables)
-- =============================================

-- 1. entity: companies, indices, commodities, nations
CREATE TABLE IF NOT EXISTS entity (
    id              INTEGER PRIMARY KEY,
    name            TEXT NOT NULL,
    entity_type     TEXT NOT NULL CHECK(entity_type IN ('company','index','commodity','nation','currency')),
    ticker          TEXT,
    incorporation_date TEXT,            -- YYYY-MM-DD (or founding date)
    incorporation_time TEXT,            -- HH:MM (if known)
    latitude        REAL,
    longitude       REAL,
    timezone        TEXT,
    place_name      TEXT,
    notes           TEXT
);

-- 2. entity_natal_planet: same structure as natal_planet but for entities
CREATE TABLE IF NOT EXISTS entity_natal_planet (
    entity_id           INTEGER NOT NULL,
    planet              TEXT NOT NULL,
    sign                TEXT NOT NULL,
    house               INTEGER,        -- nullable: house requires lagna which may be unknown
    sidereal_longitude  REAL,
    degree_in_sign      REAL,
    nakshatra           TEXT,
    nakshatra_pada      INTEGER CHECK(nakshatra_pada BETWEEN 1 AND 4),
    is_retrograde       INTEGER DEFAULT 0,
    dignity             TEXT,
    PRIMARY KEY (entity_id, planet),
    FOREIGN KEY (entity_id) REFERENCES entity(id)
);

-- =============================================
-- INDEXES (14 indexes on common query patterns)
-- =============================================

-- Dasha lookups by person + date range
CREATE INDEX IF NOT EXISTS idx_dasha_person_dates
    ON dasha(person_id, start_date, end_date);

-- Dasha hierarchy navigation
CREATE INDEX IF NOT EXISTS idx_dasha_parent
    ON dasha(parent_dasha_id);

-- Dasha level filtering
CREATE INDEX IF NOT EXISTS idx_dasha_level
    ON dasha(person_id, level);

-- Transit position by date
CREATE INDEX IF NOT EXISTS idx_transit_position_date
    ON transit_position(date);

-- Transit events by date + type
CREATE INDEX IF NOT EXISTS idx_transit_event_date_type
    ON transit_event(date, event_type);

-- Transit scores by person + date
CREATE INDEX IF NOT EXISTS idx_transit_score_person_date
    ON transit_score(person_id, date);

-- Daily recommendation by person + date
CREATE INDEX IF NOT EXISTS idx_recommendation_person_date
    ON daily_recommendation(person_id, date);

-- Daily recommendation by category
CREATE INDEX IF NOT EXISTS idx_recommendation_category
    ON daily_recommendation(person_id, date, category);

-- Astro regime by person + date
CREATE INDEX IF NOT EXISTS idx_regime_person_date
    ON astro_regime_snapshot(person_id, date);

-- Natal aspects by person
CREATE INDEX IF NOT EXISTS idx_natal_aspect_person
    ON natal_aspect(person_id);

-- Natal yoga by person
CREATE INDEX IF NOT EXISTS idx_natal_yoga_person
    ON natal_yoga(person_id);

-- Sade sati by person + dates
CREATE INDEX IF NOT EXISTS idx_sade_sati_person_dates
    ON sade_sati_period(person_id, start_date, end_date);

-- Entity by type
CREATE INDEX IF NOT EXISTS idx_entity_type
    ON entity(entity_type);

-- Planet-sector lookup
CREATE INDEX IF NOT EXISTS idx_planet_sector
    ON ref_planet_sector(planet);

-- =============================================
-- CATEGORY 6: INTERPRETATION ENGINE (4 ref tables)
-- Life themes, karmic axis, planet-house & planet-theme meanings
-- =============================================

-- 16. ref_life_theme: theme → planet/house mapping for interpretation
CREATE TABLE IF NOT EXISTS ref_life_theme (
    theme             TEXT PRIMARY KEY,
    display_name      TEXT NOT NULL,
    relevant_planets  TEXT NOT NULL,  -- JSON: ["Mercury", "Rahu"]
    relevant_houses   TEXT NOT NULL,  -- JSON: [3, 11]
    description       TEXT
);

-- 17. ref_rahu_ketu_axis: karmic direction by Rahu's house placement
CREATE TABLE IF NOT EXISTS ref_rahu_ketu_axis (
    rahu_house  INTEGER NOT NULL,      -- ketu_house is always (rahu_house+5)%12+1
    karmic_from TEXT NOT NULL,         -- what Ketu house means (past)
    karmic_to   TEXT NOT NULL,         -- what Rahu house means (future)
    life_lesson TEXT NOT NULL,
    variant_id  INTEGER NOT NULL DEFAULT 1,
    PRIMARY KEY (rahu_house, variant_id)
);

-- 18. ref_planet_house_meaning: planet in house interpretation text
CREATE TABLE IF NOT EXISTS ref_planet_house_meaning (
    planet      TEXT NOT NULL,
    house       INTEGER NOT NULL,
    meaning     TEXT NOT NULL,         -- base interpretation
    when_strong TEXT,                  -- exalted/own/moolatrikona modifier
    when_weak   TEXT,                  -- debilitated/enemy modifier
    variant_id  INTEGER DEFAULT 1,
    PRIMARY KEY (planet, house, variant_id),
    FOREIGN KEY (planet) REFERENCES ref_planet(name)
);

-- 19. ref_planet_theme_meaning: planet's meaning for a specific life theme
CREATE TABLE IF NOT EXISTS ref_planet_theme_meaning (
    planet      TEXT NOT NULL,
    theme       TEXT NOT NULL,
    meaning     TEXT NOT NULL,
    when_strong TEXT,
    when_weak   TEXT,
    variant_id  INTEGER DEFAULT 1,
    PRIMARY KEY (planet, theme, variant_id),
    FOREIGN KEY (planet) REFERENCES ref_planet(name),
    FOREIGN KEY (theme)  REFERENCES ref_life_theme(theme)
);

-- =============================================
-- CATEGORY 7: EVENT SOURCING (2 tables)
-- Immutable event log + user feedback for RL
-- =============================================

-- event_log: every interaction (append-only)
CREATE TABLE IF NOT EXISTS event_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp       TEXT NOT NULL DEFAULT (datetime('now')),
    session_id      TEXT NOT NULL,
    person_id       INTEGER,
    raw_question    TEXT NOT NULL,
    detected_intent TEXT,
    detected_themes TEXT,       -- JSON: ["technology_ai", "career"]
    planets_involved TEXT,      -- JSON: ["Mercury", "Rahu"]
    houses_involved  TEXT,      -- JSON: [3, 11]
    chart_snapshot   TEXT,      -- JSON: relevant chart data at time of query
    variants_used    TEXT,      -- JSON: [{planet, house, variant_id}, ...]
    response_text   TEXT,
    FOREIGN KEY (person_id) REFERENCES person(id)
);

CREATE INDEX IF NOT EXISTS idx_event_log_person ON event_log(person_id);
CREATE INDEX IF NOT EXISTS idx_event_log_session ON event_log(session_id);
CREATE INDEX IF NOT EXISTS idx_event_log_theme ON event_log(detected_themes);
CREATE INDEX IF NOT EXISTS idx_event_log_timestamp ON event_log(timestamp);

-- event_feedback: user ratings (separate from log for clean separation)
CREATE TABLE IF NOT EXISTS event_feedback (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id    INTEGER NOT NULL,
    rating      INTEGER CHECK(rating BETWEEN 1 AND 5),
    feedback    TEXT,
    timestamp   TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (event_id) REFERENCES event_log(id)
);

CREATE INDEX IF NOT EXISTS idx_event_feedback_event ON event_feedback(event_id);
