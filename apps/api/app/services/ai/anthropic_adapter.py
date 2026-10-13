from typing import Any, Dict, List, Optional, Tuple
import httpx

from app.core.security import sanitize_error_message
from app.services.ai.base import BaseAIAdapter


class AnthropicAdapter(BaseAIAdapter):
    provider_name = "anthropic"
    display_name = "Anthropic Claude"

    def supports_oauth(self) -> bool:
        return False

    def supports_api_key(self) -> bool:
        return True

    def get_default_model(self) -> str:
        return "claude-3-5-sonnet-20241022"

    def get_fallback_models(self) -> List[str]:
        return [
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
            "claude-3-opus-20240229",
        ]

    async def test_connection(
        self, credentials: Dict[str, Any], base_url: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        api_key = credentials.get("api_key", "").strip()
        if not api_key:
            return False, "Anthropic API key is required."

        url = (base_url or "https://api.anthropic.com/v1").rstrip("/") + "/models"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.get(url, headers=headers)
                if res.status_code == 200:
                    return True, None
                try:
                    err = res.json().get("error", {}).get("message", res.text)
                except Exception:
                    err = f"Status code {res.status_code}"
                return False, sanitize_error_message(f"Anthropic error: {err}")
        except Exception as exc:
            return False, sanitize_error_message(f"Connection error: {str(exc)}")

    async def list_models(
        self, credentials: Dict[str, Any], base_url: Optional[str] = None
    ) -> List[str]:
        api_key = credentials.get("api_key", "").strip()
        if not api_key:
            return self.get_fallback_models()

        url = (base_url or "https://api.anthropic.com/v1").rstrip("/") + "/models"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.get(url, headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    models = [item["id"] for item in data.get("data", [])]
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
        api_key = credentials.get("api_key", "").strip()
        if not api_key:
            raise ValueError("Anthropic API key is missing.")

        url = (base_url or "https://api.anthropic.com/v1").rstrip("/") + "/messages"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model or self.get_default_model(),
            "max_tokens": kwargs.get("max_tokens", 1024),
            "messages": [{"role": "user", "content": prompt}],
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(url, headers=headers, json=payload)
                if res.status_code != 200:
                    try:
                        err = res.json().get("error", {}).get("message", res.text)
                    except Exception:
                        err = res.text
                    raise RuntimeError(sanitize_error_message(f"Anthropic error: {err}"))
                data = res.json()
                content_blocks = data.get("content", [])
                text_pieces = [b.get("text", "") for b in content_blocks if b.get("type") == "text"]
                return "".join(text_pieces) or "No text returned."
        except Exception as exc:
            raise RuntimeError(sanitize_error_message(str(exc)))
