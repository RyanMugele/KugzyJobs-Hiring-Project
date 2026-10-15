import sqlite3
import json

DB_PATH = "development.db"

connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()

cursor.execute("""
    SELECT jobId, title, extractedSkills,
           extractedStyles, extractedNiches
    FROM job
    ORDER BY jobId DESC
    LIMIT 10
""")

jobs = cursor.fetchall()

if not jobs:
    print("No jobs found in database.")

for job in jobs:
    job_id, title, skills, styles, niches = job

    print(f"\nJob ID: {job_id}")
    print(f"Title: {title}")

    for label, value in [
        ("Skills", skills),
        ("Styles", styles),
        ("Niches", niches)
    ]:
        try:
            parsed = json.loads(value) if value else []
            valid = isinstance(parsed, list)
            print(f"{label}: {parsed}")
            print(f"{label} JSON valid: {valid}")
        except (TypeError, ValueError) as error:
            print(f"{label} JSON invalid: {error}")

connection.close()
