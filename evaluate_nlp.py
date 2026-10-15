import csv
from pathlib import Path

from app.nlp.job_parser import parse_job_description

BASE_DIR = Path(__file__).resolve().parent
DATASET = BASE_DIR / "data" / "evaluation" / "nlp_test_dataset.csv"
OUTPUT = BASE_DIR / "data" / "evaluation" / "nlp_evaluation_results.csv"


SKILL_ALIASES = {
    "premiere pro": "adobe premiere pro",
    "adobe premiere pro": "adobe premiere pro",
    "after effects": "after effects",
    "adobe after effects": "after effects",
    "davinci resolve": "davinci resolve",
    "resolve": "davinci resolve",
    "final cut pro": "final cut pro",
    "capcut": "capcut",
}

def normalize(values, category=None):
    normalized = set()

    for value in values:
        cleaned = value.strip().casefold()

        if not cleaned:
            continue

        if category == "skills":
            cleaned = SKILL_ALIASES.get(cleaned, cleaned)

        normalized.add(cleaned)

    return normalized


def parse_expected(value, category):
    return normalize(value.split("|"), category)


def evaluate():
    categories = ["skills", "styles", "niches"]

    scores = {
        category: {"tp": 0, "fp": 0, "fn": 0}
        for category in categories
    }

    results = []

    with DATASET.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            prediction = parse_job_description(row["job_description"])

            result = {
                "job_id": row["job_id"],
                "job_description": row["job_description"],
            }

            for category in categories:
                expected = parse_expected(
                  row[f"expected_{category}"], category
                )
                predicted = normalize(
                  prediction[category], category
                )

                tp = len(expected & predicted)
                fp = len(predicted - expected)
                fn = len(expected - predicted)

                scores[category]["tp"] += tp
                scores[category]["fp"] += fp
                scores[category]["fn"] += fn

                result[f"{category}_expected"] = "|".join(sorted(expected))
                result[f"{category}_predicted"] = "|".join(sorted(predicted))
                result[f"{category}_tp"] = tp
                result[f"{category}_fp"] = fp
                result[f"{category}_fn"] = fn

            results.append(result)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    print("\n===== NLP EVALUATION RESULTS =====")

    for category, counts in scores.items():
        tp = counts["tp"]
        fp = counts["fp"]
        fn = counts["fn"]

        precision = tp / (tp + fp) if tp + fp else 0
        recall = tp / (tp + fn) if tp + fn else 0
        f1 = (
            2 * precision * recall / (precision + recall)
            if precision + recall else 0
        )

        print(f"\n{category.upper()}")
        print(f"True Positives: {tp}")
        print(f"False Positives: {fp}")
        print(f"False Negatives: {fn}")
        print(f"Precision: {precision:.2%}")
        print(f"Recall: {recall:.2%}")
        print(f"F1-score: {f1:.2%}")

    print(f"\nDetailed results saved to: {OUTPUT}")


if __name__ == "__main__":
    evaluate()
