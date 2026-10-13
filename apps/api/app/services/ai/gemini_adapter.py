from datetime import datetime, timedelta
import time
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode
import httpx

from app.core.config import settings
from app.core.security import sanitize_error_message
from app.services.ai.base import BaseAIAdapter


class GeminiAdapter(BaseAIAdapter):
    provider_name = "gemini"
    display_name = "Google Gemini"

    def supports_oauth(self) -> bool:
        return True

    def supports_api_key(self) -> bool:
        return True

    def is_oauth_configured(self) -> bool:
        return bool(settings.GOOGLE_OAUTH_CLIENT_ID and settings.GOOGLE_OAUTH_CLIENT_SECRET)

    def get_default_model(self) -> str:
        return "gemini-1.5-flash"

    def get_fallback_models(self) -> List[str]:
        return ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash", "gemini-1.0-pro"]

    def build_oauth_authorize_url(
        self, redirect_uri: str, state: str, code_challenge: Optional[str] = None
    ) -> str:
        if not self.is_oauth_configured():
            raise ValueError(
                "Google OAuth credentials (GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET) "
                "are not configured in the environment."
            )
        params: Dict[str, str] = {
            "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "https://www.googleapis.com/auth/generative-language",
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }
        if code_challenge:
            params["code_challenge"] = code_challenge
            params["code_challenge_method"] = "S256"

        return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"

    async def exchange_oauth_code(
        self, code: str, redirect_uri: str, code_verifier: Optional[str] = None
    ) -> Dict[str, Any]:
        url = "https://oauth2.googleapis.com/token"
        payload = {
            "code": code,
            "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
            "client_secret": settings.GOOGLE_OAUTH_CLIENT_SECRET,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }
        if code_verifier:
            payload["code_verifier"] = code_verifier

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                res = await client.post(url, data=payload)
                if res.status_code != 200:
                    try:
                        err = res.json().get("error_description", res.text)
                    except Exception:
                        err = res.text
                    raise RuntimeError(sanitize_error_message(f"Google token exchange failed: {err}"))
                data = res.json()
                expires_in = data.get("expires_in", 3600)
                expires_at = (datetime.utcnow() + timedelta(seconds=expires_in)).isoformat()
                return {
                    "access_token": data.get("access_token"),
                    "refresh_token": data.get("refresh_token"),
                    "expires_at": expires_at,
                    "token_type": "Bearer",
                }
        except Exception as exc:
            raise RuntimeError(sanitize_error_message(str(exc)))

    async def refresh_oauth_token(self, refresh_token: str) -> Dict[str, Any]:
        url = "https://oauth2.googleapis.com/token"
        payload = {
            "refresh_token": refresh_token,
            "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
            "client_secret": settings.GOOGLE_OAUTH_CLIENT_SECRET,
            "grant_type": "refresh_token",
        }

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                res = await client.post(url, data=payload)
                if res.status_code != 200:
                    raise RuntimeError("Failed to refresh Google OAuth token.")
                data = res.json()
                expires_in = data.get("expires_in", 3600)
                expires_at = (datetime.utcnow() + timedelta(seconds=expires_in)).isoformat()
                return {
                    "access_token": data.get("access_token"),
                    "expires_at": expires_at,
                }
        except Exception as exc:
            raise RuntimeError(sanitize_error_message(str(exc)))

    async def revoke_oauth_token(self, token: str) -> bool:
        url = "https://oauth2.googleapis.com/revoke"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(url, data={"token": token})
                return res.status_code == 200
        except Exception:
            return False

    async def _get_auth_headers_or_params(
        self, credentials: Dict[str, Any]
    ) -> Tuple[Dict[str, str], Dict[str, str]]:
        """Return (headers, params) depending on API key or OAuth Bearer token."""
        headers: Dict[str, str] = {}
        params: Dict[str, str] = {}

        if "api_key" in credentials and credentials["api_key"]:
            params["key"] = credentials["api_key"]
        elif "access_token" in credentials and credentials["access_token"]:
            # Check if token is expired and refresh token is available
            refresh_token = credentials.get("refresh_token")
            expires_at_str = credentials.get("expires_at")
            if refresh_token and expires_at_str:
                try:
                    exp_dt = datetime.fromisoformat(expires_at_str)
                    if exp_dt <= datetime.utcnow() + timedelta(seconds=60):
                        new_tok = await self.refresh_oauth_token(refresh_token)
                        credentials["access_token"] = new_tok["access_token"]
                        credentials["expires_at"] = new_tok["expires_at"]
                except Exception:
                    pass
            headers["Authorization"] = f"Bearer {credentials['access_token']}"
        else:
            raise ValueError("No API key or OAuth access token found for Google Gemini.")

        return headers, params

    async def test_connection(
        self, credentials: Dict[str, Any], base_url: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        try:
            headers, params = await self._get_auth_headers_or_params(credentials)
        except Exception as exc:
            return False, sanitize_error_message(str(exc))

        url = (base_url or "https://generativelanguage.googleapis.com/v1beta").rstrip("/") + "/models"

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.get(url, headers=headers, params=params)
                if res.status_code == 200:
                    return True, None
                try:
                    err = res.json().get("error", {}).get("message", res.text)
                except Exception:
                    err = f"Status code {res.status_code}"
                return False, sanitize_error_message(f"Gemini error: {err}")
        except Exception as exc:
            return False, sanitize_error_message(f"Connection error: {str(exc)}")

    async def list_models(
        self, credentials: Dict[str, Any], base_url: Optional[str] = None
    ) -> List[str]:
        try:
            headers, params = await self._get_auth_headers_or_params(credentials)
            url = (base_url or "https://generativelanguage.googleapis.com/v1beta").rstrip("/") + "/models"
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.get(url, headers=headers, params=params)
                if res.status_code == 200:
                    data = res.json()
                    models = [
                        m["name"].replace("models/", "")
                        for m in data.get("models", [])
                        if "generateContent" in m.get("supportedGenerationMethods", [])
                    ]
                    if models:
                        return sorted(models)
        except Exception:
            pass

        return self.get_fallback_models()

    async def generate_text(
        self,
        prompt: str,
        model: str,
        credentials: Dict[str, Any],
        base_url: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        headers, params = await self._get_auth_headers_or_params(credentials)
        clean_model = (model or self.get_default_model()).replace("models/", "")
        url = (
            f"{(base_url or 'https://generativelanguage.googleapis.com/v1beta').rstrip('/')}"
            f"/models/{clean_model}:generateContent"
        )
        headers["Content-Type"] = "application/json"
        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}],
                }
            ]
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(url, headers=headers, params=params, json=payload)
                if res.status_code != 200:
                    try:
                        err = res.json().get("error", {}).get("message", res.text)
                    except Exception:
                        err = res.text
                    raise RuntimeError(sanitize_error_message(f"Gemini error: {err}"))
                data = res.json()
                candidates = data.get("candidates", [])
                if not candidates:
                    return "No response generated."
                parts = candidates[0].get("content", {}).get("parts", [])
                return "".join(p.get("text", "") for p in parts)
        except Exception as exc:
            raise RuntimeError(sanitize_error_message(str(exc)))
