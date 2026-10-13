from typing import Any, Dict, List, Optional, Tuple
import httpx

from app.core.security import sanitize_error_message
from app.services.ai.base import BaseAIAdapter


class OllamaAdapter(BaseAIAdapter):
    provider_name = "ollama"
    display_name = "Ollama (Local)"

    def supports_oauth(self) -> bool:
        return False

    def supports_api_key(self) -> bool:
        return False

    def get_default_model(self) -> str:
        return "llama3.1"

    def get_fallback_models(self) -> List[str]:
        return ["llama3.1", "mistral", "phi3", "qwen2.5", "gemma2"]

    def _resolve_base_url(self, credentials: Dict[str, Any], base_url: Optional[str] = None) -> str:
        url = base_url or credentials.get("base_url") or "http://localhost:11434"
        return url.rstrip("/")

    async def test_connection(
        self, credentials: Dict[str, Any], base_url: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        url = self._resolve_base_url(credentials, base_url)
        headers: Dict[str, str] = {}
        api_key = credentials.get("api_key")
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.get(f"{url}/api/tags", headers=headers)
                if res.status_code == 200:
                    return True, None
                # Try /api/version
                v_res = await client.get(f"{url}/api/version", headers=headers)
                if v_res.status_code == 200:
                    return True, None
                return False, f"Ollama returned status code {res.status_code}"
        except httpx.ConnectError:
            return (
                False,
                f"Could not connect to Ollama at {url}. Ensure Ollama is running (`ollama serve`).",
            )
        except Exception as exc:
            return False, sanitize_error_message(f"Ollama error: {str(exc)}")

    async def list_models(
        self, credentials: Dict[str, Any], base_url: Optional[str] = None
    ) -> List[str]:
        url = self._resolve_base_url(credentials, base_url)
        headers: Dict[str, str] = {}
        api_key = credentials.get("api_key")
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(f"{url}/api/tags", headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    models = [m["name"] for m in data.get("models", []) if "name" in m]
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
        url = self._resolve_base_url(credentials, base_url)
        headers = {"Content-Type": "application/json"}
        api_key = credentials.get("api_key")
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        payload = {
            "model": model or self.get_default_model(),
            "prompt": prompt,
            "stream": False,
        }

        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                res = await client.post(f"{url}/api/generate", headers=headers, json=payload)
                if res.status_code != 200:
                    raise RuntimeError(f"Ollama error status code {res.status_code}: {res.text}")
                data = res.json()
                return data.get("response", "")
        except httpx.ConnectError:
            raise RuntimeError(f"Could not connect to Ollama at {url}. Ensure Ollama is running.")
        except Exception as exc:
            raise RuntimeError(sanitize_error_message(str(exc)))
