"""Injection déterministe des 15 types d'anomalies requis. Chaque anomalie
mute explicitement le manifest (ou l'ExpectedContract concerné) et enregistre
un `AnomalyRecord` avec un ground truth exploitable pour les futurs tests RAG.

Le compte par type (3) est arbitraire mais fixe : reproductible avec le même
seed, documenté dans PHASE-2-REPORT.md."""

import random
from datetime import date, timedelta

from rag_enterprise_lab.domain.anomalies import AnomalyRecord, AnomalyType
from rag_enterprise_lab.domain.documents import DocumentManifestEntry
from rag_enterprise_lab.domain.models import Classification, DocumentStatus
from rag_enterprise_lab.domain.sales import ExpectedContract, SignatureStatus
from rag_enterprise_lab.domain.version_authority import authority_level_for
from rag_enterprise_lab.generation.document_taxonomy_rules import SIGNABLE_TYPES
from rag_enterprise_lab.identity.groups import RAG_ALL_EMPLOYEES

INSTANCES_PER_TYPE = 3


class _AnomalyCounter:
    def __init__(self) -> None:
        self._n = 0

    def next_id(self) -> str:
        self._n += 1
        return f"ANOM-{self._n:05d}"

    @property
    def current(self) -> int:
        return self._n


def _pick(rng: random.Random, candidates: list, k: int) -> list:
    candidates = sorted(candidates, key=lambda e: getattr(e, "document_id", str(e)))
    k = min(k, len(candidates))
    return rng.sample(candidates, k=k) if k else []


def inject_anomalies(
    rng: random.Random,
    manifest: list[DocumentManifestEntry],
    expected_contracts: list[ExpectedContract],
    *,
    reference_date: date,
) -> tuple[list[AnomalyRecord], int]:
    counter = _AnomalyCounter()
    records: list[AnomalyRecord] = []
    superseded_by: dict[str, str] = {
        e.supersedes: e.document_id for e in manifest if e.supersedes
    }

    # 1) OBSOLETE_VERSION : un document déjà remplacé n'a pas été repassé
    #    à SUPERSEDED (le système "a oublié" de purger l'ancienne version).
    candidates = [
        e for e in manifest if e.status == DocumentStatus.SUPERSEDED and e.document_id in superseded_by
    ]
    for entry in _pick(rng, candidates, INSTANCES_PER_TYPE):
        head_id = superseded_by[entry.document_id]
        entry.status = DocumentStatus.SIGNED
        entry.authority_level = authority_level_for(entry.document_type, entry.status)
        records.append(
            AnomalyRecord(
                anomaly_id=counter.next_id(),
                type=AnomalyType.OBSOLETE_VERSION,
                document_ids=[entry.document_id],
                description=(
                    f"{entry.document_id} reste marqué {entry.status.value} alors qu'il est "
                    f"remplacé par {head_id}."
                ),
                ground_truth={"correct_status": "SUPERSEDED", "current_head_document_id": head_id},
            )
        )

    # 2) EXPIRED_DOCUMENT : valid_to dans le passé mais statut encore actif.
    candidates = [
        e
        for e in manifest
        if e.status in (DocumentStatus.SIGNED, DocumentStatus.APPROVED)
        and e.valid_to is not None
        and e.valid_to >= reference_date
    ]
    for entry in _pick(rng, candidates, INSTANCES_PER_TYPE):
        entry.valid_to = reference_date - timedelta(days=rng.randint(10, 120))
        records.append(
            AnomalyRecord(
                anomaly_id=counter.next_id(),
                type=AnomalyType.EXPIRED_DOCUMENT,
                document_ids=[entry.document_id],
                description=f"{entry.document_id} a une valid_to passée mais reste {entry.status.value}.",
                ground_truth={"expected_status": "EXPIRED", "valid_to": entry.valid_to.isoformat()},
            )
        )

    # 3) DUPLICATE : deux document_id distincts, même title/type/related_customer_id.
    same_type_pool = [e for e in manifest if e.related_customer_id]
    originals = _pick(rng, same_type_pool, INSTANCES_PER_TYPE)
    used_ids = {e.document_id for e in originals}
    for original in originals:
        other_candidates = [
            e for e in manifest if e.document_id != original.document_id and e.document_id not in used_ids
        ]
        duplicate = _pick(rng, other_candidates, 1)[0]
        used_ids.add(duplicate.document_id)
        duplicate.title = original.title
        duplicate.document_type = original.document_type
        duplicate.related_customer_id = original.related_customer_id
        records.append(
            AnomalyRecord(
                anomaly_id=counter.next_id(),
                type=AnomalyType.DUPLICATE,
                document_ids=[original.document_id, duplicate.document_id],
                description=f"{duplicate.document_id} duplique {original.document_id}.",
                ground_truth={"duplicate_of": original.document_id, "duplicate": duplicate.document_id},
            )
        )

    # 4) MISSING_OWNER
    for entry in _pick(rng, list(manifest), INSTANCES_PER_TYPE):
        original_owner = entry.owner
        entry.owner = ""
        records.append(
            AnomalyRecord(
                anomaly_id=counter.next_id(),
                type=AnomalyType.MISSING_OWNER,
                document_ids=[entry.document_id],
                description=f"{entry.document_id} n'a plus de owner renseigné.",
                ground_truth={"expected_owner": original_owner},
            )
        )

    # 5) WRONG_CLASSIFICATION : reclassé PUBLIC alors qu'il devrait être restreint.
    candidates = [
        e
        for e in manifest
        if e.classification
        in (
            Classification.SENSITIVE_PERSONAL_DATA,
            Classification.PERSONAL_DATA,
            Classification.RESTRICTED,
        )
    ]
    for entry in _pick(rng, candidates, INSTANCES_PER_TYPE):
        original = entry.classification
        entry.classification = Classification.PUBLIC
        records.append(
            AnomalyRecord(
                anomaly_id=counter.next_id(),
                type=AnomalyType.WRONG_CLASSIFICATION,
                document_ids=[entry.document_id],
                description=f"{entry.document_id} est classé PUBLIC au lieu de {original.value}.",
                ground_truth={"expected_classification": original.value},
            )
        )

    # 6) ACL_INCOHERENT : allowed_groups trop permissif pour la classification.
    candidates = [
        e
        for e in manifest
        if e.classification in (Classification.RESTRICTED, Classification.SENSITIVE_PERSONAL_DATA)
        and RAG_ALL_EMPLOYEES not in e.allowed_groups
    ]
    for entry in _pick(rng, candidates, INSTANCES_PER_TYPE):
        original_groups = list(entry.allowed_groups)
        entry.allowed_groups = [RAG_ALL_EMPLOYEES]
        records.append(
            AnomalyRecord(
                anomaly_id=counter.next_id(),
                type=AnomalyType.ACL_INCOHERENT,
                document_ids=[entry.document_id],
                description=(
                    f"{entry.document_id} ({entry.classification.value}) est ouvert à "
                    f"{RAG_ALL_EMPLOYEES}."
                ),
                ground_truth={"expected_allowed_groups": original_groups},
            )
        )

    # 7) INCOMPLETE_DOCUMENT : valid_from manquant sur un document signé.
    candidates = [
        e for e in manifest if e.status == DocumentStatus.SIGNED and e.valid_from is not None
    ]
    for entry in _pick(rng, candidates, INSTANCES_PER_TYPE):
        original = entry.valid_from
        entry.valid_from = None
        records.append(
            AnomalyRecord(
                anomaly_id=counter.next_id(),
                type=AnomalyType.INCOMPLETE_DOCUMENT,
                document_ids=[entry.document_id],
                description=f"{entry.document_id} est SIGNED sans valid_from.",
                ground_truth={"missing_field": "valid_from", "expected_value": original.isoformat()},
            )
        )

    # 8) OBSOLETE_PRICING
    candidates = [
        e
        for e in manifest
        if e.document_type == "PRICING_GRID"
        and e.status == DocumentStatus.APPROVED
        and e.valid_to is not None
        and e.valid_to >= reference_date
    ]
    for entry in _pick(rng, candidates, INSTANCES_PER_TYPE):
        entry.valid_to = reference_date - timedelta(days=rng.randint(30, 200))
        records.append(
            AnomalyRecord(
                anomaly_id=counter.next_id(),
                type=AnomalyType.OBSOLETE_PRICING,
                document_ids=[entry.document_id],
                description=f"{entry.document_id} (grille tarifaire) a expiré mais reste APPROVED.",
                ground_truth={"expected_status": "EXPIRED"},
            )
        )

    # 9) CRM_STATUS_INCOHERENT : ExpectedContract SIGNED sans contrat signé au manifest.
    signed_contracts = [
        ec for ec in expected_contracts if ec.signature_status == SignatureStatus.SIGNED
    ]
    for ec in _pick(rng, signed_contracts, INSTANCES_PER_TYPE):
        matching = [
            e
            for e in manifest
            if e.document_type == "CLIENT_CONTRACT"
            and e.related_customer_id == ec.client_id
            and e.status == DocumentStatus.SIGNED
        ]
        target_ids = []
        if matching:
            doc = matching[0]
            doc.status = DocumentStatus.DRAFT
            doc.authority_level = authority_level_for(doc.document_type, doc.status)
            target_ids = [doc.document_id]
        records.append(
            AnomalyRecord(
                anomaly_id=counter.next_id(),
                type=AnomalyType.CRM_STATUS_INCOHERENT,
                document_ids=target_ids,
                description=(
                    f"ExpectedContract {ec.expected_contract_id} (client {ec.client_id}) est "
                    "SIGNED côté CRM sans CLIENT_CONTRACT signé correspondant au manifest."
                ),
                ground_truth={
                    "expected_contract_id": ec.expected_contract_id,
                    "client_id": ec.client_id,
                    "issue": "signed_crm_without_signed_document",
                },
            )
        )

    # 10) UNSIGNED_DOCUMENT : contrat ancien jamais signé.
    candidates = [e for e in manifest if e.document_type in SIGNABLE_TYPES]
    for entry in _pick(rng, candidates, INSTANCES_PER_TYPE):
        entry.status = DocumentStatus.DRAFT
        entry.signed_at = None
        entry.approved_at = None
        entry.created_at = entry.created_at.replace(year=entry.created_at.year - 2)
        entry.authority_level = authority_level_for(entry.document_type, entry.status)
        records.append(
            AnomalyRecord(
                anomaly_id=counter.next_id(),
                type=AnomalyType.UNSIGNED_DOCUMENT,
                document_ids=[entry.document_id],
                description=f"{entry.document_id} créé il y a plus de 2 ans, toujours DRAFT.",
                ground_truth={"issue": "created_long_ago_never_signed"},
            )
        )

    # 11) PARTIAL_SIGNATURE
    partial = [
        ec for ec in expected_contracts if ec.signature_status == SignatureStatus.PARTIALLY_SIGNED
    ]
    for ec in _pick(rng, partial, INSTANCES_PER_TYPE):
        matching_doc = next(
            (e for e in manifest if e.related_expected_contract_id == ec.expected_contract_id), None
        )
        records.append(
            AnomalyRecord(
                anomaly_id=counter.next_id(),
                type=AnomalyType.PARTIAL_SIGNATURE,
                document_ids=[matching_doc.document_id] if matching_doc else [],
                description=f"ExpectedContract {ec.expected_contract_id} est PARTIALLY_SIGNED.",
                ground_truth={
                    "expected_contract_id": ec.expected_contract_id,
                    "signature_status": "PARTIALLY_SIGNED",
                },
            )
        )

    # 12) OCR_RISK : signalement pour les futurs tests Docling (aucun champ manifest dédié).
    for entry in _pick(rng, list(manifest), INSTANCES_PER_TYPE):
        records.append(
            AnomalyRecord(
                anomaly_id=counter.next_id(),
                type=AnomalyType.OCR_RISK,
                document_ids=[entry.document_id],
                description=f"{entry.document_id} signalé à risque OCR (scan basse qualité simulé).",
                ground_truth={"ocr_confidence_expected": "LOW"},
            )
        )

    # 13) INCOHERENT_DATES : signed_at avant created_at.
    candidates = [e for e in manifest if e.signed_at is not None]
    for entry in _pick(rng, candidates, INSTANCES_PER_TYPE):
        entry.signed_at = entry.created_at - timedelta(days=5)
        records.append(
            AnomalyRecord(
                anomaly_id=counter.next_id(),
                type=AnomalyType.INCOHERENT_DATES,
                document_ids=[entry.document_id],
                description=f"{entry.document_id} : signed_at antérieur à created_at.",
                ground_truth={"issue": "signed_at_before_created_at"},
            )
        )

    # 14 & 15) CONTRADICTORY_DOCUMENTS / AMENDMENT_CONTRADICTS_CONTRACT sont
    # matérialisées à partir du registre de conflits (voir conflict_generator)
    # pour éviter toute divergence entre les deux registres — voir
    # `attach_conflict_anomalies`, appelée juste après avec `counter.current`.

    return records, counter.current


def attach_conflict_anomalies(counter_start: int, conflicts: list) -> list[AnomalyRecord]:
    """Crée les anomalies CONTRADICTORY_DOCUMENTS / AMENDMENT_CONTRADICTS_CONTRACT
    à partir du registre de conflits, pour rester cohérent avec son ground truth."""
    records: list[AnomalyRecord] = []
    n = counter_start
    for conflict in conflicts:
        n += 1
        anomaly_type = (
            AnomalyType.AMENDMENT_CONTRADICTS_CONTRACT
            if conflict.category.value
            in ("PAYMENT_TERMS", "PRICING", "SLA", "NOTICE_PERIOD", "RENEWAL")
            else AnomalyType.CONTRADICTORY_DOCUMENTS
        )
        records.append(
            AnomalyRecord(
                anomaly_id=f"ANOM-{n:05d}",
                type=anomaly_type,
                document_ids=list(conflict.document_ids),
                description=(
                    f"Conflit {conflict.conflict_id} ({conflict.category.value}) sur {conflict.field}."
                ),
                ground_truth={
                    "conflict_id": conflict.conflict_id,
                    "ground_truth_value": conflict.ground_truth_value,
                    "ground_truth_source_document_id": conflict.ground_truth_source_document_id,
                },
            )
        )
    return records
