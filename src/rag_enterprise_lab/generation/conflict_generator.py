"""Génération déterministe de scénarios de conflits documentaires connus, sur
les 7 catégories minimales demandées. Le ground truth applique toujours la
règle d'autorité (AUTHORITY_RANK) ou la source de vérité calculable
(PostgreSQL / Phase 1) — jamais une heuristique de fraîcheur."""

from rag_enterprise_lab.domain.commercial import Client
from rag_enterprise_lab.domain.conflicts import ConflictCategory, ConflictRecord
from rag_enterprise_lab.domain.documents import DocumentManifestEntry
from rag_enterprise_lab.domain.models import DocumentStatus

INSTANCES_PER_TYPE = 3

# field, valeur côté contrat de base, valeur côté avenant (l'avenant gagne :
# SIGNED_AMENDMENT > SIGNED_CONTRACT dans AUTHORITY_RANK).
_AMENDMENT_FIELD_VALUES: dict[ConflictCategory, tuple[str, object, object]] = {
    ConflictCategory.PAYMENT_TERMS: ("payment_terms_days", 30, 45),
    ConflictCategory.CONTRACT_DATES: ("contract_end_date_offset_days", 365, 730),
    ConflictCategory.SLA: ("sla_response_hours", 48, 24),
    ConflictCategory.NOTICE_PERIOD: ("notice_period_days", 60, 90),
    ConflictCategory.RENEWAL: ("auto_renewal", False, True),
}


def _amendment_pairs(
    manifest: list[DocumentManifestEntry],
) -> list[tuple[DocumentManifestEntry, DocumentManifestEntry]]:
    by_id = {e.document_id: e for e in manifest}
    pairs = [
        (by_id[e.supersedes], e)
        for e in manifest
        if e.document_type == "CONTRACT_AMENDMENT" and e.supersedes in by_id
    ]
    pairs.sort(key=lambda p: p[1].document_id)
    return pairs


def _pricing_version_pairs(
    manifest: list[DocumentManifestEntry],
) -> list[tuple[DocumentManifestEntry, DocumentManifestEntry]]:
    by_id = {e.document_id: e for e in manifest}
    pairs = [
        (by_id[e.supersedes], e)
        for e in manifest
        if e.document_type == "PRICING_GRID" and e.supersedes in by_id
    ]
    pairs.sort(key=lambda p: p[1].document_id)
    return pairs


def generate_conflicts(
    manifest: list[DocumentManifestEntry],
    clients: list[Client],
) -> tuple[list[ConflictRecord], int]:
    records: list[ConflictRecord] = []
    counter = 0

    amendment_pairs = iter(_amendment_pairs(manifest))
    for category in (
        ConflictCategory.PAYMENT_TERMS,
        ConflictCategory.CONTRACT_DATES,
        ConflictCategory.SLA,
        ConflictCategory.NOTICE_PERIOD,
        ConflictCategory.RENEWAL,
    ):
        field, base_value, override_value = _AMENDMENT_FIELD_VALUES[category]
        for _ in range(INSTANCES_PER_TYPE):
            pair = next(amendment_pairs, None)
            if pair is None:
                break
            base, amendment = pair
            counter += 1
            records.append(
                ConflictRecord(
                    conflict_id=f"CONF-{counter:05d}",
                    category=category,
                    field=field,
                    document_ids=[base.document_id, amendment.document_id],
                    values_by_document={
                        base.document_id: base_value,
                        amendment.document_id: override_value,
                    },
                    ground_truth_value=override_value,
                    ground_truth_source_document_id=amendment.document_id,
                    resolution_rule=(
                        "SIGNED_AMENDMENT outrank SIGNED_CONTRACT dans AUTHORITY_RANK "
                        "(docs/version-resolution/README.md)"
                    ),
                )
            )

    for base, current in _pricing_version_pairs(manifest)[:INSTANCES_PER_TYPE]:
        counter += 1
        records.append(
            ConflictRecord(
                conflict_id=f"CONF-{counter:05d}",
                category=ConflictCategory.PRICING,
                field="unit_price_eur",
                document_ids=[base.document_id, current.document_id],
                values_by_document={base.document_id: 100.0, current.document_id: 120.0},
                ground_truth_value=120.0,
                ground_truth_source_document_id=current.document_id,
                resolution_rule=(
                    "Version non supersedée (APPROVED_PRICING_GRID) prévaut sur la version "
                    "SUPERSEDED de la même grille tarifaire."
                ),
            )
        )

    expired_or_superseded = sorted(
        (
            e
            for e in manifest
            if e.document_type == "CLIENT_CONTRACT"
            and e.status in (DocumentStatus.EXPIRED, DocumentStatus.SUPERSEDED)
            and e.related_customer_id
        ),
        key=lambda e: e.document_id,
    )
    picked_clients: set[str] = set()
    for entry in expired_or_superseded:
        if len(picked_clients) >= INSTANCES_PER_TYPE:
            break
        if entry.related_customer_id is None or entry.related_customer_id in picked_clients:
            continue
        picked_clients.add(entry.related_customer_id)
        client = next(c for c in clients if c.customer_id == entry.related_customer_id)
        counter += 1
        records.append(
            ConflictRecord(
                conflict_id=f"CONF-{counter:05d}",
                category=ConflictCategory.CUSTOMER_STATUS,
                field="customer_status",
                document_ids=[entry.document_id],
                values_by_document={
                    entry.document_id: f"implicite {entry.status.value} (contrat)"
                },
                ground_truth_value=client.status.value,
                ground_truth_source_document_id=f"CRM:{client.customer_id}",
                resolution_rule=(
                    "PostgreSQL (registre client Phase 1) est la source de vérité calculable "
                    "du statut commercial, pas un document individuel (CLAUDE.md § PostgreSQL)."
                ),
            )
        )

    return records, counter
