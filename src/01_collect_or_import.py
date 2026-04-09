from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from google_play_scraper import Sort, app, reviews_all


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
RAW_PATH = DATA_DIR / "reviews_raw.jsonl"
METADATA_PATH = DATA_DIR / "dataset_metadata.json"

APP_ID = "de.moodpath.android"
APP_NAME = "MindDoc: Mental Health Support"
COUNTRY = "ca"
LANGUAGE = "en"
MAX_REVIEWS = 5000


@dataclass
class RawReview:
    id: str
    app_id: str
    app_name: str
    source: str
    country: str
    language: str
    score: int
    thumbs_up_count: int
    reviewed_at: str
    app_version: str | None
    review_created_version: str | None
    content: str


def fetch_reviews() -> tuple[list[RawReview], dict]:
    info = app(APP_ID, lang=LANGUAGE, country=COUNTRY)
    scraped = reviews_all(
        APP_ID,
        lang=LANGUAGE,
        country=COUNTRY,
        sort=Sort.NEWEST,
        sleep_milliseconds=0,
    )
    selected = scraped[:MAX_REVIEWS]
    reviews_payload = [
        RawReview(
            id=item["reviewId"],
            app_id=APP_ID,
            app_name=APP_NAME,
            source="google_play_scraper",
            country=COUNTRY,
            language=LANGUAGE,
            score=int(item.get("score", 0) or 0),
            thumbs_up_count=int(item.get("thumbsUpCount", 0) or 0),
            reviewed_at=item["at"].astimezone(timezone.utc).isoformat(),
            app_version=item.get("appVersion"),
            review_created_version=item.get("reviewCreatedVersion"),
            content=(item.get("content") or "").strip(),
        )
        for item in selected
    ]
    metadata = {
        "app_name": info.get("title", APP_NAME),
        "app_id": APP_ID,
        "store_url": f"https://play.google.com/store/apps/details?id={APP_ID}&hl=en_CA&pli=1",
        "collection_method": {
            "source": "Google Play Store",
            "tool": "google-play-scraper",
            "sort": "NEWEST",
            "language": LANGUAGE,
            "country": COUNTRY,
            "max_reviews_requested": MAX_REVIEWS,
            "reviews_available_from_scraper": len(scraped),
            "reviews_extracted_raw": len(reviews_payload),
            "collected_at_utc": datetime.now(timezone.utc).isoformat(),
        },
        "app_store_metadata": {
            "developer": info.get("developer"),
            "installs": info.get("installs"),
            "ratings": info.get("ratings"),
            "reviews_field_from_store": info.get("reviews"),
            "updated": info.get("updated"),
            "version": info.get("version"),
        },
    }
    return reviews_payload, metadata


def write_jsonl(path: Path, rows: list[RawReview]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(asdict(row), ensure_ascii=False) + "\n")


def raw_dataset_exists() -> bool:
    return RAW_PATH.exists() and RAW_PATH.stat().st_size > 0


def metadata_exists() -> bool:
    return METADATA_PATH.exists() and bool(METADATA_PATH.read_text(encoding="utf-8").strip())


def count_jsonl_rows(path: Path) -> int:
    count = 0
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                count += 1
    return count


def ensure_metadata_for_existing_raw() -> None:
    if metadata_exists():
        return
    info = app(APP_ID, lang=LANGUAGE, country=COUNTRY)
    existing_count = count_jsonl_rows(RAW_PATH)
    metadata = {
        "app_name": info.get("title", APP_NAME),
        "app_id": APP_ID,
        "store_url": f"https://play.google.com/store/apps/details?id={APP_ID}&hl=en_CA&pli=1",
        "collection_method": {
            "source": "Google Play Store",
            "tool": "google-play-scraper",
            "sort": "NEWEST",
            "language": LANGUAGE,
            "country": COUNTRY,
            "max_reviews_requested": MAX_REVIEWS,
            "reviews_available_from_scraper": None,
            "reviews_extracted_raw": existing_count,
            "collected_at_utc": datetime.now(timezone.utc).isoformat(),
            "collection_note": "Metadata was regenerated from the existing committed raw dataset without refetching reviews.",
        },
        "app_store_metadata": {
            "developer": info.get("developer"),
            "installs": info.get("installs"),
            "ratings": info.get("ratings"),
            "reviews_field_from_store": info.get("reviews"),
            "updated": info.get("updated"),
            "version": info.get("version"),
        },
    }
    METADATA_PATH.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true", help="Fetch a fresh raw dataset from Google Play.")
    args = parser.parse_args()

    if raw_dataset_exists() and not args.refresh:
        ensure_metadata_for_existing_raw()
        print(f"Using existing raw dataset at {RAW_PATH}")
        return

    reviews_payload, metadata = fetch_reviews()
    write_jsonl(RAW_PATH, reviews_payload)
    existing = {}
    if METADATA_PATH.exists():
        content = METADATA_PATH.read_text(encoding="utf-8").strip()
        if content:
            existing = json.loads(content)
    merged = {**existing, **metadata}
    METADATA_PATH.write_text(json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(reviews_payload)} raw reviews to {RAW_PATH}")


if __name__ == "__main__":
    main()
