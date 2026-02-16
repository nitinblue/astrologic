from kundali_engine.core.database.connection import get_connection
from kundali_engine.chart.kundali import Kundali
from kundali_engine.core.birth import BirthData
from kundali_engine.core.planet import PlanetPosition
from datetime import datetime


SIGNS = [
    "Aries","Taurus","Gemini","Cancer","Leo","Virgo",
    "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"
]

ELEMENT_MAP = {
    "Aries": "Fire", "Leo": "Fire", "Sagittarius": "Fire",
    "Taurus": "Earth", "Virgo": "Earth", "Capricorn": "Earth",
    "Gemini": "Air", "Libra": "Air", "Aquarius": "Air",
    "Cancer": "Water", "Scorpio": "Water", "Pisces": "Water"
}

MODALITY_MAP = {
    "Aries": "Cardinal", "Cancer": "Cardinal", "Libra": "Cardinal", "Capricorn": "Cardinal",
    "Taurus": "Fixed", "Leo": "Fixed", "Scorpio": "Fixed", "Aquarius": "Fixed",
    "Gemini": "Mutable", "Virgo": "Mutable", "Sagittarius": "Mutable", "Pisces": "Mutable"
}

PLANET_HINDI_MAP = {
    "Sun": "सूर्य",
    "Moon": "चंद्र",
    "Mars": "मंगल",
    "Mercury": "बुध",
    "Jupiter": "गुरु",
    "Venus": "शुक्र",
    "Saturn": "शनि",
    "Rahu": "राहु",
    "Ketu": "केतु"
}

SIGN_HINDI_MAP = {
    "Aries": "मेष",
    "Taurus": "वृषभ",
    "Gemini": "मिथुन",
    "Cancer": "कर्क",
    "Leo": "सिंह",
    "Virgo": "कन्या",
    "Libra": "तुला",
    "Scorpio": "वृश्चिक",
    "Sagittarius": "धनु",
    "Capricorn": "मकर",
    "Aquarius": "कुंभ",
    "Pisces": "मीन"
}


def western_sun_sign(month: int, day: int) -> str:
    # Approximate tropical sun sign (sufficient for identity display)
    boundaries = [
        (3, 21, "Aries"), (4, 20, "Taurus"), (5, 21, "Gemini"),
        (6, 21, "Cancer"), (7, 23, "Leo"), (8, 23, "Virgo"),
        (9, 23, "Libra"), (10, 23, "Scorpio"), (11, 22, "Sagittarius"),
        (12, 22, "Capricorn"), (1, 20, "Aquarius"), (2, 19, "Pisces")
    ]

    for m, d, sign in boundaries:
        if (month, day) >= (m, d):
            return sign
    return "Pisces"


def load_kundali_from_db(person_id: int = 1) -> Kundali:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM person WHERE id = ?", (person_id,))
    person = cur.fetchone()
    if not person:
        raise ValueError("Person not found")

    birth_data = BirthData(
        date_time_utc=datetime.fromisoformat(person["dob"] + "T" + person["tob"]),
        latitude=person["latitude"],
        longitude=person["longitude"]
    )

    cur.execute("SELECT * FROM natal_planet WHERE person_id = ?", (person_id,))
    planets = {}
    for row in cur.fetchall():
        planets[row["planet"]] = PlanetPosition(
            name=row["planet"],
            longitude=0.0,
            sign=row["sign"],
            house=row["house"],
            nakshatra=None,
            retrograde=False
        )

    # Lagna = sign ruling house 1
    lagna = next(p.sign for p in planets.values() if p.house == 1)

    start = SIGNS.index(lagna)
    houses = {i + 1: SIGNS[(start + i) % 12] for i in range(12)}

    conn.close()
    return Kundali(birth_data, lagna, planets, houses)


if __name__ == "__main__":
    kundali = load_kundali_from_db(1)

    sun_sign = kundali.planets["Sun"].sign
    moon_sign = kundali.planets["Moon"].sign
    rising_sign = kundali.lagna

    dob = kundali.birth_data.date_time_utc
    western_sun = western_sun_sign(dob.month, dob.day)

    print("\n=== STATIC ASTRO PROFILE ===\n")
    #print(f"Vedic Sun Sign     : {sun_sign}")
    #print(f"Vedic Moon Sign    : {moon_sign}")
    #print(f"Vedic Rising (Lagna): {rising_sign}")
    #print(f"Western Sun Sign   : {western_sun}")

    print(f"Vedic Sun Sign      : {sun_sign} ({SIGN_HINDI_MAP[sun_sign]})")
    print(f"Vedic Moon Sign     : {moon_sign} ({SIGN_HINDI_MAP[moon_sign]})")
    print(f"Vedic Rising (Lagna): {rising_sign} ({SIGN_HINDI_MAP[rising_sign]})")
    print(f"Western Sun Sign    : {western_sun} ({SIGN_HINDI_MAP[western_sun]})")
    
    print("\n--- Planetary Placements (Natal) ---")
    for p in kundali.planets.values():
        print(f"{p.name:<8} : {p.sign:<12} | House {p.house}")

    elements = {}
    modalities = {}

    for p in kundali.planets.values():
        elements[ELEMENT_MAP[p.sign]] = elements.get(ELEMENT_MAP[p.sign], 0) + 1
        modalities[MODALITY_MAP[p.sign]] = modalities.get(MODALITY_MAP[p.sign], 0) + 1

    print("\n--- Dominance Summary ---")
    print("Elements :", elements)
    print("Modalities:", modalities)

    print("\n(These values are immutable and should be cached.)")
