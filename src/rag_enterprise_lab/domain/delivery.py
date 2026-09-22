from datetime import date
from enum import StrEnum

from pydantic import BaseModel, Field


class ProjectStatus(StrEnum):
    ACTIVE = "ACTIVE"
    DELIVERED = "DELIVERED"
    ON_HOLD = "ON_HOLD"
    CANCELLED = "CANCELLED"


class Project(BaseModel):
    project_id: str
    project_code: str
    name: str
    client_id: str
    status: ProjectStatus
    delivery_lead_id: str
    team_member_ids: list[str] = Field(default_factory=list)
    start_date: date
