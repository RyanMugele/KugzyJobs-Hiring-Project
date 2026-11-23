
import re

import spacy
from spacy.matcher import PhraseMatcher


# Lightweight tokenizer for phrase matching.
nlp = spacy.blank("en")


# Canonical labels and their recognized alternatives.
VOCABULARY = {
    "skills": {
        "Adobe Premiere Pro": [
            "Adobe Premiere Pro", "Premiere Pro",
            "Adobe Premiere", "Premiere specialist",
            "Premiere editing",
        ],
        "After Effects": [
            "After Effects", "Adobe After Effects",
        ],
        "DaVinci Resolve": [
            "DaVinci Resolve", "Davinci",
        ],
        "Final Cut Pro": [
            "Final Cut Pro", "FCP",
        ],
        "CapCut": ["CapCut"],
        "Color Grading": [
            "Color Grading",
            "Colour Grading",
            "Color Correction",
            "Colour Correction",
            "Colorist",
            "Colourist",
        ],
        "Motion Graphics": [
            "Motion Graphics", "Animated Graphics",
        ],
        "Sound Design": [
            "Sound Design", "Audio Editing",
        ],
        "Subtitling": [
            "Subtitles", "Subtitling", "Captions",
            "Closed Captions",
        ],
        "Transitions": [
            "Transitions",
            "Smooth Transitions",
            "Video Transitions",
            "Transition Effects",
            "Seamless Transitions",
        ],
    },
    "styles": {
        "fast-paced": [
            "Fast-paced", "Fast paced", "Fast cuts",
            "Quick cuts", "Rapid cuts",
        ],
        "cinematic": [
            "Cinematic", "Film-like",
        ],
        "documentary": ["Documentary"],
        "montage": ["Montage", "Highlight Montage"],
        "short-form": [
            "Short-form", "Short form", "Shortform",
            "TikTok videos", "TikToks",
            "Instagram Reels", "YouTube Shorts",
        ],
        "storytelling": [
            "Storytelling", "Narrative Editing",
        ],
        "minimalist": [
            "Minimalist", "Minimal Editing",
        ],
    },
    "niches": {
        "gaming": [
            "Gaming", "Gaming Streams",
            "Gaming Highlights",
        ],
        "travel": ["Travel", "Travel Vlogs"],
        "lifestyle": ["Lifestyle"],
        "sports": ["Sports", "Sporting"],
        "education": [
            "Education", "Educational",
            "Tutorial Videos",
        ],
        "technology": [
            "Technology", "Tech Reviews",
        ],
        "beauty": [
            "Beauty", "Makeup Tutorials",
        ],
        "fitness": [
            "Fitness", "Workout Videos",
        ],
        "documentary": [
            "Documentary Editor",
            "Documentary Content",
        ],
        "wedding": [
            "Wedding",
            "Wedding Video",
            "Wedding Videography",
            "Wedding Film",
            "Wedding Highlights",
            "Wedding Editor",
        ],
        "corporate": [
            "Corporate",
            "Corporate Video",
            "Corporate Video Editor",
            "Business Video",
            "Company Video",
            "Promotional Video",
        ],
    },
}


matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
MATCH_LABELS = {}

for category, labels in VOCABULARY.items():
    for canonical, alternatives in labels.items():
        key = f"{category}::{canonical}"
        patterns = [nlp.make_doc(term) for term in alternatives]
        matcher.add(key, patterns)
        MATCH_LABELS[key] = (category, canonical)


def normalize_text(text):
    """Normalize whitespace and common hyphen variants."""
    text = re.sub(r"[\u2010-\u2015]", "-", text)
    return re.sub(r"\s+", " ", text).strip()


def parse_job_description(description):
    """
    Extract canonical skills, editing styles, and content niches.

    Returns:
        dict: {'skills': [], 'styles': [], 'niches': []}
    """
    if not isinstance(description, str):
        raise ValueError("Job description must be text.")

    description = normalize_text(description)

    if not description:
        raise ValueError("Job description cannot be empty.")

    doc = nlp(description)
    results = {
        "skills": [],
        "styles": [],
        "niches": [],
    }

    matches = sorted(
        matcher(doc),
        key=lambda match: (
            -(match[2] - match[1]),
            match[1],
        ),
    )

    used_tokens = set()

    for match_id, start, end in matches:
        if any(i in used_tokens for i in range(start, end)):
            continue

        key = nlp.vocab.strings[match_id]
        category, canonical = MATCH_LABELS[key]

        if canonical not in results[category]:
            results[category].append(canonical)

        used_tokens.update(range(start, end))

    # Maintain the original parser's special handling of
    # "documentary editor" as a content niche.
    if re.search(r"\bdocumentary\s+editors?\b", description, re.I):
        if "documentary" not in results["niches"]:
            results["niches"].append("documentary")
        results["styles"] = [
            value for value in results["styles"]
            if value != "documentary"
        ]

    return results

def parse_portfolio_details(title="", description="", skill_tags=""):
    """
    Extract skills, editing styles, and content niches
    from an editor's portfolio information.
    """
    portfolio_text = " ".join(
        str(value)
        for value in (title, description, skill_tags)
        if value
    ).strip()

    if not portfolio_text:
        return {
            "skills": [],
            "styles": [],
            "niches": [],
        }

    return parse_job_description(portfolio_text)
