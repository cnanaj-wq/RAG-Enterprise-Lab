from datetime import date, datetime, time

from rag_enterprise_lab.domain.document_taxonomy import DocumentDomain
from rag_enterprise_lab.domain.documents import (
    AUTHORITY_RANK,
    AuthorityLevel,
    DocumentManifestEntry,
    GenerationStatus,
    RetentionPolicy,
)
from rag_enterprise_lab.domain.models import Classification, DocumentStatus
from rag_enterprise_lab.domain.version_authority import (
    authority_level_for,
    resolve_authoritative_version,
)


def _dt(year: int, month: int, day: int) -> datetime:
    """Datetime naïf (cohérent avec tout le domaine documentaire, qui ne
    manipule pas de fuseau horaire)."""
    return datetime.combine(date(year, month, day), time())


def _entry(**overrides) -> DocumentManifestEntry:
    base = {
        "document_id": "DOC-TEST",
        "title": "Test",
        "document_type": "CLIENT_CONTRACT",
        "domain": DocumentDomain.LEGAL_CONTRACTS,
        "source_system": "Test",
        "owner": "EMP-0001",
        "classification": Classification.CONFIDENTIAL,
        "version": "1.0",
        "status": DocumentStatus.SIGNED,
        "created_at": _dt(2024, 1, 1),
        "authority_level": AuthorityLevel.SIGNED_CONTRACT,
        "retention_policy": RetentionPolicy.TEN_YEARS,
        "checksum": "sha256-placeholder-test",
        "storage_target": "r2://test/test.md",
        "generation_status": GenerationStatus.NOT_GENERATED,
    }
    base.update(overrides)
    return DocumentManifestEntry(**base)


def test_authority_rank_order_matches_specification():
    ordered = sorted(AUTHORITY_RANK, key=lambda level: AUTHORITY_RANK[level])
    assert ordered == [
        AuthorityLevel.SIGNED_AMENDMENT,
        AuthorityLevel.SIGNED_CONTRACT,
        AuthorityLevel.SIGNED_PURCHASE_ORDER,
        AuthorityLevel.APPROVED_PROPOSAL,
        AuthorityLevel.APPROVED_PRICING_GRID,
        AuthorityLevel.DRAFT,
    ]


def test_authority_level_for_is_deterministic():
    for _ in range(5):
        assert (
            authority_level_for("CLIENT_CONTRACT", DocumentStatus.SIGNED)
            == AuthorityLevel.SIGNED_CONTRACT
        )
        assert (
            authority_level_for("CONTRACT_AMENDMENT", DocumentStatus.SIGNED)
            == AuthorityLevel.SIGNED_AMENDMENT
        )
        assert authority_level_for("RUNBOOK", DocumentStatus.APPROVED) == AuthorityLevel.DRAFT


def test_older_signed_contract_beats_newer_draft():
    """Une version plus récente n'est PAS automatiquement applicable : un
    SIGNED_CONTRACT plus ancien bat un DRAFT plus récent."""
    older_signed_contract = _entry(
        document_id="DOC-OLD-SIGNED",
        status=DocumentStatus.SIGNED,
        authority_level=AuthorityLevel.SIGNED_CONTRACT,
        created_at=_dt(2023, 1, 1),
        valid_from=date(2023, 1, 10),
    )
    newer_draft = _entry(
        document_id="DOC-NEW-DRAFT",
        document_type="PROPOSAL",
        status=DocumentStatus.DRAFT,
        authority_level=AuthorityLevel.DRAFT,
        created_at=_dt(2026, 1, 1),
        valid_from=date(2026, 1, 5),
    )
    winner = resolve_authoritative_version([older_signed_contract, newer_draft])
    assert winner.document_id == "DOC-OLD-SIGNED"


def test_signed_amendment_beats_signed_contract_regardless_of_recency():
    older_amendment = _entry(
        document_id="DOC-AMENDMENT",
        document_type="CONTRACT_AMENDMENT",
        status=DocumentStatus.SIGNED,
        authority_level=AuthorityLevel.SIGNED_AMENDMENT,
        created_at=_dt(2022, 1, 1),
    )
    newer_contract = _entry(
        document_id="DOC-CONTRACT",
        status=DocumentStatus.SIGNED,
        authority_level=AuthorityLevel.SIGNED_CONTRACT,
        created_at=_dt(2025, 1, 1),
    )
    winner = resolve_authoritative_version([newer_contract, older_amendment])
    assert winner.document_id == "DOC-AMENDMENT"


def test_amendment_chains_exist_in_generated_dataset(document_dataset):
    by_id = {e.document_id for e in document_dataset.manifest}
    amendments = [
        e
        for e in document_dataset.manifest
        if e.document_type == "CONTRACT_AMENDMENT" and e.supersedes in by_id
    ]
    assert len(amendments) >= 5
