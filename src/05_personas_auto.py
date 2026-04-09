from __future__ import annotations

import json
import os
import time
from collections import Counter
from pathlib import Path

import numpy as np
import requests
from sklearn.cluster import MiniBatchKMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
PROMPTS_PATH = ROOT / "prompts" / "prompt_auto.json"
REVIEW_GROUPS_PATH = DATA_DIR / "review_groups_auto.json"
PERSONAS_PATH = ROOT / "personas" / "personas_auto.json"
CLEAN_REVIEWS_PATH = DATA_DIR / "reviews_clean.jsonl"

MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
CLUSTER_COUNT = 5
REPRESENTATIVE_REVIEWS = 12
EXAMPLE_REVIEWS = 2
EVIDENCE_REVIEWS = 3

GROUPING_PROMPT_TEMPLATE = """You are assisting with software requirements engineering.

You will receive one automatically discovered cluster of app reviews for MindDoc.
Your job is to label the cluster and generate one grounded persona from it.

Rules:
- Use only the evidence provided in the reviews and top terms.
- Do not invent specific prices, time windows, privacy controls, integrations, or features unless they are directly supported by the reviews.
- Keep the persona general enough to represent the cluster, but grounded in the evidence.
- Give the persona a distinct, specific name for this cluster. Avoid generic names such as "Mindful User" or "User".
- Write concise, concrete software-oriented output.
- Return valid JSON only.

Return this JSON object:
{{
  "theme": "short cluster theme",
  "persona": {{
    "name": "persona name",
    "description": "1 sentence",
    "goals": ["goal 1", "goal 2", "goal 3"],
    "pain_points": ["pain point 1", "pain point 2", "pain point 3"],
    "context": ["context 1", "context 2"],
    "constraints": ["constraint 1", "constraint 2"]
  }}
}}

Cluster ID: {cluster_id}
Top terms: {top_terms}

Representative reviews:
{reviews_block}
"""


def load_clean_reviews() -> list[dict]:
    rows = []
    with CLEAN_REVIEWS_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


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


def build_clusters(reviews: list[dict]) -> tuple[np.ndarray, TfidfVectorizer, MiniBatchKMeans]:
    vectorizer = TfidfVectorizer(max_features=3000, ngram_range=(1, 2), min_df=3)
    matrix = vectorizer.fit_transform([review["cleaned_text"] for review in reviews])
    model = MiniBatchKMeans(n_clusters=CLUSTER_COUNT, random_state=42, n_init=10, batch_size=256)
    labels = model.fit_predict(matrix)
    return labels, vectorizer, model


def representative_indices(cluster_matrix, center_vector: np.ndarray, top_n: int) -> list[int]:
    similarities = cosine_similarity(cluster_matrix, center_vector.reshape(1, -1)).ravel()
    ranked = np.argsort(similarities)[::-1]
    return ranked[:top_n].tolist()


def update_prompt_file() -> None:
    payload: dict[str, object] = {
        "model": MODEL,
        "grouping_prompt_template": GROUPING_PROMPT_TEMPLATE,
        "grouping_temperature": 0.2,
    }
    if PROMPTS_PATH.exists():
        existing = json.loads(PROMPTS_PATH.read_text(encoding="utf-8"))
        for key in ("spec_prompt_template", "spec_temperature", "tests_prompt_template", "tests_temperature"):
            if key in existing:
                payload[key] = existing[key]
    PROMPTS_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def ensure_unique_persona_names(personas: list[dict], groups: list[dict]) -> None:
    counts = Counter(persona["name"] for persona in personas)
    group_themes = {group["group_id"]: group["theme"] for group in groups}
    for persona in personas:
        if counts[persona["name"]] > 1:
            theme = group_themes.get(persona["derived_from_group"], persona["derived_from_group"])
            persona["name"] = f"{theme} User"


def main() -> None:
    reviews = load_clean_reviews()
    labels, vectorizer, model = build_clusters(reviews)
    matrix = vectorizer.transform([review["cleaned_text"] for review in reviews])
    terms = vectorizer.get_feature_names_out()

    cluster_to_indices: dict[int, list[int]] = {}
    for index, label in enumerate(labels):
        cluster_to_indices.setdefault(int(label), []).append(index)

    ordered_clusters = sorted(cluster_to_indices.items(), key=lambda item: len(item[1]), reverse=True)

    groups = []
    personas = []

    for sequence, (cluster_label, indices) in enumerate(ordered_clusters, start=1):
        cluster_id = f"A{sequence}"
        cluster_matrix = matrix[indices]
        centroid = model.cluster_centers_[cluster_label]
        rep_positions = representative_indices(cluster_matrix, centroid, REPRESENTATIVE_REVIEWS)
        representative_reviews = [reviews[indices[pos]] for pos in rep_positions]

        top_term_ids = np.argsort(centroid)[::-1][:10]
        top_terms = [terms[idx] for idx in top_term_ids if centroid[idx] > 0]
        reviews_block = "\n".join(
            f'- {review["id"]}: {review["original_text"]}'
            for review in representative_reviews
        )

        prompt_text = GROUPING_PROMPT_TEMPLATE.format(
            cluster_id=cluster_id,
            top_terms=", ".join(top_terms),
            reviews_block=reviews_block,
        )
        llm_output = call_groq(
            messages=[{"role": "user", "content": prompt_text}],
            response_format={"type": "json_object"},
            temperature=0.2,
        )

        groups.append(
            {
                "group_id": cluster_id,
                "theme": llm_output["theme"].strip(),
                "review_ids": [reviews[index]["id"] for index in indices],
                "example_reviews": [
                    review["original_text"] for review in representative_reviews[:EXAMPLE_REVIEWS]
                ],
            }
        )

        personas.append(
            {
                "id": f"AP{sequence}",
                "name": llm_output["persona"]["name"].strip(),
                "description": llm_output["persona"]["description"].strip(),
                "derived_from_group": cluster_id,
                "goals": [goal.strip() for goal in llm_output["persona"]["goals"][:3]],
                "pain_points": [item.strip() for item in llm_output["persona"]["pain_points"][:3]],
                "context": [item.strip() for item in llm_output["persona"]["context"][:2]],
                "constraints": [item.strip() for item in llm_output["persona"]["constraints"][:2]],
                "evidence_reviews": [review["id"] for review in representative_reviews[:EVIDENCE_REVIEWS]],
            }
        )

    ensure_unique_persona_names(personas, groups)

    REVIEW_GROUPS_PATH.write_text(json.dumps({"groups": groups}, indent=2, ensure_ascii=False), encoding="utf-8")
    PERSONAS_PATH.write_text(json.dumps({"personas": personas}, indent=2, ensure_ascii=False), encoding="utf-8")
    update_prompt_file()
    print(f"Wrote {len(groups)} automatic review groups to {REVIEW_GROUPS_PATH}")
    print(f"Wrote {len(personas)} automatic personas to {PERSONAS_PATH}")


if __name__ == "__main__":
    main()
