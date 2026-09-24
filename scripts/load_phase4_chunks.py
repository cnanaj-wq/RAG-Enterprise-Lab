from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_DIR = ROOT / "data" / "examples"

CONTAINER = "genai-postgres"
DATABASE = "rag_enterprise_lab"
DB_USER = "genai"

CHUNK_SIZE = 700
CHUNK_OVERLAP = 100


def split_text(text: str) -> list[str]:
    text = text.strip()

    if not text:
        return []

    chunks: list[str] = []
    start = 0

    while start < len(text):
        end = min(start + CHUNK_SIZE, len(text))
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        start = max(end - CHUNK_OVERLAP, start + 1)

    return chunks


def sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def build_sql() -> str:
    statements: list[str] = [
        "BEGIN;",
    ]

    loaded_documents = 0
    loaded_chunks = 0

    for path in sorted(EXAMPLES_DIR.glob("*.md")):
        document_id = path.stem
        content = path.read_text(encoding="utf-8")
        chunks = split_text(content)

        if not chunks:
            continue

        check_sql = f"""
SELECT id
FROM document_versions
WHERE document_id = {sql_literal(document_id)};
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
                "-Atc",
                check_sql,
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )

        version_id = result.stdout.strip()

        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip())

        if not version_id:
            continue

        loaded_documents += 1

        statements.append(
            f"""
DELETE FROM chunks
WHERE document_version_id = {version_id};
""".strip()
        )

        for ordinal, chunk in enumerate(chunks):
            metadata = json.dumps(
                {
                    "source": "local_example",
                    "filename": path.name,
                    "chunking": {
                        "size": CHUNK_SIZE,
                        "overlap": CHUNK_OVERLAP,
                    },
                },
                ensure_ascii=False,
            )

            statements.append(
                f"""
INSERT INTO chunks (
    document_version_id,
    ordinal,
    page_number,
    section_path,
    content,
    embedding,
    metadata
)
VALUES (
    {version_id},
    {ordinal},
    NULL,
    ARRAY[]::TEXT[],
    {sql_literal(chunk)},
    NULL,
    {sql_literal(metadata)}::jsonb
);
""".strip()
            )

            loaded_chunks += 1

    statements.extend(
        [
            "COMMIT;",
            "",
            f"SELECT {loaded_documents} AS source_documents, {loaded_chunks} AS inserted_chunks;",
            "",
            """
SELECT
    dv.domain,
    count(*) AS chunks
FROM chunks c
JOIN document_versions dv
  ON dv.id = c.document_version_id
GROUP BY dv.domain
ORDER BY dv.domain;
""".strip(),
        ]
    )

    return "\n\n".join(statements)


def run_psql(sql: str) -> None:
    result = subprocess.run(
        [
            "docker",
            "exec",
            "-i",
            CONTAINER,
            "psql",
            "-v",
            "ON_ERROR_STOP=1",
            "-U",
            DB_USER,
            "-d",
            DATABASE,
        ],
        input=sql,
        text=True,
        encoding="utf-8",
        check=False,
    )

    if result.returncode != 0:
        raise SystemExit(result.returncode)


def main() -> None:
    sql = build_sql()
    run_psql(sql)


if __name__ == "__main__":
    main()
