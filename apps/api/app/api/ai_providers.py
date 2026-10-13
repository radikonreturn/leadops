import base64
from datetime import datetime, timedelta
import hashlib
import secrets
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    decrypt_credentials,
    encrypt_credentials,
    mask_api_key,
    sanitize_error_message,
)
from app.models.ai_connection import UserAIConnection, UserAISettings
from app.models.oauth_state import OAuthState
from app.models.user import User
from app.schemas.ai_provider import (
    AISettingsResponse,
    ConnectAPIKeyRequest,
    ConnectLocalRequest,
    OAuthAuthorizeResponse,
    OAuthCallbackRequest,
    ProviderConnectionResponse,
    TestConnectionRequest,
    TestConnectionResponse,
    TestGenerateRequest,
    TestGenerateResponse,
    UpdateAISettingsRequest,
    UpdateModelRequest,
)
from app.services.ai.registry import SUPPORTED_PROVIDERS, get_adapter, list_all_adapters

router = APIRouter(prefix="/api/ai", tags=["ai-providers"])


def _pkce_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("utf-8")


def _get_user_settings(db: Session, user_id: int) -> UserAISettings:
    user_settings = db.query(UserAISettings).filter(UserAISettings.user_id == user_id).first()
    if not user_settings:
        user_settings = UserAISettings(user_id=user_id)
        db.add(user_settings)
        db.commit()
        db.refresh(user_settings)
    return user_settings


@router.get("/providers", response_model=List[ProviderConnectionResponse])
def list_providers(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> List[ProviderConnectionResponse]:
    connections = {
        c.provider: c
        for c in db.query(UserAIConnection)
        .filter(UserAIConnection.user_id == current_user.id)
        .all()
    }
    user_settings = _get_user_settings(db, current_user.id)

    results: List[ProviderConnectionResponse] = []
    for adapter in list_all_adapters():
        p_name = adapter.provider_name
        conn = connections.get(p_name)
        is_default = (user_settings.default_provider == p_name)

        if conn:
            conn_status = conn.status
            if conn.token_expires_at and conn.token_expires_at < datetime.utcnow():
                conn_status = "expired"
            results.append(
                ProviderConnectionResponse(
                    provider=p_name,
                    name=adapter.display_name,
                    connection_method=conn.connection_method,
                    status=conn_status,
                    status_message=conn.status_message,
                    selected_model=conn.selected_model or adapter.get_default_model(),
                    available_models=conn.available_models or adapter.get_fallback_models(),
                    base_url=conn.base_url,
                    key_preview=conn.key_preview,
                    supports_oauth=adapter.supports_oauth(),
                    supports_api_key=adapter.supports_api_key(),
                    is_oauth_configured=adapter.is_oauth_configured(),
                    oauth_limitation=adapter.oauth_limitation(),
                    is_default=is_default,
                    updated_at=conn.updated_at,
                )
            )
        else:
            results.append(
                ProviderConnectionResponse(
                    provider=p_name,
                    name=adapter.display_name,
                    connection_method=None,
                    status="disconnected",
                    status_message=None,
                    selected_model=adapter.get_default_model(),
                    available_models=adapter.get_fallback_models(),
                    base_url=None,
                    key_preview=None,
                    supports_oauth=adapter.supports_oauth(),
                    supports_api_key=adapter.supports_api_key(),
                    is_oauth_configured=adapter.is_oauth_configured(),
                    oauth_limitation=adapter.oauth_limitation(),
                    is_default=is_default,
                    updated_at=None,
                )
            )

    return results


@router.post("/providers/{provider}/connect", response_model=ProviderConnectionResponse)
async def connect_provider(
    provider: str,
    payload: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProviderConnectionResponse:
    try:
        adapter = get_adapter(provider)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    p_name = adapter.provider_name
    credentials: Dict[str, Any] = {}
    base_url = payload.get("base_url")
    selected_model = payload.get("selected_model")

    if p_name == "ollama":
        base_url = (base_url or "http://localhost:11434").strip()
        credentials["base_url"] = base_url
        if payload.get("api_key"):
            credentials["api_key"] = payload["api_key"].strip()
        conn_method = "local"
        key_prev = None
    else:
        api_key = payload.get("api_key", "").strip()
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="API key is required to connect this provider.",
            )
        credentials["api_key"] = api_key
        if base_url:
            credentials["base_url"] = base_url.strip()
        conn_method = "api_key"
        key_prev = mask_api_key(api_key)

    # Test the connection before persisting
    success, err_msg = await adapter.test_connection(credentials, base_url)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=sanitize_error_message(err_msg or "Could not connect to provider with the provided credentials."),
        )

    # Discover models
    discovered_models = await adapter.list_models(credentials, base_url)
    if not selected_model:
        selected_model = adapter.get_default_model()

    encrypted = encrypt_credentials(credentials)

    conn = (
        db.query(UserAIConnection)
        .filter(UserAIConnection.user_id == current_user.id, UserAIConnection.provider == p_name)
        .first()
    )
    if not conn:
        conn = UserAIConnection(
            user_id=current_user.id,
            provider=p_name,
            connection_method=conn_method,
            status="connected",
            status_message=None,
            selected_model=selected_model,
            available_models=discovered_models,
            base_url=base_url,
            encrypted_credentials=encrypted,
            key_preview=key_prev,
            token_expires_at=None,
        )
        db.add(conn)
    else:
        conn.connection_method = conn_method
        conn.status = "connected"
        conn.status_message = None
        conn.selected_model = selected_model
        conn.available_models = discovered_models
        conn.base_url = base_url
        conn.encrypted_credentials = encrypted
        conn.key_preview = key_prev
        conn.token_expires_at = None
        conn.updated_at = datetime.utcnow()

    # Set as default if user has no default provider yet
    user_settings = _get_user_settings(db, current_user.id)
    if not user_settings.default_provider:
        user_settings.default_provider = p_name
        user_settings.default_model = selected_model

    db.commit()
    db.refresh(conn)

    return ProviderConnectionResponse(
        provider=p_name,
        name=adapter.display_name,
        connection_method=conn.connection_method,
        status=conn.status,
        status_message=conn.status_message,
        selected_model=conn.selected_model,
        available_models=conn.available_models or adapter.get_fallback_models(),
        base_url=conn.base_url,
        key_preview=conn.key_preview,
        supports_oauth=adapter.supports_oauth(),
        supports_api_key=adapter.supports_api_key(),
        is_oauth_configured=adapter.is_oauth_configured(),
        oauth_limitation=adapter.oauth_limitation(),
        is_default=(user_settings.default_provider == p_name),
        updated_at=conn.updated_at,
    )


@router.post("/providers/{provider}/test", response_model=TestConnectionResponse)
async def test_provider_connection(
    provider: str,
    payload: Optional[TestConnectionRequest] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TestConnectionResponse:
    try:
        adapter = get_adapter(provider)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    credentials: Dict[str, Any] = {}
    base_url = payload.base_url if payload else None

    # If test payload supplies api_key directly, test with that
    if payload and payload.api_key:
        credentials["api_key"] = payload.api_key.strip()
        if payload.base_url:
            credentials["base_url"] = payload.base_url.strip()
    else:
        # Otherwise test existing stored connection
        conn = (
            db.query(UserAIConnection)
            .filter(UserAIConnection.user_id == current_user.id, UserAIConnection.provider == adapter.provider_name)
            .first()
        )
        if not conn or not conn.encrypted_credentials:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{adapter.display_name} is not connected yet.",
            )
        try:
            credentials = decrypt_credentials(conn.encrypted_credentials)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not decrypt stored credentials.",
            )
        base_url = conn.base_url

    success, err = await adapter.test_connection(credentials, base_url)
    models: List[str] = []
    if success:
        models = await adapter.list_models(credentials, base_url)
        # If testing saved connection, update status in DB
        conn = (
            db.query(UserAIConnection)
            .filter(UserAIConnection.user_id == current_user.id, UserAIConnection.provider == adapter.provider_name)
            .first()
        )
        if conn:
            conn.status = "connected"
            conn.status_message = None
            if models:
                conn.available_models = models
            conn.updated_at = datetime.utcnow()
            db.commit()
        return TestConnectionResponse(
            success=True,
            message=f"Successfully connected to {adapter.display_name}.",
            models=models,
        )
    else:
        conn = (
            db.query(UserAIConnection)
            .filter(UserAIConnection.user_id == current_user.id, UserAIConnection.provider == adapter.provider_name)
            .first()
        )
        if conn:
            conn.status = "error"
            conn.status_message = err
            conn.updated_at = datetime.utcnow()
            db.commit()
        return TestConnectionResponse(
            success=False,
            message=err or f"Failed to connect to {adapter.display_name}.",
            models=[],
        )


@router.delete("/providers/{provider}", status_code=status.HTTP_204_NO_CONTENT)
async def disconnect_provider(
    provider: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    try:
        adapter = get_adapter(provider)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    conn = (
        db.query(UserAIConnection)
        .filter(UserAIConnection.user_id == current_user.id, UserAIConnection.provider == adapter.provider_name)
        .first()
    )
    if not conn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{adapter.display_name} connection not found.",
        )

    # Attempt upstream token revocation if OAuth
    if conn.connection_method == "oauth" and conn.encrypted_credentials:
        try:
            creds = decrypt_credentials(conn.encrypted_credentials)
            token_to_revoke = creds.get("refresh_token") or creds.get("access_token")
            if token_to_revoke:
                await adapter.revoke_oauth_token(token_to_revoke)
        except Exception:
            pass

    db.delete(conn)

    # If this was default provider, clear or switch default
    user_settings = _get_user_settings(db, current_user.id)
    if user_settings.default_provider == adapter.provider_name:
        other_conn = (
            db.query(UserAIConnection)
            .filter(UserAIConnection.user_id == current_user.id, UserAIConnection.provider != adapter.provider_name)
            .first()
        )
        if other_conn:
            user_settings.default_provider = other_conn.provider
            user_settings.default_model = other_conn.selected_model
        else:
            user_settings.default_provider = None
            user_settings.default_model = None

    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/providers/{provider}/model", response_model=ProviderConnectionResponse)
def update_provider_model(
    provider: str,
    payload: UpdateModelRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProviderConnectionResponse:
    try:
        adapter = get_adapter(provider)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    conn = (
        db.query(UserAIConnection)
        .filter(UserAIConnection.user_id == current_user.id, UserAIConnection.provider == adapter.provider_name)
        .first()
    )
    if not conn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{adapter.display_name} is not connected.",
        )

    conn.selected_model = payload.selected_model
    conn.updated_at = datetime.utcnow()

    user_settings = _get_user_settings(db, current_user.id)
    if user_settings.default_provider == adapter.provider_name:
        user_settings.default_model = payload.selected_model

    db.commit()
    db.refresh(conn)

    return ProviderConnectionResponse(
        provider=adapter.provider_name,
        name=adapter.display_name,
        connection_method=conn.connection_method,
        status=conn.status,
        status_message=conn.status_message,
        selected_model=conn.selected_model,
        available_models=conn.available_models or adapter.get_fallback_models(),
        base_url=conn.base_url,
        key_preview=conn.key_preview,
        supports_oauth=adapter.supports_oauth(),
        supports_api_key=adapter.supports_api_key(),
        is_oauth_configured=adapter.is_oauth_configured(),
        oauth_limitation=adapter.oauth_limitation(),
        is_default=(user_settings.default_provider == adapter.provider_name),
        updated_at=conn.updated_at,
    )


# --- OAuth Endpoints ---

@router.get("/providers/{provider}/oauth/authorize", response_model=OAuthAuthorizeResponse)
def authorize_oauth(
    provider: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OAuthAuthorizeResponse:
    try:
        adapter = get_adapter(provider)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    if not adapter.supports_oauth():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=adapter.oauth_limitation() or f"OAuth is not supported for {adapter.display_name}.",
        )

    if not adapter.is_oauth_configured():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=adapter.oauth_limitation() or f"OAuth credentials not configured for {adapter.display_name}.",
        )

    state = secrets.token_urlsafe(32)
    code_verifier = secrets.token_urlsafe(64)
    code_challenge = _pkce_challenge(code_verifier)
    redirect_uri = f"{settings.OAUTH_REDIRECT_BASE_URL.rstrip('/')}/settings/ai-providers/callback"

    # Store OAuth state for CSRF and PKCE validation
    oauth_state = OAuthState(
        user_id=current_user.id,
        provider=adapter.provider_name,
        state=state,
        code_verifier=code_verifier,
        redirect_uri=redirect_uri,
        expires_at=datetime.utcnow() + timedelta(minutes=10),
    )
    db.add(oauth_state)
    db.commit()

    auth_url = adapter.build_oauth_authorize_url(
        redirect_uri=redirect_uri, state=state, code_challenge=code_challenge
    )
    return OAuthAuthorizeResponse(authorization_url=auth_url, state=state)


@router.post("/providers/{provider}/oauth/callback", response_model=ProviderConnectionResponse)
async def oauth_callback(
    provider: str,
    payload: OAuthCallbackRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProviderConnectionResponse:
    try:
        adapter = get_adapter(provider)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    # Validate state and ensure it belongs to the current user
    oauth_state = (
        db.query(OAuthState)
        .filter(
            OAuthState.user_id == current_user.id,
            OAuthState.provider == adapter.provider_name,
            OAuthState.state == payload.state,
        )
        .first()
    )
    if not oauth_state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or unrecognized OAuth state parameter (CSRF protection).",
        )

    if oauth_state.expires_at < datetime.utcnow():
        db.delete(oauth_state)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OAuth authorization request has expired. Please try connecting again.",
        )

    # Exchange code for tokens
    try:
        tokens = await adapter.exchange_oauth_code(
            code=payload.code,
            redirect_uri=oauth_state.redirect_uri,
            code_verifier=oauth_state.code_verifier,
        )
    except Exception as exc:
        db.delete(oauth_state)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=sanitize_error_message(f"OAuth exchange failed: {str(exc)}"),
        )

    # Clean up state
    db.delete(oauth_state)

    # Discover models with new credentials
    discovered_models = await adapter.list_models(tokens)
    encrypted = encrypt_credentials(tokens)
    token_exp = None
    if tokens.get("expires_at"):
        try:
            token_exp = datetime.fromisoformat(tokens["expires_at"])
        except Exception:
            pass

    key_preview = None
    if tokens.get("api_key"):
        key_preview = mask_api_key(tokens["api_key"])
    elif tokens.get("access_token"):
        key_preview = f"oauth-{adapter.provider_name[:4]}"

    conn = (
        db.query(UserAIConnection)
        .filter(UserAIConnection.user_id == current_user.id, UserAIConnection.provider == adapter.provider_name)
        .first()
    )
    if not conn:
        conn = UserAIConnection(
            user_id=current_user.id,
            provider=adapter.provider_name,
            connection_method="oauth",
            status="connected",
            status_message=None,
            selected_model=adapter.get_default_model(),
            available_models=discovered_models,
            base_url=None,
            encrypted_credentials=encrypted,
            key_preview=key_preview,
            token_expires_at=token_exp,
        )
        db.add(conn)
    else:
        conn.connection_method = "oauth"
        conn.status = "connected"
        conn.status_message = None
        conn.selected_model = conn.selected_model or adapter.get_default_model()
        conn.available_models = discovered_models
        conn.encrypted_credentials = encrypted
        conn.key_preview = key_preview
        conn.token_expires_at = token_exp
        conn.updated_at = datetime.utcnow()

    user_settings = _get_user_settings(db, current_user.id)
    if not user_settings.default_provider:
        user_settings.default_provider = adapter.provider_name
        user_settings.default_model = conn.selected_model

    db.commit()
    db.refresh(conn)

    return ProviderConnectionResponse(
        provider=adapter.provider_name,
        name=adapter.display_name,
        connection_method=conn.connection_method,
        status=conn.status,
        status_message=conn.status_message,
        selected_model=conn.selected_model,
        available_models=conn.available_models or adapter.get_fallback_models(),
        base_url=conn.base_url,
        key_preview=conn.key_preview,
        supports_oauth=adapter.supports_oauth(),
        supports_api_key=adapter.supports_api_key(),
        is_oauth_configured=adapter.is_oauth_configured(),
        oauth_limitation=adapter.oauth_limitation(),
        is_default=(user_settings.default_provider == adapter.provider_name),
        updated_at=conn.updated_at,
    )


# --- Settings & Test Generation ---

@router.get("/settings", response_model=AISettingsResponse)
def get_ai_settings(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> AISettingsResponse:
    user_settings = _get_user_settings(db, current_user.id)
    return AISettingsResponse(
        default_provider=user_settings.default_provider,
        default_model=user_settings.default_model,
    )


@router.patch("/settings", response_model=AISettingsResponse)
def update_ai_settings(
    payload: UpdateAISettingsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AISettingsResponse:
    user_settings = _get_user_settings(db, current_user.id)

    if payload.default_provider is not None:
        if payload.default_provider:
            # Validate provider exists and user has connected it
            try:
                adapter = get_adapter(payload.default_provider)
            except ValueError as exc:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
            conn = (
                db.query(UserAIConnection)
                .filter(UserAIConnection.user_id == current_user.id, UserAIConnection.provider == adapter.provider_name)
                .first()
            )
            if not conn or conn.status != "connected":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot set {adapter.display_name} as default because it is not connected.",
                )
            user_settings.default_provider = adapter.provider_name
            if not payload.default_model:
                user_settings.default_model = conn.selected_model or adapter.get_default_model()
        else:
            user_settings.default_provider = None
            user_settings.default_model = None

    if payload.default_model is not None and user_settings.default_provider:
        user_settings.default_model = payload.default_model

    user_settings.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user_settings)

    return AISettingsResponse(
        default_provider=user_settings.default_provider,
        default_model=user_settings.default_model,
    )


@router.post("/test-generate", response_model=TestGenerateResponse)
async def test_generate_text(
    payload: TestGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TestGenerateResponse:
    user_settings = _get_user_settings(db, current_user.id)
    provider_name = payload.provider or user_settings.default_provider

    if not provider_name:
        # Fallback to any connected provider
        first_conn = (
            db.query(UserAIConnection)
            .filter(UserAIConnection.user_id == current_user.id, UserAIConnection.status == "connected")
            .first()
        )
        if first_conn:
            provider_name = first_conn.provider

    if not provider_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No AI provider is connected. Please connect a provider first.",
        )

    try:
        adapter = get_adapter(provider_name)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    conn = (
        db.query(UserAIConnection)
        .filter(UserAIConnection.user_id == current_user.id, UserAIConnection.provider == adapter.provider_name)
        .first()
    )
    if not conn or not conn.encrypted_credentials:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{adapter.display_name} is not connected.",
        )

    try:
        credentials = decrypt_credentials(conn.encrypted_credentials)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not decrypt stored credentials.",
        )

    model = payload.model or conn.selected_model or adapter.get_default_model()

    try:
        text = await adapter.generate_text(
            prompt=payload.prompt,
            model=model,
            credentials=credentials,
            base_url=conn.base_url,
        )
        return TestGenerateResponse(
            response=text,
            provider=adapter.provider_name,
            model=model,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=sanitize_error_message(f"Generation error: {str(exc)}"),
        )
