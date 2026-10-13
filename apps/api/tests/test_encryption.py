import pytest
from app.core.security import (
    decrypt_credentials,
    encrypt_credentials,
    mask_api_key,
    sanitize_error_message,
)


def test_encryption_and_decryption_roundtrip():
    payload = {
        "api_key": "sk-proj-1234567890abcdef1234567890",
        "access_token": "ya29.a0AfH6SMDIEXAMPLE",
        "base_url": "https://custom.endpoint.com/v1",
    }
    encrypted = encrypt_credentials(payload)
    assert isinstance(encrypted, str)
    assert "sk-proj" not in encrypted
    assert "ya29" not in encrypted

    decrypted = decrypt_credentials(encrypted)
    assert decrypted == payload


def test_decrypt_invalid_ciphertext_raises_error():
    with pytest.raises(ValueError, match="Could not decrypt"):
        decrypt_credentials("invalid-tampered-ciphertext")


def test_api_key_masking():
    assert mask_api_key("") == ""
    assert mask_api_key("short") == "••••••••"
    # Standard OpenAI key
    masked_openai = mask_api_key("sk-1234567890abcdef")
    assert masked_openai.startswith("sk-...")
    assert masked_openai.endswith("cdef")
    assert "1234567890ab" not in masked_openai

    # Gemini key
    masked_gemini = mask_api_key("AIzaSyD-1234567890abcdef")
    assert masked_gemini.startswith("AI...")
    assert masked_gemini.endswith("cdef")
    assert "1234567890ab" not in masked_gemini


def test_sanitize_error_message_strips_secrets():
    err_msg = "Error 401: Invalid key sk-abcdef1234567890123456 for model gpt-4o"
    sanitized = sanitize_error_message(err_msg)
    assert "sk-abcdef" not in sanitized
    assert "[REDACTED]" in sanitized

    bearer_err = "Unauthorized Bearer ya29.a0AfH6SMDILONGSECRETTOKEN provided"
    sanitized_bearer = sanitize_error_message(bearer_err)
    assert "ya29" not in sanitized_bearer
    assert "[REDACTED]" in sanitized_bearer
