from __future__ import annotations

import os
import subprocess
from pathlib import Path

from openai import OpenAI


ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"

CONTAINER = "genai-postgres"
DATABASE = "rag_enterprise_lab"
DB_USER = "genai"

MODEL = "text-embedding-3-small"


def load_env() -> None:
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()

        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        os.environ.setdefault(key, value)


def vector_literal(values: list[float]) -> str:
    return "[" + ",".join(str(v) for v in values) + "]"


def main() -> None:
    load_env()

    question = "Axion Solutions contract"

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    response = client.embeddings.create(
        model=MODEL,
        input=question,
    )

    embedding = response.data[0].embedding

    print(f"Question    : {question}")
    print(f"Dimensions  : {len(embedding)}")

    vector = vector_literal(embedding)

    safe_question = question.replace("'", "''")

    sql = f"""
SELECT
    document_id,
    title,
    lexical_rank,
    semantic_rank,
    round(hybrid_score::numeric, 6) AS hybrid_score
FROM search_authorized_chunks(
    '{safe_question}',
    ARRAY['RAG_LEGAL'],
    '{vector}'::vector,
    10
);
""".strip()

    subprocess.run(
        [
            "docker",
            "exec",
            "-i",
            CONTAINER,
            "psql",
            "-U",
            DB_USER,
            "-d",
            DATABASE,
            "-c",
            sql,
        ],
        check=False,
    )


if __name__ == "__main__":
    main()





