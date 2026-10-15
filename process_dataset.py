import csv
import json
from pathlib import Path

from app.nlp.job_parser import parse_job_description

# Locate the project directory
BASE_DIR = Path(__file__).resolve().parent

# Input and output locations
INPUT_FILE = BASE_DIR / "data" / "raw" / "job_descriptions.csv"
OUTPUT_FILE = BASE_DIR / "data" / "processed" / "parsed_jobs.csv"


def process_dataset():
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with INPUT_FILE.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        if not {"job_id", "description"}.issubset(reader.fieldnames or []):
            raise ValueError("CSV must contain job_id and description columns.")

        jobs = list(reader)

    processed_jobs = []

    for job in jobs:
        description = job["description"]
        result = parse_job_description(description)

        processed_jobs.append({
            "job_id": job["job_id"],
            "description": description,
            "skills": json.dumps(result["skills"]),
            "styles": json.dumps(result["styles"]),
            "niches": json.dumps(result["niches"]),
        })

    with OUTPUT_FILE.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "job_id",
                "description",
                "skills",
                "styles",
                "niches",
            ],
        )

        writer.writeheader()
        writer.writerows(processed_jobs)

    print(f"Successfully processed {len(processed_jobs)} jobs!")
    print(f"Results saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    process_dataset()
