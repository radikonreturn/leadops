from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.schemas.offer import OfferResponse


class CampaignBase(BaseModel):
    name: str
    description: Optional[str] = None
    offer_id: Optional[int] = None
    status: str = "Active"
    target_industry: Optional[str] = None
    target_company_size: Optional[str] = None
    target_location: Optional[str] = None


class CampaignCreate(CampaignBase):
    pass


class CampaignResponse(CampaignBase):
    id: int
    created_at: datetime
    offer: Optional[OfferResponse] = None
    leads_count: int = 0
    qualified_count: int = 0
    contacted_count: int = 0
    replies_count: int = 0

    model_config = ConfigDict(from_attributes=True)
