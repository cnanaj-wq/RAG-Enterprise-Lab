"""Génération déterministe d'une opportunité (contrat attendu) par client actif,
support du scénario 'clôture commerciale mensuelle'."""

import random
from datetime import date, timedelta

from rag_enterprise_lab.domain.commercial import Client, Segment
from rag_enterprise_lab.domain.sales import Opportunity, SignatureStatus

SIGNATURE_STATUS_WEIGHTS: list[tuple[SignatureStatus, int]] = [
    (SignatureStatus.SIGNED, 40),
    (SignatureStatus.SENT, 15),
    (SignatureStatus.VIEWED, 12),
    (SignatureStatus.PARTIALLY_SIGNED, 10),
    (SignatureStatus.NOT_SENT, 13),
    (SignatureStatus.DECLINED, 5),
    (SignatureStatus.BLOCKED, 5),
]

SEGMENT_BASE_AMOUNT: dict[Segment, float] = {
    Segment.SMB: 15_000.0,
    Segment.MID_MARKET: 45_000.0,
    Segment.ENTERPRISE: 120_000.0,
    Segment.STRATEGIC: 300_000.0,
}


def _weighted_choice[T](rng: random.Random, weighted: list[tuple[T, int]]) -> T:
    population = [item for item, _ in weighted]
    weights = [w for _, w in weighted]
    return rng.choices(population, weights=weights, k=1)[0]


def generate_opportunities(
    rng: random.Random,
    *,
    clients: list[Client],
    reference_month_start: date,
) -> list[Opportunity]:
    opportunities: list[Opportunity] = []
    for i, client in enumerate(clients, start=1):
        base = SEGMENT_BASE_AMOUNT[client.segment]
        variance = rng.uniform(0.7, 1.4)
        opportunities.append(
            Opportunity(
                opportunity_id=f"OPP-{i:04d}",
                client_id=client.customer_id,
                sales_owner_id=client.account_manager_id,
                expected_close_date=reference_month_start + timedelta(days=rng.randint(0, 27)),
                expected_amount=round(base * variance, 2),
                signature_status=_weighted_choice(rng, SIGNATURE_STATUS_WEIGHTS),
                created_date=reference_month_start - timedelta(days=rng.randint(5, 60)),
            )
        )
    return opportunities
