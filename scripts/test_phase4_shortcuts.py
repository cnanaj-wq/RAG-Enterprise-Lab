from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]

CONTAINER = "genai-postgres"
DATABASE = "rag_enterprise_lab"
DB_USER = "genai"

COMPLETENESS_CONFIG = ROOT / "config" / "completeness" / "client.yml"


AUTHORITY_RANK = {
    "SIGNED_AMENDMENT": 0,
    "SIGNED_CONTRACT": 1,
    "SIGNED_PURCHASE_ORDER": 2,
    "APPROVED_PROPOSAL": 3,
    "APPROVED_PRICING_GRID": 4,
    "DRAFT": 5,
}


def run_sql(sql: str) -> str:
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

    return result.stdout.strip()


def sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def fetch_client_documents(client_name: str) -> list[dict[str, str]]:
    sql = f"""
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
WHERE title ILIKE '%' || {sql_literal(client_name)} || '%'
ORDER BY created_at;
"""

    output = run_sql(sql)

    if not output:
        return []

    rows: list[dict[str, str]] = []

    for line in output.splitlines():
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


def resolve_authority(
    documents: list[dict[str, str]],
) -> dict[str, str]:
    best_rank = min(
        AUTHORITY_RANK.get(doc["authority_level"], 999)
        for doc in documents
    )

    same_authority = [
        doc
        for doc in documents
        if AUTHORITY_RANK.get(
            doc["authority_level"],
            999,
        )
        == best_rank
    ]

    return sorted(
        same_authority,
        key=lambda doc: (
            doc["valid_from"],
            doc["created_at"],
        ),
        reverse=True,
    )[0]


def load_completeness_config() -> dict:
    return yaml.safe_load(
        COMPLETENESS_CONFIG.read_text(
            encoding="utf-8"
        )
    )


def shortcut_contract(client_name: str) -> None:
    documents = fetch_client_documents(client_name)

    print("🧭 Shortcut : /contrat")
    print()

    if not documents:
        print("⚠️ Aucun document trouvé.")
        return

    authoritative = resolve_authority(documents)

    print(f"📄 Client               : {client_name}")
    print(
        f"⚖️ Document faisant foi : "
        f"{authoritative['document_id']}"
    )
    print(
        f"📝 Type                 : "
        f"{authoritative['document_type']}"
    )
    print(
        f"✅ Statut               : "
        f"{authoritative['status']}"
    )
    print(
        f"🏛️ Autorité            : "
        f"{authoritative['authority_level']}"
    )
    print(
        f"📅 Valid from           : "
        f"{authoritative['valid_from'] or '-'}"
    )
    print(
        f"🔗 Supersedes           : "
        f"{authoritative['supersedes'] or '-'}"
    )


def shortcut_conflicts(client_name: str) -> None:
    documents = fetch_client_documents(client_name)

    print("🧭 Shortcut : /conflits")
    print()

    if len(documents) <= 1:
        print("✅ Aucun conflit documentaire détecté.")
        return

    authorities = {
        doc["authority_level"]
        for doc in documents
    }

    print(f"⚠️ Documents trouvés   : {len(documents)}")
    print(
        "⚖️ Niveaux d'autorité : "
        + ", ".join(sorted(authorities))
    )
    print()

    for doc in documents:
        print(
            f"📄 {doc['document_id']} | "
            f"{doc['document_type']} | "
            f"v{doc['version_label']} | "
            f"{doc['status']} | "
            f"{doc['authority_level']}"
        )


def shortcut_sources(client_name: str) -> None:
    documents = fetch_client_documents(client_name)

    print("🧭 Shortcut : /sources")
    print()

    if not documents:
        print("⚠️ Aucune source trouvée.")
        return

    for doc in documents:
        print(
            f"📄 {doc['document_id']} — "
            f"{doc['title']} "
            f"[{doc['status']} / "
            f"{doc['authority_level']}]"
        )


def shortcut_completeness(
    client_name: str,
) -> None:
    documents = fetch_client_documents(client_name)
    config = load_completeness_config()

    print("🧭 Shortcut : /completude")
    print()

    if not documents:
        print("⚠️ Aucun document trouvé.")
        return

    mandatory = config["client_dossier"]["mandatory"]
    rules = config["client_dossier"].get(
        "rules",
        {},
    )

    present_types = {
        doc["document_type"]
        for doc in documents
    }

    present = [
        document_type
        for document_type in mandatory
        if document_type in present_types
    ]

    missing = [
        document_type
        for document_type in mandatory
        if document_type not in present_types
    ]

    total = len(mandatory)
    present_count = len(present)

    completeness = (
        (present_count / total) * 100
        if total
        else 0.0
    )

    print(f"📄 Client               : {client_name}")
    print(
        f"📊 Complétude           : "
        f"{present_count}/{total} "
        f"({completeness:.1f} %)"
    )
    print()

    print("✅ Documents présents")
    for document_type in present:
        print(f"   ✅ {document_type}")

    print()
    print("❌ Documents manquants")
    for document_type in missing:
        print(f"   ❌ {document_type}")

    print()
    print("🛡️ Règles de contrôle")

    insurance_days = rules.get(
        "insurance_warning_days"
    )

    registry_days = rules.get(
        "company_registry_max_age_days"
    )

    if insurance_days is not None:
        print(
            f"   ⚠️ Assurance : alerte "
            f"{insurance_days} jours avant échéance"
        )

    if registry_days is not None:
        print(
            f"   📅 Extrait registre : "
            f"âge maximal {registry_days} jours"
        )

    print()

    if completeness == 100:
        print("✅ Dossier documentaire complet.")
    elif completeness >= 80:
        print(
            "⚠️ Dossier presque complet : "
            "quelques pièces restent à fournir."
        )
    else:
        print(
            "🚨 Dossier incomplet : "
            "action documentaire requise."
        )


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "shortcut",
        choices=[
            "contrat",
            "conflits",
            "sources",
            "completude",
        ],
    )

    parser.add_argument(
        "client",
        help=(
            "Nom du client, "
            "ex: Axion Solutions"
        ),
    )

    args = parser.parse_args()

    if args.shortcut == "contrat":
        shortcut_contract(args.client)

    elif args.shortcut == "conflits":
        shortcut_conflicts(args.client)

    elif args.shortcut == "sources":
        shortcut_sources(args.client)

    elif args.shortcut == "completude":
        shortcut_completeness(args.client)


if __name__ == "__main__":
    main()