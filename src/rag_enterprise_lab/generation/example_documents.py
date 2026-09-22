"""Matérialise au maximum 50 documents physiques (Markdown uniquement) parmi
le manifest de 5000 entrées, pour servir de fixtures aux futurs tests
Docling. Aucun PDF/DOCX/XLSX/PPTX n'est généré ; Docling n'est pas installé.
"""

from pathlib import Path

from rag_enterprise_lab.domain.anomalies import AnomalyRecord, AnomalyType
from rag_enterprise_lab.domain.conflicts import ConflictRecord
from rag_enterprise_lab.domain.documents import DocumentManifestEntry, GenerationStatus

MAX_EXAMPLES = 50

_REPRESENTATIVE_TYPES = [
    "NDA",
    "PRICING_GRID",
    "SUPPLIER_CONTRACT",
    "EMPLOYMENT_CONTRACT",
    "PROCEDURE",
    "INCIDENT_REPORT",
    "SECURITY_POLICY",
    "PROPOSAL",
]


def _render_markdown(entry: DocumentManifestEntry, extra_blocks: list[str]) -> str:
    header = [
        f"# {entry.title}",
        "",
        f"- document_id: {entry.document_id}",
        f"- document_type: {entry.document_type}",
        f"- domain: {entry.domain.value}",
        f"- version: {entry.version}",
        f"- status: {entry.status.value}",
        f"- classification: {entry.classification.value}",
        f"- valid_from: {entry.valid_from}",
        f"- valid_to: {entry.valid_to}",
        f"- owner: {entry.owner}",
    ]
    footer = [
        "",
        "_Document d'exemple synthétique — GenAI Enterprise Lab. Aucune donnée réelle._",
    ]
    body = [""]
    for block in extra_blocks:
        body.append(block)
        body.append("")
    return "\n".join(header + body + footer)


def select_and_materialize_examples(
    manifest: list[DocumentManifestEntry],
    conflicts: list[ConflictRecord],
    anomalies: list[AnomalyRecord],
    *,
    out_dir: Path,
) -> list[DocumentManifestEntry]:
    by_id = {e.document_id: e for e in manifest}
    selected: dict[str, list[str]] = {}

    payment_conflict = next(
        (c for c in conflicts if c.category.value == "PAYMENT_TERMS"), None
    )
    if payment_conflict:
        base_id, amendment_id = payment_conflict.document_ids
        base_days = payment_conflict.values_by_document[base_id]
        amendment_days = payment_conflict.values_by_document[amendment_id]
        selected[base_id] = [
            "## Clause de paiement (contrat client)",
            f"Délai de paiement : {base_days} jours.",
        ]
        selected[amendment_id] = [
            "## Avenant — modification de la clause de paiement",
            (
                f"Nouveau délai de paiement : {amendment_days} jours "
                f"(remplace le contrat initial {base_id})."
            ),
        ]

    for doc_type in _REPRESENTATIVE_TYPES:
        candidate = next(
            (e for e in manifest if e.document_type == doc_type and e.document_id not in selected),
            None,
        )
        if candidate:
            selected[candidate.document_id] = []

    expired = next((a for a in anomalies if a.type == AnomalyType.EXPIRED_DOCUMENT), None)
    if expired and expired.document_ids:
        doc_id = expired.document_ids[0]
        entry = by_id[doc_id]
        selected.setdefault(doc_id, []).append(
            "## Anomalie — document expiré\n"
            f"valid_to = {expired.ground_truth.get('valid_to')} (passé), "
            f"mais statut resté {entry.status.value}."
        )

    contradiction = next(
        (
            a
            for a in anomalies
            if a.type in (AnomalyType.CONTRADICTORY_DOCUMENTS, AnomalyType.AMENDMENT_CONTRADICTS_CONTRACT)
        ),
        None,
    )
    if contradiction:
        for doc_id in contradiction.document_ids:
            if doc_id in by_id:
                selected.setdefault(doc_id, []).append(
                    f"## Contradiction connue\nVoir {contradiction.anomaly_id} — "
                    f"ground truth : {contradiction.ground_truth}."
                )

    out_dir.mkdir(parents=True, exist_ok=True)
    materialized: list[DocumentManifestEntry] = []
    for doc_id in list(selected.keys())[:MAX_EXAMPLES]:
        entry = by_id[doc_id]
        filename = f"{doc_id}.md"
        content = _render_markdown(entry, selected[doc_id])
        (out_dir / filename).write_text(content, encoding="utf-8")
        entry.generation_status = GenerationStatus.EXAMPLE_GENERATED
        entry.storage_target = f"local://data/examples/{filename}"
        materialized.append(entry)
    return materialized
