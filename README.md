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

## Start the API

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

## Start the frontend

In a second terminal:

```bash
cd apps/web
cp .env.example .env.local
npm ci
npm run dev
```

Open `http://localhost:3000`. `NEXT_PUBLIC_API_URL` in `apps/web/.env.local` must point to the API; it defaults to `http://localhost:8000`.

## Verification

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

## API endpoints

- `GET /health`
- `GET /api/dashboard/summary`
- `GET`, `POST /api/leads`
- `GET`, `PATCH`, `DELETE /api/leads/{lead_id}`
- `PATCH /api/leads/{lead_id}/status`
