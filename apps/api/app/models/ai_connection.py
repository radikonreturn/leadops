from datetime import datetime
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class UserAIConnection(Base):
    __tablename__ = "user_ai_connections"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    provider = Column(String(50), nullable=False)  # openai, gemini, anthropic, openrouter, ollama
    connection_method = Column(String(20), nullable=False, default="api_key")  # api_key, oauth, local
    status = Column(String(20), nullable=False, default="connected")  # connected, error, expired, disconnected
    status_message = Column(Text, nullable=True)
    selected_model = Column(String(100), nullable=True)
    available_models = Column(JSON, nullable=True)
    base_url = Column(String(255), nullable=True)
    encrypted_credentials = Column(Text, nullable=True)
    key_preview = Column(String(30), nullable=True)
    token_expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User", backref="ai_connections")

    __table_args__ = (
        UniqueConstraint("user_id", "provider", name="uq_user_ai_provider"),
    )


class UserAISettings(Base):
    __tablename__ = "user_ai_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    default_provider = Column(String(50), nullable=True)
    default_model = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User", backref="ai_settings", uselist=False)
