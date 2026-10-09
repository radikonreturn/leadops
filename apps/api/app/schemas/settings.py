from typing import Optional, Dict, Any
from pydantic import BaseModel


class SystemSettingsResponse(BaseModel):
    ai_provider: str
    openai_configured: bool
    openai_model: str
    gemini_configured: bool
    gemini_model: str
    anthropic_configured: bool
    anthropic_model: str
    ollama_base_url: str
    ollama_model: str
    default_email_style: str
    user_name: str
    user_role: str
    default_sender_name: str
    gmail_integrated: bool = False
    monthly_requests_used: int = 1240
    monthly_requests_limit: int = 5000


class SystemSettingsUpdate(BaseModel):
    ai_provider: Optional[str] = None
    openai_api_key: Optional[str] = None
    openai_model: Optional[str] = None
    gemini_api_key: Optional[str] = None
    gemini_model: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    anthropic_model: Optional[str] = None
    ollama_base_url: Optional[str] = None
    ollama_model: Optional[str] = None
    default_email_style: Optional[str] = None
    user_name: Optional[str] = None
    user_role: Optional[str] = None
    default_sender_name: Optional[str] = None
