"""Le manifest Phase 2 ne doit jamais être modifié silencieusement : le
placeholder original et le checksum réel coexistent dans ProcessingRecord."""

from rag_enterprise_lab.adapters.r2 import InMemoryObjectStore
from rag_enterprise_lab.domain.processing import ProcessingStatus
from rag_enterprise_lab.ingestion.pipeline import generate_and_upload


def test_expected_placeholder_and_actual_checksum_both_preserved(document_dataset, tmp_path):
    entries = document_dataset.manifest[:3]
    store = InMemoryObjectStore()
    result = generate_and_upload(entries, store, dry_run=False, temp_dir=tmp_path / "t")

    by_id = {e.document_id: e for e in entries}
    for record in result.records:
        assert record.status == ProcessingStatus.UPLOADED
        original_entry = by_id[record.document_id]
        # Le placeholder du manifest original n'a pas été touché.
        assert record.expected_checksum_placeholder == original_entry.checksum
        assert record.expected_checksum_placeholder.startswith("sha256-placeholder-")
        # Le checksum réel est un vrai sha256 (64 hex chars), distinct du placeholder.
        assert record.actual_checksum is not None
        assert len(record.actual_checksum) == 64
        assert record.actual_checksum != record.expected_checksum_placeholder
