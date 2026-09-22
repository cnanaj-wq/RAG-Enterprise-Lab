from datetime import date
from enum import StrEnum

from pydantic import BaseModel


class SignatureStatus(StrEnum):
    NOT_SENT = "NOT_SENT"
    SENT = "SENT"
    VIEWED = "VIEWED"
    PARTIALLY_SIGNED = "PARTIALLY_SIGNED"
    SIGNED = "SIGNED"
    DECLINED = "DECLINED"
    BLOCKED = "BLOCKED"


class OpportunityStage(StrEnum):
    OPEN = "OPEN"
    WON = "WON"
    LOST = "LOST"


class Opportunity(BaseModel):
    """La poursuite commerciale elle-même (pipeline). Ne porte PAS le statut de
    signature : celui-ci appartient exclusivement à ExpectedContract, pour que
    l'opportunité, le contrat attendu et le statut de signature restent trois
    informations distinctes et non ambiguës (voir PHASE-2-REPORT.md § 0)."""

    opportunity_id: str
    client_id: str
    sales_owner_id: str
    stage: OpportunityStage
    expected_close_date: date
    expected_amount: float
    created_date: date


class ExpectedContract(BaseModel):
    """Le contrat attendu associé à une opportunité : porte le suivi de
    signature pour le scénario de clôture commerciale mensuelle."""

    expected_contract_id: str
    opportunity_id: str
    client_id: str
    sales_owner_id: str
    expected_close_date: date
    expected_amount: float
    signature_status: SignatureStatus
    created_date: date
