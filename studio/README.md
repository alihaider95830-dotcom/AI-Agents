# Studio

A new full-stack Python/Next.js monorepo with:

- `frontend/` for the Next.js app placeholder
- `backend/` for the FastAPI API
- `workers/` for Celery workers

## Setup

1. Clone the repository.
2. Copy the example environment file:

   ```bash
   cp .env.example .env
   ```

3. Update `.env` with your local values.
4. Start the services:

   ```bash
   docker compose up --build
   ```

## Services

- `postgres` on port `5432`
- `redis` on port `6379`
- `backend` on port `8000`

## Backend

The FastAPI app reads configuration from environment variables using `pydantic-settings`. Once the stack is running, you can verify the API with:

```bash
curl http://localhost:8000/health
```
