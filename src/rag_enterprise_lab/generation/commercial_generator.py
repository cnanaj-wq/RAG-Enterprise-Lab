"""Génération déterministe des référentiels commerciaux (clients, prospects,
partenaires, fournisseurs)."""

import random
from datetime import date, timedelta

from rag_enterprise_lab.domain.commercial import (
    Client,
    ClientStatus,
    Partner,
    PartnerType,
    Prospect,
    ProspectStatus,
    RiskLevel,
    Segment,
    Supplier,
    SupplierCategory,
)
from rag_enterprise_lab.domain.organization import Employee
from rag_enterprise_lab.generation.namebank import (
    COMPANY_ROOTS,
    COMPANY_SUFFIXES,
    COUNTRIES,
    INDUSTRIES,
)

SEGMENT_WEIGHTS: list[tuple[Segment, int]] = [
    (Segment.SMB, 35),
    (Segment.MID_MARKET, 35),
    (Segment.ENTERPRISE, 20),
    (Segment.STRATEGIC, 10),
]

RISK_WEIGHTS: list[tuple[RiskLevel, int]] = [
    (RiskLevel.LOW, 55),
    (RiskLevel.MEDIUM, 35),
    (RiskLevel.HIGH, 10),
]


class CompanyNameFactory:
    """Combinaisons racine + suffixe garanties uniques (40 x 10 = 400 combos)."""

    def __init__(self, rng: random.Random) -> None:
        combos = [f"{root} {suffix}" for root in COMPANY_ROOTS for suffix in COMPANY_SUFFIXES]
        rng.shuffle(combos)
        self._pool = iter(combos)

    def make(self) -> str:
        return next(self._pool)


def _weighted_choice[T](rng: random.Random, weighted: list[tuple[T, int]]) -> T:
    population = [item for item, _ in weighted]
    weights = [w for _, w in weighted]
    return rng.choices(population, weights=weights, k=1)[0]


def _random_past_date(rng: random.Random, reference: date, max_days: int) -> date:
    return reference - timedelta(days=rng.randint(0, max_days))


def generate_clients(
    rng: random.Random,
    *,
    count: int,
    account_managers: list[Employee],
    sales_managers: list[Employee],
    names: CompanyNameFactory,
    reference_date: date,
) -> list[Client]:
    clients: list[Client] = []
    for i in range(1, count + 1):
        account_manager = account_managers[(i - 1) % len(account_managers)]
        sales_manager = sales_managers[(i - 1) % len(sales_managers)]
        clients.append(
            Client(
                customer_id=f"CLI-{i:04d}",
                client_code=f"C{i:03d}",
                name=names.make(),
                industry=rng.choice(INDUSTRIES),
                segment=_weighted_choice(rng, SEGMENT_WEIGHTS),
                account_manager_id=account_manager.employee_id,
                sales_manager_id=sales_manager.employee_id,
                status=ClientStatus.ACTIVE,
                risk_level=_weighted_choice(rng, RISK_WEIGHTS),
                creation_date=_random_past_date(rng, reference_date, 1800),
            )
        )
    return clients


def generate_prospects(
    rng: random.Random,
    *,
    count: int,
    owners: list[Employee],
    names: CompanyNameFactory,
    reference_date: date,
) -> list[Prospect]:
    statuses = list(ProspectStatus)
    prospects: list[Prospect] = []
    for i in range(1, count + 1):
        prospects.append(
            Prospect(
                prospect_id=f"PRO-{i:04d}",
                name=names.make(),
                industry=rng.choice(INDUSTRIES),
                segment=_weighted_choice(rng, SEGMENT_WEIGHTS),
                owner_id=owners[(i - 1) % len(owners)].employee_id,
                status=statuses[(i - 1) % len(statuses)],
                creation_date=_random_past_date(rng, reference_date, 365),
            )
        )
    return prospects


def generate_partners(
    rng: random.Random,
    *,
    count: int,
    names: CompanyNameFactory,
    reference_date: date,
) -> list[Partner]:
    types = list(PartnerType)
    partners: list[Partner] = []
    for i in range(1, count + 1):
        partners.append(
            Partner(
                partner_id=f"PAR-{i:04d}",
                name=names.make(),
                partner_type=types[(i - 1) % len(types)],
                country=rng.choice(COUNTRIES),
                creation_date=_random_past_date(rng, reference_date, 1800),
            )
        )
    return partners


def generate_suppliers(
    rng: random.Random,
    *,
    count: int,
    names: CompanyNameFactory,
    reference_date: date,
) -> list[Supplier]:
    categories = list(SupplierCategory)
    suppliers: list[Supplier] = []
    for i in range(1, count + 1):
        suppliers.append(
            Supplier(
                supplier_id=f"SUP-{i:04d}",
                name=names.make(),
                category=categories[(i - 1) % len(categories)],
                country=rng.choice(COUNTRIES),
                criticality=_weighted_choice(rng, RISK_WEIGHTS),
                creation_date=_random_past_date(rng, reference_date, 1800),
            )
        )
    return suppliers
