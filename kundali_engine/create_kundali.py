"""
CLI tool to compute and store a Vedic natal chart (Kundali).

Usage:
  python -m kundali_engine.create_kundali '{
    "name": "Priyanka Jain",
    "dob": "1981-11-24",
    "tob": "06:10",
    "place": "Ranchi, India",
    "lat": 23.3441,
    "lon": 85.3096,
    "tz": "IST"
  }'

  # Or from a file:
  python -m kundali_engine.create_kundali --file people.json

  people.json can be a single object or an array of objects.

Required JSON fields: name, dob (YYYY-MM-DD), tob (HH:MM), lat, lon
Optional: place, tz (default "IST")
"""
import json
import sys
import math
from datetime import datetime, timedelta
from pathlib import Path

from skyfield.api import load as sky_load

from kundali_engine.core.database.connection import get_connection

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

NAKSHATRAS = [
    ("Ashwini", "Ketu"), ("Bharani", "Venus"), ("Krittika", "Sun"),
    ("Rohini", "Moon"), ("Mrigashira", "Mars"), ("Ardra", "Rahu"),
    ("Punarvasu", "Jupiter"), ("Pushya", "Saturn"), ("Ashlesha", "Mercury"),
    ("Magha", "Ketu"), ("Purva Phalguni", "Venus"), ("Uttara Phalguni", "Sun"),
    ("Hasta", "Moon"), ("Chitra", "Mars"), ("Swati", "Rahu"),
    ("Vishakha", "Jupiter"), ("Anuradha", "Saturn"), ("Jyeshtha", "Mercury"),
    ("Mula", "Ketu"), ("Purva Ashada", "Venus"), ("Uttara Ashada", "Sun"),
    ("Shravana", "Moon"), ("Dhanishta", "Mars"), ("Shatabhisha", "Rahu"),
    ("Purva Bhadrapada", "Jupiter"), ("Uttara Bhadrapada", "Saturn"), ("Revati", "Mercury"),
]

# Exaltation / debilitation for dignity lookup
EXALTATION = {
    "Sun": ("Aries", 10), "Moon": ("Taurus", 3), "Mars": ("Capricorn", 28),
    "Mercury": ("Virgo", 15), "Jupiter": ("Cancer", 5), "Venus": ("Pisces", 27),
    "Saturn": ("Libra", 20), "Rahu": ("Taurus", None), "Ketu": ("Scorpio", None),
}
DEBILITATION = {
    "Sun": ("Libra", 10), "Moon": ("Scorpio", 3), "Mars": ("Cancer", 28),
    "Mercury": ("Pisces", 15), "Jupiter": ("Capricorn", 5), "Venus": ("Virgo", 27),
    "Saturn": ("Aries", 20), "Rahu": ("Scorpio", None), "Ketu": ("Taurus", None),
}
MOOLATRIKONA = {
    "Sun": ("Leo", 0, 20), "Moon": ("Taurus", 3, 30), "Mars": ("Aries", 0, 12),
    "Mercury": ("Virgo", 15, 20), "Jupiter": ("Sagittarius", 0, 10),
    "Venus": ("Libra", 0, 15), "Saturn": ("Aquarius", 0, 20),
}
OWNERSHIP = {
    "Sun": ["Leo"], "Moon": ["Cancer"], "Mars": ["Aries", "Scorpio"],
    "Mercury": ["Gemini", "Virgo"], "Jupiter": ["Sagittarius", "Pisces"],
    "Venus": ["Taurus", "Libra"], "Saturn": ["Capricorn", "Aquarius"],
    "Rahu": [], "Ketu": [],
}
FRIENDS = {
    "Sun": {"Moon", "Mars", "Jupiter"}, "Moon": {"Sun", "Mercury"},
    "Mars": {"Sun", "Moon", "Jupiter"}, "Mercury": {"Sun", "Venus"},
    "Jupiter": {"Sun", "Moon", "Mars"}, "Venus": {"Mercury", "Saturn"},
    "Saturn": {"Mercury", "Venus"}, "Rahu": {"Mercury", "Venus", "Saturn"},
    "Ketu": {"Mars", "Jupiter"},
}
ENEMIES = {
    "Sun": {"Venus", "Saturn", "Rahu", "Ketu"},
    "Moon": {"Rahu", "Ketu"},
    "Mars": {"Mercury", "Rahu", "Ketu"},
    "Mercury": {"Moon", "Rahu", "Ketu"},
    "Jupiter": {"Mercury", "Venus", "Rahu", "Ketu"},
    "Venus": {"Sun", "Moon", "Rahu", "Ketu"},
    "Saturn": {"Sun", "Moon", "Mars", "Rahu", "Ketu"},
    "Rahu": {"Sun", "Moon", "Mars"},
    "Ketu": {"Sun", "Moon"},
}

# Combustion thresholds
COMBUSTION = {
    "Moon": (12, 12), "Mars": (17, 17), "Mercury": (14, 12),
    "Jupiter": (11, 11), "Venus": (10, 8), "Saturn": (15, 15),
}

TZ_OFFSETS = {
    "IST": 5.5, "UTC": 0, "EST": -5, "CST": -6, "PST": -8,
    "GMT": 0, "CET": 1, "JST": 9, "AEST": 10,
}

# ---------------------------------------------------------------------------
# Ephemeris computation
# ---------------------------------------------------------------------------

# Lazy-load skyfield data (cached after first call)
_ts = None
_eph = None

def _get_ephemeris():
    global _ts, _eph
    if _ts is None:
        _ts = sky_load.timescale()
        _eph = sky_load('de421.bsp')
    return _ts, _eph


def _lahiri_ayanamsa(jd):
    """Approximate Lahiri ayanamsa for a Julian date."""
    # Lahiri ayanamsa: ~23.85° at J2000.0 (2451545.0), precessing ~50.29"/year
    t_centuries = (jd - 2451545.0) / 36525.0
    return 23.85 + (50.29 / 3600.0) * t_centuries * 100


def compute_planetary_positions(dob_str, tob_str, lat, lon, tz_str="IST"):
    """
    Compute sidereal positions of all 9 Vedic planets + Lagna.

    Returns: (lagna_sign, lagna_degree, planets_list)
    where each planet is a dict with keys:
        planet, sign, house, sidereal_longitude, degree_in_sign,
        nakshatra, nakshatra_pada, is_retrograde, speed, dignity, is_combust
    """
    ts, eph = _get_ephemeris()

    # Parse date/time and convert to UTC
    dt_local = datetime.fromisoformat(f"{dob_str}T{tob_str}")
    tz_offset = TZ_OFFSETS.get(tz_str.upper(), 5.5)
    dt_utc = dt_local - timedelta(hours=tz_offset)

    t = ts.utc(dt_utc.year, dt_utc.month, dt_utc.day,
               dt_utc.hour, dt_utc.minute, dt_utc.second)

    # Ayanamsa
    jd = t.tt
    ayanamsa = _lahiri_ayanamsa(jd)

    earth = eph['earth']

    # Skyfield body names
    body_map = {
        "Sun": "sun", "Moon": "moon", "Mars": "mars",
        "Mercury": "mercury", "Jupiter": "jupiter barycenter",
        "Venus": "venus", "Saturn": "saturn barycenter",
    }

    # Compute tropical ecliptic longitudes
    tropical = {}
    speeds = {}
    for planet, body_name in body_map.items():
        body = eph[body_name]
        astrometric = earth.at(t).observe(body)
        _, ecl_lon, _ = astrometric.ecliptic_latlon()
        tropical[planet] = ecl_lon.degrees

        # Speed: compare with position 1 day later
        t_next = ts.utc(dt_utc.year, dt_utc.month, dt_utc.day + 1,
                        dt_utc.hour, dt_utc.minute, dt_utc.second)
        _, ecl_lon_next, _ = earth.at(t_next).observe(body).ecliptic_latlon()
        speed = ecl_lon_next.degrees - ecl_lon.degrees
        if speed > 180:
            speed -= 360
        elif speed < -180:
            speed += 360
        speeds[planet] = speed

    # Convert to sidereal
    sidereal = {}
    for planet, trop_lon in tropical.items():
        sid = (trop_lon - ayanamsa) % 360
        sidereal[planet] = sid

    # Rahu/Ketu: mean lunar nodes
    # Skyfield doesn't directly give lunar nodes, so compute from Moon's node
    # Using mean node approximation
    _compute_lunar_nodes(t, jd, ayanamsa, sidereal, speeds)

    # Compute Lagna (Ascendant)
    lagna_tropical = _compute_lagna_degree(dt_utc, lat, lon, t)
    lagna_sidereal = (lagna_tropical - ayanamsa) % 360
    lagna_sign = SIGNS[int(lagna_sidereal // 30)]
    lagna_degree = lagna_sidereal % 30

    # Build house map (whole sign)
    lagna_idx = SIGNS.index(lagna_sign)
    houses = {i + 1: SIGNS[(lagna_idx + i) % 12] for i in range(12)}
    sign_to_house = {sign: house for house, sign in houses.items()}

    # Sun longitude for combustion check
    sun_sid = sidereal["Sun"]

    # Build planet result list
    planets = []
    for planet_name in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]:
        sid_lon = sidereal[planet_name]
        sign_idx = int(sid_lon // 30)
        sign = SIGNS[sign_idx]
        deg_in_sign = sid_lon % 30
        house = sign_to_house.get(sign, 0)

        # Nakshatra
        nak_idx = int(sid_lon / (360 / 27))
        nak_name, nak_ruler = NAKSHATRAS[nak_idx]
        pada = int((sid_lon % (360 / 27)) / (360 / 108)) + 1

        # Retrograde
        speed = speeds.get(planet_name, 0)
        is_retro = speed < 0

        # Dignity
        dignity = _compute_dignity(planet_name, sign, deg_in_sign)

        # Combustion
        is_combust = False
        if planet_name not in ("Sun", "Rahu", "Ketu"):
            angular_dist = abs(sid_lon - sun_sid)
            if angular_dist > 180:
                angular_dist = 360 - angular_dist
            if planet_name in COMBUSTION:
                threshold = COMBUSTION[planet_name][1 if is_retro else 0]
                is_combust = angular_dist < threshold

        planets.append({
            "planet": planet_name,
            "sign": sign,
            "house": house,
            "sidereal_longitude": round(sid_lon, 4),
            "degree_in_sign": round(deg_in_sign, 4),
            "nakshatra": nak_name,
            "nakshatra_pada": pada,
            "is_retrograde": int(is_retro),
            "speed": round(speed, 4),
            "dignity": dignity,
            "is_combust": int(is_combust),
        })

    return lagna_sign, round(lagna_degree, 4), planets


def _compute_lunar_nodes(t, jd, ayanamsa, sidereal, speeds):
    """Compute mean Rahu/Ketu using standard formula."""
    # Mean longitude of Rahu (ascending node)
    # Using Meeus formula
    T = (jd - 2451545.0) / 36525.0
    # Mean longitude of ascending node (tropical)
    omega = 125.04452 - 1934.136261 * T + 0.0020708 * T * T
    omega = omega % 360
    rahu_sid = (omega - ayanamsa) % 360
    ketu_sid = (rahu_sid + 180) % 360

    sidereal["Rahu"] = rahu_sid
    sidereal["Ketu"] = ketu_sid

    # Rahu/Ketu are always retrograde, ~0.053 deg/day
    speeds["Rahu"] = -0.053
    speeds["Ketu"] = -0.053


def _compute_lagna_degree(dt_utc, lat, lon, t):
    """Compute tropical ascendant degree."""
    import math

    # Use Skyfield's precise GMST (in hours -> degrees)
    gmst_deg = t.gmst * 15.0

    # Local Sidereal Time (RAMC)
    lst = (gmst_deg + lon) % 360

    # Obliquity of ecliptic
    T = (t.tt - 2451545.0) / 36525.0
    eps = 23.4393 - 0.0130 * T
    eps_rad = math.radians(eps)
    lat_rad = math.radians(lat)
    lst_rad = math.radians(lst)

    # Ascendant formula with quadrant correction:
    # ASC = atan(-cos(RAMC) / (sin(eps)*tan(lat) + cos(eps)*sin(RAMC)))
    # When RAMC is in 180-360, ASC must be in 0-180 and vice versa.
    numerator = -math.cos(lst_rad)
    denominator = (math.sin(eps_rad) * math.tan(lat_rad)
                   + math.cos(eps_rad) * math.sin(lst_rad))
    asc = math.degrees(math.atan(numerator / denominator)) if denominator != 0 else 0.0

    if lst >= 180:
        asc = asc % 180          # ASC in 0..180
    else:
        asc = (asc % 180) + 180  # ASC in 180..360

    return asc


def _compute_dignity(planet, sign, deg_in_sign):
    """Determine dignity level of a planet in a sign."""
    # Exaltation
    if planet in EXALTATION:
        ex_sign, _ = EXALTATION[planet]
        if sign == ex_sign:
            return "exalted"

    # Debilitation
    if planet in DEBILITATION:
        deb_sign, _ = DEBILITATION[planet]
        if sign == deb_sign:
            return "debilitated"

    # Moolatrikona
    if planet in MOOLATRIKONA:
        mt_sign, mt_start, mt_end = MOOLATRIKONA[planet]
        if sign == mt_sign and mt_start <= deg_in_sign <= mt_end:
            return "moolatrikona"

    # Own sign
    if sign in OWNERSHIP.get(planet, []):
        return "own"

    # Friendly / Enemy / Neutral (based on sign ruler)
    sign_ruler = _sign_ruler(sign)
    if sign_ruler == planet:
        return "own"
    if sign_ruler in FRIENDS.get(planet, set()):
        return "friendly"
    if sign_ruler in ENEMIES.get(planet, set()):
        return "enemy"

    return "neutral"


def _sign_ruler(sign):
    """Get the ruling planet of a sign."""
    rulers = {
        "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury",
        "Cancer": "Moon", "Leo": "Sun", "Virgo": "Mercury",
        "Libra": "Venus", "Scorpio": "Mars", "Sagittarius": "Jupiter",
        "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter",
    }
    return rulers[sign]


# ---------------------------------------------------------------------------
# Database operations
# ---------------------------------------------------------------------------

def store_kundali(person_data, lagna_sign, lagna_degree, planets):
    """Store person + natal planets in the v2 database."""
    conn = get_connection()
    cur = conn.cursor()

    # Insert or update person
    cur.execute(
        """INSERT OR REPLACE INTO person
           (name, dob, tob, latitude, longitude, timezone, place_name, ayanamsa, lagna_sign, lagna_degree)
           VALUES (?, ?, ?, ?, ?, ?, ?, 'Lahiri', ?, ?)""",
        (person_data["name"], person_data["dob"], person_data["tob"],
         person_data["lat"], person_data["lon"],
         person_data.get("tz", "IST"), person_data.get("place", ""),
         lagna_sign, lagna_degree),
    )
    person_id = cur.lastrowid

    # Insert natal planets
    for p in planets:
        cur.execute(
            """INSERT OR REPLACE INTO natal_planet
               (person_id, planet, sign, house, sidereal_longitude, degree_in_sign,
                nakshatra, nakshatra_pada, is_retrograde, is_combust, dignity, speed, strength)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1.0)""",
            (person_id, p["planet"], p["sign"], p["house"],
             p["sidereal_longitude"], p["degree_in_sign"],
             p["nakshatra"], p["nakshatra_pada"],
             p["is_retrograde"], p["is_combust"], p["dignity"], p["speed"]),
        )

    conn.commit()
    conn.close()
    return person_id


# ---------------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------------

def print_kundali(name, lagna_sign, lagna_degree, planets):
    """Pretty-print the computed kundali."""
    print(f"\n{'=' * 60}")
    print(f"  KUNDALI: {name}")
    print(f"{'=' * 60}")
    print(f"  Lagna (Ascendant): {lagna_sign} ({lagna_degree:.2f})")

    # Sun/Moon signs
    sun = next(p for p in planets if p["planet"] == "Sun")
    moon = next(p for p in planets if p["planet"] == "Moon")
    print(f"  Sun Sign:  {sun['sign']}  |  Moon Sign: {moon['sign']}")
    print(f"  Moon Nakshatra: {moon['nakshatra']} (Pada {moon['nakshatra_pada']})")
    print()

    # Planet table
    hdr = f"  {'Planet':<9s} {'Sign':<13s} {'H':>2s}  {'Deg':>7s}  {'Nakshatra':<20s} {'Pd':>2s} {'R':>1s} {'C':>1s} {'Dignity':<12s}"
    print(hdr)
    print(f"  {'-' * len(hdr.strip())}")
    for p in planets:
        retro = "R" if p["is_retrograde"] else ""
        combust = "C" if p["is_combust"] else ""
        print(f"  {p['planet']:<9s} {p['sign']:<13s} {p['house']:>2d}  "
              f"{p['degree_in_sign']:>7.2f}  {p['nakshatra']:<20s} {p['nakshatra_pada']:>2d} "
              f"{retro:>1s} {combust:>1s} {p['dignity']:<12s}")

    print()


# ---------------------------------------------------------------------------
# Main CLI
# ---------------------------------------------------------------------------

def process_one(data):
    """Compute and store kundali for one person."""
    lagna_sign, lagna_degree, planets = compute_planetary_positions(
        data["dob"], data["tob"], data["lat"], data["lon"],
        data.get("tz", "IST"),
    )

    person_id = store_kundali(data, lagna_sign, lagna_degree, planets)
    print_kundali(data["name"], lagna_sign, lagna_degree, planets)
    print(f"  Stored as person_id={person_id} in astro_v2.db")
    print()
    return person_id


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    if sys.argv[1] == "--file":
        filepath = sys.argv[2]
        with open(filepath, "r") as f:
            data = json.load(f)
    else:
        data = json.loads(sys.argv[1])

    # Handle single object or array
    if isinstance(data, list):
        for entry in data:
            process_one(entry)
    else:
        process_one(data)


if __name__ == "__main__":
    main()
