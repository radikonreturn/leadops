from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    website = Column(String(255), nullable=False)
    contact_name = Column(String(150), nullable=False, default="")
    industry = Column(String(100), nullable=False, index=True)
    location = Column(String(150), nullable=True, index=True)
    employee_range = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    leads = relationship("Lead", back_populates="company", cascade="all, delete-orphan")
