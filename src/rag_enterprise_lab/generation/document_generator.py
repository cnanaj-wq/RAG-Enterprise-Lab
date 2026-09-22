"""Génération déterministe du manifest de 5000 ressources documentaires
(métadonnées uniquement — voir generation/example_documents.py pour les
≤50 exemples physiques)."""

import random
from datetime import date, datetime, time, timedelta

from rag_enterprise_lab.domain.commercial import Client, Supplier
from rag_enterprise_lab.domain.delivery import Project
from rag_enterprise_lab.domain.document_taxonomy import (
    DOCUMENT_TYPES_BY_DOMAIN,
    DOMAIN_VOLUME,
    SOURCE_SYSTEMS_BY_DOMAIN,
    DocumentDomain,
)
from rag_enterprise_lab.domain.documents import DocumentManifestEntry, GenerationStatus
from rag_enterprise_lab.domain.models import Classification, DocumentStatus
from rag_enterprise_lab.domain.organization import Department, Employee
from rag_enterprise_lab.domain.sales import ExpectedContract, Opportunity
from rag_enterprise_lab.domain.version_authority import authority_level_for
from rag_enterprise_lab.generation.document_taxonomy_rules import (
    DOMAIN_BASE_GROUP,
    DOMAIN_RETENTION,
    SIGNABLE_TYPES,
    TYPE_CLASSIFICATION,
)
from rag_enterprise_lab.identity.groups import (
    RAG_ALL_EMPLOYEES,
    RAG_EXECUTIVE,
    RAG_FINANCE,
    RAG_LEGAL,
    client_group,
    project_group,
)

SIGNABLE_STATUS_WEIGHTS: list[tuple[DocumentStatus, int]] = [
    (DocumentStatus.DRAFT, 8),
    (DocumentStatus.IN_REVIEW, 7),
    (DocumentStatus.APPROVED, 10),
    (DocumentStatus.SIGNED, 55),
    (DocumentStatus.SUPERSEDED, 10),
    (DocumentStatus.EXPIRED, 7),
    (DocumentStatus.QUARANTINED, 3),
]

NON_SIGNABLE_STATUS_WEIGHTS: list[tuple[DocumentStatus, int]] = [
    (DocumentStatus.DRAFT, 15),
    (DocumentStatus.IN_REVIEW, 10),
    (DocumentStatus.APPROVED, 55),
    (DocumentStatus.SUPERSEDED, 10),
    (DocumentStatus.EXPIRED, 7),
    (DocumentStatus.QUARANTINED, 3),
]


def _weighted_choice[T](rng: random.Random, weighted: list[tuple[T, int]]) -> T:
    population = [item for item, _ in weighted]
    weights = [w for _, w in weighted]
    return rng.choices(population, weights=weights, k=1)[0]


def _random_datetime(rng: random.Random, reference_date: date, max_days_back: int) -> datetime:
    day = reference_date - timedelta(days=rng.randint(0, max_days_back))
    return datetime.combine(day, time(hour=rng.randint(8, 18), minute=rng.randint(0, 59)))


def _owner_pools(employees: list[Employee]) -> dict[DocumentDomain, list[Employee]]:
    legal = [e for e in employees if RAG_LEGAL in e.security_groups]
    finance = [e for e in employees if RAG_FINANCE in e.security_groups]
    return {
        DocumentDomain.HR: [e for e in employees if e.department is Department.HR],
        DocumentDomain.LEGAL_CONTRACTS: legal,
        DocumentDomain.CLIENTS_PROSPECTS: [
            e for e in employees if e.department is Department.SALES_ACCOUNT
        ],
        DocumentDomain.PRICING_SALES: [
            e for e in employees if e.department is Department.SALES_ACCOUNT
        ],
        DocumentDomain.IT_ARCHITECTURE_SECURITY: [
            e for e in employees if e.department is Department.IT_CYBERSECURITY
        ],
        DocumentDomain.PROJECTS_PROCEDURES: [
            e
            for e in employees
            if e.department in (Department.CONSULTING, Department.DATA_AI, Department.ENGINEERING)
        ],
        DocumentDomain.FINANCE_COMPLIANCE: finance,
    }


def _allowed_groups_for(
    domain: DocumentDomain,
    classification: Classification,
    related_customer_id: str | None,
    related_project_id: str | None,
    client_group_by_customer_id: dict[str, str],
    project_group_by_project_id: dict[str, str],
) -> list[str]:
    base_group = DOMAIN_BASE_GROUP[domain]
    if classification in (Classification.PUBLIC, Classification.INTERNAL):
        groups = [RAG_ALL_EMPLOYEES]
    else:
        groups = [base_group]
        if classification == Classification.RESTRICTED:
            groups.append(RAG_EXECUTIVE)

    if related_customer_id and classification is not Classification.PUBLIC:
        client_grp = client_group_by_customer_id.get(related_customer_id)
        if client_grp:
            groups.append(client_grp)
    if related_project_id:
        project_grp = project_group_by_project_id.get(related_project_id)
        if project_grp:
            groups.append(project_grp)

    deduped: list[str] = []
    for g in groups:
        if g not in deduped:
            deduped.append(g)
    return deduped


def _title_for(document_type: str, index: int, related_label: str | None) -> str:
    label = document_type.replace("_", " ").title()
    if related_label:
        return f"{label} — {related_label}"
    return f"{label} #{index:04d}"


def generate_manifest(
    rng: random.Random,
    *,
    employees: list[Employee],
    clients: list[Client],
    suppliers: list[Supplier],
    projects: list[Project],
    opportunities: list[Opportunity],
    expected_contracts: list[ExpectedContract],
    reference_date: date,
) -> list[DocumentManifestEntry]:
    owner_pools = _owner_pools(employees)
    client_group_by_id = {c.customer_id: client_group(c.client_code) for c in clients}
    project_group_by_id = {p.project_id: project_group(p.project_code) for p in projects}
    expected_contract_by_client = {ec.client_id: ec for ec in expected_contracts}

    entries: list[DocumentManifestEntry] = []
    counter = 0

    for domain in DocumentDomain:
        types = DOCUMENT_TYPES_BY_DOMAIN[domain]
        volume = DOMAIN_VOLUME[domain]
        source_systems = SOURCE_SYSTEMS_BY_DOMAIN[domain]
        owners = owner_pools[domain] or employees
        retention = DOMAIN_RETENTION[domain]

        for i in range(volume):
            counter += 1
            document_id = f"DOC-{counter:05d}"
            document_type = types[i % len(types)]
            classification = TYPE_CLASSIFICATION[document_type]
            owner = owners[i % len(owners)]
            source_system = source_systems[i % len(source_systems)]

            related_customer_id: str | None = None
            related_supplier_id: str | None = None
            related_employee_id: str | None = None
            related_project_id: str | None = None
            related_opportunity_id: str | None = None
            related_expected_contract_id: str | None = None

            if domain is DocumentDomain.HR:
                related_employee_id = employees[i % len(employees)].employee_id
            elif domain is DocumentDomain.LEGAL_CONTRACTS:
                if document_type == "SUPPLIER_CONTRACT":
                    related_supplier_id = suppliers[i % len(suppliers)].supplier_id
                elif document_type in ("CLIENT_CONTRACT", "NDA", "DPA", "CONTRACT_AMENDMENT"):
                    client = clients[i % len(clients)]
                    related_customer_id = client.customer_id
                    ec = expected_contract_by_client.get(client.customer_id)
                    if ec:
                        related_expected_contract_id = ec.expected_contract_id
                        related_opportunity_id = ec.opportunity_id
            elif domain is DocumentDomain.CLIENTS_PROSPECTS:
                if document_type != "PROSPECT_FILE":
                    related_customer_id = clients[i % len(clients)].customer_id
            elif domain is DocumentDomain.PRICING_SALES:
                client = clients[i % len(clients)]
                related_customer_id = client.customer_id
                ec = expected_contract_by_client.get(client.customer_id)
                if ec and document_type in ("PROPOSAL", "PURCHASE_ORDER"):
                    related_expected_contract_id = ec.expected_contract_id
                    related_opportunity_id = ec.opportunity_id
            elif domain is DocumentDomain.IT_ARCHITECTURE_SECURITY:
                related_project_id = projects[i % len(projects)].project_id
                related_employee_id = owner.employee_id
            elif domain is DocumentDomain.PROJECTS_PROCEDURES:
                related_project_id = projects[i % len(projects)].project_id
            elif domain is DocumentDomain.FINANCE_COMPLIANCE and document_type == "INVOICE":
                related_customer_id = clients[i % len(clients)].customer_id

            is_signable = document_type in SIGNABLE_TYPES
            status = _weighted_choice(
                rng, SIGNABLE_STATUS_WEIGHTS if is_signable else NON_SIGNABLE_STATUS_WEIGHTS
            )

            created_at = _random_datetime(rng, reference_date, max_days_back=1095)
            approved_at = None
            signed_at = None
            if status in (
                DocumentStatus.APPROVED,
                DocumentStatus.SIGNED,
                DocumentStatus.SUPERSEDED,
                DocumentStatus.EXPIRED,
            ):
                approved_at = created_at + timedelta(days=rng.randint(3, 20))
            if is_signable and status in (
                DocumentStatus.SIGNED,
                DocumentStatus.SUPERSEDED,
                DocumentStatus.EXPIRED,
            ):
                signed_at = (approved_at or created_at) + timedelta(days=rng.randint(1, 15))

            valid_from = (signed_at or approved_at or created_at).date()
            valid_to = valid_from + timedelta(days=365 * rng.randint(1, 3))
            if status == DocumentStatus.EXPIRED and valid_to >= reference_date:
                valid_to = reference_date - timedelta(days=rng.randint(1, 200))
            if status != DocumentStatus.EXPIRED and valid_to < reference_date:
                valid_to = reference_date + timedelta(days=rng.randint(30, 400))

            authority_level = authority_level_for(document_type, status)

            related_label: str | None = None
            if related_customer_id:
                related_label = next(
                    (c.name for c in clients if c.customer_id == related_customer_id), None
                )
            elif related_supplier_id:
                related_label = next(
                    (s.name for s in suppliers if s.supplier_id == related_supplier_id), None
                )
            elif related_employee_id:
                emp = next((e for e in employees if e.employee_id == related_employee_id), None)
                related_label = f"{emp.first_name} {emp.last_name}" if emp else None
            elif related_project_id:
                related_label = next(
                    (p.name for p in projects if p.project_id == related_project_id), None
                )

            title = _title_for(document_type, i + 1, related_label)
            allowed_groups = _allowed_groups_for(
                domain,
                classification,
                related_customer_id,
                related_project_id,
                client_group_by_id,
                project_group_by_id,
            )

            entries.append(
                DocumentManifestEntry(
                    document_id=document_id,
                    title=title,
                    document_type=document_type,
                    domain=domain,
                    source_system=source_system,
                    owner=owner.employee_id,
                    classification=classification,
                    version="1.0",
                    status=status,
                    valid_from=valid_from,
                    valid_to=valid_to,
                    created_at=created_at,
                    approved_at=approved_at,
                    signed_at=signed_at,
                    supersedes=None,
                    authority_level=authority_level,
                    related_customer_id=related_customer_id,
                    related_supplier_id=related_supplier_id,
                    related_employee_id=related_employee_id,
                    related_project_id=related_project_id,
                    related_opportunity_id=related_opportunity_id,
                    related_expected_contract_id=related_expected_contract_id,
                    contains_personal_data=classification
                    in (Classification.PERSONAL_DATA, Classification.SENSITIVE_PERSONAL_DATA),
                    retention_policy=retention,
                    allowed_groups=allowed_groups,
                    checksum=f"sha256-placeholder-{document_id}",
                    storage_target=(
                        f"r2://rag-enterprise-lab-prod/{domain.name.lower()}/{document_id}.md"
                    ),
                    generation_status=GenerationStatus.NOT_GENERATED,
                )
            )
    return entries
