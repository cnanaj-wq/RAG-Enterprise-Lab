"""Modèle de manifest documentaire Phase 2. Un `DocumentManifestEntry` décrit
une ressource documentaire (métadonnées uniquement) — le contenu physique
n'existe que pour au plus 50 exemples (`generation_status=EXAMPLE_GENERATED`).
"""

from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from rag_enterprise_lab.domain.document_taxonomy import DocumentDomain
from rag_enterprise_lab.domain.models import Classification, DocumentStatus


class AuthorityLevel(StrEnum):
    """Autorité légale d'une version, distincte de sa date (chronological
    version) et de sa fenêtre de validité métier (business validity). Un
    avenant signé plus ancien reste plus autoritaire qu'un contrat signé plus
    récent. Voir docs/version-resolution/README.md."""

    SIGNED_AMENDMENT = "SIGNED_AMENDMENT"
    SIGNED_CONTRACT = "SIGNED_CONTRACT"
    SIGNED_PURCHASE_ORDER = "SIGNED_PURCHASE_ORDER"
    APPROVED_PROPOSAL = "APPROVED_PROPOSAL"
    APPROVED_PRICING_GRID = "APPROVED_PRICING_GRID"
    DRAFT = "DRAFT"


# Rang configurable : plus petit = plus autoritaire. Seule source de vérité
# pour tout classement d'autorité (jamais recodé ailleurs).
AUTHORITY_RANK: dict[AuthorityLevel, int] = {
    AuthorityLevel.SIGNED_AMENDMENT: 0,
    AuthorityLevel.SIGNED_CONTRACT: 1,
    AuthorityLevel.SIGNED_PURCHASE_ORDER: 2,
    AuthorityLevel.APPROVED_PROPOSAL: 3,
    AuthorityLevel.APPROVED_PRICING_GRID: 4,
    AuthorityLevel.DRAFT: 5,
}


class GenerationStatus(StrEnum):
    NOT_GENERATED = "NOT_GENERATED"
    EXAMPLE_GENERATED = "EXAMPLE_GENERATED"


class RetentionPolicy(StrEnum):
    THREE_YEARS = "3_YEARS"
    FIVE_YEARS = "5_YEARS"
    SEVEN_YEARS = "7_YEARS"
    TEN_YEARS = "10_YEARS"
    PERMANENT = "PERMANENT"


class DocumentManifestEntry(BaseModel):
    document_id: str
    title: str
    document_type: str
    domain: DocumentDomain
    source_system: str
    owner: str  # employee_id
    classification: Classification
    version: str
    status: DocumentStatus
    valid_from: date | None = None
    valid_to: date | None = None
    created_at: datetime
    approved_at: datetime | None = None
    signed_at: datetime | None = None
    supersedes: str | None = None
    authority_level: AuthorityLevel

    related_customer_id: str | None = None
    related_supplier_id: str | None = None
    related_employee_id: str | None = None
    related_project_id: str | None = None
    related_opportunity_id: str | None = None
    related_expected_contract_id: str | None = None

    contains_personal_data: bool = False
    retention_policy: RetentionPolicy
    allowed_groups: list[str] = Field(default_factory=list)
    checksum: str
    storage_target: str
    generation_status: GenerationStatus = GenerationStatus.NOT_GENERATED
