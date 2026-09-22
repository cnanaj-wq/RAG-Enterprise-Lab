"""Ground truth exploitable pour tester automatiquement le futur RAG :
dérivé des conflits (valeur applicable), de la complétude (dossiers client)
et du scénario de clôture commerciale (signature_rate). Jev n'est jamais
utilisé pour produire ces réponses (calcul déterministe uniquement)."""

from rag_enterprise_lab.domain.commercial import Client
from rag_enterprise_lab.domain.completeness import compute_completeness
from rag_enterprise_lab.domain.conflicts import ConflictRecord
from rag_enterprise_lab.domain.documents import DocumentManifestEntry
from rag_enterprise_lab.domain.expected_answers import ExpectedAnswer
from rag_enterprise_lab.domain.sales import ExpectedContract, SignatureStatus


def generate_expected_answers(
    *,
    conflicts: list[ConflictRecord],
    manifest: list[DocumentManifestEntry],
    clients: list[Client],
    expected_contracts: list[ExpectedContract],
) -> list[ExpectedAnswer]:
    answers: list[ExpectedAnswer] = []
    n = 0

    for conflict in conflicts:
        n += 1
        answers.append(
            ExpectedAnswer(
                question_id=f"QA-{n:05d}",
                category=f"CONFLICT_{conflict.category.value}",
                question=(
                    f"Quelle est la valeur applicable de '{conflict.field}' parmi les documents "
                    f"{', '.join(conflict.document_ids)} ?"
                ),
                expected_answer=conflict.ground_truth_value,
                source_document_ids=[conflict.ground_truth_source_document_id],
            )
        )

    doc_types_by_customer: dict[str, set[str]] = {}
    for entry in manifest:
        if entry.related_customer_id:
            doc_types_by_customer.setdefault(entry.related_customer_id, set()).add(
                entry.document_type
            )

    for client in sorted(clients, key=lambda c: c.customer_id)[:5]:
        present = doc_types_by_customer.get(client.customer_id, set())
        result = compute_completeness(
            dossier_type="CLIENT", related_id=client.customer_id, present_document_types=present
        )
        n += 1
        answers.append(
            ExpectedAnswer(
                question_id=f"QA-{n:05d}",
                category="COMPLETENESS_CLIENT_DOSSIER",
                question=f"Le dossier client {client.customer_id} ({client.name}) est-il complet ?",
                expected_answer={
                    "is_complete": result.is_complete,
                    "missing_types": result.missing_types,
                },
                source_document_ids=[],
            )
        )

    signed = sum(1 for ec in expected_contracts if ec.signature_status == SignatureStatus.SIGNED)
    total = len(expected_contracts)
    n += 1
    answers.append(
        ExpectedAnswer(
            question_id=f"QA-{n:05d}",
            category="SIGNATURE_RATE",
            question="Quel est le signature_rate du mois (contrats attendus signés / contrats attendus) ?",
            expected_answer=round(signed / total, 4) if total else 0.0,
            source_document_ids=[],
        )
    )

    return answers
