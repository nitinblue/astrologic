from kundali_engine.core.database.connection import get_connection

def load_kundali():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT OR REPLACE INTO person
        VALUES (2, 'Name', 'YYYY-mm-dd', '09:45', 21.19, 81.28, 'IST')
    """)

    planets = [
        ("Sun", "Aquarius", 11, 0.6),
        ("Moon", "Sagittarius", 9, 0.8),
        ("Mars", "Aries", 1, 0.9),
        ("Mercury", "Aquarius", 11, 0.7),
        ("Jupiter", "Sagittarius", 9, 0.9),
        ("Venus", "Capricorn", 10, 0.6),
        ("Saturn", "Aquarius", 11, 0.9),
        ("Rahu", "Cancer", 4, 0.7),
        ("Ketu", "Capricorn", 10, 0.7)
    ]

    for p in planets:
        cur.execute(
            "INSERT OR REPLACE INTO natal_planet VALUES (1,?,?,?,?)", p
        )

    cur.execute("""
        INSERT OR REPLACE INTO dasha
        (person_id, level, planet, start_date, end_date)
        VALUES (1, 'maha', 'Saturn', '2020-01-01', '2039-01-01')
    """)

    conn.commit()
    conn.close()

    print("✅ Kundali loaded into database")

if __name__ == "__main__":
    load_kundali()
