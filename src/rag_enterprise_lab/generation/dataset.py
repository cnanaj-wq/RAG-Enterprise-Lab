"""Orchestrateur Phase 1 : construit le dataset synthétique complet à partir
d'un seed unique, de façon déterministe, reproductible et idempotente.
"""

import json
import random
from datetime import date
from pathlib import Path

from pydantic import BaseModel, Field

from rag_enterprise_lab.domain.commercial import Client, Partner, Prospect, Supplier
from rag_enterprise_lab.domain.delivery import Project
from rag_enterprise_lab.domain.organization import Employee
from rag_enterprise_lab.domain.sales import Opportunity
from rag_enterprise_lab.generation.commercial_generator import (
    CompanyNameFactory,
    generate_clients,
    generate_partners,
    generate_prospects,
    generate_suppliers,
)
from rag_enterprise_lab.generation.delivery_generator import generate_projects
from rag_enterprise_lab.generation.organization_generator import (
    account_manager_pool,
    delivery_lead_pool,
    delivery_member_pool,
    generate_employees,
    sales_manager_pool,
)
from rag_enterprise_lab.generation.sales_generator import generate_opportunities
from rag_enterprise_lab.identity.groups import STATIC_GROUPS, client_group, project_group

REFERENCE_MONTH_START = date(2026, 9, 1)

CLIENT_COUNT = 65
PROSPECT_COUNT = 120
PARTNER_COUNT = 30
SUPPLIER_COUNT = 80


class OrganizationDataset(BaseModel):
    seed: int
    reference_date: date
    employees: list[Employee]
    clients: list[Client]
    prospects: list[Prospect]
    partners: list[Partner]
    suppliers: list[Supplier]
    projects: list[Project]
    opportunities: list[Opportunity]
    identity_groups: list[str] = Field(default_factory=list)


def _add_group(employee: Employee, group: str) -> None:
    if group not in employee.security_groups:
        employee.security_groups.append(group)


def generate_dataset(seed: int) -> OrganizationDataset:
    rng = random.Random(seed)

    employees = generate_employees(rng)
    employees_by_id = {e.employee_id: e for e in employees}

    names = CompanyNameFactory(rng)

    account_managers = account_manager_pool(employees)
    managers = sales_manager_pool(employees)
    clients = generate_clients(
        rng,
        count=CLIENT_COUNT,
        account_managers=account_managers,
        sales_managers=managers,
        names=names,
        reference_date=REFERENCE_MONTH_START,
    )

    all_sales = [e for e in employees if e.department.value == "Sales / Account"]
    prospects = generate_prospects(
        rng,
        count=PROSPECT_COUNT,
        owners=all_sales,
        names=names,
        reference_date=REFERENCE_MONTH_START,
    )

    partners = generate_partners(
        rng, count=PARTNER_COUNT, names=names, reference_date=REFERENCE_MONTH_START
    )
    suppliers = generate_suppliers(
        rng, count=SUPPLIER_COUNT, names=names, reference_date=REFERENCE_MONTH_START
    )

    leads = delivery_lead_pool(employees)
    members = delivery_member_pool(employees)
    projects = generate_projects(
        rng,
        clients=clients,
        leads=leads,
        members=members,
        reference_date=REFERENCE_MONTH_START,
    )

    opportunities = generate_opportunities(
        rng, clients=clients, reference_month_start=REFERENCE_MONTH_START
    )

    # --- Câblage ACL/RBAC : appartenance client -----------------------------
    for client in clients:
        group = client_group(client.client_code)
        for emp_id in (client.account_manager_id, client.sales_manager_id):
            emp = employees_by_id[emp_id]
            _add_group(emp, group)
            if client.customer_id not in emp.client_memberships:
                emp.client_memberships.append(client.customer_id)

    # --- Câblage ACL/RBAC : appartenance projet -----------------------------
    for project in projects:
        group = project_group(project.project_code)
        member_ids = set(project.team_member_ids) | {project.delivery_lead_id}
        for emp_id in member_ids:
            emp = employees_by_id[emp_id]
            _add_group(emp, group)
            if project.project_id not in emp.project_memberships:
                emp.project_memberships.append(project.project_id)
            client = next(c for c in clients if c.customer_id == project.client_id)
            if client.customer_id not in emp.client_memberships:
                emp.client_memberships.append(client.customer_id)

    identity_groups = sorted(
        set(STATIC_GROUPS)
        | {client_group(c.client_code) for c in clients}
        | {project_group(p.project_code) for p in projects}
    )

    return OrganizationDataset(
        seed=seed,
        reference_date=REFERENCE_MONTH_START,
        employees=employees,
        clients=clients,
        prospects=prospects,
        partners=partners,
        suppliers=suppliers,
        projects=projects,
        opportunities=opportunities,
        identity_groups=identity_groups,
    )


_FILES = {
    "employees.json": "employees",
    "clients.json": "clients",
    "prospects.json": "prospects",
    "partners.json": "partners",
    "suppliers.json": "suppliers",
    "projects.json": "projects",
    "opportunities.json": "opportunities",
}


def write_dataset(dataset: OrganizationDataset, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for filename, attr in _FILES.items():
        items = getattr(dataset, attr)
        payload = [item.model_dump(mode="json") for item in items]
        (out_dir / filename).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    manifest = {
        "seed": dataset.seed,
        "reference_date": dataset.reference_date.isoformat(),
        "counts": {attr: len(getattr(dataset, attr)) for attr in _FILES.values()},
        "identity_groups_count": len(dataset.identity_groups),
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (out_dir / "identity_groups.json").write_text(
        json.dumps(dataset.identity_groups, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
