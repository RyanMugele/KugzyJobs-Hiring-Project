
"""NLP Test 07: Evaluate job description extraction accuracy."""

from app.nlp.job_parser import parse_job_description

# Ground-truth labels manually defined for each description.
# These test cases are illustrative, not a real-world benchmark.
TEST_CASES = [
    {
        "text": "Need a gaming editor skilled in CapCut for fast-paced TikTok videos.",
        "expected": {
            "skills": ["CapCut"],
            "styles": ["fast-paced", "short-form"],
            "niches": ["gaming"],
        },
    },
    {
        "text": "Looking for a wedding editor proficient in DaVinci Resolve and color grading, with a cinematic style.",
        "expected": {
            "skills": ["DaVinci Resolve", "Color Grading"],
            "styles": ["cinematic"],
            "niches": ["wedding"],
        },
    },
    {
        "text": "Need a documentary editor for long-form YouTube videos with subtitles.",
        "expected": {
            "skills": ["Subtitling"],
            "styles": ["documentary"],
            "niches": ["documentary"],
        },
    },
    {
        "text": "Hiring a corporate editor who can create motion graphics and smooth transitions.",
        "expected": {
            "skills": ["Motion Graphics", "Transitions"],
            "styles": [],
            "niches": ["corporate"],
        },
    },
    {
        "text": "Seeking a travel vlogger editor who uses Adobe Premiere Pro.",
        "expected": {
            "skills": ["Adobe Premiere Pro"],
            "styles": [],
            "niches": ["travel"],
        },
    },
    {
        "text": "Need a sports highlights editor using After Effects for fast-paced cuts.",
        "expected": {
            "skills": ["After Effects"],
            "styles": ["fast-paced"],
            "niches": ["sports"],
        },
    },
    {
        "text": "Looking for a fitness content editor experienced with CapCut.",
        "expected": {
            "skills": ["CapCut"],
            "styles": [],
            "niches": ["fitness"],
        },
    },
    {
        "text": "Need a technology review editor using Final Cut Pro.",
        "expected": {
            "skills": ["Final Cut Pro"],
            "styles": [],
            "niches": ["technology"],
        },
    },
    {
        "text": "Hiring a beauty tutorial editor for Instagram Reels with captions.",
        "expected": {
            "skills": ["Subtitling"],
            "styles": ["short-form"],
            "niches": ["beauty"],
        },
    },
    {
        "text": "Need an educational video editor who creates tutorial videos with sound design.",
        "expected": {
            "skills": ["Sound Design"],
            "styles": [],
            "niches": ["education"],
        },
    },
    {
        "text": "Looking for a lifestyle editor for minimalist videos.",
        "expected": {
            "skills": [],
            "styles": ["minimalist"],
            "niches": ["lifestyle"],
        },
    },
    {
        "text": "Need a gaming editor for YouTube Shorts with subtitles and transitions.",
        "expected": {
            "skills": ["Subtitling", "Transitions"],
            "styles": ["short-form"],
            "niches": ["gaming"],
        },
    },
    {
        "text": "Hiring a corporate editor experienced in Adobe Premiere Pro and motion graphics.",
        "expected": {
            "skills": ["Adobe Premiere Pro", "Motion Graphics"],
            "styles": [],
            "niches": ["corporate"],
        },
    },
    {
        "text": "Need a wedding video editor for cinematic storytelling.",
        "expected": {
            "skills": [],
            "styles": ["cinematic", "storytelling"],
            "niches": ["wedding"],
        },
    },
    {
        "text": "Looking for a documentary editor with color correction experience.",
        "expected": {
            "skills": ["Color Grading"],
            "styles": ["documentary"],
            "niches": ["documentary"],
        },
    },
    {
        "text": "Need someone to edit gaming streams into quick cuts.",
        "expected": {
            "skills": [],
            "styles": ["fast-paced"],
            "niches": ["gaming"],
        },
    },
    {
        "text": "Looking for a creator who can produce montage videos with After Effects.",
        "expected": {
            "skills": ["After Effects"],
            "styles": ["montage"],
            "niches": [],
        },
    },
    {
        "text": "Need a professional editor with experience in audio editing and captions.",
        "expected": {
            "skills": ["Sound Design", "Subtitling"],
            "styles": [],
            "niches": [],
        },
    },
    {
        "text": "Hiring an editor for gaming highlights using DaVinci Resolve.",
        "expected": {
            "skills": ["DaVinci Resolve"],
            "styles": [],
            "niches": ["gaming"],
        },
    },
    {
        "text": "Looking for an editor to produce short-form travel videos using CapCut.",
        "expected": {
            "skills": ["CapCut"],
            "styles": ["short-form"],
            "niches": ["travel"],
        },
    },
]


def normalize(values):
    return {str(value).strip().lower() for value in (values or [])}


def evaluate():
    categories = ("skills", "styles", "niches")
    totals = {
        category: {"tp": 0, "fp": 0, "fn": 0}
        for category in categories
    }

    exact_matches = 0

    print("\nNLP TEST 07 - EXTRACTION ACCURACY")
    print("=" * 65)

    for index, case in enumerate(TEST_CASES, start=1):
        actual = parse_job_description(case["text"])
        all_correct = True

        for category in categories:
            expected_set = normalize(case["expected"][category])
            actual_set = normalize(actual.get(category, []))

            totals[category]["tp"] += len(expected_set & actual_set)
            totals[category]["fp"] += len(actual_set - expected_set)
            totals[category]["fn"] += len(expected_set - actual_set)

            if expected_set != actual_set:
                all_correct = False
                print(f"\nCase {index} - {category.upper()}")
                print("Description:", case["text"])
                print("Expected:", sorted(expected_set))
                print("Actual:  ", sorted(actual_set))

        if all_correct:
            exact_matches += 1

    print("\n" + "=" * 65)
    print("CATEGORY METRICS")
    print("-" * 65)

    overall = {"tp": 0, "fp": 0, "fn": 0}

    for category in categories:
        counts = totals[category]

        tp = counts["tp"]
        fp = counts["fp"]
        fn = counts["fn"]

        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = (
            2 * precision * recall / (precision + recall)
            if precision + recall else 0.0
        )

        print(
            f"{category.title():10} "
            f"Precision: {precision:.2%} | "
            f"Recall: {recall:.2%} | "
            f"F1: {f1:.2%}"
        )

        for key in overall:
            overall[key] += counts[key]

    tp, fp, fn = overall["tp"], overall["fp"], overall["fn"]

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall else 0.0
    )

    print("-" * 65)
    print(f"Overall precision: {precision:.2%}")
    print(f"Overall recall:    {recall:.2%}")
    print(f"Overall F1-score:  {f1:.2%}")
    print(
        f"Exact case matches: {exact_matches}/{len(TEST_CASES)} "
        f"({exact_matches / len(TEST_CASES):.2%})"
    )


if __name__ == "__main__":
    evaluate()
