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


def load_env_file() -> None:
    if not ENV_PATH.exists():
        return

    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()

        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)

        if key and key not in os.environ:
            os.environ[key] = value


def fetch_chunks() -> list[tuple[int, str]]:
    sql = """
SELECT
    id,
    encode(convert_to(content, 'UTF8'), 'hex')
FROM chunks
WHERE embedding IS NULL
ORDER BY id;
""".strip()

    result = subprocess.run(
        [
            "docker",
            "exec",
            CONTAINER,
            "psql",
            "-U",
            DB_USER,
            "-d",
            DATABASE,
            "-At",
            "-F",
            "\t",
            "-c",
            sql,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())

    rows: list[tuple[int, str]] = []

    for line in result.stdout.splitlines():
        if not line.strip():
            continue

        chunk_id_text, content_hex = line.split("\t", 1)
        content = bytes.fromhex(content_hex).decode("utf-8")
        rows.append((int(chunk_id_text), content))

    return rows


def vector_literal(values: list[float]) -> str:
    return "[" + ",".join(str(value) for value in values) + "]"


def update_embedding(chunk_id: int, embedding: list[float]) -> None:
    vector = vector_literal(embedding)

    sql = f"""
UPDATE chunks
SET embedding = '{vector}'::vector
WHERE id = {chunk_id};
""".strip()

    result = subprocess.run(
        [
            "docker",
            "exec",
            CONTAINER,
            "psql",
            "-v",
            "ON_ERROR_STOP=1",
            "-U",
            DB_USER,
            "-d",
            DATABASE,
            "-c",
            sql,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())


def main() -> None:
    load_env_file()

    api_key = os.getenv("OPENAI_API_KEY", "").strip()

    if not api_key:
        raise RuntimeError("OPENAI_API_KEY absente")

    chunks = fetch_chunks()

    print(f"Chunks sans embedding : {len(chunks)}")

    if not chunks:
        print("Rien a faire.")
        return

    client = OpenAI(api_key=api_key)

    for index, (chunk_id, content) in enumerate(chunks, start=1):
        response = client.embeddings.create(
            model=MODEL,
            input=content,
        )

        embedding = response.data[0].embedding

        if len(embedding) != 1536:
            raise RuntimeError(
                f"Dimension inattendue pour chunk {chunk_id}: "
                f"{len(embedding)}"
            )

        update_embedding(chunk_id, embedding)

        print(
            f"[{index}/{len(chunks)}] "
            f"chunk={chunk_id} "
            f"dimensions={len(embedding)}"
        )

    print("Embeddings termines.")


if __name__ == "__main__":
    main()
