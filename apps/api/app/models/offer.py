from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


class Offer(Base):
    __tablename__ = "offers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    target_industries = Column(JSON, default=list)  # ["Manufacturing", "Automotive", "Packaging"]
    problems_solved = Column(JSON, default=list)    # ["Manual Excel reporting", "OEE visibility"]
    price_min = Column(Float, nullable=False, default=0.0)
    price_max = Column(Float, nullable=False, default=0.0)
    currency = Column(String(10), default="TRY")
    keywords = Column(JSON, default=list)           # ["dashboard", "oee", "reporting"]
    created_at = Column(DateTime, default=datetime.utcnow)

    leads = relationship("Lead", back_populates="recommended_offer")
    campaigns = relationship("Campaign", back_populates="offer")
