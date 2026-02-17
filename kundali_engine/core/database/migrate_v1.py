"""
Migrate data from v1 schema (astro.db) to v2 schema (astro_v2.db).

Migrates:
  - person table (adds new nullable columns)
  - natal_planet table (maps old columns to new, adds nullable new columns)
  - dasha table (maps to new schema with parent_dasha_id)
  - astro_regime_snapshot (maps to enhanced schema)
"""
import sqlite3
from pathlib import Path

V1_DB = Path(__file__).resolve().parents[3] / "astro.db"
V2_DB = Path(__file__).resolve().parents[3] / "astro_v2.db"


def migrate():
    if not V1_DB.exists():
        print(f"No v1 database found at {V1_DB}, skipping migration")
        return

    if not V2_DB.exists():
        print(f"v2 database not found at {V2_DB}. Run init_db.py first.")
        return

    v1 = sqlite3.connect(V1_DB)
    v1.row_factory = sqlite3.Row
    v2 = sqlite3.connect(V2_DB)
    v2.execute("PRAGMA foreign_keys = ON")

    _migrate_person(v1, v2)
    _migrate_natal_planet(v1, v2)
    _migrate_dasha(v1, v2)
    _migrate_regime(v1, v2)

    v2.commit()
    v1.close()
    v2.close()
    print("Migration from v1 to v2 complete")


def _migrate_person(v1, v2):
    rows = v1.execute("SELECT * FROM person").fetchall()
    count = 0
    for r in rows:
        v2.execute(
            """INSERT OR REPLACE INTO person
               (id, name, dob, tob, latitude, longitude, timezone)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (r["id"], r["name"], r["dob"], r["tob"],
             r["latitude"], r["longitude"], r["timezone"]),
        )
        count += 1
    print(f"  Migrated {count} person rows")


def _migrate_natal_planet(v1, v2):
    rows = v1.execute("SELECT * FROM natal_planet").fetchall()
    count = 0
    for r in rows:
        v2.execute(
            """INSERT OR REPLACE INTO natal_planet
               (person_id, planet, sign, house, strength)
               VALUES (?, ?, ?, ?, ?)""",
            (r["person_id"], r["planet"], r["sign"],
             r["house"], r["strength"]),
        )
        count += 1
    print(f"  Migrated {count} natal_planet rows")


def _migrate_dasha(v1, v2):
    rows = v1.execute("SELECT * FROM dasha").fetchall()
    count = 0
    for r in rows:
        v2.execute(
            """INSERT OR REPLACE INTO dasha
               (id, person_id, level, planet, start_date, end_date)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (r["id"], r["person_id"], r["level"], r["planet"],
             r["start_date"], r["end_date"]),
        )
        count += 1
    print(f"  Migrated {count} dasha rows")


def _migrate_regime(v1, v2):
    # Check if any data exists
    rows = v1.execute("SELECT * FROM astro_regime_snapshot").fetchall()
    count = 0
    for r in rows:
        v2.execute(
            """INSERT OR REPLACE INTO astro_regime_snapshot
               (person_id, date, directional_bias, volatility_bias,
                risk_multiplier, allowed_strategies, favored_sectors, explanation)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (r["person_id"], r["date"], r["directional_bias"],
             r["volatility_bias"], r["risk_multiplier"],
             r["allowed_strategies"], r["favored_sectors"],
             r["explanation"]),
        )
        count += 1
    if count:
        print(f"  Migrated {count} astro_regime_snapshot rows")
    else:
        print("  No astro_regime_snapshot data to migrate")


if __name__ == "__main__":
    migrate()
