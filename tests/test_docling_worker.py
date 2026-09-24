import hashlib

import pytest

from rag_enterprise_lab.adapters.docling import MockDoclingAdapter
from rag_enterprise_lab.adapters.r2 import InMemoryObjectStore
from rag_enterprise_lab.domain.processing import ProcessingStatus, QuarantineReason
from rag_enterprise_lab.generation.document_format_rules import format_for
from rag_enterprise_lab.ingestion.pipeline import generate_and_upload
from rag_enterprise_lab.storage.bucket_layout import raw_key
from rag_enterprise_lab.worker.docling_worker import run_worker


def _uploaded_batch(document_dataset, n, tmp_path):
    entries = document_dataset.manifest[:n]
    store = InMemoryObjectStore()
    generate_and_upload(entries, store, dry_run=False, temp_dir=tmp_path / "t")
    return entries, store


def test_worker_requires_document_id_or_limit(document_dataset):
    with pytest.raises(ValueError):
        run_worker(
            document_id=None,
            limit=None,
            store=InMemoryObjectStore(),
            parser=MockDoclingAdapter(),
            manifest=document_dataset.manifest[:1],
        )


def test_worker_unknown_document_id_raises(document_dataset):
    with pytest.raises(ValueError, match="unknown document_id"):
        run_worker(
            document_id="DOES-NOT-EXIST",
            limit=None,
            store=InMemoryObjectStore(),
            parser=MockDoclingAdapter(),
            manifest=document_dataset.manifest[:1],
        )


def test_worker_success_path_single_document(document_dataset, tmp_path):
    entries, store = _uploaded_batch(document_dataset, 3, tmp_path)
    target = entries[0]

    result = run_worker(
        document_id=target.document_id, limit=None, store=store, parser=MockDoclingAdapter(), manifest=entries
    )

    assert result.stats.processed == 1
    assert result.stats.uploaded == 1
    assert result.stats.quarantined == 0
    record = result.records[0]
    assert record.status == ProcessingStatus.PROCESSED
    assert f"processed/{target.document_id}/document.json" in record.processed_keys
    assert f"processed/{target.document_id}/content.md" in record.processed_keys
    assert f"processed/{target.document_id}/metadata.json" in record.processed_keys


def test_worker_limit_mode_processes_first_n(document_dataset, tmp_path):
    entries, store = _uploaded_batch(document_dataset, 5, tmp_path)

    result = run_worker(
        document_id=None, limit=3, store=store, parser=MockDoclingAdapter(), manifest=entries
    )

    assert result.stats.processed == 3
    assert result.stats.uploaded == 3


def test_worker_document_id_takes_priority_over_limit(document_dataset, tmp_path):
    entries, store = _uploaded_batch(document_dataset, 5, tmp_path)
    target = entries[2]

    result = run_worker(
        document_id=target.document_id, limit=5, store=store, parser=MockDoclingAdapter(), manifest=entries
    )

    assert result.stats.processed == 1
    assert result.records[0].document_id == target.document_id


def test_worker_quarantine_path_never_discards_document(document_dataset):
    entry = document_dataset.manifest[0]
    ext = format_for(entry.document_id, entry.document_type)
    key = raw_key(entry.document_id, entry.domain, ext)
    store = InMemoryObjectStore()
    store.put_bytes(key, b"", content_type="application/octet-stream", checksum=hashlib.sha256(b"").hexdigest())

    result = run_worker(
        document_id=entry.document_id, limit=None, store=store, parser=MockDoclingAdapter(), manifest=[entry]
    )

    assert result.stats.quarantined == 1
    record = result.records[0]
    assert record.status == ProcessingStatus.QUARANTINED
    assert record.quarantine_reason == QuarantineReason.CORRUPTED_FILE
    assert store.head(key) is not None  # jamais supprimé silencieusement


def test_worker_creates_no_local_temp_files(document_dataset, tmp_path):
    entries, store = _uploaded_batch(document_dataset, 2, tmp_path)
    upload_temp_dir = tmp_path / "t"

    run_worker(document_id=None, limit=2, store=store, parser=MockDoclingAdapter(), manifest=entries)

    # ingest() traite les octets en mémoire : aucun fichier temporaire créé
    # côté worker pour le contenu du document (au-delà de ceux, déjà
    # nettoyés, de l'upload amont simulé ci-dessus).
    assert list(upload_temp_dir.glob("*")) == []


def test_worker_never_logs_credentials(document_dataset, tmp_path, monkeypatch):
    monkeypatch.setenv("R2_ACCESS_KEY_ID", "AKIA_FAKE_TEST_ONLY")
    monkeypatch.setenv("R2_SECRET_ACCESS_KEY", "fake-secret-test-only")
    entries, store = _uploaded_batch(document_dataset, 1, tmp_path)

    result = run_worker(
        document_id=entries[0].document_id,
        limit=None,
        store=store,
        parser=MockDoclingAdapter(),
        manifest=entries,
    )

    serialized = str(result.stats.model_dump()) + " ".join(
        str(e.model_dump()) for e in result.audit_events
    )
    assert "AKIA_FAKE_TEST_ONLY" not in serialized
    assert "fake-secret-test-only" not in serialized
