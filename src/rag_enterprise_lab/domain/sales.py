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


class Opportunity(BaseModel):
    opportunity_id: str
    client_id: str
    sales_owner_id: str
    expected_close_date: date
    expected_amount: float
    signature_status: SignatureStatus
    created_date: date
