# Repository Guidelines

## Project Structure & Module Organization

LeadOps contains two applications:
- `apps/web/`: Next.js with React, TypeScript, and Tailwind CSS. App Router pages, layouts, and global styles live in `src/app/`; static assets belong in `public/`.
- `apps/api/`: Python API scaffold with FastAPI dependencies. Under `app/`, `core/` contains settings and database setup, `models/` contains SQLAlchemy entities, `schemas/` contains Pydantic schemas, and `services/research/` contains scraping security logic.
- `apps/api/tests/` is currently empty. `docs/` and `docker/` are placeholders.

Keep database entities, request/response schemas, and service logic in their respective modules.

## Build, Test, and Development Commands

Run frontend commands from `apps/web/`:
- `npm ci`: install dependencies from the lockfile.
- `npm run dev`: start the local development server at `http://localhost:3000`.
- `npm run build`: create a production build.
- `npm start`: serve the production build.
- `npm run lint`: run ESLint with Next.js Core Web Vitals and TypeScript rules.

From `apps/api/`, use a Python virtual environment and run `python -m pip install -r requirements.txt`. Run `python -m pytest tests` once tests exist. No runnable API entry point is currently present.

## Coding Style & Naming Conventions

Match existing formatting: two-space indentation, double quotes, and semicolons in TypeScript; four-space indentation in Python. Use PascalCase for components and classes, camelCase for JavaScript variables, and snake_case for Python functions and modules. Preserve Next.js filenames such as `page.tsx` and `layout.tsx`. TypeScript strict mode is enabled; `@/*` maps to `src/*`.

## Testing Guidelines

Backend dependencies include pytest and pytest-asyncio; no coverage threshold is configured. Add backend tests as `apps/api/tests/test_*.py`, with `test_*` functions. Mock external AI and HTTP calls. No frontend test runner is configured; run lint and build, and manually verify affected pages.

## Commit & Pull Request Guidelines

Git history is unavailable in this checkout. Use concise imperative commit subjects, such as `Add lead validation`. PRs should describe changes, link relevant issues, report validation results, and include screenshots for UI changes.

## Configuration & Agent Instructions

API settings load `.env` relative to the working directory. Keep database credentials and provider keys out of commits. Before frontend code changes, follow `apps/web/AGENTS.md` and consult its referenced local Next.js documentation.
