"""Génération déterministe et reproductible des 120 collaborateurs.

La hiérarchie est construite couche par couche (Direction -> têtes de
département -> [leads] -> contributeurs) de sorte que chaque manager existe
déjà lorsqu'un rapport est créé : aucun cycle n'est possible par construction.
"""

import random

from rag_enterprise_lab.domain.organization import (
    DEPARTMENT_BUSINESS_UNIT,
    DEPARTMENT_HEADCOUNT,
    Clearance,
    Department,
    Employee,
    EmploymentType,
    SeniorityLevel,
)
from rag_enterprise_lab.generation.namebank import (
    CORPORATE_EMAIL_DOMAIN,
    FIRST_NAMES,
    LAST_NAMES,
    LOCATIONS,
)
from rag_enterprise_lab.identity.groups import (
    DEPARTMENT_GROUPS,
    RAG_ALL_EMPLOYEES,
    RAG_FINANCE,
    RAG_LEGAL,
)
from rag_enterprise_lab.identity.rbac import Role

EMPLOYMENT_TYPE_WEIGHTS: list[tuple[EmploymentType, int]] = [
    (EmploymentType.CDI, 85),
    (EmploymentType.CDD, 6),
    (EmploymentType.FREELANCE, 5),
    (EmploymentType.APPRENTICESHIP, 4),
]

IC_SENIORITY_WEIGHTS: list[tuple[SeniorityLevel, int]] = [
    (SeniorityLevel.JUNIOR, 30),
    (SeniorityLevel.CONFIRMED, 45),
    (SeniorityLevel.SENIOR, 25),
]

# Départements dont les collaborateurs manipulent régulièrement des données
# personnelles / financières sensibles (RGPD, paie, contrats) : clearance
# relevée par défaut. Voir docs/architecture/03-data-governance-rgpd.md.
ELEVATED_BY_DEFAULT_DEPARTMENTS = {Department.FINANCE_LEGAL, Department.HR}

# Spécialisation Finance / Legal : 3 titres finance + 3 titres legal,
# répartis de façon déterministe sur les 6 contributeurs du département.
FINANCE_LEGAL_TRACKS: list[tuple[str, str]] = [
    ("Financial Controller", "FINANCE"),
    ("Legal Counsel", "LEGAL"),
    ("Accountant", "FINANCE"),
    ("Contracts Manager", "LEGAL"),
    ("FP&A Analyst", "FINANCE"),
    ("Compliance Officer", "LEGAL"),
]


class _IdFactory:
    def __init__(self) -> None:
        self._counter = 0

    def next(self) -> str:
        self._counter += 1
        return f"EMP-{self._counter:04d}"


class _NameFactory:
    """Distribue des combinaisons prénom/nom sans répétition d'email."""

    def __init__(self, rng: random.Random) -> None:
        self._rng = rng
        self._used_emails: set[str] = set()

    def make(self) -> tuple[str, str, str]:
        first = self._rng.choice(FIRST_NAMES)
        last = self._rng.choice(LAST_NAMES)
        base = f"{first}.{last}".lower()
        email = f"{base}@{CORPORATE_EMAIL_DOMAIN}"
        suffix = 1
        while email in self._used_emails:
            suffix += 1
            email = f"{base}{suffix}@{CORPORATE_EMAIL_DOMAIN}"
        self._used_emails.add(email)
        return first, last, email


def _weighted_choice[T](rng: random.Random, weighted: list[tuple[T, int]]) -> T:
    population = [item for item, _ in weighted]
    weights = [w for _, w in weighted]
    return rng.choices(population, weights=weights, k=1)[0]


def _base_groups(department: Department, specialization: str | None) -> list[str]:
    groups = [RAG_ALL_EMPLOYEES]
    if department is Department.FINANCE_LEGAL and specialization is not None:
        groups.append(RAG_LEGAL if specialization == "LEGAL" else RAG_FINANCE)
    else:
        groups.extend(DEPARTMENT_GROUPS[department])
    return groups


def _clearance_for(department: Department, tier: str) -> Clearance:
    if tier == "EXECUTIVE":
        return Clearance.EXECUTIVE
    if tier in ("HEAD", "LEAD") or department in ELEVATED_BY_DEFAULT_DEPARTMENTS:
        return Clearance.ELEVATED
    return Clearance.STANDARD


class OrganizationBuilder:
    def __init__(self, rng: random.Random) -> None:
        self._rng = rng
        self._ids = _IdFactory()
        self._names = _NameFactory(rng)
        self.employees: list[Employee] = []

    def add(
        self,
        *,
        department: Department,
        job_title: str,
        manager_id: str | None,
        tier: str,
        seniority: SeniorityLevel,
        identity_roles: list[Role],
        specialization: str | None = None,
    ) -> Employee:
        first, last, email = self._names.make()
        emp = Employee(
            employee_id=self._ids.next(),
            first_name=first,
            last_name=last,
            corporate_email=email,
            department=department,
            business_unit=DEPARTMENT_BUSINESS_UNIT[department],
            job_title=job_title,
            manager_id=manager_id,
            location=self._rng.choice(LOCATIONS),
            employment_type=_weighted_choice(self._rng, EMPLOYMENT_TYPE_WEIGHTS),
            seniority_level=seniority,
            active=True,
            security_groups=_base_groups(department, specialization),
            identity_roles=[r.value for r in identity_roles],
            clearance=_clearance_for(department, tier),
        )
        self.employees.append(emp)
        return emp

    def ic_seniority(self) -> SeniorityLevel:
        return _weighted_choice(self._rng, IC_SENIORITY_WEIGHTS)

    def build_layered_department(
        self,
        department: Department,
        head_title: str,
        reports_to: Employee,
        lead_title: str,
        ic_title: str,
        lead_count: int,
        ic_count: int,
    ) -> Employee:
        head = self.add(
            department=department,
            job_title=head_title,
            manager_id=reports_to.employee_id,
            tier="HEAD",
            seniority=SeniorityLevel.HEAD,
            identity_roles=[Role.DEPARTMENT_HEAD, Role.MANAGER],
        )
        leads = [
            self.add(
                department=department,
                job_title=lead_title,
                manager_id=head.employee_id,
                tier="LEAD",
                seniority=SeniorityLevel.LEAD,
                identity_roles=[Role.TEAM_LEAD, Role.MANAGER],
            )
            for _ in range(lead_count)
        ]
        for i in range(ic_count):
            lead = leads[i % lead_count]
            self.add(
                department=department,
                job_title=ic_title,
                manager_id=lead.employee_id,
                tier="IC",
                seniority=self.ic_seniority(),
                identity_roles=[Role.EMPLOYEE],
            )
        return head

    def build_flat_department(
        self,
        department: Department,
        head_title: str,
        reports_to: Employee,
        ic_title: str,
        ic_count: int,
        ic_identity_roles: list[Role],
        head_identity_roles: list[Role],
    ) -> Employee:
        head = self.add(
            department=department,
            job_title=head_title,
            manager_id=reports_to.employee_id,
            tier="HEAD",
            seniority=SeniorityLevel.HEAD,
            identity_roles=head_identity_roles,
        )
        for _ in range(ic_count):
            self.add(
                department=department,
                job_title=ic_title,
                manager_id=head.employee_id,
                tier="IC",
                seniority=self.ic_seniority(),
                identity_roles=ic_identity_roles,
            )
        return head

    def build_finance_legal_department(
        self,
        department: Department,
        head_title: str,
        reports_to: Employee,
        ic_count: int,
    ) -> Employee:
        head = self.add(
            department=department,
            job_title=head_title,
            manager_id=reports_to.employee_id,
            tier="HEAD",
            seniority=SeniorityLevel.HEAD,
            identity_roles=[Role.DEPARTMENT_HEAD, Role.MANAGER, Role.FINANCE_ADMIN, Role.LEGAL_ADMIN],
            specialization=None,
        )
        for i in range(ic_count):
            title, track = FINANCE_LEGAL_TRACKS[i % len(FINANCE_LEGAL_TRACKS)]
            role = Role.LEGAL_ADMIN if track == "LEGAL" else Role.FINANCE_ADMIN
            self.add(
                department=department,
                job_title=title,
                manager_id=head.employee_id,
                tier="IC",
                seniority=self.ic_seniority(),
                identity_roles=[Role.EMPLOYEE, role],
                specialization=track,
            )
        return head


def generate_employees(rng: random.Random) -> list[Employee]:
    builder = OrganizationBuilder(rng)

    # --- Direction (6) -----------------------------------------------------
    ceo = builder.add(
        department=Department.DIRECTION,
        job_title="Chief Executive Officer",
        manager_id=None,
        tier="EXECUTIVE",
        seniority=SeniorityLevel.EXECUTIVE,
        identity_roles=[Role.EXECUTIVE],
    )
    c_level_titles = {
        "COO": "Chief Operating Officer",
        "CFO": "Chief Financial Officer",
        "CTO": "Chief Technology Officer",
        "CHRO": "Chief Human Resources Officer",
        "CRO": "Chief Revenue Officer",
    }
    direction: dict[str, Employee] = {"CEO": ceo}
    for code, title in c_level_titles.items():
        direction[code] = builder.add(
            department=Department.DIRECTION,
            job_title=title,
            manager_id=ceo.employee_id,
            tier="EXECUTIVE",
            seniority=SeniorityLevel.EXECUTIVE,
            identity_roles=[Role.EXECUTIVE],
        )

    # --- Sales / Account (18) : structure imposée ---------------------------
    sales_director = builder.add(
        department=Department.SALES_ACCOUNT,
        job_title="Sales Director",
        manager_id=direction["CRO"].employee_id,
        tier="HEAD",
        seniority=SeniorityLevel.HEAD,
        identity_roles=[Role.SALES_DIRECTOR, Role.DEPARTMENT_HEAD, Role.MANAGER],
    )
    sales_managers = [
        builder.add(
            department=Department.SALES_ACCOUNT,
            job_title="Sales Manager",
            manager_id=sales_director.employee_id,
            tier="LEAD",
            seniority=SeniorityLevel.LEAD,
            identity_roles=[Role.SALES_MANAGER, Role.MANAGER],
        )
        for _ in range(2)
    ]
    for i in range(8):
        builder.add(
            department=Department.SALES_ACCOUNT,
            job_title="Account Executive",
            manager_id=sales_managers[i % 2].employee_id,
            tier="IC",
            seniority=builder.ic_seniority(),
            identity_roles=[Role.ACCOUNT_MANAGER],
        )
    for i in range(4):
        builder.add(
            department=Department.SALES_ACCOUNT,
            job_title="Key Account Manager",
            manager_id=sales_managers[i % 2].employee_id,
            tier="IC",
            seniority=builder.ic_seniority(),
            identity_roles=[Role.ACCOUNT_MANAGER],
        )
    for _ in range(3):
        builder.add(
            department=Department.SALES_ACCOUNT,
            job_title="Sales Operations Analyst",
            manager_id=sales_director.employee_id,
            tier="IC",
            seniority=builder.ic_seniority(),
            identity_roles=[Role.SALES_OPERATIONS],
        )

    # --- Consulting (34) = 1 head + 4 leads + 29 consultants -----------------
    builder.build_layered_department(
        Department.CONSULTING,
        "Head of Consulting",
        direction["COO"],
        "Consulting Team Lead",
        "Consultant",
        lead_count=4,
        ic_count=DEPARTMENT_HEADCOUNT[Department.CONSULTING] - 1 - 4,
    )

    # --- Data & AI (20) = 1 head + 3 leads + 16 ICs ---------------------------
    builder.build_layered_department(
        Department.DATA_AI,
        "Head of Data & AI",
        direction["CTO"],
        "Data & AI Team Lead",
        "Data / ML Engineer",
        lead_count=3,
        ic_count=DEPARTMENT_HEADCOUNT[Department.DATA_AI] - 1 - 3,
    )

    # --- Engineering (16) = 1 head + 2 leads + 13 ICs -------------------------
    builder.build_layered_department(
        Department.ENGINEERING,
        "Head of Engineering",
        direction["CTO"],
        "Engineering Team Lead",
        "Software Engineer",
        lead_count=2,
        ic_count=DEPARTMENT_HEADCOUNT[Department.ENGINEERING] - 1 - 2,
    )

    # --- Départements plats --------------------------------------------------
    builder.build_flat_department(
        Department.IT_CYBERSECURITY,
        "Head of IT & Cybersecurity",
        direction["COO"],
        "IT / Security Analyst",
        DEPARTMENT_HEADCOUNT[Department.IT_CYBERSECURITY] - 1,
        ic_identity_roles=[Role.EMPLOYEE, Role.IT_ADMIN],
        head_identity_roles=[Role.DEPARTMENT_HEAD, Role.MANAGER, Role.IT_ADMIN],
    )

    builder.build_flat_department(
        Department.HR,
        "Head of HR",
        direction["CHRO"],
        "HR Business Partner",
        DEPARTMENT_HEADCOUNT[Department.HR] - 1,
        ic_identity_roles=[Role.EMPLOYEE, Role.HR_ADMIN],
        head_identity_roles=[Role.DEPARTMENT_HEAD, Role.MANAGER, Role.HR_ADMIN],
    )

    builder.build_finance_legal_department(
        Department.FINANCE_LEGAL,
        "Head of Finance & Legal",
        direction["CFO"],
        DEPARTMENT_HEADCOUNT[Department.FINANCE_LEGAL] - 1,
    )

    builder.build_flat_department(
        Department.MARKETING_PARTNERSHIPS,
        "Head of Marketing & Partnerships",
        direction["CRO"],
        "Marketing & Partnerships Specialist",
        DEPARTMENT_HEADCOUNT[Department.MARKETING_PARTNERSHIPS] - 1,
        ic_identity_roles=[Role.EMPLOYEE],
        head_identity_roles=[Role.DEPARTMENT_HEAD, Role.MANAGER],
    )

    employees = builder.employees

    # --- Variance réaliste du champ `active` (n'affecte pas les effectifs) --
    inactive_candidates = sorted(
        (e for e in employees if "Head" not in e.job_title and "Chief" not in e.job_title),
        key=lambda e: e.employee_id,
    )
    for emp in rng.sample(inactive_candidates, k=min(3, len(inactive_candidates))):
        emp.active = False

    return employees


def account_manager_pool(employees: list[Employee]) -> list[Employee]:
    return [e for e in employees if e.job_title in ("Account Executive", "Key Account Manager")]


def sales_manager_pool(employees: list[Employee]) -> list[Employee]:
    return [e for e in employees if e.job_title == "Sales Manager"]


def delivery_lead_pool(employees: list[Employee]) -> list[Employee]:
    return [
        e
        for e in employees
        if e.department in (Department.CONSULTING, Department.DATA_AI, Department.ENGINEERING)
        and ("Lead" in e.job_title or "Head" in e.job_title)
    ]


def delivery_member_pool(employees: list[Employee]) -> list[Employee]:
    return [
        e
        for e in employees
        if e.department in (Department.CONSULTING, Department.DATA_AI, Department.ENGINEERING)
    ]
