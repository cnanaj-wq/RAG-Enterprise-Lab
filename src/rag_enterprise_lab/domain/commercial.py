from datetime import date
from enum import StrEnum

from pydantic import BaseModel


class Segment(StrEnum):
    SMB = "SMB"
    MID_MARKET = "MID_MARKET"
    ENTERPRISE = "ENTERPRISE"
    STRATEGIC = "STRATEGIC"


class RiskLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ClientStatus(StrEnum):
    ACTIVE = "ACTIVE"
    AT_RISK = "AT_RISK"
    CHURNED = "CHURNED"


class ProspectStatus(StrEnum):
    NEW = "NEW"
    QUALIFIED = "QUALIFIED"
    IN_DISCUSSION = "IN_DISCUSSION"
    LOST = "LOST"


class PartnerType(StrEnum):
    TECHNOLOGY = "TECHNOLOGY"
    RESELLER = "RESELLER"
    INTEGRATOR = "INTEGRATOR"
    ALLIANCE = "ALLIANCE"


class SupplierCategory(StrEnum):
    CLOUD_INFRASTRUCTURE = "CLOUD_INFRASTRUCTURE"
    SOFTWARE_LICENSE = "SOFTWARE_LICENSE"
    FACILITIES = "FACILITIES"
    CONSULTING_SUBCONTRACTOR = "CONSULTING_SUBCONTRACTOR"
    LEGAL_SERVICES = "LEGAL_SERVICES"
    HR_SERVICES = "HR_SERVICES"
    MARKETING_SERVICES = "MARKETING_SERVICES"
    HARDWARE = "HARDWARE"


class Client(BaseModel):
    customer_id: str
    client_code: str
    name: str
    industry: str
    segment: Segment
    account_manager_id: str
    sales_manager_id: str
    status: ClientStatus = ClientStatus.ACTIVE
    risk_level: RiskLevel
    creation_date: date


class Prospect(BaseModel):
    prospect_id: str
    name: str
    industry: str
    segment: Segment
    owner_id: str
    status: ProspectStatus
    creation_date: date


class Partner(BaseModel):
    partner_id: str
    name: str
    partner_type: PartnerType
    country: str
    creation_date: date


class Supplier(BaseModel):
    supplier_id: str
    name: str
    category: SupplierCategory
    country: str
    criticality: RiskLevel
    creation_date: date
