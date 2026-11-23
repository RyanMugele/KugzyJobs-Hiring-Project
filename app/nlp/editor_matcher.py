
"""NLP-based matching between video editing jobs and editors."""

import re


def normalize_terms(value):
    """Convert comma-separated text or lists into normalized terms."""
    if not value:
        return set()

    if isinstance(value, str):
        value = value.strip()

        # Remove brackets from stored list representations
        if value.startswith("[") and value.endswith("]"):
            value = value[1:-1]

        terms = re.split(r"[,;]", value)

    elif isinstance(value, (list, tuple, set)):
        terms = value

    else:
        return set()

    return {
        str(term).strip().strip("'\"").strip().lower()
        for term in terms
        if str(term).strip().strip("'\"").strip()
    }


def calculate_match_score(job_data, editor_data):
    """
    Calculate an editor's compatibility with a job.

    Both arguments are dictionaries containing skills,
    styles and niches.
    """
    weights = {
        "skills": 0.50,
        "styles": 0.25,
        "niches": 0.25,
    }

    total_score = 0.0
    available_weight = 0.0

    for category, weight in weights.items():
        required = normalize_terms(job_data.get(category))
        offered = normalize_terms(editor_data.get(category))

        if not required:
            continue

        available_weight += weight
        matched = required.intersection(offered)
        category_score = len(matched) / len(required)
        total_score += category_score * weight

    if available_weight == 0:
        return 0.0

    return round((total_score / available_weight) * 100, 2)
