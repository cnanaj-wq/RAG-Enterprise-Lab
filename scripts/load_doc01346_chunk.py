from __future__ import annotations

import subprocess

from rag_enterprise_lab.adapters.r2 import R2StorageAdapter
from rag_enterprise_lab.core.config import Settings


DOCUMENT_ID = "DOC-01346"
OBJECT_KEY = f"processed/{DOCUMENT_ID}/content.md"

CONTAINER = "genai-postgres"
DATABASE = "rag_enterprise_lab"
DB_USER = "genai"


def sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def main() -> None:
    store = R2StorageAdapter(Settings())

    content = store.get_bytes(
        OBJECT_KEY
    ).decode("utf-8")

    sql = f"""
DELETE FROM chunks
WHERE document_version_id = (
    SELECT id
    FROM document_versions
    WHERE document_id = {sql_literal(DOCUMENT_ID)}
);

INSERT INTO chunks (
    document_version_id,
    ordinal,
    page_number,
    section_path,
    content,
    embedding,
    metadata
)
SELECT
    id,
    0,
    NULL,
    ARRAY[]::TEXT[],
    {sql_literal(content)},
    NULL,
    '{{"source":"r2_docling","document_id":"DOC-01346"}}'::jsonb
FROM document_versions
WHERE document_id = {sql_literal(DOCUMENT_ID)};

SELECT
    count(*) AS chunks_doc_01346
FROM chunks c
JOIN document_versions dv
  ON dv.id = c.document_version_id
WHERE dv.document_id = {sql_literal(DOCUMENT_ID)};
""".strip()

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
            "-c",
            sql,
        ],
        text=True,
        encoding="utf-8",
        check=False,
    )

    if result.returncode != 0:
        raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()