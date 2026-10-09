from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict
from app.schemas.company import CompanyResponse, CompanyCreate
from app.schemas.offer import OfferResponse
from app.schemas.ai import AIAnalysisResponse
from app.schemas.email import EmailResponse


class ActivityResponse(BaseModel):
    id: int
    lead_id: int
    type: str
    description: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LeadBase(BaseModel):
    fit_score: int = 0
    opportunity_score: int = 0
    status: str = "New"
    source: str = "Manual"
    recommended_offer_id: Optional[int] = None
    notes: Optional[str] = None


class LeadCreate(BaseModel):
    company: CompanyCreate
    source: str = "Manual"
    recommended_offer_id: Optional[int] = None
    notes: Optional[str] = None


class LeadUpdate(BaseModel):
    fit_score: Optional[int] = None
    opportunity_score: Optional[int] = None
    status: Optional[str] = None
    recommended_offer_id: Optional[int] = None
    notes: Optional[str] = None
    score_breakdown: Optional[Dict[str, Any]] = None


class LeadStatusUpdate(BaseModel):
    status: str


class LeadResponse(BaseModel):
    id: int
    company_id: int
    fit_score: int
    opportunity_score: int
    status: str
    source: str
    recommended_offer_id: Optional[int] = None
    score_breakdown: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    company: CompanyResponse
    recommended_offer: Optional[OfferResponse] = None

    model_config = ConfigDict(from_attributes=True)


class LeadDetailResponse(LeadResponse):
    ai_analysis: Optional[AIAnalysisResponse] = None
    emails: List[EmailResponse] = []
    activities: List[ActivityResponse] = []

    model_config = ConfigDict(from_attributes=True)
