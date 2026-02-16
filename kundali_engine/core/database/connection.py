import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[3] / "astro.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
