from typing import Dict, List
from app.services.ai.anthropic_adapter import AnthropicAdapter
from app.services.ai.base import BaseAIAdapter
from app.services.ai.gemini_adapter import GeminiAdapter
from app.services.ai.ollama_adapter import OllamaAdapter
from app.services.ai.openai_adapter import OpenAIAdapter
from app.services.ai.openrouter_adapter import OpenRouterAdapter

_ADAPTERS: Dict[str, BaseAIAdapter] = {
    "openai": OpenAIAdapter(),
    "gemini": GeminiAdapter(),
    "anthropic": AnthropicAdapter(),
    "openrouter": OpenRouterAdapter(),
    "ollama": OllamaAdapter(),
}

SUPPORTED_PROVIDERS: List[str] = list(_ADAPTERS.keys())


def get_adapter(provider: str) -> BaseAIAdapter:
    """Return the adapter instance for a supported AI provider."""
    normalized = provider.lower().strip()
    if normalized not in _ADAPTERS:
        raise ValueError(
            f"Unsupported provider '{provider}'. Supported providers are: {', '.join(SUPPORTED_PROVIDERS)}"
        )
    return _ADAPTERS[normalized]


def list_all_adapters() -> List[BaseAIAdapter]:
    """Return all registered adapter instances."""
    return list(_ADAPTERS.values())
