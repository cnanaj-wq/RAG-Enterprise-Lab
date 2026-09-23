import copy
import hashlib

import pytest

from rag_enterprise_lab.adapters.docling import MockDoclingAdapter, UnsupportedFormatError
from rag_enterprise_lab.adapters.r2 import InMemoryObjectStore
from rag_enterprise_lab.domain.processing import ProcessingStatus, QuarantineReason
from rag_enterprise_lab.generation.document_format_rules import format_for
from rag_enterprise_lab.ingestion.pipeline import generate_and_upload, ingest
from rag_enterprise_lab.ingestion.temp_guard import TempDiskLimitExceeded
from rag_enterprise_lab.storage.bucket_layout import raw_key


@pytest.fixture
def small_batch(document_dataset):
    return document_dataset.manifest[:15]


def test_dry_run_creates_zero_remote_objects(small_batch, tmp_path):
    store = InMemoryObjectStore()
    result = generate_and_upload(small_batch, store, dry_run=True, temp_dir=tmp_path / "t")
    assert result.stats.processed == len(small_batch)
    assert result.stats.uploaded == 0
    assert store.keys() == []


def test_limit_n_is_respected(small_batch, tmp_path):
    store = InMemoryObjectStore()
    result = generate_and_upload(small_batch, store, dry_run=False, limit=5, temp_dir=tmp_path / "t")
    assert result.stats.processed == 5
    assert len(store.keys()) == 5


def test_upload_is_idempotent_on_rerun(small_batch, tmp_path):
    store = InMemoryObjectStore()
    first = generate_and_upload(small_batch, store, dry_run=False, temp_dir=tmp_path / "t1")
    assert first.stats.uploaded == len(small_batch)
    assert first.stats.skipped == 0

    second = generate_and_upload(small_batch, store, dry_run=False, temp_dir=tmp_path / "t2")
    assert second.stats.uploaded == 0
    assert second.stats.skipped == len(small_batch)
    assert len(store.keys()) == len(small_batch)  # aucun doublon


def test_overwrite_protection_on_content_conflict(small_batch, tmp_path):
    store = InMemoryObjectStore()
    generate_and_upload(small_batch, store, dry_run=False, temp_dir=tmp_path / "t1")

    mutated = copy.deepcopy(small_batch)
    original_key = raw_key(
        mutated[0].document_id, mutated[0].domain, format_for(mutated[0].document_id, mutated[0].document_type)
    )
    original_bytes = store.get_bytes(original_key)
    mutated[0].title = mutated[0].title + " (contenu modifié)"

    result = generate_and_upload(mutated, store, dry_run=False, temp_dir=tmp_path / "t2")
    assert result.stats.conflicts == 1
    assert result.stats.uploaded == 0
    # l'objet existant n'a PAS été écrasé silencieusement
    assert store.get_bytes(original_key) == original_bytes
    conflict_records = [r for r in result.records if r.status == ProcessingStatus.FAILED]
    assert any("CONFLICT" in (r.error_message or "") for r in conflict_records)


def test_cleanup_tempfile_after_each_upload(small_batch, tmp_path):
    temp_dir = tmp_path / "t"
    store = InMemoryObjectStore()
    generate_and_upload(small_batch, store, dry_run=False, temp_dir=temp_dir)
    assert list(temp_dir.glob("*")) == []  # tout est nettoyé après le run


def test_max_local_temp_mb_stops_the_whole_run(small_batch, tmp_path):
    store = InMemoryObjectStore()
    with pytest.raises(TempDiskLimitExceeded):
        generate_and_upload(small_batch, store, dry_run=False, max_temp_mb=0, temp_dir=tmp_path / "t")
    assert store.keys() == []


def test_no_credentials_appear_in_audit_events(small_batch, tmp_path):
    store = InMemoryObjectStore()
    result = generate_and_upload(small_batch, store, dry_run=False, temp_dir=tmp_path / "t")
    serialized = " ".join(str(e.model_dump()) for e in result.audit_events)
    for forbidden in ("R2_SECRET_ACCESS_KEY", "R2_ACCESS_KEY_ID", "aws_secret", "password"):
        assert forbidden not in serialized


def test_ingest_processed_artifacts_structure(small_batch, tmp_path):
    store = InMemoryObjectStore()
    generate_and_upload(small_batch, store, dry_run=False, temp_dir=tmp_path / "t")

    manifest_by_id = {e.document_id: e for e in small_batch}
    parser = MockDoclingAdapter()
    result = ingest([e.document_id for e in small_batch], manifest_by_id, store, parser)

    assert result.stats.uploaded == len(small_batch)  # tous traités avec succès
    processed_record = next(r for r in result.records if r.status == ProcessingStatus.PROCESSED)
    doc_id = processed_record.document_id
    assert f"processed/{doc_id}/document.json" in processed_record.processed_keys
    assert f"processed/{doc_id}/content.md" in processed_record.processed_keys
    assert f"processed/{doc_id}/metadata.json" in processed_record.processed_keys


def test_ingest_produces_tables_json_for_tabular_formats(document_dataset, tmp_path):
    tabular = [
        e
        for e in document_dataset.manifest
        if format_for(e.document_id, e.document_type) in ("csv", "xlsx")
    ][:5]
    assert tabular, "expected at least one csv/xlsx document in the generated manifest"
    store = InMemoryObjectStore()
    generate_and_upload(tabular, store, dry_run=False, temp_dir=tmp_path / "t")
    manifest_by_id = {e.document_id: e for e in tabular}
    result = ingest([e.document_id for e in tabular], manifest_by_id, store, MockDoclingAdapter())
    record = result.records[0]
    assert any(key.endswith("tables.json") for key in record.processed_keys)


def test_ingest_missing_raw_object_fails_without_crashing(document_dataset):
    entry = document_dataset.manifest[0]
    store = InMemoryObjectStore()  # rien n'a été uploadé
    result = ingest([entry.document_id], {entry.document_id: entry}, store, MockDoclingAdapter())
    assert result.stats.failed == 1
    assert result.records[0].status == ProcessingStatus.FAILED


def test_ingest_quarantines_corrupted_raw_object(document_dataset):
    entry = document_dataset.manifest[0]
    ext = format_for(entry.document_id, entry.document_type)
    key = raw_key(entry.document_id, entry.domain, ext)
    store = InMemoryObjectStore()
    store.put_bytes(key, b"", content_type="application/octet-stream", checksum=hashlib.sha256(b"").hexdigest())

    result = ingest([entry.document_id], {entry.document_id: entry}, store, MockDoclingAdapter())
    assert result.stats.quarantined == 1
    record = result.records[0]
    assert record.status == ProcessingStatus.QUARANTINED
    assert record.quarantine_reason == QuarantineReason.CORRUPTED_FILE
    # le document brut n'a pas été supprimé : il a été copié en quarantaine
    assert any(k.startswith("quarantine/") for k in store.keys())  # noqa: SIM118 - keys() maison, pas un dict
    assert store.head(key) is not None


def test_ingest_quarantine_routing_for_unsupported_format(document_dataset):
    entry = document_dataset.manifest[0]
    ext = format_for(entry.document_id, entry.document_type)
    key = raw_key(entry.document_id, entry.domain, ext)
    content = b"some raw content, irrelevant to this routing test"
    store = InMemoryObjectStore()
    store.put_bytes(key, content, content_type="application/octet-stream", checksum=hashlib.sha256(content).hexdigest())

    class _AlwaysUnsupportedParser:
        def parse(self, *, document_id: str, content: bytes, extension: str):
            raise UnsupportedFormatError(f"unsupported: {extension}")

    result = ingest([entry.document_id], {entry.document_id: entry}, store, _AlwaysUnsupportedParser())
    assert result.stats.quarantined == 1
    assert result.records[0].quarantine_reason == QuarantineReason.UNSUPPORTED_FORMAT
    assert store.head(key) is not None  # raw jamais supprimé


def test_ingest_checksum_mismatch_triggers_quarantine(document_dataset):
    entry = document_dataset.manifest[0]
    ext = format_for(entry.document_id, entry.document_type)
    key = raw_key(entry.document_id, entry.domain, ext)
    store = InMemoryObjectStore()
    # checksum stocké volontairement incohérent avec le contenu réel.
    store.put_bytes(key, b"real content here", content_type="application/octet-stream", checksum="deadbeef")

    result = ingest([entry.document_id], {entry.document_id: entry}, store, MockDoclingAdapter())
    assert result.stats.quarantined == 1
    assert result.records[0].quarantine_reason == QuarantineReason.CHECKSUM_MISMATCH
