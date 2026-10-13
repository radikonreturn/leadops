from typing import Any, Dict, List, Optional, Tuple
import httpx

from app.core.security import sanitize_error_message
from app.services.ai.base import BaseAIAdapter


class OpenAIAdapter(BaseAIAdapter):
    provider_name = "openai"
    display_name = "OpenAI"

    def supports_oauth(self) -> bool:
        return False

    def supports_api_key(self) -> bool:
        return True

    def get_default_model(self) -> str:
        return "gpt-4o-mini"

    def get_fallback_models(self) -> List[str]:
        return ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"]

    async def test_connection(
        self, credentials: Dict[str, Any], base_url: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        api_key = credentials.get("api_key", "").strip()
        if not api_key:
            return False, "API key is required."

        url = (base_url or "https://api.openai.com/v1").rstrip("/") + "/models"
        headers = {"Authorization": f"Bearer {api_key}"}

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.get(url, headers=headers)
                if res.status_code == 200:
                    return True, None
                error_body = res.json().catch(lambda: {}) if hasattr(res, "json") else {}
                detail = ""
                try:
                    detail = res.json().get("error", {}).get("message", "")
                except Exception:
                    detail = f"Status code {res.status_code}"
                return False, sanitize_error_message(f"OpenAI error: {detail or res.text}")
        except Exception as exc:
            return False, sanitize_error_message(f"Connection error: {str(exc)}")

    async def list_models(
        self, credentials: Dict[str, Any], base_url: Optional[str] = None
    ) -> List[str]:
        api_key = credentials.get("api_key", "").strip()
        if not api_key:
            return self.get_fallback_models()

        url = (base_url or "https://api.openai.com/v1").rstrip("/") + "/models"
        headers = {"Authorization": f"Bearer {api_key}"}

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.get(url, headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    models = [
                        item["id"]
                        for item in data.get("data", [])
                        if "gpt" in item.get("id", "").lower() or "o1" in item.get("id", "").lower()
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
        api_key = credentials.get("api_key", "").strip()
        if not api_key:
            raise ValueError("OpenAI API key is missing.")

        url = (base_url or "https://api.openai.com/v1").rstrip("/") + "/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
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
                    raise RuntimeError(sanitize_error_message(f"OpenAI error: {err}"))
                data = res.json()
                return data["choices"][0]["message"]["content"]
        except Exception as exc:
            raise RuntimeError(sanitize_error_message(str(exc)))
