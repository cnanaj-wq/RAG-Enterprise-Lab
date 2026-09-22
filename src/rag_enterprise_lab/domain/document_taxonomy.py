"""Taxonomie documentaire Phase 2 : 7 domaines, volumes exacts (5000 total),
types de documents par domaine. Source de vérité pour le générateur et pour
`docs/document-model/`."""

from enum import StrEnum


class DocumentDomain(StrEnum):
    HR = "RH"
    LEGAL_CONTRACTS = "Legal / Contracts"
    CLIENTS_PROSPECTS = "Clients / Prospects"
    PRICING_SALES = "Pricing / Sales"
    IT_ARCHITECTURE_SECURITY = "IT / Architecture / Security"
    PROJECTS_PROCEDURES = "Projects / Procedures"
    FINANCE_COMPLIANCE = "Finance / Compliance"


# Volumes exacts demandés (somme = 5000).
DOMAIN_VOLUME: dict[DocumentDomain, int] = {
    DocumentDomain.HR: 950,
    DocumentDomain.LEGAL_CONTRACTS: 850,
    DocumentDomain.CLIENTS_PROSPECTS: 900,
    DocumentDomain.PRICING_SALES: 450,
    DocumentDomain.IT_ARCHITECTURE_SECURITY: 850,
    DocumentDomain.PROJECTS_PROCEDURES: 600,
    DocumentDomain.FINANCE_COMPLIANCE: 400,
}

TOTAL_DOCUMENT_COUNT = sum(DOMAIN_VOLUME.values())

DOCUMENT_TYPES_BY_DOMAIN: dict[DocumentDomain, list[str]] = {
    DocumentDomain.HR: [
        "EMPLOYMENT_CONTRACT",
        "EMPLOYMENT_AMENDMENT",
        "JOB_DESCRIPTION",
        "HR_POLICY",
        "COLLECTIVE_AGREEMENT",
        "ONBOARDING_DOCUMENT",
        "PAYROLL_RECORD",
    ],
    DocumentDomain.LEGAL_CONTRACTS: [
        "CLIENT_CONTRACT",
        "SUPPLIER_CONTRACT",
        "PARTNER_CONTRACT",
        "NDA",
        "DPA",
        "CONTRACT_AMENDMENT",
    ],
    DocumentDomain.CLIENTS_PROSPECTS: [
        "PROSPECT_FILE",
        "CLIENT_DOSSIER",
        "BUSINESS_CONTACT",
        "TECHNICAL_CONTACT",
        "COMPANY_REGISTRY_EXTRACT",
        "INSURANCE_CERTIFICATE",
        "SECURITY_APPENDIX",
    ],
    DocumentDomain.PRICING_SALES: [
        "PROPOSAL",
        "PURCHASE_ORDER",
        "PRICING_GRID",
        "DISCOUNT_POLICY",
    ],
    DocumentDomain.IT_ARCHITECTURE_SECURITY: [
        "ARCHITECTURE",
        "RUNBOOK",
        "INCIDENT_REPORT",
        "POSTMORTEM",
        "API_DOCUMENTATION",
        "SECURITY_POLICY",
    ],
    DocumentDomain.PROJECTS_PROCEDURES: [
        "PROJECT_CHARTER",
        "PROJECT_STATUS_REPORT",
        "PROCEDURE",
        "DELIVERY_PLAN",
        "MEETING_MINUTES",
    ],
    DocumentDomain.FINANCE_COMPLIANCE: [
        "INVOICE",
        "BUDGET",
        "FINANCE_POLICY",
        "COMPLIANCE_REPORT",
    ],
}

SOURCE_SYSTEMS_BY_DOMAIN: dict[DocumentDomain, list[str]] = {
    DocumentDomain.HR: ["Workday", "SharePoint"],
    DocumentDomain.LEGAL_CONTRACTS: ["DocuSign", "SharePoint"],
    DocumentDomain.CLIENTS_PROSPECTS: ["Salesforce", "SharePoint"],
    DocumentDomain.PRICING_SALES: ["Salesforce", "DocuSign"],
    DocumentDomain.IT_ARCHITECTURE_SECURITY: ["Confluence", "SharePoint"],
    DocumentDomain.PROJECTS_PROCEDURES: ["Confluence", "SharePoint"],
    DocumentDomain.FINANCE_COMPLIANCE: ["SAP", "SharePoint"],
}
