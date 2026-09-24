"""Entrypoint Cloud Run Job — worker Docling distant (Phase 3).

Architecture : Cloudflare R2 EU -> Google Cloud Run Job -> Docling ->
R2 processed/quarantine. Réutilise `ingestion.pipeline.ingest`, qui traite
chaque document en mémoire (jamais de fichier temporaire disque pour son
contenu) : aucun document n'est jamais persisté localement sur le worker.

Variables d'environnement (jamais de secret en dur) :
  R2_ENDPOINT, R2_BUCKET, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY
  DOCUMENT_ID   -> traite un seul document (prioritaire sur LIMIT)
  LIMIT         -> traite les N premiers documents du manifest
"""

import json
import os

from rag_enterprise_lab.adapters.docling import DoclingWorkerAdapter, DocumentParserPort
from rag_enterprise_lab.adapters.r2 import ObjectStorePort, R2StorageAdapter, credentials_available
from rag_enterprise_lab.core.config import Settings
from rag_enterprise_lab.domain.documents import DocumentManifestEntry
from rag_enterprise_lab.ingestion.pipeline import ingest
from rag_enterprise_lab.ingestion.stats import RunResult
from rag_enterprise_lab.storage.bucket_layout import manifest_key


def run_worker(
    *,
    document_id: str | None,
    limit: int | None,
    store: ObjectStorePort,
    parser: DocumentParserPort,
    manifest: list[DocumentManifestEntry],
) -> RunResult:
    if not document_id and not limit:
        raise ValueError("worker requires DOCUMENT_ID or LIMIT")

    manifest_by_id = {e.document_id: e for e in manifest}
    if document_id:
        if document_id not in manifest_by_id:
            raise ValueError(f"unknown document_id: {document_id}")
        ids = [document_id]
    else:
        ids = list(manifest_by_id)[:limit]

    return ingest(ids, manifest_by_id, store, parser)


def _load_manifest(store: ObjectStorePort) -> list[DocumentManifestEntry]:
    payload = store.get_bytes(manifest_key("document_manifest.json"))
    return [DocumentManifestEntry(**entry) for entry in json.loads(payload)]


def main() -> int:
    settings = Settings()
    if not credentials_available(settings):
        print("BLOCKED_BY_CREDENTIALS: R2_ENDPOINT/R2_BUCKET/R2_ACCESS_KEY_ID/R2_SECRET_ACCESS_KEY missing.")
        return 1

    document_id = os.environ.get("DOCUMENT_ID") or None
    limit_raw = os.environ.get("LIMIT")
    limit = int(limit_raw) if limit_raw else None

    store = R2StorageAdapter(settings)
    parser = DoclingWorkerAdapter()
    manifest = _load_manifest(store)

    result = run_worker(
        document_id=document_id, limit=limit, store=store, parser=parser, manifest=manifest
    )
    for field, value in result.stats.model_dump().items():
        print(f"{field}: {value}")

    for record in result.records:
        if record.status.value in ("QUARANTINED", "FAILED"):
            reason = record.quarantine_reason.value if record.quarantine_reason else "NONE"
            print(
                f"record_error: document_id={record.document_id} "
                f"status={record.status.value} "
                f"reason={reason} "
                f"error={record.error_message}"
            )

    return 0 if result.stats.failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
