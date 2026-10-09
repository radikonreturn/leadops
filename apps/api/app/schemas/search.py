from typing import List, Optional
from pydantic import BaseModel


class LeadSearchQuery(BaseModel):
    query: str
    industry: Optional[str] = None
    location: Optional[str] = "Türkiye"
    company_size: Optional[str] = None
    limit: int = 10
    source_type: str = "search"  # manual, search, directory


class LeadDiscoveryResult(BaseModel):
    name: str
    website: str
    industry: str
    location: str
    employee_range: str
    description: str
    email: Optional[str] = None
    phone: Optional[str] = None
    estimated_fit_score: int
    relevance_reason: str
    matched_offer_title: Optional[str] = None
