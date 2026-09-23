"""Convention de layout du bucket R2 (S3-compatible), Phase 3.

raw/{domaine}/{document_id}.{ext}
processed/{document_id}/{document.json,content.md,metadata.json,tables.json?}
quarantine/{document_id}.{ext}
archive/{document_id}.{ext}
manifests/{filename}
"""

from rag_enterprise_lab.domain.document_taxonomy import DocumentDomain

# Sous-dossiers raw/ demandés (hr, legal, clients, pricing, technical,
# projects, finance) — distincts des noms d'enum DocumentDomain.
RAW_DOMAIN_FOLDER: dict[DocumentDomain, str] = {
    DocumentDomain.HR: "hr",
    DocumentDomain.LEGAL_CONTRACTS: "legal",
    DocumentDomain.CLIENTS_PROSPECTS: "clients",
    DocumentDomain.PRICING_SALES: "pricing",
    DocumentDomain.IT_ARCHITECTURE_SECURITY: "technical",
    DocumentDomain.PROJECTS_PROCEDURES: "projects",
    DocumentDomain.FINANCE_COMPLIANCE: "finance",
}

RAW_PREFIXES = tuple(f"raw/{folder}/" for folder in RAW_DOMAIN_FOLDER.values())
TOP_LEVEL_PREFIXES = ("raw/", "processed/", "quarantine/", "archive/", "manifests/")


def raw_key(document_id: str, domain: DocumentDomain, extension: str) -> str:
    folder = RAW_DOMAIN_FOLDER[domain]
    return f"raw/{folder}/{document_id}.{extension.lstrip('.')}"


def processed_key(document_id: str, artifact: str) -> str:
    return f"processed/{document_id}/{artifact}"


def quarantine_key(document_id: str, extension: str) -> str:
    return f"quarantine/{document_id}.{extension.lstrip('.')}"


def archive_key(document_id: str, extension: str) -> str:
    return f"archive/{document_id}.{extension.lstrip('.')}"


def manifest_key(filename: str) -> str:
    return f"manifests/{filename}"
