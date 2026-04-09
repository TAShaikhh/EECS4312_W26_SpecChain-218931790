from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_DIRS = [
    "data",
    "personas",
    "spec",
    "tests",
    "metrics",
    "prompts",
    "src",
]

REQUIRED_FILES = [
    "data/reviews_raw.jsonl",
    "data/reviews_clean.jsonl",
    "data/dataset_metadata.json",
    "data/review_groups_manual.json",
    "data/review_groups_auto.json",
    "data/review_groups_hybrid.json",
    "personas/personas_manual.json",
    "personas/personas_auto.json",
    "personas/personas_hybrid.json",
    "spec/spec_manual.md",
    "spec/spec_auto.md",
    "spec/spec_hybrid.md",
    "tests/tests_manual.json",
    "tests/tests_auto.json",
    "tests/tests_hybrid.json",
    "metrics/metrics_manual.json",
    "metrics/metrics_auto.json",
    "metrics/metrics_hybrid.json",
    "metrics/metrics_summary.json",
    "prompts/prompt_auto.json",
    "src/00_validate_repo.py",
    "src/01_collect_or_import.py",
    "src/02_clean.py",
    "src/05_personas_auto.py",
    "src/06_spec_generate.py",
    "src/07_tests_generate.py",
    "src/08_metrics.py",
    "src/run_all.py",
]


def validate_json(path: Path) -> None:
    json.loads(path.read_text(encoding="utf-8"))


def validate_jsonl(path: Path) -> None:
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if line.strip():
                try:
                    json.loads(line)
                except json.JSONDecodeError as exc:
                    raise SystemExit(f"{path.relative_to(ROOT)} invalid at line {line_number}: {exc}") from exc


def validate_contents() -> None:
    validate_jsonl(ROOT / "data/reviews_raw.jsonl")
    validate_jsonl(ROOT / "data/reviews_clean.jsonl")

    for relative_path in [
        "data/dataset_metadata.json",
        "data/review_groups_manual.json",
        "data/review_groups_auto.json",
        "data/review_groups_hybrid.json",
        "personas/personas_manual.json",
        "personas/personas_auto.json",
        "personas/personas_hybrid.json",
        "tests/tests_manual.json",
        "tests/tests_auto.json",
        "tests/tests_hybrid.json",
        "metrics/metrics_manual.json",
        "metrics/metrics_auto.json",
        "metrics/metrics_hybrid.json",
        "metrics/metrics_summary.json",
        "prompts/prompt_auto.json",
    ]:
        validate_json(ROOT / relative_path)


def main() -> None:
    print("Checking repository structure...")

    missing_paths: list[str] = []

    for dirname in REQUIRED_DIRS:
        path = ROOT / dirname
        if path.exists():
            print(f"{dirname}/ found")
        else:
            print(f"{dirname}/ missing")
            missing_paths.append(dirname)

    for relative_path in REQUIRED_FILES:
        path = ROOT / relative_path
        if path.exists():
            print(f"{relative_path} found")
        else:
            print(f"{relative_path} missing")
            missing_paths.append(relative_path)

    if missing_paths:
        raise SystemExit("Repository validation failed.")

    validate_contents()
    print("Repository validation complete")


if __name__ == "__main__":
    main()
