from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, HttpUrl, field_validator


LEAD_STATUSES = ("New", "Qualified", "Contacted", "Replied", "Won", "Lost")
LeadStatus = Literal["New", "Qualified", "Contacted", "Replied", "Won", "Lost"]


class LeadPayload(BaseModel):
    company_name: str
    website: HttpUrl
    contact_name: str
    email: Optional[EmailStr] = None
    industry: str
    source: str = "Manual"
    status: LeadStatus = "New"
    notes: Optional[str] = None

    @field_validator("company_name", "contact_name", "industry", "source")
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field is required.")
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
    status: Optional[LeadStatus] = None
    notes: Optional[str] = None

    @field_validator("company_name", "contact_name", "industry", "source")
    @classmethod
    def require_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("This field is required.")
        return value


class LeadStatusUpdate(BaseModel):
    status: LeadStatus


class LeadResponse(BaseModel):
    id: int
    company_name: str
    website: str
    contact_name: str
    email: Optional[str] = None
    industry: str
    source: str
    status: LeadStatus
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
