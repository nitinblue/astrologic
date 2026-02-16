from pathlib import Path
from .connection import get_connection

def initialize_database():
    conn = get_connection()
    cur = conn.cursor()

    schema_path = Path(__file__).parent / "schema.sql"
    with open(schema_path, "r") as f:
        schema_sql = f.read()

    cur.executescript(schema_sql)
    conn.commit()
    conn.close()

    print("✅ Astro database initialized")

if __name__ == "__main__":
    initialize_database()
