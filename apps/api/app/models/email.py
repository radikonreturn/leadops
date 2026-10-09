from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class Email(Base):
    __tablename__ = "emails"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)
    
    recipient_email = Column(String(255), nullable=True)
    subject = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    style = Column(String(50), default="Professional")    # Professional, Friendly, Direct
    status = Column(String(50), default="Draft", index=True) # Draft, Approved, Sent, Replied
    why_generated = Column(Text, nullable=True)           # Strategic explanation of why this hook/offer was chosen
    external_draft_id = Column(String(255), nullable=True)# For Gmail or external email client draft linkage
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    lead = relationship("Lead", back_populates="emails")
