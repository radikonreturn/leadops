from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


class AIAnalysis(Base):
    __tablename__ = "ai_analyses"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    company_summary = Column(Text, nullable=False)
    observed_facts = Column(JSON, default=list)            # List of factual bullet points with evidence
    inferred_pain_points = Column(JSON, default=list)      # Likely pain points (explicitly tagged as inference)
    automation_opportunities = Column(JSON, default=list)  # Automation & software opportunities
    sales_angle = Column(Text, nullable=False)             # Best positioning angle for outreach
    confidence = Column(String(50), default="High")        # High, Medium, Low, or Insufficient Evidence
    fit_score = Column(Integer, default=0)
    opportunity_score = Column(Integer, default=0)
    raw_output = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    lead = relationship("Lead", back_populates="ai_analysis")
