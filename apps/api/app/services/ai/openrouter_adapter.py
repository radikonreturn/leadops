from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode
import httpx

from app.core.config import settings
from app.core.security import sanitize_error_message
from app.services.ai.base import BaseAIAdapter


class OpenRouterAdapter(BaseAIAdapter):
    provider_name = "openrouter"
    display_name = "OpenRouter"

    def supports_oauth(self) -> bool:
        return True

    def supports_api_key(self) -> bool:
        return True

    def is_oauth_configured(self) -> bool:
        # OpenRouter PKCE flow does not require a pre-registered secret,
        # but requires redirect_uri and code_challenge.
        return True

    def get_default_model(self) -> str:
        return "meta-llama/llama-3.3-70b-instruct"

    def get_fallback_models(self) -> List[str]:
        return [
            "meta-llama/llama-3.3-70b-instruct",
            "google/gemini-2.0-flash-exp:free",
            "anthropic/claude-3.5-sonnet",
            "openai/gpt-4o-mini",
            "mistralai/mistral-7b-instruct:free",
        ]

    def build_oauth_authorize_url(
        self, redirect_uri: str, state: str, code_challenge: Optional[str] = None
    ) -> str:
        params: Dict[str, str] = {
            "callback_url": redirect_uri,
            "state": state,
        }
        if code_challenge:
            params["code_challenge"] = code_challenge
            params["code_challenge_method"] = "S256"
        return f"https://openrouter.ai/auth?{urlencode(params)}"

    async def exchange_oauth_code(
        self, code: str, redirect_uri: str, code_verifier: Optional[str] = None
    ) -> Dict[str, Any]:
        url = "https://openrouter.ai/api/v1/auth/keys"
        payload: Dict[str, str] = {"code": code}
        if code_verifier:
            payload["code_verifier"] = code_verifier

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code != 200:
                    try:
                        err = res.json().get("error", {}).get("message", res.text)
                    except Exception:
                        err = res.text
                    raise RuntimeError(sanitize_error_message(f"OpenRouter token exchange failed: {err}"))
                data = res.json()
                key = data.get("key")
                if not key:
                    raise RuntimeError("No API key returned from OpenRouter OAuth exchange.")
                return {
                    "api_key": key,
                    "token_type": "api_key",
                }
        except Exception as exc:
            raise RuntimeError(sanitize_error_message(str(exc)))

    async def test_connection(
        self, credentials: Dict[str, Any], base_url: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        api_key = credentials.get("api_key", "").strip()
        if not api_key:
            return False, "OpenRouter API key is required."

        url = (base_url or "https://openrouter.ai/api/v1").rstrip("/") + "/auth/key"
        headers = {"Authorization": f"Bearer {api_key}"}

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.get(url, headers=headers)
                if res.status_code == 200:
                    return True, None
                # Fallback check against /models if /auth/key returns non-200
                models_url = (base_url or "https://openrouter.ai/api/v1").rstrip("/") + "/models"
                m_res = await client.get(models_url, headers=headers)
                if m_res.status_code == 200:
                    return True, None

                try:
                    err = res.json().get("error", {}).get("message", res.text)
                except Exception:
                    err = f"Status code {res.status_code}"
                return False, sanitize_error_message(f"OpenRouter error: {err}")
        except Exception as exc:
            return False, sanitize_error_message(f"Connection error: {str(exc)}")

    async def list_models(
        self, credentials: Dict[str, Any], base_url: Optional[str] = None
    ) -> List[str]:
        api_key = credentials.get("api_key", "").strip()
        url = (base_url or "https://openrouter.ai/api/v1").rstrip("/") + "/models"
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.get(url, headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    models = [item["id"] for item in data.get("data", [])]
                    if models:
                        return sorted(models)[:40]  # Return top 40 popular models
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
        api_key = credentials.get("api_key", "").strip()
        if not api_key:
            raise ValueError("OpenRouter API key is missing.")

        url = (base_url or "https://openrouter.ai/api/v1").rstrip("/") + "/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:3000",
            "X-Title": "LeadOps",
        }
        payload = {
            "model": model or self.get_default_model(),
            "messages": [{"role": "user", "content": prompt}],
            "temperature": kwargs.get("temperature", 0.7),
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(url, headers=headers, json=payload)
                if res.status_code != 200:
                    try:
                        err = res.json().get("error", {}).get("message", res.text)
                    except Exception:
                        err = res.text
                    raise RuntimeError(sanitize_error_message(f"OpenRouter error: {err}"))
                data = res.json()
                return data["choices"][0]["message"]["content"]
        except Exception as exc:
            raise RuntimeError(sanitize_error_message(str(exc)))
