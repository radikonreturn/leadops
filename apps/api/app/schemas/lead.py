from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, HttpUrl, field_validator


LEAD_STATUSES = {"New", "Qualified", "Contacted", "Replied", "Won", "Lost"}


class LeadPayload(BaseModel):
    company_name: str
    website: HttpUrl
    contact_name: str
    email: Optional[EmailStr] = None
    industry: str
    source: str = "Manual"
    status: str = "New"
    notes: Optional[str] = None

    @field_validator("company_name", "contact_name", "industry")
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field is required.")
        return value

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        if value not in LEAD_STATUSES:
            raise ValueError(f"Status must be one of: {', '.join(sorted(LEAD_STATUSES))}.")
        return value


class LeadCreate(LeadPayload):
    pass


class LeadUpdate(BaseModel):
    company_name: Optional[str] = None
    website: Optional[HttpUrl] = None
    contact_name: Optional[str] = None
    email: Optional[EmailStr] = None
    industry: Optional[str] = None
    source: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and value not in LEAD_STATUSES:
            raise ValueError(f"Status must be one of: {', '.join(sorted(LEAD_STATUSES))}.")
        return value


class LeadStatusUpdate(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        if value not in LEAD_STATUSES:
            raise ValueError(f"Status must be one of: {', '.join(sorted(LEAD_STATUSES))}.")
        return value


class LeadResponse(BaseModel):
    id: int
    company_name: str
    website: str
    contact_name: str
    email: Optional[str] = None
    industry: str
    source: str
    status: str
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LeadListResponse(BaseModel):
    items: List[LeadResponse]
    industries: List[str]


class DashboardSummary(BaseModel):
    total_leads: int
    new_leads: int
    qualified_prospects: int
    follow_ups_pending: int
    recent_leads: List[LeadResponse]
