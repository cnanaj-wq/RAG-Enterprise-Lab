"""Pipeline Phase 3 : manifest -> génération -> upload R2 (`generate_and_upload`)
et raw R2 -> Docling -> processed/quarantine (`ingest`).

Invariants :
- déterministe (aucun aléa) ;
- idempotent (document_id + checksum) : objet identique -> SKIP, contenu
  différent -> CONFLICT (jamais d'overwrite silencieux) ;
- jamais de suppression silencieuse d'un document problématique (quarantaine
  systématique + audit event) ;
- fichiers temporaires bornés (MAX_LOCAL_TEMP_MB) et toujours nettoyés ;
- aucun secret dans les logs/événements d'audit.
"""

import hashlib
import json
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path

from rag_enterprise_lab.adapters.docling import (
    CorruptedDocumentError,
    DocumentParserPort,
    UnsupportedFormatError,
)
from rag_enterprise_lab.adapters.r2 import ObjectStorePort
from rag_enterprise_lab.domain.documents import DocumentManifestEntry
from rag_enterprise_lab.domain.processing import (
    AuditEvent,
    ProcessingRecord,
    ProcessingStatus,
    QuarantineReason,
)
from rag_enterprise_lab.generation.document_content_generator import generate_content
from rag_enterprise_lab.generation.document_format_rules import format_for
from rag_enterprise_lab.ingestion.stats import RunResult, RunStats
from rag_enterprise_lab.ingestion.temp_guard import TempDiskLimitExceeded, TempFileGuard
from rag_enterprise_lab.storage.bucket_layout import processed_key, quarantine_key, raw_key

DEFAULT_MAX_TEMP_MB = 50


def _event(document_id: str, event_type: str, details: dict[str, object]) -> AuditEvent:
    return AuditEvent(
        document_id=document_id, event_type=event_type, timestamp=datetime.now(UTC), details=details
    )


def _record(
    entry: DocumentManifestEntry,
    status: ProcessingStatus,
    fmt: str,
    key: str | None,
    checksum: str | None,
    *,
    processed_keys: list[str] | None = None,
    quarantine_reason: QuarantineReason | None = None,
    error: str | None = None,
) -> ProcessingRecord:
    return ProcessingRecord(
        document_id=entry.document_id,
        status=status,
        format=fmt,
        raw_key=key,
        expected_checksum_placeholder=entry.checksum,
        actual_checksum=checksum,
        processed_keys=processed_keys or [],
        quarantine_reason=quarantine_reason,
        error_message=error,
        updated_at=datetime.now(UTC),
    )


def generate_and_upload(
    entries: list[DocumentManifestEntry],
    store: ObjectStorePort,
    *,
    dry_run: bool = False,
    limit: int | None = None,
    max_temp_mb: int = DEFAULT_MAX_TEMP_MB,
    temp_dir: Path | None = None,
) -> RunResult:
    start = time.monotonic()
    stats = RunStats()
    records: list[ProcessingRecord] = []
    events: list[AuditEvent] = []
    selected = entries[:limit] if limit is not None else entries

    temp_root = temp_dir or Path(tempfile.mkdtemp(prefix="rag-phase3-upload-"))
    guard = TempFileGuard(temp_root, max_temp_mb)
    try:
        for entry in selected:
            stats.processed += 1
            content, content_type, ext = generate_content(entry)
            checksum = hashlib.sha256(content).hexdigest()
            key = raw_key(entry.document_id, entry.domain, ext)

            if dry_run:
                events.append(
                    _event(entry.document_id, "DRY_RUN_WOULD_UPLOAD", {"key": key, "bytes": len(content)})
                )
                records.append(_record(entry, ProcessingStatus.PLANNED, ext, key, None))
                continue

            temp_path = guard.write(f"{entry.document_id}.{ext}", content)
            try:
                existing = store.head(key)
                if existing is not None and existing.checksum == checksum:
                    stats.skipped += 1
                    events.append(_event(entry.document_id, "SKIPPED_IDENTICAL", {"key": key}))
                    records.append(_record(entry, ProcessingStatus.UPLOADED, ext, key, checksum))
                    continue
                if existing is not None and existing.checksum != checksum:
                    stats.conflicts += 1
                    events.append(
                        _event(
                            entry.document_id,
                            "CONFLICT_CONTENT_MISMATCH",
                            {"key": key, "existing_checksum": existing.checksum, "new_checksum": checksum},
                        )
                    )
                    records.append(
                        _record(
                            entry,
                            ProcessingStatus.FAILED,
                            ext,
                            key,
                            checksum,
                            error="CONFLICT: same document_id, different content — not overwritten",
                        )
                    )
                    continue

                store.put_bytes(key, content, content_type=content_type, checksum=checksum)
                stats.uploaded += 1
                stats.bytes_uploaded += len(content)
                events.append(_event(entry.document_id, "UPLOADED", {"key": key, "bytes": len(content)}))
                records.append(_record(entry, ProcessingStatus.UPLOADED, ext, key, checksum))
            finally:
                guard.release(temp_path)
    finally:
        stats.temp_disk_current_mb = guard.current_mb
        stats.temp_disk_peak_mb = guard.peak_mb
        guard.cleanup()

    stats.duration_seconds = time.monotonic() - start
    return RunResult(stats=stats, records=records, audit_events=events)


def _quarantine(
    store: ObjectStorePort,
    entry: DocumentManifestEntry,
    content: bytes,
    ext: str,
    reason: QuarantineReason,
    error_message: str,
    stats: RunStats,
    records: list[ProcessingRecord],
    events: list[AuditEvent],
) -> None:
    """Ne supprime jamais silencieusement : le document brut est copié vers
    quarantine/ pour investigation, jamais effacé."""
    key = quarantine_key(entry.document_id, ext)
    checksum = hashlib.sha256(content).hexdigest()
    store.put_bytes(key, content, content_type="application/octet-stream", checksum=checksum)
    stats.quarantined += 1
    events.append(
        _event(entry.document_id, "QUARANTINED", {"reason": reason.value, "key": key, "error": error_message})
    )
    records.append(
        _record(
            entry,
            ProcessingStatus.QUARANTINED,
            ext,
            key,
            checksum,
            quarantine_reason=reason,
            error=error_message,
        )
    )


def ingest(
    document_ids: list[str],
    manifest_by_id: dict[str, DocumentManifestEntry],
    store: ObjectStorePort,
    parser: DocumentParserPort,
    *,
    dry_run: bool = False,
    limit: int | None = None,
) -> RunResult:
    start = time.monotonic()
    stats = RunStats()
    records: list[ProcessingRecord] = []
    events: list[AuditEvent] = []
    selected = document_ids[:limit] if limit is not None else document_ids

    for document_id in selected:
        stats.processed += 1
        entry = manifest_by_id[document_id]
        ext = format_for(document_id, entry.document_type)
        raw = raw_key(document_id, entry.domain, ext)

        if dry_run:
            events.append(_event(document_id, "DRY_RUN_WOULD_PROCESS", {"raw_key": raw}))
            continue

        head = store.head(raw)
        if head is None:
            stats.failed += 1
            events.append(_event(document_id, "PROCESSING_FAILED", {"reason": "raw object missing"}))
            records.append(_record(entry, ProcessingStatus.FAILED, ext, raw, None, error="raw object missing"))
            continue

        content = store.get_bytes(raw)
        actual_checksum = hashlib.sha256(content).hexdigest()
        if head.checksum and head.checksum != actual_checksum:
            _quarantine(
                store, entry, content, ext, QuarantineReason.CHECKSUM_MISMATCH,
                "downloaded content checksum does not match stored head checksum",
                stats, records, events,
            )
            continue

        events.append(_event(document_id, "PROCESSING_STARTED", {"raw_key": raw}))
        try:
            parsed = parser.parse(document_id=document_id, content=content, extension=ext)
        except UnsupportedFormatError as exc:
            _quarantine(
                store, entry, content, ext, QuarantineReason.UNSUPPORTED_FORMAT, str(exc), stats, records, events
            )
            continue
        except CorruptedDocumentError as exc:
            _quarantine(
                store, entry, content, ext, QuarantineReason.CORRUPTED_FILE, str(exc), stats, records, events
            )
            continue
        except Exception as exc:  # noqa: BLE001 - toute autre erreur de parsing -> quarantaine
            _quarantine(
                store, entry, content, ext, QuarantineReason.PARSING_ERROR, str(exc), stats, records, events
            )
            continue

        if parsed.metadata.get("document_id") not in (document_id, None):
            _quarantine(
                store, entry, content, ext, QuarantineReason.METADATA_MISMATCH,
                "parsed metadata document_id does not match requested document_id",
                stats, records, events,
            )
            continue

        document_json = json.dumps(
            {"document_id": document_id, "extension": ext, "text_length": len(parsed.text)},
            sort_keys=True,
        ).encode("utf-8")
        content_md = parsed.text.encode("utf-8")
        metadata_json = json.dumps(parsed.metadata, sort_keys=True, default=str).encode("utf-8")

        processed_keys: list[str] = []
        for artifact, payload in (
            ("document.json", document_json),
            ("content.md", content_md),
            ("metadata.json", metadata_json),
        ):
            artifact_key = processed_key(document_id, artifact)
            store.put_bytes(
                artifact_key,
                payload,
                content_type="application/json" if artifact.endswith(".json") else "text/markdown",
                checksum=hashlib.sha256(payload).hexdigest(),
            )
            processed_keys.append(artifact_key)

        if parsed.tables:
            tables_json = json.dumps(parsed.tables, sort_keys=True).encode("utf-8")
            tables_key = processed_key(document_id, "tables.json")
            store.put_bytes(
                tables_key, tables_json, content_type="application/json",
                checksum=hashlib.sha256(tables_json).hexdigest(),
            )
            processed_keys.append(tables_key)

        stats.uploaded += 1
        events.append(_event(document_id, "PROCESSED", {"processed_keys": processed_keys}))
        records.append(
            _record(
                entry, ProcessingStatus.PROCESSED, ext, raw, actual_checksum, processed_keys=processed_keys
            )
        )

    stats.duration_seconds = time.monotonic() - start
    return RunResult(stats=stats, records=records, audit_events=events)


__all__ = [
    "DEFAULT_MAX_TEMP_MB",
    "TempDiskLimitExceeded",
    "generate_and_upload",
    "ingest",
]
