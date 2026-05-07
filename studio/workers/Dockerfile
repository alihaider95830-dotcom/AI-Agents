FROM python:3.11-slim@sha256:0b23cfb7425d065008b778022a17b1551c82f8b4866ee5a7a200084b7e2eafbf

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
