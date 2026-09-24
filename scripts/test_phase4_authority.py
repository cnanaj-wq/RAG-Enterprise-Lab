from __future__ import annotations

import subprocess


CONTAINER = "genai-postgres"
DATABASE = "rag_enterprise_lab"
DB_USER = "genai"


AUTHORITY_RANK = {
    "SIGNED_AMENDMENT": 0,
    "SIGNED_CONTRACT": 1,
    "SIGNED_PURCHASE_ORDER": 2,
    "APPROVED_PROPOSAL": 3,
    "APPROVED_PRICING_GRID": 4,
    "DRAFT": 5,
}


def fetch_axion_documents() -> list[dict[str, str]]:
    sql = """
SELECT
    document_id,
    title,
    document_type,
    version_label,
    status,
    authority_level,
    coalesce(valid_from::text, ''),
    coalesce(created_at::text, ''),
    coalesce(supersedes_document_id, '')
FROM document_versions
WHERE title ILIKE '%Axion Solutions%'
ORDER BY created_at;
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

    rows: list[dict[str, str]] = []

    for line in result.stdout.splitlines():
        if not line.strip():
            continue

        (
            document_id,
            title,
            document_type,
            version_label,
            status,
            authority_level,
            valid_from,
            created_at,
            supersedes,
        ) = line.split("\t")

        rows.append(
            {
                "document_id": document_id,
                "title": title,
                "document_type": document_type,
                "version_label": version_label,
                "status": status,
                "authority_level": authority_level,
                "valid_from": valid_from,
                "created_at": created_at,
                "supersedes": supersedes,
            }
        )

    return rows


def main() -> None:
    documents = fetch_axion_documents()

    if not documents:
        print("Aucun document Axion trouve.")
        return

    print("Documents Axion trouves :")
    print()

    for doc in documents:
        print(
            f"{doc['document_id']} | "
            f"{doc['document_type']} | "
            f"v{doc['version_label']} | "
            f"{doc['status']} | "
            f"{doc['authority_level']} | "
            f"valid_from={doc['valid_from'] or '-'} | "
            f"supersedes={doc['supersedes'] or '-'}"
        )

    best_rank = min(
        AUTHORITY_RANK.get(doc["authority_level"], 999)
        for doc in documents
    )

    same_authority = [
        doc
        for doc in documents
        if AUTHORITY_RANK.get(doc["authority_level"], 999) == best_rank
    ]

    authoritative = sorted(
        same_authority,
        key=lambda doc: (
            doc["valid_from"],
            doc["created_at"],
        ),
        reverse=True,
    )[0]

    distinct_authorities = {
        doc["authority_level"]
        for doc in documents
    }

    conflict_candidate = (
        len(documents) > 1
        and len(distinct_authorities) > 1
    )

    print()
    print("Decision d'autorite :")
    print(f"Document faisant foi : {authoritative['document_id']}")
    print(f"Titre                : {authoritative['title']}")
    print(f"Authority level      : {authoritative['authority_level']}")
    print(f"Valid from           : {authoritative['valid_from']}")
    print(f"Conflict candidate   : {conflict_candidate}")


if __name__ == "__main__":
    main()