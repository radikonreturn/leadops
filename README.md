# LeadOps

LeadOps is a local-first B2B lead management workspace. V1 provides persistent lead CRUD, pipeline status management, search and filtering, and dashboard metrics through a Next.js frontend and FastAPI/PostgreSQL backend.

## Prerequisites

- Node.js 20.9+ and npm
- Python 3.11+
- PostgreSQL 15+ running locally

## Local database setup

Create a local PostgreSQL role and database. Choose a real password in place of `change-me`.

```sql
CREATE ROLE leadops WITH LOGIN PASSWORD 'change-me';
CREATE DATABASE leadops OWNER leadops;
```

## Start everything

After completing the database and dependency setup below, start both applications from the repository root:

```bash
npm run dev
```

This starts the API at `http://localhost:8000` and the frontend at `http://localhost:3000`. Press `Ctrl+C` once to stop both processes.

### Windows PowerShell

The dependency folders and Python virtual environments are operating-system-specific. If you use PowerShell, install the frontend dependencies from PowerShell before running the root commands:

```powershell
npm run setup:web
```

For the API, create the virtual environment from PowerShell as well:

```powershell
cd apps/api
py -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\alembic.exe upgrade head
cd ../..
```

## API setup

```bash
cd apps/api
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

The API runs at `http://localhost:8000`. Confirm it with `curl http://localhost:8000/health`.

`DATABASE_URL` in `apps/api/.env` controls the database connection. It defaults to the local database created above.

## Frontend setup

In a second terminal:

```bash
cd apps/web
cp .env.example .env.local
npm ci
npm run dev
```

`NEXT_PUBLIC_API_URL` in `apps/web/.env.local` must point to the API; it defaults to `http://localhost:8000`.

## Verification

From the repository root, run the cross-platform API test command:

```bash
npm run test:api
```

Run backend tests from the activated API virtual environment:

```bash
cd apps/api
python -m pytest tests
```

Run frontend quality checks:

```bash
cd apps/web
npm run lint
npm run build
```

The API test suite uses an isolated SQLite test database. The application itself uses PostgreSQL and Alembic migrations for persistence.

## AI Provider Connections

LeadOps includes a user-scoped, multi-provider AI connection system located at **Settings → AI Providers** (`/settings/ai-providers`).

### Supported Providers & Authentication Methods

| Provider | Connection Methods | Default / Recommended Models | OAuth Details |
|---|---|---|---|
| **OpenAI** | API Key | `gpt-4o`, `gpt-4o-mini`, `o3-mini`, `gpt-4-turbo` | Developer API access is API key only (no 3rd-party OAuth supported by OpenAI). |
| **Google Gemini** | API Key, OAuth 2.0 | `gemini-1.5-pro`, `gemini-1.5-flash`, `gemini-2.0-flash` | Google OAuth 2.0 authorization code flow with PKCE (`generative-language` scope). |
| **Anthropic Claude** | API Key | `claude-3-5-sonnet-20241022`, `claude-3-5-haiku-20241022`, `claude-3-opus-20240229` | Developer API access is API key only (Anthropic does not offer user OAuth for API execution). |
| **OpenRouter** | API Key, OAuth (PKCE) | `meta-llama/llama-3.3-70b-instruct`, `anthropic/claude-3.5-sonnet`, `deepseek/deepseek-chat` | Official OpenRouter PKCE flow with authorization code exchange and key issuance. |
| **Ollama** | Local Server URL | `llama3.1`, `mistral`, `qwen2.5`, `deepseek-r1` | Local inference server (default `http://localhost:11434`), no credentials required. |

### Security & Credential Encryption at Rest

- All user credentials (API keys, OAuth tokens, and refresh tokens) are encrypted at rest using server-side AES-256 via Fernet (`ENCRYPTION_KEY`).
- Secret keys and raw tokens are **never** returned to the frontend or browser storage (only masked formats such as `sk-...1234` are returned for UI display).
- Sensitive tokens and API keys are automatically scrubbed from runtime error logs and exception messages.
- OAuth flows enforce state CSRF validation and PKCE (`code_challenge` / `code_verifier`).
- Connections are strictly scoped to the authenticated user derived from session tokens.

### Configuration Variables (`apps/api/.env`)

```ini
# Fernet 32-byte base64 encryption key for credentials at rest
ENCRYPTION_KEY=your-32-byte-base64-or-passphrase

# Session signing key
SECRET_KEY=leadops-session-secret-change-in-production

# OAuth Application Settings (Optional - required only if enabling OAuth buttons)
OAUTH_REDIRECT_BASE_URL=http://localhost:3000/settings/ai-providers/callback
GOOGLE_OAUTH_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=your-google-client-secret
OPENROUTER_OAUTH_CLIENT_ID=your-openrouter-client-id
```

## API endpoints

- `GET /health`
- `GET /api/auth/me`
- `GET /api/dashboard/summary`
- `GET`, `POST /api/leads`
- `GET`, `PATCH`, `DELETE /api/leads/{lead_id}`
- `PATCH /api/leads/{lead_id}/status`
- `GET /api/ai-providers` - List provider connection statuses and supported methods
- `POST /api/ai-providers/{provider}/connect` - Connect via API key or base URL
- `DELETE /api/ai-providers/{provider}` - Disconnect and remove stored credentials
- `POST /api/ai-providers/{provider}/test` - Test connection and validate credentials
- `POST /api/ai-providers/{provider}/model` - Update selected model for provider
- `GET /api/ai-providers/settings` - Get user AI settings (default provider and model)
- `POST /api/ai-providers/settings` - Update default provider and model
- `GET /api/ai-providers/{provider}/oauth/url` - Generate OAuth authorization URL with state & PKCE
- `POST /api/ai-providers/{provider}/oauth/callback` - Complete OAuth token exchange with CSRF validation
- `POST /api/ai-providers/test-generation` - Test text generation using user's configured provider
