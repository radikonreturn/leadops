from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple


class BaseAIAdapter(ABC):
    provider_name: str
    display_name: str

    @abstractmethod
    def supports_oauth(self) -> bool:
        """Return True if this provider officially supports OAuth for user API access."""
        ...

    @abstractmethod
    def supports_api_key(self) -> bool:
        """Return True if this provider supports connecting via direct API key."""
        ...

    def is_oauth_configured(self) -> bool:
        """Return True if server-side OAuth credentials (e.g. client ID) are set."""
        return False

    def oauth_limitation(self) -> Optional[str]:
        """Explanation if OAuth cannot be legitimately supported for this provider."""
        if not self.supports_oauth():
            return f"{self.display_name} does not offer an official OAuth flow for user API access. Use an API key instead."
        if not self.is_oauth_configured():
            return f"OAuth is supported by {self.display_name}, but server credentials (Client ID) are not yet configured in environment."
        return None

    @abstractmethod
    def get_default_model(self) -> str:
        """Return the default model recommended for this provider."""
        ...

    @abstractmethod
    def get_fallback_models(self) -> List[str]:
        """Return a curated list of fallback models when remote discovery fails."""
        ...

    @abstractmethod
    async def test_connection(
        self, credentials: Dict[str, Any], base_url: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """Test authentication and connectivity. Returns (success, optional_error_message)."""
        ...

    @abstractmethod
    async def list_models(
        self, credentials: Dict[str, Any], base_url: Optional[str] = None
    ) -> List[str]:
        """Fetch available models from the provider or return fallback models."""
        ...

    @abstractmethod
    async def generate_text(
        self,
        prompt: str,
        model: str,
        credentials: Dict[str, Any],
        base_url: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """Execute text generation through the provider."""
        ...

    def build_oauth_authorize_url(
        self, redirect_uri: str, state: str, code_challenge: Optional[str] = None
    ) -> str:
        """Generate the external OAuth authorization URL."""
        raise NotImplementedError(f"OAuth is not supported for {self.display_name}.")

    async def exchange_oauth_code(
        self, code: str, redirect_uri: str, code_verifier: Optional[str] = None
    ) -> Dict[str, Any]:
        """Exchange the OAuth authorization code for credentials/tokens."""
        raise NotImplementedError(f"OAuth is not supported for {self.display_name}.")

    async def refresh_oauth_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh an expired OAuth access token if supported."""
        raise NotImplementedError(f"Token refresh is not supported for {self.display_name}.")

    async def revoke_oauth_token(self, token: str) -> bool:
        """Revoke stored OAuth tokens with the upstream provider if supported."""
        return True
