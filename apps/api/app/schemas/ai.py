from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict


class ScoreMetric(BaseModel):
    label: str
    label_tr: Optional[str] = None
    score: int
    max_score: int
    reason: str


class FitScoreBreakdown(BaseModel):
    industry_match: ScoreMetric
    company_size: ScoreMetric
    digital_opportunity: ScoreMetric
    website_signals: ScoreMetric
    contactability: ScoreMetric
    portfolio_match: ScoreMetric


class AIAnalysisResponse(BaseModel):
    id: int
    lead_id: int
    company_summary: str
    observed_facts: List[str] = []
    inferred_pain_points: List[str] = []
    automation_opportunities: List[str] = []
    sales_angle: str
    confidence: str
    fit_score: int
    opportunity_score: int
    raw_output: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WebsiteResearchResult(BaseModel):
    url: str
    pages_scraped: List[str] = []
    page_count: int
    cleaned_text: str
    facts_detected: List[str] = []
    technologies_detected: List[str] = []
    status: str
