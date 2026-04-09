from __future__ import annotations

import json
import re
import string
from dataclasses import dataclass
from pathlib import Path

import emoji
import nltk
from num2words import num2words
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
RAW_PATH = DATA_DIR / "reviews_raw.jsonl"
CLEAN_PATH = DATA_DIR / "reviews_clean.jsonl"
METADATA_PATH = DATA_DIR / "dataset_metadata.json"

MIN_TOKEN_COUNT = 3


@dataclass
class CleanedReview:
    id: str
    score: int
    reviewed_at: str
    original_text: str
    cleaned_text: str


def ensure_nltk_resources() -> None:
    resources = [
        ("corpora/stopwords", "stopwords"),
        ("corpora/wordnet", "wordnet"),
        ("corpora/omw-1.4", "omw-1.4"),
    ]
    for resource_path, resource_name in resources:
        try:
            nltk.data.find(resource_path)
        except LookupError:
            nltk.download(resource_name, quiet=True)


def replace_numbers(text: str) -> str:
    def repl(match: re.Match[str]) -> str:
        value = match.group(0)
        try:
            if "." in value:
                whole, fraction = value.split(".", 1)
                whole_text = num2words(int(whole))
                fraction_text = " ".join(num2words(int(char)) for char in fraction if char.isdigit())
                return f"{whole_text} point {fraction_text}"
            return num2words(int(value))
        except Exception:
            return value

    return re.sub(r"\d+(?:\.\d+)?", repl, text)


def normalize_text(text: str, stop_words: set[str], lemmatizer: WordNetLemmatizer) -> str:
    text = emoji.replace_emoji(text, replace=" ")
    text = replace_numbers(text)
    text = text.lower()
    text = text.replace("’", "'")
    text = text.translate(str.maketrans({char: " " for char in string.punctuation}))
    text = re.sub(r"[^a-z\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    tokens = []
    for token in text.split():
        if token in stop_words:
            continue
        lemma = lemmatizer.lemmatize(token)
        if lemma:
            tokens.append(lemma)
    return " ".join(tokens)


def load_raw_reviews() -> list[dict]:
    rows = []
    with RAW_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[CleanedReview]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row.__dict__, ensure_ascii=False) + "\n")


def main() -> None:
    ensure_nltk_resources()
    stop_words = set(stopwords.words("english"))
    lemmatizer = WordNetLemmatizer()
    raw_reviews = load_raw_reviews()

    cleaned_reviews: list[CleanedReview] = []
    seen_original_keys: set[str] = set()
    removal_counts = {
        "duplicates_removed": 0,
        "empty_removed": 0,
        "short_removed": 0,
    }

    for review in raw_reviews:
        original_text = (review.get("content") or "").strip()
        key = re.sub(r"\s+", " ", original_text.lower()).strip()
        if not original_text:
            removal_counts["empty_removed"] += 1
            continue
        if key in seen_original_keys:
            removal_counts["duplicates_removed"] += 1
            continue
        seen_original_keys.add(key)
        cleaned_text = normalize_text(original_text, stop_words, lemmatizer)
        if not cleaned_text:
            removal_counts["empty_removed"] += 1
            continue
        if len(cleaned_text.split()) < MIN_TOKEN_COUNT:
            removal_counts["short_removed"] += 1
            continue
        cleaned_reviews.append(
            CleanedReview(
                id=review["id"],
                score=int(review.get("score", 0) or 0),
                reviewed_at=review.get("reviewed_at", ""),
                original_text=original_text,
                cleaned_text=cleaned_text,
            )
        )

    write_jsonl(CLEAN_PATH, cleaned_reviews)

    metadata = {}
    if METADATA_PATH.exists():
        content = METADATA_PATH.read_text(encoding="utf-8").strip()
        if content:
            metadata = json.loads(content)
    metadata["dataset_size"] = {
        "raw_reviews": len(raw_reviews),
        "cleaned_reviews": len(cleaned_reviews),
    }
    metadata["cleaning_decisions"] = {
        "duplicates_removed_using": "case-insensitive normalized original review text",
        "empty_entries_removed": True,
        "extremely_short_threshold_tokens": MIN_TOKEN_COUNT,
        "punctuation_removed": True,
        "special_characters_removed": True,
        "emojis_removed": True,
        "numbers_converted_to_text": True,
        "extra_whitespace_removed": True,
        "lowercased": True,
        "stop_words_removed": True,
        "lemmatized": True,
        "removal_counts": removal_counts,
    }
    METADATA_PATH.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(cleaned_reviews)} cleaned reviews to {CLEAN_PATH}")


if __name__ == "__main__":
    main()
