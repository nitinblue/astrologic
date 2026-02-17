from pathlib import Path
from .connection import get_connection


def initialize_database():
    conn = get_connection()
    cur = conn.cursor()

    schema_path = Path(__file__).parent / "schema_v2.sql"
    with open(schema_path, "r") as f:
        schema_sql = f.read()

    cur.executescript(schema_sql)
    conn.commit()
    conn.close()

    # Seed reference data after schema creation
    from .seed_reference_data import seed_all
    seed_all()

    # Seed interpretation tables (life themes, karmic axis, planet meanings)
    from .seed_interpretation_data import seed_interpretation_tables
    seed_interpretation_tables()

    print("Database initialized with v2 schema + interpretation data")


if __name__ == "__main__":
    initialize_database()
