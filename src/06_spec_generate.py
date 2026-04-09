from __future__ import annotations

import json
import os
import time
from collections import Counter
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parents[1]
PERSONAS_PATH = ROOT / "personas" / "personas_auto.json"
GROUPS_PATH = ROOT / "data" / "review_groups_auto.json"
SPEC_PATH = ROOT / "spec" / "spec_auto.md"
PROMPTS_PATH = ROOT / "prompts" / "prompt_auto.json"

MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
AMBIGUOUS_TERMS = {
    "easy",
    "simple",
    "intuitive",
    "user-friendly",
    "helpful",
    "supportive",
    "better",
}
FORBIDDEN_DETAILS = {
    "tutorial",
    "feelings wheel",
    "support feature",
    "non-judgmental",
}

SPEC_PROMPT_TEMPLATE = """You are generating software requirements for MindDoc from one automatically derived persona.

Rules:
- Produce exactly 2 requirements for this persona and no others.
- Use grounded, software-oriented requirements only.
- Do not invent exact prices, durations, thresholds, integrations, or workflows unless they are directly justified by the persona summary.
- Each description must be a clear singular requirement using 'shall'.
- Use the persona name exactly as provided for "source_persona".
- Set "traceability_group" to the provided group ID exactly.
- Do not introduce new UI elements or workflows unless the persona text clearly supports them. Avoid invented items such as tutorials, feelings wheels, support features, visual dashboards, or non-judgmental responses unless they appear in the persona evidence.
- Avoid ambiguous adjectives such as user-friendly, easy, simple, intuitive, seamless, supportive, helpful, or better.
- Acceptance criteria must be testable and observable but should avoid fabricated numeric thresholds.
- Return valid JSON only.

Return:
{{
  "requirements": [
    {{
      "id": "AR1",
      "description": "The system shall ...",
      "source_persona": "persona name",
      "traceability_group": "A1",
      "acceptance_criteria": "Given ... When ... Then ..."
    }}
  ]
}}

Persona:
{persona_block}
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


def update_prompt_file() -> None:
    existing = json.loads(PROMPTS_PATH.read_text(encoding="utf-8")) if PROMPTS_PATH.exists() else {}
    payload = {}
    for key in ("model", "grouping_prompt_template", "grouping_temperature", "tests_prompt_template", "tests_temperature"):
        if key in existing:
            payload[key] = existing[key]
    payload["spec_prompt_template"] = SPEC_PROMPT_TEMPLATE
    payload["spec_temperature"] = 0.2
    PROMPTS_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def contains_disallowed_language(text: str) -> bool:
    lowered = text.lower()
    return any(term in lowered for term in FORBIDDEN_DETAILS)


def validate_requirements(requirements: list[dict], group_to_persona: dict[str, str]) -> list[str]:
    issues = []
    ids = [requirement.get("id", "").strip() for requirement in requirements]
    if len(ids) != len(set(ids)):
        issues.append("Requirement IDs must be unique.")

    counts = Counter()
    for requirement in requirements:
        group_id = requirement.get("traceability_group", "").strip()
        if group_id not in group_to_persona:
            issues.append(f"Unknown traceability group: {group_id}")
            continue
        counts[group_id] += 1

        description = requirement.get("description", "").strip()
        acceptance = requirement.get("acceptance_criteria", "").strip()
        if contains_disallowed_language(description) or contains_disallowed_language(acceptance):
            issues.append(f"Requirement {requirement.get('id', '<missing>')} uses ambiguous or unsupported language.")

    for group_id in group_to_persona:
        if counts[group_id] != 2:
            issues.append(f"Expected 2 requirements for {group_id}, found {counts[group_id]}.")

    return issues


def main() -> None:
    personas = json.loads(PERSONAS_PATH.read_text(encoding="utf-8"))["personas"]
    groups = {group["group_id"]: group for group in json.loads(GROUPS_PATH.read_text(encoding="utf-8"))["groups"]}
    group_to_persona = {persona["derived_from_group"]: persona["name"] for persona in personas}

    personas_block = "\n".join(
        [
            json.dumps(
                {
                    "id": persona["id"],
                    "name": persona["name"],
                    "derived_from_group": persona["derived_from_group"],
                    "group_theme": groups[persona["derived_from_group"]]["theme"],
                    "description": persona["description"],
                    "goals": persona["goals"],
                    "pain_points": persona["pain_points"],
                    "context": persona["context"],
                    "constraints": persona["constraints"],
                },
                ensure_ascii=False,
            )
            for persona in personas
        ]
    )

    requirements = []
    requirement_counter = 1
    last_feedback = ""

    for persona in personas:
        persona_block = json.dumps(
            {
                "id": persona["id"],
                "name": persona["name"],
                "derived_from_group": persona["derived_from_group"],
                "group_theme": groups[persona["derived_from_group"]]["theme"],
                "description": persona["description"],
                "goals": persona["goals"],
                "pain_points": persona["pain_points"],
                "context": persona["context"],
                "constraints": persona["constraints"],
            },
            ensure_ascii=False,
        )
        prompt_text = SPEC_PROMPT_TEMPLATE.format(persona_block=persona_block)
        persona_requirements = None
        feedback = ""

        for _ in range(6):
            effective_prompt = prompt_text if not feedback else f"{prompt_text}\nCorrection feedback:\n{feedback}\n"
            result = call_groq(
                messages=[{"role": "user", "content": effective_prompt}],
                response_format={"type": "json_object"},
                temperature=0.0,
            )
            candidate_requirements = result["requirements"]
            if len(candidate_requirements) != 2:
                feedback = f"Expected exactly 2 requirements for persona {persona['name']}, received {len(candidate_requirements)}."
                continue

            for requirement in candidate_requirements:
                requirement["id"] = f"AR{requirement_counter}"
                requirement_counter += 1
                requirement["source_persona"] = persona["name"]
                requirement["traceability_group"] = persona["derived_from_group"]

            issues = validate_requirements(candidate_requirements, {persona["derived_from_group"]: persona["name"]})
            if not issues:
                persona_requirements = candidate_requirements
                break
            feedback = "\n".join(issues)
            last_feedback = feedback

        if persona_requirements is None:
            raise RuntimeError(
                f"Unable to generate valid automated requirements for {persona['id']}.\n{feedback or last_feedback}"
            )
        requirements.extend(persona_requirements)

    issues = validate_requirements(requirements, group_to_persona)
    if issues:
        raise RuntimeError(f"Automated requirements failed final validation.\n{chr(10).join(issues)}")

    sections = []
    for requirement in requirements:
        sections.append(
            "\n".join(
                [
                    f"# Requirement ID: {requirement['id']}",
                    "",
                    f"- Description: [{requirement['description'].strip()}]",
                    f"- Source Persona: [{requirement['source_persona'].strip()}]",
                    f"- Traceability: [Derived from review group {requirement['traceability_group'].strip()}]",
                    f"- Acceptance Criteria: [{requirement['acceptance_criteria'].strip()}]",
                ]
            )
        )

    SPEC_PATH.write_text("\n\n".join(sections) + "\n", encoding="utf-8")
    update_prompt_file()
    print(f"Wrote {len(requirements)} automated requirements to {SPEC_PATH}")


if __name__ == "__main__":
    main()
