from enum import StrEnum

from pydantic import BaseModel, Field


class ConflictCategory(StrEnum):
    PAYMENT_TERMS = "PAYMENT_TERMS"
    PRICING = "PRICING"
    CONTRACT_DATES = "CONTRACT_DATES"
    SLA = "SLA"
    NOTICE_PERIOD = "NOTICE_PERIOD"
    RENEWAL = "RENEWAL"
    CUSTOMER_STATUS = "CUSTOMER_STATUS"


class ConflictRecord(BaseModel):
    conflict_id: str
    category: ConflictCategory
    field: str
    document_ids: list[str] = Field(default_factory=list)
    values_by_document: dict[str, object] = Field(default_factory=dict)
    ground_truth_value: object
    ground_truth_source_document_id: str
    resolution_rule: str
