from __future__ import annotations

import json
import os
from pathlib import Path

from anthropic import Anthropic
from anthropic.types import TextBlock
from pydantic import BaseModel, Field


ROOT = Path(__file__).resolve().parents[3]
ENV_PATH = ROOT / ".env"

CLAUDE_MODEL = "claude-sonnet-5"


class JudgeResult(BaseModel):
    relevance: float = Field(ge=0.0, le=1.0)
    faithfulness: float = Field(ge=0.0, le=1.0)
    completeness: float = Field(ge=0.0, le=1.0)
    conflict_awareness: float = Field(ge=0.0, le=1.0)
    overall: float = Field(ge=0.0, le=1.0)
    verdict: str
    reason: str


def load_env() -> None:
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()

        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        os.environ.setdefault(key, value)


def evaluate(
    *,
    question: str,
    answer: str,
    context: str,
) -> JudgeResult:
    load_env()

    client = Anthropic(
        api_key=os.environ["CLAUDE_API_KEY"]
    )

    prompt = f"""
Tu es un LLM-as-a-Judge pour un système RAG d'entreprise.

Évalue uniquement à partir de :
1. la question utilisateur ;
2. le contexte autorisé fourni ;
3. la réponse produite.

Critères :
- relevance : la réponse répond-elle réellement à la question ?
- faithfulness : chaque affirmation importante est-elle supportée par le contexte ?
- completeness : les éléments importants disponibles dans le contexte sont-ils couverts ?
- conflict_awareness : la réponse respecte-t-elle les conflits de versions et l'autorité documentaire ?

Règles :
- Ne récompense jamais une information absente du contexte.
- Si une affirmation est inventée, faithfulness doit fortement baisser.
- Si le document faisant foi est ignoré, conflict_awareness doit fortement baisser.
- verdict doit être PASS, REVIEW ou FAIL.
- Retourne uniquement un JSON valide.

QUESTION
{question}

CONTEXTE
{context}

RÉPONSE
{answer}

FORMAT JSON ATTENDU
{{
  "relevance": 0.0,
  "faithfulness": 0.0,
  "completeness": 0.0,
  "conflict_awareness": 0.0,
  "overall": 0.0,
  "verdict": "PASS",
  "reason": "..."
}}
""".strip()

    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=500,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )

    text_block = next(
        (
            block
            for block in response.content
            if isinstance(block, TextBlock)
        ),
        None,
    )

    if text_block is None:
        raise ValueError("Claude Judge returned no text block")

    raw = text_block.text.strip()

    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:].strip()

    data = json.loads(raw)

    return JudgeResult.model_validate(data)