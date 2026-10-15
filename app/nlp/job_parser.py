import spacy
from spacy.matcher import PhraseMatcher

# Load the English NLP model
nlp = spacy.load("en_core_web_sm")

# Domain-specific vocabulary for video editing
VOCABULARY = {
    "skills": [
        "Adobe Premiere Pro",
        "Premiere Pro",
        "After Effects",
        "DaVinci Resolve",
        "Final Cut Pro",
        "CapCut",
        "Color Grading",
        "Motion Graphics",
        "Sound Design",
    ],
    "styles": [
        "Fast-paced",
        "Cinematic",
        "Documentary",
        "Montage",
        "Short-form",
        "Storytelling",
        "Minimalist",
    ],
    "niches": [
        "Gaming",
        "Travel",
        "Lifestyle",
        "Sports",
        "Education",
        "Technology",
        "Beauty",
        "Fitness",
    ],
}

# Build a case-insensitive phrase matcher
matcher = PhraseMatcher(nlp.vocab, attr="LOWER")

for category, phrases in VOCABULARY.items():
    patterns = [nlp.make_doc(phrase) for phrase in phrases]
    matcher.add(category, patterns)


def parse_job_description(description):
    """Extract video-editing skills, styles and niches."""
    if not isinstance(description, str):
        raise ValueError("Job description must be text.")

    if not description.strip():
        raise ValueError("Job description cannot be empty.")

    doc = nlp(description)

    results = {
        "skills": [],
        "styles": [],
        "niches": [],
    }

    
    # Prioritizing longer phrases to avoid overlapping matches
    matches = sorted(
        matcher(doc),
        key=lambda match: (
            -(match[2] - match[1]),
            match[1]
        )
    )

    used_tokens = set()

    for match_id, start, end in matches:
        if any(i in used_tokens for i in range(start, end)):
            continue

        category = nlp.vocab.strings[match_id]
        phrase = doc[start:end].text
        
        # Classify "documentary editor" as a documentary niche
        if category == "styles" and phrase.casefold() == "documentary":
           next_token = doc[end] if end < len(doc) else None

           if next_token is not None and next_token.lower_ in {
               "editor", "editors"
        }:
                if "documentary" not in [
                    value.casefold() for value in results["niches"]
                ]:
                    results["niches"].append("documentary")
                continue

        if phrase.casefold() not in [
            value.casefold() for value in results[category]
        ]:
            results[category].append(phrase)

        used_tokens.update(range(start, end))


    return results
