import base64
import hashlib
import hmac
import json
import time
from typing import Any, Dict, Optional

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def _b64url_decode(data: str) -> bytes:
    padding = 4 - (len(data) % 4)
    if padding != 4:
        data += "=" * padding
    return base64.urlsafe_b64decode(data.encode("utf-8"))


def create_access_token(user_id: int, email: str, expires_in_seconds: int = 86400 * 30) -> str:
    """Create a signed HMAC-SHA256 session token for a user."""
    secret = settings.SECRET_KEY.encode("utf-8")
    payload = {
        "sub": user_id,
        "email": email,
        "exp": int(time.time()) + expires_in_seconds,
    }
    payload_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    encoded_payload = _b64url_encode(payload_bytes)
    signature = hmac.new(secret, encoded_payload.encode("utf-8"), hashlib.sha256).digest()
    encoded_signature = _b64url_encode(signature)
    return f"{encoded_payload}.{encoded_signature}"


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify and decode a signed session token. Returns payload dict or None."""
    if not token or "." not in token:
        return None
    try:
        encoded_payload, encoded_signature = token.split(".", 1)
        secret = settings.SECRET_KEY.encode("utf-8")
        expected_sig = hmac.new(secret, encoded_payload.encode("utf-8"), hashlib.sha256).digest()
        actual_sig = _b64url_decode(encoded_signature)
        if not hmac.compare_digest(expected_sig, actual_sig):
            return None
        payload_bytes = _b64url_decode(encoded_payload)
        payload = json.loads(payload_bytes.decode("utf-8"))
        if payload.get("exp", 0) < int(time.time()):
            return None
        return payload
    except Exception:
        return None


def get_or_create_default_user(db: Session) -> User:
    """Bootstrap the default local workspace user if no users exist."""
    user = db.query(User).first()
    if user is None:
        user = User(
            email="manager@leadops.local",
            name=getattr(settings, "USER_NAME", "Lead Manager"),
            role=getattr(settings, "USER_ROLE", "Lead manager"),
            plan="Pro Plan",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def get_current_user(
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
    x_auth_token: Optional[str] = Header(default=None, alias="X-Auth-Token"),
) -> User:
    """Derive authenticated user from bearer token or header. Rejects unauthorized requests."""
    token = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    elif x_auth_token:
        token = x_auth_token.strip()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.get(User, payload["sub"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User associated with this token was not found.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def get_current_user_optional(
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
    x_auth_token: Optional[str] = Header(default=None, alias="X-Auth-Token"),
) -> User:
    """Authenticate existing token, or bootstrap the default user in local development."""
    token = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    elif x_auth_token:
        token = x_auth_token.strip()

    if token:
        payload = decode_access_token(token)
        if payload and "sub" in payload:
            user = db.get(User, payload["sub"])
            if user:
                return user

    # Fallback to local default workspace user
    return get_or_create_default_user(db)
