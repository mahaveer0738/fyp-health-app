"""
Database Migration Script — Adds new columns to visit_history table.
Run this once to upgrade your existing database schema.

Usage:
    python -m backend.db.migrate
"""
import sqlite3
import os

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = os.path.join(BACKEND_DIR, "data", "fyp_health.db")

# New columns to add to the visit_history table
NEW_COLUMNS = [
    ("triage_confidence", "REAL"),
    ("heart_rate", "REAL"),
    ("systolic_bp", "REAL"),
    ("oxygen_saturation", "REAL"),
    ("body_temperature", "REAL"),
    ("pain_level", "INTEGER"),
    ("latitude", "REAL"),
    ("longitude", "REAL"),
    ("location_string", "TEXT"),
    ("arrival_mode", "TEXT"),
    ("input_mode", "TEXT DEFAULT 'manual'"),
    ("ocr_extracted", "BOOLEAN DEFAULT 0"),
]

def migrate():
    if not os.path.exists(db_path):
        print(f"[ERROR] Database not found at: {db_path}")
        print("   Run the backend server first to create it.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get existing columns in visit_history
    cursor.execute("PRAGMA table_info(visit_history);")
    existing_cols = {row[1] for row in cursor.fetchall()}
    print(f"[INFO] Existing columns: {existing_cols}")

    added = 0
    for col_name, col_type in NEW_COLUMNS:
        if col_name not in existing_cols:
            sql = f"ALTER TABLE visit_history ADD COLUMN {col_name} {col_type};"
            print(f"   [+] Adding column: {col_name} ({col_type})")
            cursor.execute(sql)
            added += 1
        else:
            print(f"   [=] Column already exists: {col_name}")

    conn.commit()
    conn.close()

    if added > 0:
        print(f"\n[DONE] Migration complete! Added {added} new column(s) to visit_history.")
    else:
        print(f"\n[OK] No migration needed -- all columns already exist.")

if __name__ == "__main__":
    migrate()
