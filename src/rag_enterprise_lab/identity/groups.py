from rag_enterprise_lab.domain.organization import Department

RAG_ALL_EMPLOYEES = "RAG_ALL_EMPLOYEES"
RAG_HR = "RAG_HR"
RAG_FINANCE = "RAG_FINANCE"
RAG_LEGAL = "RAG_LEGAL"
RAG_SALES = "RAG_SALES"
RAG_IT = "RAG_IT"
RAG_DATA_AI = "RAG_DATA_AI"
RAG_ENGINEERING = "RAG_ENGINEERING"
RAG_EXECUTIVE = "RAG_EXECUTIVE"
RAG_MARKETING = "RAG_MARKETING"

# Ajout Phase 1 : la liste fournie ne couvre pas le département Consulting
# (34 collaborateurs, 28 % de l'effectif). Un groupe dédié est nécessaire pour que
# "groupes départementaux cohérents" reste vrai pour les 9 départements. Voir
# PHASE-1-REPORT.md, section "Points bloquants / remarques".
RAG_CONSULTING = "RAG_CONSULTING"

STATIC_GROUPS: list[str] = [
    RAG_ALL_EMPLOYEES,
    RAG_HR,
    RAG_FINANCE,
    RAG_LEGAL,
    RAG_SALES,
    RAG_IT,
    RAG_DATA_AI,
    RAG_ENGINEERING,
    RAG_EXECUTIVE,
    RAG_MARKETING,
    RAG_CONSULTING,
]

# Groupe(s) départemental(aux) par défaut. Finance / Legal est affiné par
# spécialisation de poste dans le générateur (RAG_FINANCE ou RAG_LEGAL).
DEPARTMENT_GROUPS: dict[Department, list[str]] = {
    Department.DIRECTION: [RAG_EXECUTIVE],
    Department.SALES_ACCOUNT: [RAG_SALES],
    Department.CONSULTING: [RAG_CONSULTING],
    Department.DATA_AI: [RAG_DATA_AI],
    Department.ENGINEERING: [RAG_ENGINEERING],
    Department.IT_CYBERSECURITY: [RAG_IT],
    Department.HR: [RAG_HR],
    Department.FINANCE_LEGAL: [RAG_FINANCE, RAG_LEGAL],
    Department.MARKETING_PARTNERSHIPS: [RAG_MARKETING],
}


def client_group(client_code: str) -> str:
    return f"RAG_CLIENT_{client_code}"


def project_group(project_code: str) -> str:
    return f"RAG_PROJECT_{project_code}"
