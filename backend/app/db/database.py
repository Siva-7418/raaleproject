import sqlite3
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DB_DIR = BASE_DIR / "data"
DB_PATH = DB_DIR / "app.db"
SCHEMA_PATH = BASE_DIR / "backend" / "app" / "db" / "schema.sql"

def get_db_path(db_file=None):
    if db_file:
        return Path(db_file)
    DB_DIR.mkdir(parents=True, exist_ok=True)
    return DB_PATH

def get_connection(db_file=None):
    target_path = get_db_path(db_file)
    conn = sqlite3.connect(target_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db(db_file=None):
    target_path = get_db_path(db_file)
    if target_path != Path(":memory:"):
        target_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()
    
    conn = get_connection(db_file)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='identities';")
        table_exists = cursor.fetchone()
        
        if not table_exists:
            conn.executescript(schema_sql)
            conn.commit()
    finally:
        conn.close()

if __name__ == "__main__":
    init_db()
    print(f"Database initialized successfully at {DB_PATH}")
