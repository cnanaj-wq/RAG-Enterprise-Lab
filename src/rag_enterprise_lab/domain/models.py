from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class Classification(StrEnum):
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    CONFIDENTIAL = "CONFIDENTIAL"
    RESTRICTED = "RESTRICTED"
    PERSONAL_DATA = "PERSONAL_DATA"
    SENSITIVE_PERSONAL_DATA = "SENSITIVE_PERSONAL_DATA"

class DocumentStatus(StrEnum):
    DRAFT = "DRAFT"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    SIGNED = "SIGNED"
    SUPERSEDED = "SUPERSEDED"
    EXPIRED = "EXPIRED"
    QUARANTINED = "QUARANTINED"

class DocumentRecord(BaseModel):
    document_id: str
    title: str
    document_type: str
    version: str
    status: DocumentStatus
    owner: str
    classification: Classification
    source_system: str
    allowed_groups: list[str] = Field(default_factory=list)
    valid_from: date | None = None
    valid_to: date | None = None
    supersedes: str | None = None
    contains_personal_data: bool = False
    checksum: str | None = None
    ingestion_date: datetime | None = None

class UserContext(BaseModel):
    user_id: str
    department: str | None = None
    groups: list[str] = Field(default_factory=list)
    attributes: dict[str, str] = Field(default_factory=dict)

class AccessDecision(BaseModel):
    allowed: bool
    reason: str
    matched_groups: list[str] = Field(default_factory=list)
