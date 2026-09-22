from enum import StrEnum

from pydantic import BaseModel, Field


class Department(StrEnum):
    DIRECTION = "Direction"
    SALES_ACCOUNT = "Sales / Account"
    CONSULTING = "Consulting"
    DATA_AI = "Data & AI"
    ENGINEERING = "Engineering"
    IT_CYBERSECURITY = "IT / Cybersecurity"
    HR = "RH"
    FINANCE_LEGAL = "Finance / Legal"
    MARKETING_PARTNERSHIPS = "Marketing / Partnerships"


class BusinessUnit(StrEnum):
    CORPORATE = "Corporate"
    GO_TO_MARKET = "Go-To-Market"
    DELIVERY = "Delivery"


class EmploymentType(StrEnum):
    CDI = "CDI"
    CDD = "CDD"
    FREELANCE = "FREELANCE"
    APPRENTICESHIP = "APPRENTICESHIP"


class SeniorityLevel(StrEnum):
    JUNIOR = "JUNIOR"
    CONFIRMED = "CONFIRMED"
    SENIOR = "SENIOR"
    LEAD = "LEAD"
    HEAD = "HEAD"
    EXECUTIVE = "EXECUTIVE"


class Clearance(StrEnum):
    STANDARD = "STANDARD"
    ELEVATED = "ELEVATED"
    EXECUTIVE = "EXECUTIVE"


CLEARANCE_RANK: dict[Clearance, int] = {
    Clearance.STANDARD: 0,
    Clearance.ELEVATED: 1,
    Clearance.EXECUTIVE: 2,
}

# Effectifs exacts (source : demande Phase 1). Somme = 120.
DEPARTMENT_HEADCOUNT: dict[Department, int] = {
    Department.DIRECTION: 6,
    Department.SALES_ACCOUNT: 18,
    Department.CONSULTING: 34,
    Department.DATA_AI: 20,
    Department.ENGINEERING: 16,
    Department.IT_CYBERSECURITY: 8,
    Department.HR: 7,
    Department.FINANCE_LEGAL: 7,
    Department.MARKETING_PARTNERSHIPS: 4,
}

DEPARTMENT_BUSINESS_UNIT: dict[Department, BusinessUnit] = {
    Department.DIRECTION: BusinessUnit.CORPORATE,
    Department.HR: BusinessUnit.CORPORATE,
    Department.FINANCE_LEGAL: BusinessUnit.CORPORATE,
    Department.SALES_ACCOUNT: BusinessUnit.GO_TO_MARKET,
    Department.MARKETING_PARTNERSHIPS: BusinessUnit.GO_TO_MARKET,
    Department.CONSULTING: BusinessUnit.DELIVERY,
    Department.DATA_AI: BusinessUnit.DELIVERY,
    Department.ENGINEERING: BusinessUnit.DELIVERY,
    Department.IT_CYBERSECURITY: BusinessUnit.DELIVERY,
}


class Employee(BaseModel):
    employee_id: str
    first_name: str
    last_name: str
    corporate_email: str
    department: Department
    business_unit: BusinessUnit
    job_title: str
    manager_id: str | None = None
    location: str
    employment_type: EmploymentType
    seniority_level: SeniorityLevel
    active: bool = True
    security_groups: list[str] = Field(default_factory=list)
    identity_roles: list[str] = Field(default_factory=list)
    clearance: Clearance = Clearance.STANDARD
    project_memberships: list[str] = Field(default_factory=list)
    client_memberships: list[str] = Field(default_factory=list)
