"""
Seed all 15 ref_ tables with classical Vedic Astrology data.
Source: VEDIC_ASTROLOGY.md and standard Jyotish texts.
"""
import json
from .connection import get_connection


def seed_all():
    conn = get_connection()
    cur = conn.cursor()

    _seed_ref_sign(cur)
    _seed_ref_planet(cur)
    _seed_ref_nakshatra(cur)
    _seed_ref_dignity(cur)
    _seed_ref_moolatrikona(cur)
    _seed_ref_ownership(cur)
    _seed_ref_natural_relationship(cur)
    _seed_ref_aspect_rule(cur)
    _seed_ref_house(cur)
    _seed_ref_dasha_sequence(cur)
    _seed_ref_ashtakavarga_rule(cur)
    _seed_ref_combustion_range(cur)
    _seed_ref_planet_sector(cur)
    _seed_ref_planet_commodity(cur)
    _seed_ref_strategy_class(cur)

    conn.commit()
    conn.close()
    print("Seeded all 15 reference tables")


# ---------- 1. ref_sign (12 rows) ----------

def _seed_ref_sign(cur):
    signs = [
        # (name, number, sanskrit, symbol, element, modality, ruler, gender, nature, deg_start, deg_end)
        ("Aries",       1,  "Mesha",       "Ram",       "Fire",  "Cardinal", "Mars",    "Male",   "Cruel",  0,   30),
        ("Taurus",      2,  "Vrishabha",   "Bull",      "Earth", "Fixed",    "Venus",   "Female", "Gentle", 30,  60),
        ("Gemini",      3,  "Mithuna",     "Twins",     "Air",   "Mutable",  "Mercury", "Male",   "Cruel",  60,  90),
        ("Cancer",      4,  "Karka",       "Crab",      "Water", "Cardinal", "Moon",    "Female", "Gentle", 90,  120),
        ("Leo",         5,  "Simha",       "Lion",      "Fire",  "Fixed",    "Sun",     "Male",   "Cruel",  120, 150),
        ("Virgo",       6,  "Kanya",       "Maiden",    "Earth", "Mutable",  "Mercury", "Female", "Gentle", 150, 180),
        ("Libra",       7,  "Tula",        "Scales",    "Air",   "Cardinal", "Venus",   "Male",   "Cruel",  180, 210),
        ("Scorpio",     8,  "Vrishchika",  "Scorpion",  "Water", "Fixed",    "Mars",    "Female", "Gentle", 210, 240),
        ("Sagittarius", 9,  "Dhanu",       "Archer",    "Fire",  "Mutable",  "Jupiter", "Male",   "Cruel",  240, 270),
        ("Capricorn",   10, "Makara",      "Crocodile", "Earth", "Cardinal", "Saturn",  "Female", "Gentle", 270, 300),
        ("Aquarius",    11, "Kumbha",      "Pot",       "Air",   "Fixed",    "Saturn",  "Male",   "Cruel",  300, 330),
        ("Pisces",      12, "Meena",       "Fish",      "Water", "Mutable",  "Jupiter", "Female", "Gentle", 330, 360),
    ]
    cur.executemany(
        "INSERT OR REPLACE INTO ref_sign VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        signs,
    )


# ---------- 2. ref_planet (9 rows) ----------

def _seed_ref_planet(cur):
    planets = [
        # (name, sanskrit, symbol, nature, gender, element, dasha_years, avg_daily_motion, naisargika_bala, dig_bala_house)
        ("Sun",     "Surya",   "\u2609", "Malefic",  "Male",    "Fire",  6,   1.0,    60.0,  10),
        ("Moon",    "Chandra", "\u263D", "Benefic",  "Female",  "Water", 10,  13.17,  51.4,  4),
        ("Mars",    "Mangala", "\u2642", "Malefic",  "Male",    "Fire",  7,   0.52,   17.1,  10),
        ("Mercury", "Budha",   "\u263F", "Neutral",  "Neutral", "Earth", 17,  1.38,   25.7,  1),
        ("Jupiter", "Guru",    "\u2643", "Benefic",  "Male",    "Ether", 16,  0.08,   34.3,  1),
        ("Venus",   "Shukra",  "\u2640", "Benefic",  "Female",  "Water", 20,  1.2,    42.8,  4),
        ("Saturn",  "Shani",   "\u2644", "Malefic",  "Neutral", "Air",   19,  0.03,   8.6,   7),
        ("Rahu",    "Rahu",    "\u260A", "Malefic",  None,      "Smoke", 18,  0.05,   None,  None),
        ("Ketu",    "Ketu",    "\u260B", "Malefic",  None,      "Fire",  7,   0.05,   None,  None),
    ]
    cur.executemany(
        "INSERT OR REPLACE INTO ref_planet VALUES (?,?,?,?,?,?,?,?,?,?)",
        planets,
    )


# ---------- 3. ref_nakshatra (27 rows) ----------

def _seed_ref_nakshatra(cur):
    # Each nakshatra spans 13deg20min = 13.3333 degrees
    span = 13 + 1/3
    nakshatras = [
        # (name, number, ruler, deity, nature, signs JSON)
        ("Ashwini",           1,  "Ketu",    "Ashwini Kumaras", "Swift",          '["Aries"]'),
        ("Bharani",           2,  "Venus",   "Yama",            "Fierce",         '["Aries"]'),
        ("Krittika",          3,  "Sun",     "Agni",            "Sharp",          '["Aries","Taurus"]'),
        ("Rohini",            4,  "Moon",    "Brahma",          "Fixed",          '["Taurus"]'),
        ("Mrigashira",        5,  "Mars",    "Soma",            "Soft",           '["Taurus","Gemini"]'),
        ("Ardra",             6,  "Rahu",    "Rudra",           "Sharp",          '["Gemini"]'),
        ("Punarvasu",         7,  "Jupiter", "Aditi",           "Movable",        '["Gemini","Cancer"]'),
        ("Pushya",            8,  "Saturn",  "Brihaspati",      "Light",          '["Cancer"]'),
        ("Ashlesha",          9,  "Mercury", "Nagas",           "Sharp",          '["Cancer"]'),
        ("Magha",             10, "Ketu",    "Pitris",          "Fierce",         '["Leo"]'),
        ("Purva Phalguni",    11, "Venus",   "Bhaga",           "Fierce",         '["Leo"]'),
        ("Uttara Phalguni",   12, "Sun",     "Aryaman",         "Fixed",          '["Leo","Virgo"]'),
        ("Hasta",             13, "Moon",    "Savitar",          "Light",          '["Virgo"]'),
        ("Chitra",            14, "Mars",    "Vishwakarma",     "Soft",           '["Virgo","Libra"]'),
        ("Swati",             15, "Rahu",    "Vayu",            "Movable",        '["Libra"]'),
        ("Vishakha",          16, "Jupiter", "Indra-Agni",      "Sharp",          '["Libra","Scorpio"]'),
        ("Anuradha",          17, "Saturn",  "Mitra",           "Soft",           '["Scorpio"]'),
        ("Jyeshtha",          18, "Mercury", "Indra",           "Sharp",          '["Scorpio"]'),
        ("Mula",              19, "Ketu",    "Nirriti",         "Sharp",          '["Sagittarius"]'),
        ("Purva Ashada",      20, "Venus",   "Apas",            "Fierce",         '["Sagittarius"]'),
        ("Uttara Ashada",     21, "Sun",     "Vishvadevas",     "Fixed",          '["Sagittarius","Capricorn"]'),
        ("Shravana",          22, "Moon",    "Vishnu",          "Movable",        '["Capricorn"]'),
        ("Dhanishta",         23, "Mars",    "Vasus",           "Movable",        '["Capricorn","Aquarius"]'),
        ("Shatabhisha",       24, "Rahu",    "Varuna",          "Movable",        '["Aquarius"]'),
        ("Purva Bhadrapada",  25, "Jupiter", "Aja Ekapad",      "Fierce",         '["Aquarius","Pisces"]'),
        ("Uttara Bhadrapada", 26, "Saturn",  "Ahir Budhnya",    "Fixed",          '["Pisces"]'),
        ("Revati",            27, "Mercury", "Pushan",          "Soft",           '["Pisces"]'),
    ]
    for name, num, ruler, deity, nature, signs in nakshatras:
        deg_start = round((num - 1) * span, 4)
        deg_end = round(num * span, 4)
        cur.execute(
            "INSERT OR REPLACE INTO ref_nakshatra VALUES (?,?,?,?,?,?,?,?)",
            (name, num, deg_start, deg_end, ruler, deity, nature, signs),
        )


# ---------- 4. ref_dignity (18 rows) ----------

def _seed_ref_dignity(cur):
    dignities = [
        # (planet, dignity_type, sign, exact_degree)
        ("Sun",     "exaltation",   "Aries",      10),
        ("Sun",     "debilitation", "Libra",       10),
        ("Moon",    "exaltation",   "Taurus",      3),
        ("Moon",    "debilitation", "Scorpio",     3),
        ("Mars",    "exaltation",   "Capricorn",   28),
        ("Mars",    "debilitation", "Cancer",      28),
        ("Mercury", "exaltation",   "Virgo",       15),
        ("Mercury", "debilitation", "Pisces",      15),
        ("Jupiter", "exaltation",   "Cancer",      5),
        ("Jupiter", "debilitation", "Capricorn",   5),
        ("Venus",   "exaltation",   "Pisces",      27),
        ("Venus",   "debilitation", "Virgo",       27),
        ("Saturn",  "exaltation",   "Libra",       20),
        ("Saturn",  "debilitation", "Aries",       20),
        ("Rahu",    "exaltation",   "Taurus",      None),
        ("Rahu",    "debilitation", "Scorpio",     None),
        ("Ketu",    "exaltation",   "Scorpio",     None),
        ("Ketu",    "debilitation", "Taurus",      None),
    ]
    cur.executemany(
        "INSERT OR REPLACE INTO ref_dignity VALUES (?,?,?,?)",
        dignities,
    )


# ---------- 5. ref_moolatrikona (7 rows) ----------

def _seed_ref_moolatrikona(cur):
    moolatrikona = [
        ("Sun",     "Leo",         0,  20),
        ("Moon",    "Taurus",      3,  30),
        ("Mars",    "Aries",       0,  12),
        ("Mercury", "Virgo",       15, 20),
        ("Jupiter", "Sagittarius", 0,  10),
        ("Venus",   "Libra",       0,  15),
        ("Saturn",  "Aquarius",    0,  20),
    ]
    cur.executemany(
        "INSERT OR REPLACE INTO ref_moolatrikona VALUES (?,?,?,?)",
        moolatrikona,
    )


# ---------- 6. ref_ownership (12 rows) ----------

def _seed_ref_ownership(cur):
    ownership = [
        ("Aries",       "Mars"),
        ("Taurus",      "Venus"),
        ("Gemini",      "Mercury"),
        ("Cancer",      "Moon"),
        ("Leo",         "Sun"),
        ("Virgo",       "Mercury"),
        ("Libra",       "Venus"),
        ("Scorpio",     "Mars"),
        ("Sagittarius", "Jupiter"),
        ("Capricorn",   "Saturn"),
        ("Aquarius",    "Saturn"),
        ("Pisces",      "Jupiter"),
    ]
    cur.executemany(
        "INSERT OR REPLACE INTO ref_ownership VALUES (?,?)",
        ownership,
    )


# ---------- 7. ref_natural_relationship (81 rows) ----------

def _seed_ref_natural_relationship(cur):
    # From VEDIC_ASTROLOGY.md section 9
    relationships = {
        "Sun":     {"Moon": "Friend", "Mars": "Friend", "Jupiter": "Friend",
                    "Mercury": "Neutral", "Venus": "Enemy", "Saturn": "Enemy",
                    "Rahu": "Enemy", "Ketu": "Enemy"},
        "Moon":    {"Sun": "Friend", "Mercury": "Friend",
                    "Mars": "Neutral", "Jupiter": "Neutral", "Venus": "Neutral", "Saturn": "Neutral",
                    "Rahu": "Enemy", "Ketu": "Enemy"},
        "Mars":    {"Sun": "Friend", "Moon": "Friend", "Jupiter": "Friend",
                    "Venus": "Neutral", "Saturn": "Neutral",
                    "Mercury": "Enemy", "Rahu": "Enemy", "Ketu": "Enemy"},
        "Mercury": {"Sun": "Friend", "Venus": "Friend",
                    "Mars": "Neutral", "Jupiter": "Neutral", "Saturn": "Neutral",
                    "Moon": "Enemy", "Rahu": "Enemy", "Ketu": "Enemy"},
        "Jupiter": {"Sun": "Friend", "Moon": "Friend", "Mars": "Friend",
                    "Saturn": "Neutral",
                    "Mercury": "Enemy", "Venus": "Enemy", "Rahu": "Enemy", "Ketu": "Enemy"},
        "Venus":   {"Mercury": "Friend", "Saturn": "Friend",
                    "Mars": "Neutral", "Jupiter": "Neutral",
                    "Sun": "Enemy", "Moon": "Enemy", "Rahu": "Enemy", "Ketu": "Enemy"},
        "Saturn":  {"Mercury": "Friend", "Venus": "Friend",
                    "Jupiter": "Neutral",
                    "Sun": "Enemy", "Moon": "Enemy", "Mars": "Enemy", "Rahu": "Enemy", "Ketu": "Enemy"},
        "Rahu":    {"Mercury": "Friend", "Venus": "Friend", "Saturn": "Friend",
                    "Jupiter": "Neutral",
                    "Sun": "Enemy", "Moon": "Enemy", "Mars": "Enemy"},
        "Ketu":    {"Mars": "Friend", "Jupiter": "Friend",
                    "Mercury": "Neutral", "Venus": "Neutral", "Saturn": "Neutral",
                    "Sun": "Enemy", "Moon": "Enemy"},
    }

    planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
    rows = []
    for p in planets:
        for op in planets:
            if p == op:
                rel = "Neutral"  # self-relationship
            else:
                rel = relationships[p].get(op, "Neutral")
            rows.append((p, op, rel))

    cur.executemany(
        "INSERT OR REPLACE INTO ref_natural_relationship VALUES (?,?,?)",
        rows,
    )


# ---------- 8. ref_aspect_rule (~14 rows) ----------

def _seed_ref_aspect_rule(cur):
    # All planets get 7th house aspect; Mars/Jupiter/Saturn/Rahu/Ketu get specials
    rules = [
        # Standard 7th house aspect for all
        ("Sun",     7, 1.0),
        ("Moon",    7, 1.0),
        ("Mars",    7, 1.0),
        ("Mercury", 7, 1.0),
        ("Jupiter", 7, 1.0),
        ("Venus",   7, 1.0),
        ("Saturn",  7, 1.0),
        ("Rahu",    7, 1.0),
        ("Ketu",    7, 1.0),
        # Mars special aspects: 4th and 8th
        ("Mars",    4, 1.0),
        ("Mars",    8, 1.0),
        # Jupiter special aspects: 5th and 9th
        ("Jupiter", 5, 1.0),
        ("Jupiter", 9, 1.0),
        # Saturn special aspects: 3rd and 10th
        ("Saturn",  3, 1.0),
        ("Saturn",  10, 1.0),
        # Rahu/Ketu special aspects: 5th and 9th (widely accepted view)
        ("Rahu",    5, 1.0),
        ("Rahu",    9, 1.0),
        ("Ketu",    5, 1.0),
        ("Ketu",    9, 1.0),
    ]
    cur.executemany(
        "INSERT OR REPLACE INTO ref_aspect_rule VALUES (?,?,?)",
        rules,
    )


# ---------- 9. ref_house (12 rows) ----------

def _seed_ref_house(cur):
    houses = [
        # (number, sanskrit, english, domain, kendra, trikona, upachaya, dusthana, maraka, domain_group)
        (1,  "Tanu",    "Self",           "Body, personality",          1, 1, 0, 0, 0, "Dharma"),
        (2,  "Dhana",   "Wealth",         "Money, speech, family",      0, 0, 0, 0, 1, "Artha"),
        (3,  "Sahaja",  "Siblings",       "Courage, skills, siblings",  0, 0, 1, 0, 0, "Kama"),
        (4,  "Sukha",   "Happiness",      "Home, mother, property",     1, 0, 0, 0, 0, "Moksha"),
        (5,  "Putra",   "Children",       "Intelligence, creativity",   0, 1, 0, 0, 0, "Dharma"),
        (6,  "Ripu",    "Enemies",        "Conflict, disease, service", 0, 0, 1, 1, 0, "Artha"),
        (7,  "Yuvati",  "Spouse",         "Partnership, marriage",      1, 0, 0, 0, 1, "Kama"),
        (8,  "Randhra", "Transformation", "Death, hidden, inheritance", 0, 0, 0, 1, 0, "Moksha"),
        (9,  "Dharma",  "Fortune",        "Luck, father, philosophy",   0, 1, 0, 0, 0, "Dharma"),
        (10, "Karma",   "Career",         "Profession, status",         1, 0, 1, 0, 0, "Artha"),
        (11, "Labha",   "Gains",          "Income, networks, profits",  0, 0, 1, 0, 0, "Kama"),
        (12, "Vyaya",   "Loss",           "Expenses, spirituality",     0, 0, 0, 1, 0, "Moksha"),
    ]
    cur.executemany(
        "INSERT OR REPLACE INTO ref_house VALUES (?,?,?,?,?,?,?,?,?,?)",
        houses,
    )


# ---------- 10. ref_dasha_sequence (9 rows) ----------

def _seed_ref_dasha_sequence(cur):
    sequence = [
        (1, "Ketu",    7),
        (2, "Venus",   20),
        (3, "Sun",     6),
        (4, "Moon",    10),
        (5, "Mars",    7),
        (6, "Rahu",    18),
        (7, "Jupiter", 16),
        (8, "Saturn",  19),
        (9, "Mercury", 17),
    ]
    cur.executemany(
        "INSERT OR REPLACE INTO ref_dasha_sequence VALUES (?,?,?)",
        sequence,
    )


# ---------- 11. ref_ashtakavarga_rule (8 rows) ----------

def _seed_ref_ashtakavarga_rule(cur):
    rules = [
        ("Sun",     json.dumps([1, 2, 4, 7, 8, 9, 10, 11])),
        ("Moon",    json.dumps([3, 6, 7, 8, 10, 11])),
        ("Mars",    json.dumps([1, 2, 4, 7, 8, 10, 11])),
        ("Mercury", json.dumps([1, 2, 4, 7, 8, 9, 10, 11])),
        ("Jupiter", json.dumps([1, 2, 3, 4, 7, 8, 10, 11])),
        ("Venus",   json.dumps([1, 2, 3, 4, 5, 8, 9, 11])),
        ("Saturn",  json.dumps([3, 5, 6, 11])),
        ("Lagna",   json.dumps([3, 6, 10, 11])),
    ]
    cur.executemany(
        "INSERT OR REPLACE INTO ref_ashtakavarga_rule VALUES (?,?)",
        rules,
    )


# ---------- 12. ref_combustion_range (6 rows) ----------

def _seed_ref_combustion_range(cur):
    ranges = [
        # (planet, normal_range_degrees, retrograde_range_or_null)
        ("Moon",    12, None),
        ("Mars",    17, None),
        ("Mercury", 14, 12),
        ("Jupiter", 11, None),
        ("Venus",   10, 8),
        ("Saturn",  15, None),
    ]
    cur.executemany(
        "INSERT OR REPLACE INTO ref_combustion_range VALUES (?,?,?)",
        ranges,
    )


# ---------- 13. ref_planet_sector (~25 rows) ----------

def _seed_ref_planet_sector(cur):
    cur.execute("DELETE FROM ref_planet_sector")
    sectors = [
        ("Sun",     "Government/PSU",  "primary"),
        ("Sun",     "Gold",            "primary"),
        ("Moon",    "FMCG",            "primary"),
        ("Moon",    "Silver",          "primary"),
        ("Moon",    "Consumer",        "secondary"),
        ("Mars",    "Defense",         "primary"),
        ("Mars",    "Metals",          "primary"),
        ("Mars",    "Energy",          "primary"),
        ("Mars",    "Real Estate",     "secondary"),
        ("Mercury", "IT",             "primary"),
        ("Mercury", "FinTech",        "primary"),
        ("Mercury", "Telecom",        "primary"),
        ("Jupiter", "Banking",        "primary"),
        ("Jupiter", "Insurance",      "primary"),
        ("Jupiter", "Education",      "secondary"),
        ("Venus",   "Auto",           "primary"),
        ("Venus",   "Media",          "primary"),
        ("Venus",   "Luxury",         "primary"),
        ("Venus",   "Hotels",         "secondary"),
        ("Saturn",  "Infrastructure", "primary"),
        ("Saturn",  "Oil & Gas",      "primary"),
        ("Saturn",  "Utilities",      "primary"),
        ("Rahu",    "Technology",     "primary"),
        ("Rahu",    "Crypto",         "primary"),
        ("Rahu",    "Foreign",        "secondary"),
        ("Ketu",    "Pharma",         "primary"),
        ("Ketu",    "Research",       "secondary"),
    ]
    cur.executemany(
        "INSERT OR REPLACE INTO ref_planet_sector (planet, sector, affinity) VALUES (?,?,?)",
        sectors,
    )


# ---------- 14. ref_planet_commodity (~15 rows) ----------

def _seed_ref_planet_commodity(cur):
    cur.execute("DELETE FROM ref_planet_commodity")
    commodities = [
        ("Sun",     "Gold",         "primary"),
        ("Jupiter", "Gold",         "secondary"),
        ("Saturn",  "Gold",         "secondary"),
        ("Moon",    "Silver",       "primary"),
        ("Venus",   "Silver",       "secondary"),
        ("Saturn",  "Crude Oil",    "primary"),
        ("Mars",    "Crude Oil",    "secondary"),
        ("Rahu",    "Crude Oil",    "secondary"),
        ("Venus",   "Copper",       "primary"),
        ("Mars",    "Copper",       "secondary"),
        ("Rahu",    "Natural Gas",  "primary"),
        ("Saturn",  "Natural Gas",  "secondary"),
        ("Mars",    "Natural Gas",  "secondary"),
        ("Moon",    "Agricultural", "primary"),
        ("Venus",   "Agricultural", "secondary"),
        ("Mercury", "Agricultural", "secondary"),
    ]
    cur.executemany(
        "INSERT OR REPLACE INTO ref_planet_commodity (planet, commodity, affinity) VALUES (?,?,?)",
        commodities,
    )


# ---------- 15. ref_strategy_class (~8 rows) ----------

def _seed_ref_strategy_class(cur):
    strategies = [
        ("momentum",        "Trend following, breakout strategies",
         json.dumps(["Mars", "Sun", "Rahu"]),
         json.dumps(["Saturn"])),
        ("mean_reversion",  "Counter-trend, reversion to average",
         json.dumps(["Saturn", "Venus"]),
         json.dumps(["Mars", "Rahu"])),
        ("scalping",        "Ultra-short-term, high-frequency",
         json.dumps(["Mercury", "Moon"]),
         json.dumps(["Saturn"])),
        ("swing",           "Multi-day position trading",
         json.dumps(["Jupiter", "Venus"]),
         json.dumps(["Rahu", "Ketu"])),
        ("positional",      "Long-term holding, accumulation",
         json.dumps(["Jupiter", "Saturn"]),
         json.dumps(["Mars", "Rahu"])),
        ("options_buying",  "Directional option premium buying",
         json.dumps(["Mars", "Rahu"]),
         json.dumps(["Saturn", "Ketu"])),
        ("options_selling", "Premium decay, theta strategies",
         json.dumps(["Saturn", "Venus"]),
         json.dumps(["Mars", "Rahu"])),
        ("hedging",         "Risk reduction, portfolio protection",
         json.dumps(["Saturn", "Ketu"]),
         json.dumps(["Rahu"])),
    ]
    cur.executemany(
        "INSERT OR REPLACE INTO ref_strategy_class VALUES (?,?,?,?)",
        strategies,
    )


def print_counts():
    conn = get_connection()
    cur = conn.cursor()
    tables = [
        "ref_sign", "ref_planet", "ref_nakshatra", "ref_dignity",
        "ref_moolatrikona", "ref_ownership", "ref_natural_relationship",
        "ref_aspect_rule", "ref_house", "ref_dasha_sequence",
        "ref_ashtakavarga_rule", "ref_combustion_range",
        "ref_planet_sector", "ref_planet_commodity", "ref_strategy_class",
    ]
    for t in tables:
        cur.execute(f"SELECT COUNT(*) FROM {t}")
        count = cur.fetchone()[0]
        print(f"  {t:<30s} : {count} rows")
    conn.close()


if __name__ == "__main__":
    seed_all()
    print_counts()
