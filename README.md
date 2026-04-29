# AI Agents

AI Agents is a report-generation workspace built around a four-stage agent
pipeline and a full-stack Studio app. The pipeline researches a topic, turns the
findings into an outline, drafts a cited Markdown report, and runs a QA pass.
Studio wraps that workflow with authentication, credits, report jobs, streaming
progress, and a web dashboard.

## Project Layout

> [!IMPORTANT]
> `studio/backend/` is the canonical Python package root. All `pytest` invocations and import paths use it as their base (e.g. `from backend.api.deps import …`). There is **no** top-level `backend/` or `frontend/` directory — those paths exist only inside `studio/`.

```text
.
|-- agents/                  # Standalone researcher, planner, writer, and QA agents
|-- schemas/                 # Pydantic contracts for findings, outlines, drafts, reports
|-- tests/                   # Unit tests for the standalone agent pipeline
|-- studio/
|   |-- backend/             # FastAPI API, SQLAlchemy models, Celery tasks, tools
|   |-- frontend/            # Next.js dashboard (pnpm workspace)
|   |-- workers/             # Worker Dockerfile
|   |-- docker-compose.yml   # Postgres, Redis, backend, and worker services
|   `-- alembic.ini          # Database migration config (run from studio/)
`-- exceptions.py            # Shared pipeline exceptions
```


## Features

- Four-stage report pipeline: Researcher, Planner, Writer, QA.
- Validated data contracts with Pydantic.
- Search, scraping, chunking, embeddings, and FAISS vector-store tooling.
- FastAPI backend with versioned API routes.
- Supabase-based authentication.
- Credit tracking and billing usage history.
- Celery background jobs backed by Redis.
- Server-sent events for report progress streaming.
- PostgreSQL persistence with Alembic migrations.
- Next.js frontend with report generation, dashboard, reports, settings, and auth views.
- Jest and Pytest coverage for frontend, backend, and core agent behavior.

## Tech Stack

- Python 3.11
- FastAPI, Celery, Redis, SQLAlchemy, Alembic, PostgreSQL
- Pydantic and pydantic-settings
- LangChain, OpenAI-compatible model hooks, FAISS, tiktoken
- Next.js 14, React 18, TypeScript, Tailwind CSS, Zustand
- Supabase auth
- Stripe configuration hooks
- Jest, Testing Library, Pytest

## Current Status

The standalone pipeline in `agents/` is implemented and tested with deterministic
fallbacks. Real CrewAI execution is optional and controlled by environment flags.

The Studio app is wired for report jobs, streaming, credits, auth, storage, and
the full four-agent report pipeline. The Celery task in
`studio/backend/workers/tasks.py` calls `agents.crew.run_crew` and stores the
QA-approved Markdown output on the completed report.

## Prerequisites

- Python 3.11+
- Docker Desktop
- Node.js 20+
- PNPM via Corepack
- Supabase project credentials
- OpenAI and/or Anthropic API keys for real model-backed runs
- Stripe keys if you enable billing flows

## Quick Start

### 1. Install Python Dependencies

From the repository root:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r studio\backend\requirements.txt
```

On macOS or Linux:

```bash
python -m venv venv
source venv/bin/activate
pip install -r studio/backend/requirements.txt
```

### 2. Configure Environment Files

Create backend and frontend environment files from the examples:

```powershell
Copy-Item studio\.env.example studio\.env
Copy-Item studio\frontend\.env.local.example studio\frontend\.env.local
```

Fill in the values for:

- `DATABASE_URL`
- `REDIS_URL`
- `SECRET_KEY`
- `ADMIN_API_KEY`
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_KEY`
- `FRONTEND_URL`
- `NEXT_PUBLIC_API_URL`
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY`

When running services inside Docker Compose, the database host should usually be
`postgres`. When running local commands from your host machine, use `localhost`
for the database host.

### 3. Start Backend Services

From `studio/`:

```powershell
docker compose up --build
```

This starts:

- PostgreSQL on `localhost:5432`
- Redis on `localhost:6379`
- FastAPI backend on `localhost:8000`
- Celery worker

The frontend is not included in Docker Compose, so run it separately.

### 4. Run Database Migrations

After Postgres is running, run Alembic from `studio/`:

```powershell
alembic upgrade head
```

If your `.env` uses the Docker hostname `postgres`, switch `DATABASE_URL` to a
`localhost` URL for this host-side migration command, or run Alembic from an
environment that can resolve the Docker service name.

Optional seed data:

```powershell
python -m backend.db.seed
```

### 5. Start the Frontend

From `studio/frontend/`:

```powershell
corepack enable
corepack pnpm install
corepack pnpm dev
```

Open:

- Frontend: `http://localhost:3000`
- Backend health check: `http://localhost:8000/health`
- Backend API docs: `http://localhost:8000/docs`

## Running Tests

Standalone agent tests:

```powershell
pytest tests
```

Backend tests:

```powershell
cd studio
pytest backend\tests
```

Frontend tests:

```powershell
cd studio\frontend
corepack pnpm test
```

Frontend production build:

```powershell
cd studio\frontend
corepack pnpm build
```

## Agent Pipeline

The standalone pipeline lives in `agents/crew.py`:

```python
from agents.crew import run_crew

report = run_crew("The future of renewable energy")
print(report.markdown_output)
```

Pipeline stages:

1. `run_researcher` collects sources, extracts facts, chunks content, and stores
   vector-search context.
2. `run_planner` creates a structured report outline.
3. `run_writer` drafts a cited Markdown report.
4. `run_qa` checks citations, grammar, clarity, and quality.

By default, the project uses deterministic fallbacks where possible so tests can
run without live CrewAI execution. To opt into real CrewAI-backed agents, install
the required CrewAI dependencies and set the relevant flags:

```powershell
$env:RESEARCHER_USE_REAL_CREWAI="true"
$env:PLANNER_USE_REAL_CREWAI="true"
$env:WRITER_USE_REAL_CREWAI="true"
$env:QA_USE_REAL_CREWAI="true"
```

Useful tuning variables include:

- `RESEARCHER_MODEL_NAME`
- `RESEARCHER_MAX_SOURCES`
- `RESEARCHER_CHUNK_SIZE`
- `RESEARCHER_SIMILARITY_TOP_K`
- `PLANNER_MODEL_NAME`
- `WRITER_MODEL_NAME`
- `QA_MODEL_NAME`

## API Overview

Root health endpoints:

- `GET /health`
- `GET /health/db`

Primary backend endpoints are mounted under `/api/v1`:

- `GET /api/v1/health`
- `GET /api/v1/health/db`
- `GET /api/v1/me`
- `POST /api/v1/me/sync`
- `POST /api/v1/reports`
- `GET /api/v1/reports`
- `GET /api/v1/reports/{report_id}`
- `DELETE /api/v1/reports/{report_id}`
- `GET /api/v1/jobs/{job_id}`
- `GET /api/v1/stream/{job_id}`
- `GET /api/v1/billing/usage`
- `GET /api/v1/billing/history`
- `POST /api/v1/admin/users/{user_id}/adjust-credits`
- `POST /api/v1/admin/users/{user_id}/set-tier`
- `GET /api/v1/knowledge/{report_id}/status`
- `GET /api/v1/knowledge/{report_id}/sources`

Authenticated API calls expect a Supabase JWT bearer token.

## Development Notes

- Keep generated secrets out of git. `.env`, `.env.local`, `node_modules/`,
  `.next/`, caches, and local CrewAI storage are ignored.
- `pnpm-lock.yaml` should be committed when frontend dependencies change.
- Prefer Alembic migrations for database schema changes.
- Keep schema changes synchronized between backend Pydantic models, database
  models, and frontend TypeScript types.
- The worker integration point is `studio/backend/workers/tasks.py`.

## License

No license has been specified yet.
