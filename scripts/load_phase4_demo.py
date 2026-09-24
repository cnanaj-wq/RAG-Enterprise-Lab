from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "data" / "seed" / "document_manifest.json"

CONTAINER = "genai-postgres"
DATABASE = "rag_enterprise_lab"
DB_USER = "genai"


def load_manifest() -> list[dict[str, Any]]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def build_index(entries: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {entry["document_id"]: entry for entry in entries}


def chain_for(
    entry: dict[str, Any],
    by_id: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return the complete supersedes chain, oldest -> newest."""
    chain: list[dict[str, Any]] = []
    seen: set[str] = set()

    current: dict[str, Any] | None = entry

    while current is not None:
        document_id = current["document_id"]

        if document_id in seen:
            raise RuntimeError(f"Cycle supersedes detecte: {document_id}")

        seen.add(document_id)
        chain.append(current)

        parent_id = current.get("supersedes")
        current = by_id.get(parent_id) if parent_id else None

    chain.reverse()
    return chain


def select_demo_entries(
    entries: list[dict[str, Any]],
    limit: int,
) -> list[dict[str, Any]]:
    if limit <= 0:
        raise ValueError("--limit doit etre > 0")

    if limit >= len(entries):
        return entries

    by_id = build_index(entries)
    selected: dict[str, dict[str, Any]] = {}

    domains = sorted({entry["domain"] for entry in entries})
    per_domain = max(1, limit // len(domains))

    for domain in domains:
        domain_selected: list[dict[str, Any]] = []

        versioned = [
            entry
            for entry in entries
            if entry["domain"] == domain and entry.get("supersedes")
        ]

        for entry in versioned:
            chain = chain_for(entry, by_id)
            missing = [
                item
                for item in chain
                if item["document_id"] not in selected
                and item["document_id"] not in {
                    x["document_id"] for x in domain_selected
                }
            ]

            if missing and len(domain_selected) + len(missing) <= per_domain:
                domain_selected.extend(missing)

            if len(domain_selected) >= per_domain:
                break

        for entry in entries:
            if len(domain_selected) >= per_domain:
                break

            if entry["domain"] != domain:
                continue

            if (
                entry["document_id"] not in selected
                and entry["document_id"]
                not in {x["document_id"] for x in domain_selected}
            ):
                domain_selected.append(entry)

        for item in domain_selected:
            if len(selected) < limit:
                selected[item["document_id"]] = item

    for entry in entries:
        if len(selected) >= limit:
            break

        if entry["document_id"] not in selected:
            selected[entry["document_id"]] = entry

    return list(selected.values())[:limit]


def sql_literal(value: Any) -> str:
    if value is None:
        return "NULL"

    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"

    text = str(value).replace("'", "''")
    return f"'{text}'"


def logical_root_id(
    entry: dict[str, Any],
    by_id: dict[str, dict[str, Any]],
) -> str:
    chain = chain_for(entry, by_id)
    return chain[0]["document_id"]


def build_sql(entries: list[dict[str, Any]]) -> str:
    by_id = build_index(entries)

    statements: list[str] = [
        "BEGIN;",
        "SET CONSTRAINTS ALL DEFERRED;",
    ]

    roots = sorted(
        {
            logical_root_id(entry, by_id)
            for entry in entries
        }
    )

    for root_id in roots:
        statements.append(
            """
INSERT INTO documents (logical_document_id)
VALUES ({root})
ON CONFLICT (logical_document_id) DO NOTHING;
""".format(root=sql_literal(root_id)).strip()
        )

    for entry in entries:
        root_id = logical_root_id(entry, by_id)

        raw_key = entry["storage_target"]
        if raw_key.startswith("r2://"):
            parts = raw_key.split("/", 3)
            raw_key = parts[3] if len(parts) > 3 else raw_key

        processed_prefix = f"processed/{entry['document_id']}/"

        statements.append(
            f"""
INSERT INTO document_versions (
    document_id,
    logical_document_id,
    title,
    document_type,
    domain,
    source_system,
    owner_employee_id,
    classification,
    version_label,
    status,
    authority_level,
    valid_from,
    valid_to,
    created_at,
    approved_at,
    signed_at,
    supersedes_document_id,
    related_customer_id,
    related_supplier_id,
    related_employee_id,
    related_project_id,
    related_opportunity_id,
    related_expected_contract_id,
    contains_personal_data,
    retention_policy,
    checksum,
    raw_object_key,
    processed_prefix,
    metadata
)
SELECT
    {sql_literal(entry["document_id"])},
    d.id,
    {sql_literal(entry["title"])},
    {sql_literal(entry["document_type"])},
    {sql_literal(entry["domain"])},
    {sql_literal(entry["source_system"])},
    {sql_literal(entry["owner"])},
    {sql_literal(entry["classification"])},
    {sql_literal(entry["version"])},
    {sql_literal(entry["status"])},
    {sql_literal(entry["authority_level"])},
    {sql_literal(entry.get("valid_from"))},
    {sql_literal(entry.get("valid_to"))},
    {sql_literal(entry["created_at"])},
    {sql_literal(entry.get("approved_at"))},
    {sql_literal(entry.get("signed_at"))},
    {sql_literal(entry.get("supersedes"))},
    {sql_literal(entry.get("related_customer_id"))},
    {sql_literal(entry.get("related_supplier_id"))},
    {sql_literal(entry.get("related_employee_id"))},
    {sql_literal(entry.get("related_project_id"))},
    {sql_literal(entry.get("related_opportunity_id"))},
    {sql_literal(entry.get("related_expected_contract_id"))},
    {sql_literal(entry["contains_personal_data"])},
    {sql_literal(entry["retention_policy"])},
    {sql_literal(entry["checksum"])},
    {sql_literal(raw_key)},
    {sql_literal(processed_prefix)},
    '{{}}'::jsonb
FROM documents d
WHERE d.logical_document_id = {sql_literal(root_id)}
ON CONFLICT (document_id) DO NOTHING;
""".strip()
        )

    for entry in entries:
        for group in entry.get("allowed_groups", []):
            statements.append(
                f"""
INSERT INTO document_acl (
    document_version_id,
    group_name
)
SELECT
    dv.id,
    {sql_literal(group)}
FROM document_versions dv
WHERE dv.document_id = {sql_literal(entry["document_id"])}
ON CONFLICT DO NOTHING;
""".strip()
            )

    statements.extend(
        [
            "COMMIT;",
            "",
            r"""
SELECT
    (SELECT count(*) FROM documents) AS logical_documents,
    (SELECT count(*) FROM document_versions) AS document_versions,
    (SELECT count(*) FROM document_acl) AS acl_rows;
""".strip(),
        ]
    )

    return "\n\n".join(statements)


def run_psql(sql: str) -> None:
    command = [
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
    ]

    result = subprocess.run(
        command,
        input=sql,
        text=True,
        encoding="utf-8",
        check=False,
    )

    if result.returncode != 0:
        raise SystemExit(result.returncode)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Nombre maximal de documents a charger",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Selectionne les documents sans ecrire dans PostgreSQL",
    )
    args = parser.parse_args()

    manifest = load_manifest()
    selected = select_demo_entries(manifest, args.limit)

    versioned = sum(
        1 for entry in selected
        if entry.get("supersedes")
    )

    domains: dict[str, int] = {}
    for entry in selected:
        domains[entry["domain"]] = domains.get(entry["domain"], 0) + 1

    print(f"Manifest total     : {len(manifest)}")
    print(f"Selection          : {len(selected)}")
    print(f"Avec supersedes    : {versioned}")
    print(f"Domaines           : {domains}")

    if args.dry_run:
        print("DRY-RUN: aucune ecriture PostgreSQL")
        return

    sql = build_sql(selected)
    run_psql(sql)


if __name__ == "__main__":
    main()


