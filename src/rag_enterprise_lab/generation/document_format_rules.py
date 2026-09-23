"""Choix du format physique par type de document — cohérent avec l'usage
métier, jamais une distribution artificiellement uniforme. Les types
"contrat" alternent PDF/DOCX de façon déterministe (parité de l'index dans
document_id) pour obtenir une vraie diversité PDF/DOCX sans arbitraire."""

# Format fixe par type (pas de contrat).
FORMAT_BY_TYPE: dict[str, str] = {
    # Pricing / tableaux -> XLSX
    "PRICING_GRID": "xlsx",
    "BUDGET": "xlsx",
    "DELIVERY_PLAN": "xlsx",
    # Export tabulaire léger -> CSV
    "BUSINESS_CONTACT": "csv",
    "TECHNICAL_CONTACT": "csv",
    "PAYROLL_RECORD": "csv",
    "INVOICE": "csv",
    # Présentation -> PPTX
    "PROJECT_STATUS_REPORT": "pptx",
    # Rapport mis en forme -> HTML
    "INCIDENT_REPORT": "html",
    "POSTMORTEM": "html",
    "COMPLIANCE_REPORT": "html",
    # Documentation / procédures -> Markdown
    "RUNBOOK": "md",
    "PROCEDURE": "md",
    "ARCHITECTURE": "md",
    "API_DOCUMENTATION": "md",
    "SECURITY_POLICY": "md",
    "HR_POLICY": "md",
    "FINANCE_POLICY": "md",
    "DISCOUNT_POLICY": "md",
    "COLLECTIVE_AGREEMENT": "md",
    "MEETING_MINUTES": "md",
    # Dossiers / extraits formels -> PDF
    "CLIENT_DOSSIER": "pdf",
    "PROSPECT_FILE": "pdf",
    "COMPANY_REGISTRY_EXTRACT": "pdf",
    "INSURANCE_CERTIFICATE": "pdf",
    "SECURITY_APPENDIX": "pdf",
    "PROJECT_CHARTER": "docx",
    "JOB_DESCRIPTION": "docx",
    "ONBOARDING_DOCUMENT": "docx",
}

# Types "contrat" : alternent PDF / DOCX de façon déterministe.
CONTRACT_TYPES: frozenset[str] = frozenset(
    {
        "CLIENT_CONTRACT",
        "SUPPLIER_CONTRACT",
        "PARTNER_CONTRACT",
        "NDA",
        "DPA",
        "CONTRACT_AMENDMENT",
        "EMPLOYMENT_CONTRACT",
        "EMPLOYMENT_AMENDMENT",
        "PROPOSAL",
        "PURCHASE_ORDER",
    }
)

FORMAT_CONTENT_TYPES: dict[str, str] = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "md": "text/markdown",
    "html": "text/html",
    "csv": "text/csv",
}


def format_for(document_id: str, document_type: str) -> str:
    """Format déterministe : dépend uniquement de (document_id, document_type)."""
    if document_type in CONTRACT_TYPES:
        # Alternance déterministe PDF/DOCX à partir des derniers chiffres du
        # document_id (ex. DOC-00001 -> 1) plutôt que d'un compteur externe.
        digits = "".join(ch for ch in document_id if ch.isdigit()) or "0"
        return "pdf" if int(digits) % 2 == 0 else "docx"
    return FORMAT_BY_TYPE.get(document_type, "pdf")
