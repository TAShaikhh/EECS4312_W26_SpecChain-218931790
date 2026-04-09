from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "spec" / "spec_auto.md"
TESTS_PATH = ROOT / "tests" / "tests_auto.json"
PROMPTS_PATH = ROOT / "prompts" / "prompt_auto.json"

MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

TEST_PROMPT_TEMPLATE = """You are generating validation tests from software requirements for MindDoc.

Rules:
- Generate exactly one test scenario per requirement.
- Every test must reference the requirement ID it validates.
- Steps must be clear and executable.
- The expected result must reflect the requirement being validated.
- Do not invent screens, widgets, tutorials, feelings wheels, dashboards, or support features unless they already appear in the requirement text.
- Avoid vague wording such as easy, intuitive, user-friendly, simple, or accurate unless the requirement itself makes that observable.
- Return valid JSON only.

Return:
{{
  "tests": [
    {{
      "test_id": "AT1",
      "requirement_id": "AR1",
      "scenario": "short scenario",
      "steps": ["step 1", "step 2", "step 3"],
      "expected_result": "expected outcome"
    }}
  ]
}}

Requirements:
{requirements_block}
"""


def call_groq(messages: list[dict], response_format: dict | None = None, temperature: float = 0.2) -> dict:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set.")

    payload = {
        "model": MODEL,
        "temperature": temperature,
        "messages": messages,
    }
    if response_format is not None:
        payload["response_format"] = response_format

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    for attempt in range(3):
        response = requests.post(GROQ_URL, headers=headers, json=payload, timeout=120)
        if response.ok:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return json.loads(content)
        if attempt == 2:
            raise RuntimeError(f"Groq request failed: {response.status_code} {response.text}")
        time.sleep(2 * (attempt + 1))

    raise RuntimeError("Groq request failed after retries.")


def parse_requirements() -> list[dict]:
    content = SPEC_PATH.read_text(encoding="utf-8")
    blocks = re.findall(
        r"(# Requirement ID:\s*[A-Za-z][A-Za-z0-9_-]*.*?)(?=\n# Requirement ID:|\Z)",
        content,
        re.DOTALL,
    )
    requirements = []
    for block in blocks:
        req_id = re.search(r"# Requirement ID:\s*([A-Za-z][A-Za-z0-9_-]*)", block)
        description = re.search(r"- Description:\s*\[(.*?)\]", block, re.DOTALL)
        if req_id and description:
            requirements.append(
                {
                    "id": req_id.group(1).strip(),
                    "description": description.group(1).strip(),
                }
            )
    return requirements


def update_prompt_file() -> None:
    existing = json.loads(PROMPTS_PATH.read_text(encoding="utf-8")) if PROMPTS_PATH.exists() else {}
    payload = {}
    for key in ("model", "grouping_prompt_template", "grouping_temperature", "spec_prompt_template", "spec_temperature"):
        if key in existing:
            payload[key] = existing[key]
    payload["tests_prompt_template"] = TEST_PROMPT_TEMPLATE
    payload["tests_temperature"] = 0.2
    PROMPTS_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    requirements = parse_requirements()
    requirement_ids = [requirement["id"] for requirement in requirements]
    requirements_block = "\n".join(
        json.dumps(requirement, ensure_ascii=False) for requirement in requirements
    )

    prompt_text = TEST_PROMPT_TEMPLATE.format(requirements_block=requirements_block)
    result = call_groq(
        messages=[{"role": "user", "content": prompt_text}],
        response_format={"type": "json_object"},
        temperature=0.2,
    )
    tests = result["tests"]
    if len(tests) != len(requirements):
        raise RuntimeError(
            f"Expected {len(requirements)} automated tests, received {len(tests)}."
        )

    for index, test in enumerate(tests, start=1):
        test["test_id"] = test.get("test_id", f"AT{index}").strip() or f"AT{index}"
        if test.get("requirement_id", "").strip() not in requirement_ids:
            test["requirement_id"] = requirement_ids[index - 1]

    TESTS_PATH.write_text(json.dumps({"tests": tests}, indent=2, ensure_ascii=False), encoding="utf-8")
    update_prompt_file()
    print(f"Wrote {len(tests)} automated tests to {TESTS_PATH}")


if __name__ == "__main__":
    main()
