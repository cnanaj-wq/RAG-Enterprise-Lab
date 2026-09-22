"""Génération déterministe d'une Opportunity + son ExpectedContract par client
actif, support du scénario 'clôture commerciale mensuelle'. Les deux entités
sont distinctes : Opportunity ne porte pas signature_status (voir
domain/sales.py)."""

import random
from datetime import date, timedelta

from rag_enterprise_lab.domain.commercial import Client, Segment
from rag_enterprise_lab.domain.sales import (
    ExpectedContract,
    Opportunity,
    OpportunityStage,
    SignatureStatus,
)

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

# Dérivation déterministe du stage d'opportunité depuis le statut de
# signature de son ExpectedContract.
_STAGE_FROM_SIGNATURE: dict[SignatureStatus, OpportunityStage] = {
    SignatureStatus.SIGNED: OpportunityStage.WON,
    SignatureStatus.DECLINED: OpportunityStage.LOST,
    SignatureStatus.BLOCKED: OpportunityStage.LOST,
    SignatureStatus.NOT_SENT: OpportunityStage.OPEN,
    SignatureStatus.SENT: OpportunityStage.OPEN,
    SignatureStatus.VIEWED: OpportunityStage.OPEN,
    SignatureStatus.PARTIALLY_SIGNED: OpportunityStage.OPEN,
}


def _weighted_choice[T](rng: random.Random, weighted: list[tuple[T, int]]) -> T:
    population = [item for item, _ in weighted]
    weights = [w for _, w in weighted]
    return rng.choices(population, weights=weights, k=1)[0]


def generate_opportunities_and_contracts(
    rng: random.Random,
    *,
    clients: list[Client],
    reference_month_start: date,
) -> tuple[list[Opportunity], list[ExpectedContract]]:
    opportunities: list[Opportunity] = []
    contracts: list[ExpectedContract] = []
    for i, client in enumerate(clients, start=1):
        base = SEGMENT_BASE_AMOUNT[client.segment]
        variance = rng.uniform(0.7, 1.4)
        amount = round(base * variance, 2)
        close_date = reference_month_start + timedelta(days=rng.randint(0, 27))
        created = reference_month_start - timedelta(days=rng.randint(5, 60))
        signature_status = _weighted_choice(rng, SIGNATURE_STATUS_WEIGHTS)

        opportunity_id = f"OPP-{i:04d}"
        opportunities.append(
            Opportunity(
                opportunity_id=opportunity_id,
                client_id=client.customer_id,
                sales_owner_id=client.account_manager_id,
                stage=_STAGE_FROM_SIGNATURE[signature_status],
                expected_close_date=close_date,
                expected_amount=amount,
                created_date=created,
            )
        )
        contracts.append(
            ExpectedContract(
                expected_contract_id=f"ECT-{i:04d}",
                opportunity_id=opportunity_id,
                client_id=client.customer_id,
                sales_owner_id=client.account_manager_id,
                expected_close_date=close_date,
                expected_amount=amount,
                signature_status=signature_status,
                created_date=created,
            )
        )
    return opportunities, contracts
