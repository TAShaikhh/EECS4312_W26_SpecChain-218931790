from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent

# Stage 1: ensure the raw review dataset and dataset metadata exist.
# Produces:
# - data/reviews_raw.jsonl
# - data/dataset_metadata.json
#
# Stage 2: clean the raw review dataset.
# Produces:
# - data/reviews_clean.jsonl
# - updated data/dataset_metadata.json
#
# Stage 3: generate automated review groups and automated personas.
# Produces:
# - data/review_groups_auto.json
# - personas/personas_auto.json
# - prompts/prompt_auto.json
#
# Stage 4: generate the automated specification from the automated personas.
# Produces:
# - spec/spec_auto.md
# - updated prompts/prompt_auto.json
#
# Stage 5: generate automated validation tests from the automated specification.
# Produces:
# - tests/tests_auto.json
# - updated prompts/prompt_auto.json
#
# Stage 6: compute the automated pipeline metrics.
# Produces:
# - metrics/metrics_auto.json
SCRIPTS: list[tuple[str, list[str]]] = [
    ("01_collect_or_import.py", []),
    ("02_clean.py", []),
    ("05_personas_auto.py", []),
    ("06_spec_generate.py", []),
    ("07_tests_generate.py", []),
    ("08_metrics.py", ["--pipeline", "auto"]),
]


def main() -> None:
    for script_name, extra_args in SCRIPTS:
        script_path = ROOT / script_name
        print(f"Running {script_name}...", flush=True)
        subprocess.run([sys.executable, str(script_path), *extra_args], check=True)

    print("Automated workflow complete.", flush=True)


if __name__ == "__main__":
    main()
