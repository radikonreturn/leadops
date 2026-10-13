import base64
import hashlib
import json
import re
from typing import Any, Dict
from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


def _get_fernet() -> Fernet:
    """Derive a valid 32-byte urlsafe base64 Fernet key from settings.ENCRYPTION_KEY."""
    raw_key = getattr(settings, "ENCRYPTION_KEY", "leadops-default-insecure-dev-encryption-key-change-me")
    if isinstance(raw_key, str):
        raw_key = raw_key.encode("utf-8")

    # If it is already a valid 32-byte base64-encoded key, use it directly
    try:
        if len(base64.urlsafe_b64decode(raw_key)) == 32:
            return Fernet(raw_key)
    except Exception:
        pass

    # Otherwise, derive a 32-byte key via SHA-256
    derived = base64.urlsafe_b64encode(hashlib.sha256(raw_key).digest())
    return Fernet(derived)


def encrypt_credentials(payload: Dict[str, Any]) -> str:
    """Encrypt a dictionary of credentials (e.g., API key, OAuth tokens) at rest."""
    fernet = _get_fernet()
    data = json.dumps(payload).encode("utf-8")
    return fernet.encrypt(data).decode("utf-8")


def decrypt_credentials(encrypted_text: str) -> Dict[str, Any]:
    """Decrypt a ciphertext back into a dictionary of credentials."""
    fernet = _get_fernet()
    try:
        decrypted = fernet.decrypt(encrypted_text.encode("utf-8"))
        return json.loads(decrypted.decode("utf-8"))
    except (InvalidToken, ValueError, json.JSONDecodeError) as exc:
        raise ValueError("Could not decrypt stored credentials.") from exc


def mask_api_key(key: str) -> str:
    """Mask an API key for safe UI display (e.g., 'sk-...1a2b'). Never returns the full key."""
    if not key:
        return ""
    key = key.strip()
    if len(key) <= 8:
        return "••••••••"
    prefix = key[:3] if key.startswith("sk-") else key[:2]
    suffix = key[-4:]
    return f"{prefix}...{suffix}"


_SECRET_PATTERNS = [
    re.compile(r"sk-[a-zA-Z0-9_\-]{8,}", re.IGNORECASE),
    re.compile(r"AIza[a-zA-Z0-9_\-]{20,}", re.IGNORECASE),
    re.compile(r"Bearer\s+[a-zA-Z0-9_\-\.]{15,}", re.IGNORECASE),
    re.compile(r"key=[a-zA-Z0-9_\-]{15,}", re.IGNORECASE),
    re.compile(r"ghp_[a-zA-Z0-9]{20,}", re.IGNORECASE),
]


def sanitize_error_message(message: str) -> str:
    """Scrub sensitive credentials, tokens, and authorization headers from error messages."""
    if not message:
        return ""
    cleaned = message
    for pattern in _SECRET_PATTERNS:
        cleaned = pattern.sub("[REDACTED]", cleaned)
    return cleaned
