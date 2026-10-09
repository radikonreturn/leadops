from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    fit_score = Column(Integer, default=0)              # 0 - 100
    opportunity_score = Column(Integer, default=0)        # 0 - 100
    status = Column(String(50), default="New", index=True) 
    # Stages: New, Researched, Qualified, Contacted, Replied, Meeting, Proposal, Won, Lost
    source = Column(String(50), default="Manual")        # Manual, Search, Directory
    recommended_offer_id = Column(Integer, ForeignKey("offers.id", ondelete="SET NULL"), nullable=True)
    score_breakdown = Column(JSON, default=dict)        # { "industry_match": { "score": 25, "max": 25, "reason": "..." }, ... }
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    company = relationship("Company", back_populates="leads")
    recommended_offer = relationship("Offer", back_populates="leads")
    ai_analysis = relationship("AIAnalysis", back_populates="lead", uselist=False, cascade="all, delete-orphan")
    emails = relationship("Email", back_populates="lead", cascade="all, delete-orphan")
    activities = relationship("Activity", back_populates="lead", cascade="all, delete-orphan")
