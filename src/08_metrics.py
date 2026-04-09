from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
METRICS_DIR = ROOT / "metrics"

AMBIGUOUS_TERMS = {
    "fast",
    "easy",
    "better",
    "user-friendly",
    "quick",
    "quickly",
    "simple",
    "seamless",
    "efficient",
    "intuitive",
    "smooth",
    "appropriate",
    "reliable",
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def parse_requirements(path: Path) -> list[dict]:
    content = path.read_text(encoding="utf-8")
    blocks = re.findall(
        r"(# Requirement ID:\s*[A-Za-z][A-Za-z0-9_-]*.*?)(?=\n# Requirement ID:|\Z)",
        content,
        re.DOTALL,
    )
    requirements = []
    for block in blocks:
        req_id_match = re.search(r"# Requirement ID:\s*([A-Za-z][A-Za-z0-9_-]*)", block)
        description_match = re.search(r"- Description:\s*\[(.*?)\]", block, re.DOTALL)
        persona_match = re.search(r"- Source Persona:\s*\[(.*?)\]", block)
        acceptance_match = re.search(r"- Acceptance Criteria:\s*\[(.*?)\]", block, re.DOTALL)
        if not req_id_match:
            continue
        requirements.append(
            {
                "id": req_id_match.group(1).strip(),
                "description": (description_match.group(1).strip() if description_match else ""),
                "persona": (persona_match.group(1).strip() if persona_match else ""),
                "acceptance_criteria": (acceptance_match.group(1).strip() if acceptance_match else ""),
            }
        )
    return requirements


def contains_ambiguity(text: str) -> bool:
    lowered = text.lower()
    return any(term in lowered for term in AMBIGUOUS_TERMS)


def metric_paths(pipeline: str) -> dict[str, Path]:
    if pipeline == "manual":
        return {
            "groups": DATA_DIR / "review_groups_manual.json",
            "personas": ROOT / "personas" / "personas_manual.json",
            "spec": ROOT / "spec" / "spec_manual.md",
            "tests": ROOT / "tests" / "tests_manual.json",
            "metrics": ROOT / "metrics" / "metrics_manual.json",
            "label": "manual",
        }
    if pipeline == "auto":
        return {
            "groups": DATA_DIR / "review_groups_auto.json",
            "personas": ROOT / "personas" / "personas_auto.json",
            "spec": ROOT / "spec" / "spec_auto.md",
            "tests": ROOT / "tests" / "tests_auto.json",
            "metrics": ROOT / "metrics" / "metrics_auto.json",
            "label": "automated",
        }
    if pipeline == "hybrid":
        return {
            "groups": DATA_DIR / "review_groups_hybrid.json",
            "personas": ROOT / "personas" / "personas_hybrid.json",
            "spec": ROOT / "spec" / "spec_hybrid.md",
            "tests": ROOT / "tests" / "tests_hybrid.json",
            "metrics": ROOT / "metrics" / "metrics_hybrid.json",
            "label": "hybrid",
        }
    raise ValueError(f"Unsupported pipeline '{pipeline}'.")


def compute_metrics(pipeline: str) -> dict:
    paths = metric_paths(pipeline)
    reviews = load_jsonl(DATA_DIR / "reviews_clean.jsonl")
    groups = load_json(paths["groups"])["groups"]
    personas = load_json(paths["personas"])["personas"]
    requirements = parse_requirements(paths["spec"])
    tests = load_json(paths["tests"])["tests"]

    covered_review_ids = {review_id for group in groups for review_id in group["review_ids"]}
    tests_by_requirement: dict[str, int] = {}
    for test in tests:
        req_id = test["requirement_id"]
        tests_by_requirement[req_id] = tests_by_requirement.get(req_id, 0) + 1

    traceable_requirements = [req for req in requirements if req["persona"]]
    ambiguous_requirements = [
        req
        for req in requirements
        if contains_ambiguity(req["description"]) or contains_ambiguity(req["acceptance_criteria"])
    ]

    traceability_links = sum(len(group["review_ids"]) for group in groups)
    traceability_links += len([persona for persona in personas if persona.get("derived_from_group")])
    traceability_links += len([req for req in requirements if req["persona"]])
    traceability_links += len(tests)

    metrics = {
        "pipeline": paths["label"],
        "dataset_size": len(reviews),
        "persona_count": len(personas),
        "requirements_count": len(requirements),
        "tests_count": len(tests),
        "traceability_links": traceability_links,
        "review_coverage": round(len(covered_review_ids) / len(reviews), 4) if reviews else 0.0,
        "traceability_ratio": round(len(traceable_requirements) / len(requirements), 4) if requirements else 0.0,
        "testability_rate": round(
            len([req for req in requirements if tests_by_requirement.get(req["id"], 0) > 0]) / len(requirements),
            4,
        )
        if requirements
        else 0.0,
        "ambiguity_ratio": round(len(ambiguous_requirements) / len(requirements), 4) if requirements else 0.0,
    }
    paths["metrics"].write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")
    return metrics


def write_summary(metrics_by_pipeline: dict[str, dict]) -> dict:
    summary = {
        "manual": metrics_by_pipeline["manual"],
        "automated": metrics_by_pipeline["auto"],
        "hybrid": metrics_by_pipeline["hybrid"],
    }
    summary_path = METRICS_DIR / "metrics_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    return summary


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--pipeline", choices=["manual", "auto", "hybrid", "all"], default="manual")
    args = parser.parse_args()
    if args.pipeline == "all":
        metrics_by_pipeline = {
            pipeline: compute_metrics(pipeline) for pipeline in ["manual", "auto", "hybrid"]
        }
        summary = write_summary(metrics_by_pipeline)
        print(json.dumps(summary, indent=2))
        return

    metrics = compute_metrics(args.pipeline)
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
