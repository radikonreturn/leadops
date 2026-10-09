from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    offer_id = Column(Integer, ForeignKey("offers.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(50), default="Active")  # Active, Draft, Completed
    target_industry = Column(String(100), nullable=True)
    target_company_size = Column(String(100), nullable=True)
    target_location = Column(String(150), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    offer = relationship("Offer", back_populates="campaigns")
