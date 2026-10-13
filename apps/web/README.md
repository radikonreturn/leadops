# LeadOps web

The LeadOps frontend is a Next.js application that communicates with the local FastAPI service.

For complete local PostgreSQL and API setup, see the [repository README](../../README.md).

## Configure and run

```bash
cp .env.example .env.local
npm ci
npm run dev
```

Open `http://localhost:3000`. The API must be running at the value of `NEXT_PUBLIC_API_URL` in `.env.local`; it defaults to `http://localhost:8000`.

## Checks

```bash
npm run lint
npm run build
```
