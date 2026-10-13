from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class ProviderConnectionResponse(BaseModel):
    provider: str
    name: str
    connection_method: Optional[str] = None
    status: str
    status_message: Optional[str] = None
    selected_model: Optional[str] = None
    available_models: List[str] = []
    base_url: Optional[str] = None
    key_preview: Optional[str] = None
    supports_oauth: bool
    supports_api_key: bool
    is_oauth_configured: bool
    oauth_limitation: Optional[str] = None
    is_default: bool = False
    updated_at: Optional[datetime] = None


class ConnectAPIKeyRequest(BaseModel):
    api_key: str = Field(..., min_length=1, description="Provider API key")
    base_url: Optional[str] = Field(None, max_length=255)
    selected_model: Optional[str] = Field(None, max_length=100)


class ConnectLocalRequest(BaseModel):
    base_url: str = Field(default="http://localhost:11434", min_length=1, max_length=255)
    selected_model: Optional[str] = Field(None, max_length=100)


class UpdateModelRequest(BaseModel):
    selected_model: str = Field(..., min_length=1, max_length=100)


class TestConnectionRequest(BaseModel):
    api_key: Optional[str] = None
    base_url: Optional[str] = None


class TestConnectionResponse(BaseModel):
    success: bool
    message: str
    models: List[str] = []


class AISettingsResponse(BaseModel):
    default_provider: Optional[str] = None
    default_model: Optional[str] = None


class UpdateAISettingsRequest(BaseModel):
    default_provider: Optional[str] = None
    default_model: Optional[str] = None


class TestGenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=4000)
    provider: Optional[str] = None
    model: Optional[str] = None


class TestGenerateResponse(BaseModel):
    response: str
    provider: str
    model: str


class OAuthAuthorizeResponse(BaseModel):
    authorization_url: str
    state: str


class OAuthCallbackRequest(BaseModel):
    code: str = Field(..., min_length=1)
    state: str = Field(..., min_length=1)
