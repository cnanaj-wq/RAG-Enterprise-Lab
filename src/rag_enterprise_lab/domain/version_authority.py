"""Résolution d'autorité de version : trois notions séparées et non
confondues — version chronologique, validité métier, autorité légale. Une
version plus récente n'est PAS automatiquement la version applicable."""

from datetime import date

from rag_enterprise_lab.domain.documents import (
    AUTHORITY_RANK,
    AuthorityLevel,
    DocumentManifestEntry,
)
from rag_enterprise_lab.domain.models import DocumentStatus

# Règle déterministe : type de document + statut -> niveau d'autorité légale.
# Configurable ici, jamais dupliquée ailleurs.
_AUTHORITY_BY_TYPE_AND_STATUS: dict[tuple[str, DocumentStatus], AuthorityLevel] = {
    ("CONTRACT_AMENDMENT", DocumentStatus.SIGNED): AuthorityLevel.SIGNED_AMENDMENT,
    ("EMPLOYMENT_AMENDMENT", DocumentStatus.SIGNED): AuthorityLevel.SIGNED_AMENDMENT,
    ("CLIENT_CONTRACT", DocumentStatus.SIGNED): AuthorityLevel.SIGNED_CONTRACT,
    ("SUPPLIER_CONTRACT", DocumentStatus.SIGNED): AuthorityLevel.SIGNED_CONTRACT,
    ("PARTNER_CONTRACT", DocumentStatus.SIGNED): AuthorityLevel.SIGNED_CONTRACT,
    ("EMPLOYMENT_CONTRACT", DocumentStatus.SIGNED): AuthorityLevel.SIGNED_CONTRACT,
    ("PURCHASE_ORDER", DocumentStatus.SIGNED): AuthorityLevel.SIGNED_PURCHASE_ORDER,
    ("PROPOSAL", DocumentStatus.APPROVED): AuthorityLevel.APPROVED_PROPOSAL,
    ("PRICING_GRID", DocumentStatus.APPROVED): AuthorityLevel.APPROVED_PRICING_GRID,
}

_EPOCH = date(1970, 1, 1)


def authority_level_for(document_type: str, status: DocumentStatus) -> AuthorityLevel:
    """Détermine l'autorité légale à partir du (type, statut). DRAFT par
    défaut si aucune règle ne correspond (document non contraignant)."""
    return _AUTHORITY_BY_TYPE_AND_STATUS.get((document_type, status), AuthorityLevel.DRAFT)


def resolve_authoritative_version(
    chain: list[DocumentManifestEntry],
) -> DocumentManifestEntry:
    """Résout la version juridiquement applicable d'une chaîne de versions
    (liées par `supersedes`). Priorité : rang d'autorité le plus fort (nombre
    le plus bas) ; à égalité, `valid_from` le plus récent ; à égalité,
    `created_at` le plus récent. Explicable : chaque critère est un champ du
    manifest, aucune heuristique cachée."""
    if not chain:
        raise ValueError("cannot resolve authority on an empty chain")

    def sort_key(entry: DocumentManifestEntry) -> tuple[int, int, float]:
        valid_from_rank = -(entry.valid_from or _EPOCH).toordinal()
        created_at_rank = -entry.created_at.timestamp()
        return (AUTHORITY_RANK[entry.authority_level], valid_from_rank, created_at_rank)

    return min(chain, key=sort_key)
