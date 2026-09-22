"""Construit les chaînes de version (`supersedes`) et relie les avenants à
leur contrat de base — mutation en place, déterministe (aucun random), donc
sans impact sur la reproductibilité seed->dataset au-delà du manifest lui-même.

Garantie d'acyclicité : chaque type versionable ne peut superseder qu'un
document plus ancien du MÊME type, et un avenant ne peut superseder qu'un
document d'un type de contrat de base (jamais un autre avenant) — le graphe
`supersedes` est donc un DAG par construction.
"""

from rag_enterprise_lab.domain.documents import DocumentManifestEntry
from rag_enterprise_lab.domain.models import DocumentStatus
from rag_enterprise_lab.domain.version_authority import authority_level_for
from rag_enterprise_lab.generation.document_taxonomy_rules import (
    AMENDMENT_BASE_TYPES,
    VERSIONABLE_BASE_TYPES,
)


def _related_id(entry: DocumentManifestEntry) -> str | None:
    return entry.related_customer_id or entry.related_supplier_id or entry.related_employee_id


def link_versions_and_amendments(entries: list[DocumentManifestEntry]) -> None:
    by_type_and_related: dict[tuple[str, str], list[DocumentManifestEntry]] = {}
    for entry in entries:
        related = _related_id(entry)
        if entry.document_type in VERSIONABLE_BASE_TYPES and related:
            by_type_and_related.setdefault((entry.document_type, related), []).append(entry)

    # 1) Chaînes de version chronologiques (même type + même entité liée).
    for group in by_type_and_related.values():
        if len(group) < 2:
            continue
        group.sort(key=lambda e: e.created_at)
        for idx in range(1, len(group)):
            previous = group[idx - 1]
            current = group[idx]
            current.supersedes = previous.document_id
            current.version = f"{idx + 1}.0"
            if previous.status not in (DocumentStatus.EXPIRED, DocumentStatus.QUARANTINED):
                previous.status = DocumentStatus.SUPERSEDED
                previous.authority_level = authority_level_for(
                    previous.document_type, previous.status
                )

    # 2) Avenants -> tête courante (la plus récente) de leur contrat de base.
    current_head: dict[tuple[str, str], DocumentManifestEntry] = {
        key: group[-1] for key, group in by_type_and_related.items()
    }

    for entry in entries:
        base_types = AMENDMENT_BASE_TYPES.get(entry.document_type)
        if not base_types:
            continue
        related = _related_id(entry)
        if not related:
            continue
        for base_type in base_types:
            head = current_head.get((base_type, related))
            if head is not None:
                entry.supersedes = head.document_id
                break
