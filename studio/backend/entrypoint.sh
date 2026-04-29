#!/bin/bash
set -e

MODE=${MODE:-api}

case "$MODE" in
  api)
    echo "Starting API server..."
    exec uvicorn backend.main:app \
      --host 0.0.0.0 \
      --port "${PORT:-8000}" \
      --workers "${UVICORN_WORKERS:-2}" \
      --log-level "${LOG_LEVEL:-info}" \
      --no-access-log
    ;;
  worker)
    echo "Starting Celery worker..."
    exec celery -A backend.workers.celery_app worker \
      --loglevel="${LOG_LEVEL:-info}" \
      --queues="${CELERY_QUEUE_NAME:-studio_tasks}" \
      --concurrency="${CELERY_CONCURRENCY:-2}"
    ;;
  beat)
    echo "Starting Celery beat scheduler..."
    exec celery -A backend.workers.celery_app beat \
      --loglevel="${LOG_LEVEL:-info}" \
      --scheduler celery.beat:PersistentScheduler
    ;;
  migrate)
    echo "Running database migrations..."
    exec alembic upgrade head
    ;;
  *)
    echo "Unknown MODE: $MODE. Use: api | worker | beat | migrate"
    exit 1
    ;;
esac
