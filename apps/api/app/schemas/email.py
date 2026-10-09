from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class EmailBase(BaseModel):
    subject: str
    body: str
    style: str = "Professional"
    recipient_email: Optional[str] = None
    why_generated: Optional[str] = None


class EmailCreate(EmailBase):
    lead_id: int


class EmailUpdate(BaseModel):
    subject: Optional[str] = None
    body: Optional[str] = None
    style: Optional[str] = None
    status: Optional[str] = None
    recipient_email: Optional[str] = None


class GenerateEmailRequest(BaseModel):
    style: str = "Professional"  # Professional, Friendly, Direct
    custom_instructions: Optional[str] = None
    offer_id: Optional[int] = None


class EmailResponse(EmailBase):
    id: int
    lead_id: int
    status: str
    external_draft_id: Optional[str] = None
    sent_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
