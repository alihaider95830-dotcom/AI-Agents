FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    CELERY_QUEUE_NAME=studio_tasks

WORKDIR /app

COPY studio/backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /tmp/requirements.txt

COPY studio/backend /app/backend
COPY agents /app/agents
COPY schemas /app/schemas
COPY exceptions.py /app/exceptions.py

CMD celery -A backend.workers.celery_app worker --loglevel=info --queues="${CELERY_QUEUE_NAME}"
