from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class OfferBase(BaseModel):
    name: str
    description: str
    target_industries: List[str] = []
    problems_solved: List[str] = []
    price_min: float = 0.0
    price_max: float = 0.0
    currency: str = "TRY"
    keywords: List[str] = []


class OfferCreate(OfferBase):
    pass


class OfferUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    target_industries: Optional[List[str]] = None
    problems_solved: Optional[List[str]] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    currency: Optional[str] = None
    keywords: Optional[List[str]] = None


class OfferResponse(OfferBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
