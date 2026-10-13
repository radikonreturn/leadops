from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient

from app.core.auth import create_access_token
from app.core.database import get_db
from app.main import app
from app.models.ai_connection import UserAIConnection, UserAISettings
from app.models.user import User


@pytest.fixture
def auth_users(db):
    user1 = User(email="user1@leadops.local", name="User One", role="Sales Exec", plan="Pro")
    user2 = User(email="user2@leadops.local", name="User Two", role="Sales Lead", plan="Pro")
    db.add_all([user1, user2])
    db.commit()
    db.refresh(user1)
    db.refresh(user2)

    token1 = create_access_token(user1.id, user1.email)
    token2 = create_access_token(user2.id, user2.email)
    return {"user1": user1, "token1": token1, "user2": user2, "token2": token2}


@pytest.fixture
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()


def test_unauthenticated_request_rejected(client):
    res = client.get("/api/ai/providers")
    assert res.status_code == 401
    assert "Authentication required" in res.json()["detail"]


def test_invalid_token_rejected(client):
    res = client.get("/api/ai/providers", headers={"Authorization": "Bearer invalid.token.value"})
    assert res.status_code == 401


def test_list_providers_defaults(client, auth_users):
    headers = {"Authorization": f"Bearer {auth_users['token1']}"}
    res = client.get("/api/ai/providers", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 5
    providers = {p["provider"]: p for p in data}
    assert "openai" in providers
    assert "gemini" in providers
    assert "anthropic" in providers
    assert "openrouter" in providers
    assert "ollama" in providers

    # Verify initial disconnected status
    for p in data:
        assert p["status"] == "disconnected"
        assert p["key_preview"] is None
        assert p["is_default"] is False

    # Check OAuth capabilities
    assert providers["openai"]["supports_oauth"] is False
    assert providers["anthropic"]["supports_oauth"] is False
    assert providers["openrouter"]["supports_oauth"] is True
    assert providers["gemini"]["supports_oauth"] is True
    assert providers["ollama"]["supports_oauth"] is False


@pytest.mark.asyncio
async def test_connect_openai_api_key(client, auth_users):
    headers = {"Authorization": f"Bearer {auth_users['token1']}"}

    with patch("app.services.ai.openai_adapter.OpenAIAdapter.test_connection", new_callable=AsyncMock) as mock_test, \
         patch("app.services.ai.openai_adapter.OpenAIAdapter.list_models", new_callable=AsyncMock) as mock_models:
        mock_test.return_value = (True, None)
        mock_models.return_value = ["gpt-4o", "gpt-4o-mini"]

        payload = {
            "api_key": "sk-proj-test1234567890abcdef1234",
            "selected_model": "gpt-4o",
        }
        res = client.post("/api/ai/providers/openai/connect", json=payload, headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["provider"] == "openai"
        assert data["status"] == "connected"
        assert data["selected_model"] == "gpt-4o"
        assert data["key_preview"] == "sk-...1234"
        assert data["is_default"] is True
        # Verify secret was NEVER returned in response
        assert "sk-proj-test" not in str(data)


@pytest.mark.asyncio
async def test_user_isolation(client, auth_users):
    headers1 = {"Authorization": f"Bearer {auth_users['token1']}"}
    headers2 = {"Authorization": f"Bearer {auth_users['token2']}"}

    # User 1 connects Anthropic
    with patch("app.services.ai.anthropic_adapter.AnthropicAdapter.test_connection", new_callable=AsyncMock) as mock_test:
        mock_test.return_value = (True, None)
        res = client.post(
            "/api/ai/providers/anthropic/connect",
            json={"api_key": "sk-ant-api03-user1secretkey9999"},
            headers=headers1,
        )
        assert res.status_code == 200

    # User 1 sees connected
    res1 = client.get("/api/ai/providers", headers=headers1)
    p1 = {p["provider"]: p for p in res1.json()}
    assert p1["anthropic"]["status"] == "connected"

    # User 2 lists providers: User 2 sees Anthropic DISCONNECTED!
    res2 = client.get("/api/ai/providers", headers=headers2)
    p2 = {p["provider"]: p for p in res2.json()}
    assert p2["anthropic"]["status"] == "disconnected"
    assert p2["anthropic"]["key_preview"] is None

    # User 2 cannot disconnect User 1's provider
    del_res = client.delete("/api/ai/providers/anthropic", headers=headers2)
    assert del_res.status_code == 404


@pytest.mark.asyncio
async def test_connect_invalid_api_key_returns_400(client, auth_users):
    headers = {"Authorization": f"Bearer {auth_users['token1']}"}

    with patch("app.services.ai.openai_adapter.OpenAIAdapter.test_connection", new_callable=AsyncMock) as mock_test:
        mock_test.return_value = (False, "Incorrect API key provided: sk-invalid1234567890")

        res = client.post(
            "/api/ai/providers/openai/connect",
            json={"api_key": "sk-invalid1234567890"},
            headers=headers,
        )
        assert res.status_code == 400
        detail = res.json()["detail"]
        assert "Incorrect API key" in detail
        # Ensure secret was sanitized from error message
        assert "sk-invalid" not in detail
        assert "[REDACTED]" in detail


@pytest.mark.asyncio
async def test_connect_local_ollama(client, auth_users):
    headers = {"Authorization": f"Bearer {auth_users['token1']}"}

    with patch("app.services.ai.ollama_adapter.OllamaAdapter.test_connection", new_callable=AsyncMock) as mock_test, \
         patch("app.services.ai.ollama_adapter.OllamaAdapter.list_models", new_callable=AsyncMock) as mock_models:
        mock_test.return_value = (True, None)
        mock_models.return_value = ["llama3.1:latest", "mistral:latest"]

        res = client.post(
            "/api/ai/providers/ollama/connect",
            json={"base_url": "http://localhost:11434"},
            headers=headers,
        )
        assert res.status_code == 200
        data = res.json()
        assert data["provider"] == "ollama"
        assert data["connection_method"] == "local"
        assert data["status"] == "connected"
        assert data["base_url"] == "http://localhost:11434"


@pytest.mark.asyncio
async def test_update_selected_model(client, auth_users):
    headers = {"Authorization": f"Bearer {auth_users['token1']}"}

    with patch("app.services.ai.openai_adapter.OpenAIAdapter.test_connection", new_callable=AsyncMock) as mock_test:
        mock_test.return_value = (True, None)
        client.post(
            "/api/ai/providers/openai/connect",
            json={"api_key": "sk-test1234567890"},
            headers=headers,
        )

    res = client.patch(
        "/api/ai/providers/openai/model",
        json={"selected_model": "gpt-4-turbo"},
        headers=headers,
    )
    assert res.status_code == 200
    assert res.json()["selected_model"] == "gpt-4-turbo"


@pytest.mark.asyncio
async def test_test_connection_endpoint(client, auth_users):
    headers = {"Authorization": f"Bearer {auth_users['token1']}"}

    with patch("app.services.ai.openrouter_adapter.OpenRouterAdapter.test_connection", new_callable=AsyncMock) as mock_test:
        mock_test.return_value = (True, None)
        # Test ad-hoc credentials
        res = client.post(
            "/api/ai/providers/openrouter/test",
            json={"api_key": "sk-or-v1-adhoc-key-1234567890"},
            headers=headers,
        )
        assert res.status_code == 200
        assert res.json()["success"] is True


@pytest.mark.asyncio
async def test_disconnect_provider(client, auth_users):
    headers = {"Authorization": f"Bearer {auth_users['token1']}"}

    with patch("app.services.ai.openai_adapter.OpenAIAdapter.test_connection", new_callable=AsyncMock) as mock_test:
        mock_test.return_value = (True, None)
        client.post("/api/ai/providers/openai/connect", json={"api_key": "sk-test1234567890"}, headers=headers)

    res = client.delete("/api/ai/providers/openai", headers=headers)
    assert res.status_code == 204

    # Verify provider is now disconnected
    list_res = client.get("/api/ai/providers", headers=headers)
    p = {item["provider"]: item for item in list_res.json()}
    assert p["openai"]["status"] == "disconnected"


@pytest.mark.asyncio
async def test_default_provider_and_test_generate(client, auth_users):
    headers = {"Authorization": f"Bearer {auth_users['token1']}"}

    with patch("app.services.ai.openai_adapter.OpenAIAdapter.test_connection", new_callable=AsyncMock) as mock_test, \
         patch("app.services.ai.openai_adapter.OpenAIAdapter.generate_text", new_callable=AsyncMock) as mock_gen:
        mock_test.return_value = (True, None)
        mock_gen.return_value = "AI outreach response: Welcome to LeadOps!"

        # Connect
        client.post("/api/ai/providers/openai/connect", json={"api_key": "sk-test1234567890"}, headers=headers)

        # Test generation
        gen_res = client.post(
            "/api/ai/test-generate",
            json={"prompt": "Write an intro email", "provider": "openai"},
            headers=headers,
        )
        assert gen_res.status_code == 200
        assert gen_res.json()["response"] == "AI outreach response: Welcome to LeadOps!"
        assert gen_res.json()["provider"] == "openai"


def test_oauth_authorization_url_and_state(client, auth_users):
    headers = {"Authorization": f"Bearer {auth_users['token1']}"}

    res = client.get("/api/ai/providers/openrouter/oauth/authorize", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "authorization_url" in data
    assert "openrouter.ai/auth" in data["authorization_url"]
    assert "state=" in data["authorization_url"]
    assert "code_challenge=" in data["authorization_url"]
    assert data["state"]


def test_oauth_rejected_for_unsupported_providers(client, auth_users):
    headers = {"Authorization": f"Bearer {auth_users['token1']}"}

    res = client.get("/api/ai/providers/openai/oauth/authorize", headers=headers)
    assert res.status_code == 400
    assert "does not offer an official OAuth flow" in res.json()["detail"]


@pytest.mark.asyncio
async def test_oauth_callback_csrf_validation_and_success(client, auth_users):
    headers = {"Authorization": f"Bearer {auth_users['token1']}"}

    # 1. Invalid state is rejected (CSRF)
    invalid_res = client.post(
        "/api/ai/providers/openrouter/oauth/callback",
        json={"code": "sample_auth_code", "state": "tampered_csrf_state"},
        headers=headers,
    )
    assert invalid_res.status_code == 400
    assert "CSRF" in invalid_res.json()["detail"]

    # 2. Valid authorization flow
    auth_res = client.get("/api/ai/providers/openrouter/oauth/authorize", headers=headers)
    state = auth_res.json()["state"]

    with patch("app.services.ai.openrouter_adapter.OpenRouterAdapter.exchange_oauth_code", new_callable=AsyncMock) as mock_exch, \
         patch("app.services.ai.openrouter_adapter.OpenRouterAdapter.list_models", new_callable=AsyncMock) as mock_models:
        mock_exch.return_value = {"api_key": "sk-or-v1-oauth-exchanged-key-9999"}
        mock_models.return_value = ["meta-llama/llama-3.3-70b-instruct"]

        cb_res = client.post(
            "/api/ai/providers/openrouter/oauth/callback",
            json={"code": "valid_openrouter_code", "state": state},
            headers=headers,
        )
        assert cb_res.status_code == 200
        data = cb_res.json()
        assert data["provider"] == "openrouter"
        assert data["connection_method"] == "oauth"
        assert data["status"] == "connected"
        assert data["key_preview"] == "sk-...9999"
