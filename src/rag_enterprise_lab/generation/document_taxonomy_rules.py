"""Règles déterministes (classification, rétention, groupe ACL de base,
type signable) associées à chaque type de document Phase 2. Séparées de
`domain/document_taxonomy.py` (qui ne liste que domaines/types/volumes) pour
garder cette dernière purement descriptive."""

from rag_enterprise_lab.domain.document_taxonomy import DocumentDomain
from rag_enterprise_lab.domain.documents import RetentionPolicy
from rag_enterprise_lab.domain.models import Classification
from rag_enterprise_lab.identity.groups import (
    RAG_CONSULTING,
    RAG_FINANCE,
    RAG_HR,
    RAG_IT,
    RAG_LEGAL,
    RAG_SALES,
)

TYPE_CLASSIFICATION: dict[str, Classification] = {
    "EMPLOYMENT_CONTRACT": Classification.SENSITIVE_PERSONAL_DATA,
    "EMPLOYMENT_AMENDMENT": Classification.SENSITIVE_PERSONAL_DATA,
    "JOB_DESCRIPTION": Classification.INTERNAL,
    "HR_POLICY": Classification.INTERNAL,
    "COLLECTIVE_AGREEMENT": Classification.INTERNAL,
    "ONBOARDING_DOCUMENT": Classification.PERSONAL_DATA,
    "PAYROLL_RECORD": Classification.SENSITIVE_PERSONAL_DATA,
    "CLIENT_CONTRACT": Classification.CONFIDENTIAL,
    "SUPPLIER_CONTRACT": Classification.CONFIDENTIAL,
    "PARTNER_CONTRACT": Classification.CONFIDENTIAL,
    "NDA": Classification.CONFIDENTIAL,
    "DPA": Classification.RESTRICTED,
    "CONTRACT_AMENDMENT": Classification.CONFIDENTIAL,
    "PROSPECT_FILE": Classification.INTERNAL,
    "CLIENT_DOSSIER": Classification.CONFIDENTIAL,
    "BUSINESS_CONTACT": Classification.PERSONAL_DATA,
    "TECHNICAL_CONTACT": Classification.PERSONAL_DATA,
    "COMPANY_REGISTRY_EXTRACT": Classification.INTERNAL,
    "INSURANCE_CERTIFICATE": Classification.INTERNAL,
    "SECURITY_APPENDIX": Classification.RESTRICTED,
    "PROPOSAL": Classification.CONFIDENTIAL,
    "PURCHASE_ORDER": Classification.CONFIDENTIAL,
    "PRICING_GRID": Classification.RESTRICTED,
    "DISCOUNT_POLICY": Classification.INTERNAL,
    "ARCHITECTURE": Classification.INTERNAL,
    "RUNBOOK": Classification.INTERNAL,
    "INCIDENT_REPORT": Classification.CONFIDENTIAL,
    "POSTMORTEM": Classification.INTERNAL,
    "API_DOCUMENTATION": Classification.INTERNAL,
    "SECURITY_POLICY": Classification.RESTRICTED,
    "PROJECT_CHARTER": Classification.INTERNAL,
    "PROJECT_STATUS_REPORT": Classification.INTERNAL,
    "PROCEDURE": Classification.INTERNAL,
    "DELIVERY_PLAN": Classification.INTERNAL,
    "MEETING_MINUTES": Classification.INTERNAL,
    "INVOICE": Classification.CONFIDENTIAL,
    "BUDGET": Classification.RESTRICTED,
    "FINANCE_POLICY": Classification.INTERNAL,
    "COMPLIANCE_REPORT": Classification.RESTRICTED,
}

DOMAIN_RETENTION: dict[DocumentDomain, RetentionPolicy] = {
    DocumentDomain.HR: RetentionPolicy.TEN_YEARS,
    DocumentDomain.LEGAL_CONTRACTS: RetentionPolicy.TEN_YEARS,
    DocumentDomain.CLIENTS_PROSPECTS: RetentionPolicy.FIVE_YEARS,
    DocumentDomain.PRICING_SALES: RetentionPolicy.FIVE_YEARS,
    DocumentDomain.IT_ARCHITECTURE_SECURITY: RetentionPolicy.FIVE_YEARS,
    DocumentDomain.PROJECTS_PROCEDURES: RetentionPolicy.THREE_YEARS,
    DocumentDomain.FINANCE_COMPLIANCE: RetentionPolicy.SEVEN_YEARS,
}

DOMAIN_BASE_GROUP: dict[DocumentDomain, str] = {
    DocumentDomain.HR: RAG_HR,
    DocumentDomain.LEGAL_CONTRACTS: RAG_LEGAL,
    DocumentDomain.CLIENTS_PROSPECTS: RAG_SALES,
    DocumentDomain.PRICING_SALES: RAG_SALES,
    DocumentDomain.IT_ARCHITECTURE_SECURITY: RAG_IT,
    DocumentDomain.PROJECTS_PROCEDURES: RAG_CONSULTING,
    DocumentDomain.FINANCE_COMPLIANCE: RAG_FINANCE,
}

# Types dont l'issue "finale" normale est une signature (contrats, avenants,
# bons de commande). Les autres types s'arrêtent à APPROVED.
SIGNABLE_TYPES: set[str] = {
    "CLIENT_CONTRACT",
    "SUPPLIER_CONTRACT",
    "PARTNER_CONTRACT",
    "NDA",
    "DPA",
    "CONTRACT_AMENDMENT",
    "EMPLOYMENT_CONTRACT",
    "EMPLOYMENT_AMENDMENT",
    "PURCHASE_ORDER",
}

# Types "amendement" -> type de contrat de base qu'ils peuvent superseder,
# et champ related_* utilisé pour retrouver ce contrat de base.
AMENDMENT_BASE_TYPES: dict[str, list[str]] = {
    "CONTRACT_AMENDMENT": ["CLIENT_CONTRACT", "SUPPLIER_CONTRACT", "PARTNER_CONTRACT"],
    "EMPLOYMENT_AMENDMENT": ["EMPLOYMENT_CONTRACT"],
}

# Types "versionables" par eux-mêmes (plusieurs occurrences pour le même
# related_id forment une chaîne chronologique de versions).
VERSIONABLE_BASE_TYPES: set[str] = {
    "CLIENT_CONTRACT",
    "SUPPLIER_CONTRACT",
    "PARTNER_CONTRACT",
    "EMPLOYMENT_CONTRACT",
    "PRICING_GRID",
}
