# syntax=docker/dockerfile:1

# Stage 1: build dependencies
FROM python:3.11-slim@sha256:0b23cfb7425d065008b778022a17b1551c82f8b4866ee5a7a200084b7e2eafbf AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY studio/backend/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: runtime
FROM python:3.11-slim@sha256:0b23cfb7425d065008b778022a17b1551c82f8b4866ee5a7a200084b7e2eafbf AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# WeasyPrint and entrypoint runtime dependencies.
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    libcairo2 \
    libffi-dev \
    libgdk-pixbuf-2.0-0 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libpangoft2-1.0-0 \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /usr/local
COPY studio/backend /app/backend
COPY studio/alembic.ini /app/alembic.ini
COPY agents /app/agents
COPY schemas /app/schemas
COPY exceptions.py /app/exceptions.py
COPY studio/backend/entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh \
    && addgroup --system studio \
    && adduser --system --ingroup studio studio \
    && mkdir -p /app/data/faiss_index \
    && chown -R studio:studio /app/data

USER studio

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
