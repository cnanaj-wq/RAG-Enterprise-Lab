"""CLI Phase 3 : génération + upload R2, et ingestion Docling.

Exemples :
    python scripts/phase3_ingest.py generate_and_upload --dry-run --limit 20
    python scripts/phase3_ingest.py generate_and_upload --limit 10
    python scripts/phase3_ingest.py generate_and_upload --document-id DOC-01346
    python scripts/phase3_ingest.py ingest --limit 20
    python scripts/phase3_ingest.py ingest --document-id DOC-01346

Si les credentials R2 (R2_ENDPOINT, R2_BUCKET, R2_ACCESS_KEY_ID,
R2_SECRET_ACCESS_KEY) sont absents, le provisioning distant réel est
BLOCKED_BY_CREDENTIALS : la commande explique la checklist et s'arrête sans
inventer de bucket existant. Utiliser --dry-run pour valider le pipeline
sans réseau dans ce cas.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parent.parent / "src"),
)

from rag_enterprise_lab.adapters.docling import MockDoclingAdapter
from rag_enterprise_lab.adapters.r2 import (
    R2StorageAdapter,
    credentials_available,
)
from rag_enterprise_lab.core.config import Settings
from rag_enterprise_lab.domain.documents import DocumentManifestEntry
from rag_enterprise_lab.ingestion.pipeline import (
    DEFAULT_MAX_TEMP_MB,
    generate_and_upload,
    ingest,
)


REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = (
    REPO_ROOT
    / "data"
    / "seed"
    / "document_manifest.json"
)


def _load_manifest() -> list[DocumentManifestEntry]:
    data = json.loads(
        MANIFEST_PATH.read_text(
            encoding="utf-8"
        )
    )

    return [
        DocumentManifestEntry(**entry)
        for entry in data
    ]


def _credentials_checklist(
    settings: Settings,
) -> None:
    print(
        "BLOCKED_BY_CREDENTIALS — "
        "R2 credentials are not configured."
    )

    print(
        "Checklist to unblock remote provisioning:"
    )

    for name, value in (
        ("R2_ENDPOINT", settings.r2_endpoint),
        ("R2_BUCKET", settings.r2_bucket),
        (
            "R2_ACCESS_KEY_ID",
            settings.r2_access_key_id,
        ),
        (
            "R2_SECRET_ACCESS_KEY",
            settings.r2_secret_access_key,
        ),
    ):
        print(
            f"  [{'x' if value else ' '}] {name}"
        )

    print(
        "Set these as environment variables "
        "(never hardcode them, never commit them)."
    )

    print(
        "Until then: use --dry-run to validate "
        "the pipeline offline "
        "(zero R2 objects created)."
    )


def _filter_document(
    entries: list[DocumentManifestEntry],
    document_id: str | None,
) -> list[DocumentManifestEntry]:
    if not document_id:
        return entries

    selected = [
        entry
        for entry in entries
        if entry.document_id == document_id
    ]

    if not selected:
        raise SystemExit(
            "Document introuvable dans le manifest: "
            f"{document_id}"
        )

    return selected


def cmd_generate_and_upload(
    args: argparse.Namespace,
) -> None:
    settings = Settings()

    entries = _filter_document(
        _load_manifest(),
        args.document_id,
    )

    if (
        not args.dry_run
        and not credentials_available(settings)
    ):
        _credentials_checklist(settings)
        return

    store = (
        R2StorageAdapter(settings)
        if not args.dry_run
        else _OfflineNoopStore()
    )

    result = generate_and_upload(
        entries,
        store,
        dry_run=args.dry_run,
        limit=args.limit,
        max_temp_mb=args.max_temp_mb,
    )

    _print_stats(
        "generate_and_upload",
        result,
    )


def cmd_ingest(
    args: argparse.Namespace,
) -> None:
    settings = Settings()
    entries = _load_manifest()

    manifest_by_id = {
        entry.document_id: entry
        for entry in entries
    }

    if args.document_id:
        if args.document_id not in manifest_by_id:
            raise SystemExit(
                "Document introuvable dans le manifest: "
                f"{args.document_id}"
            )

        document_ids = [
            args.document_id
        ]

    elif args.limit:
        document_ids = list(
            manifest_by_id
        )[: args.limit]

    else:
        document_ids = list(
            manifest_by_id
        )

    if (
        not args.dry_run
        and not credentials_available(settings)
    ):
        _credentials_checklist(settings)
        return

    store = (
        R2StorageAdapter(settings)
        if not args.dry_run
        else _OfflineNoopStore()
    )

    parser = MockDoclingAdapter()

    result = ingest(
        document_ids,
        manifest_by_id,
        store,
        parser,
        dry_run=args.dry_run,
        limit=args.limit,
    )

    _print_stats(
        "ingest",
        result,
    )


class _OfflineNoopStore:
    """Store utilisé uniquement en --dry-run.

    Le pipeline ne l'appelle jamais dans cette branche.
    """


def _print_stats(
    command: str,
    result,
) -> None:
    print(
        f"=== {command} ==="
    )

    for field, value in (
        result.stats.model_dump().items()
    ):
        print(
            f"{field}: {value}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__
    )

    sub = parser.add_subparsers(
        dest="command",
        required=True,
    )

    up = sub.add_parser(
        "generate_and_upload"
    )

    up.add_argument(
        "--dry-run",
        action="store_true",
    )

    up.add_argument(
        "--limit",
        type=int,
        default=None,
    )

    up.add_argument(
        "--document-id",
        type=str,
        default=None,
    )

    up.add_argument(
        "--max-temp-mb",
        type=int,
        default=DEFAULT_MAX_TEMP_MB,
    )

    up.set_defaults(
        func=cmd_generate_and_upload
    )

    ing = sub.add_parser(
        "ingest"
    )

    ing.add_argument(
        "--dry-run",
        action="store_true",
    )

    ing.add_argument(
        "--limit",
        type=int,
        default=None,
    )

    ing.add_argument(
        "--document-id",
        type=str,
        default=None,
    )

    ing.set_defaults(
        func=cmd_ingest
    )

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()