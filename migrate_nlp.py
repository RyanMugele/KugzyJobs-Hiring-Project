import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "development.db"

new_columns = {
    "extractedSkills": "TEXT",
    "extractedStyles": "TEXT",
    "extractedNiches": "TEXT",
}

with sqlite3.connect(DB_PATH) as conn:
    existing = {
        row[1]
        for row in conn.execute("PRAGMA table_info(job)")
    }

    if not existing:
        raise RuntimeError("Job table not found. Check database path.")

    for column, column_type in new_columns.items():
        if column not in existing:
            conn.execute(
                f'ALTER TABLE job ADD COLUMN "{column}" {column_type}'
            )
            print(f"Added column: {column}")
        else:
            print(f"Column already exists: {column}")

    conn.commit()

print("NLP database migration completed successfully!")
