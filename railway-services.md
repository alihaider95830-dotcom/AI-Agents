# Railway Setup Guide

This repo is a monorepo. Use the repository root as the Railway build context and `studio/backend/Dockerfile` as the Dockerfile for every Railway service.

## Step 1 - Create Project

```bash
railway login
railway init
```

Name the project `studio-production`.

## Step 2 - Create Three Services From The Same Repo

Service 1: `studio-api`

```text
MODE=api
PORT=8000
UVICORN_WORKERS=2
```

Service 2: `studio-worker`

```text
MODE=worker
CELERY_CONCURRENCY=2
```

Service 3: `studio-beat`

```text
MODE=beat
```

Only run one `studio-beat` service. Multiple beat schedulers can enqueue duplicate periodic tasks.

## Step 3 - Run Migrations

Use Railway's pre-deploy command on `studio-api`:

```bash
MODE=migrate /entrypoint.sh
```

You can also create a short-lived service using the same image with `MODE=migrate`.

## Step 4 - Add Persistent Volume

In `studio-worker` service -> Add Volume:

```text
Mount path: /app/data
VECTOR_STORE_PATH=/app/data/faiss_index
```

The API service does not need this volume. The worker needs it because FAISS indexes and cleanup jobs use the vector store path.

## Step 5 - Add Environment Variables

Copy values from `.env.production.example`. Set the shared values on all three services, and then set the service-specific variables from Step 2.

Use Railway shared variables for:

```text
DATABASE_URL
REDIS_URL
SECRET_KEY
FRONTEND_URL
OPENAI_API_KEY
ANTHROPIC_API_KEY
SUPABASE_URL
SUPABASE_ANON_KEY
SUPABASE_SERVICE_KEY
STRIPE_SECRET_KEY
STRIPE_WEBHOOK_SECRET
STRIPE_PRO_PRICE_ID
STRIPE_AGENCY_PRICE_ID
ADMIN_API_KEY
VECTOR_STORE_PATH
LOG_LEVEL
ENVIRONMENT
ALLOWED_HOSTS
METRICS_TOKEN
```

Use:

```text
ENVIRONMENT=production
ALLOWED_HOSTS=api.yourdomain.com,your-service.up.railway.app
```

Keep Railway's generated host in `ALLOWED_HOSTS` until the custom domain is active, otherwise platform health checks can be rejected by trusted-host validation.

## Step 6 - Add Custom Domain

In `studio-api` service -> Settings -> Networking -> Custom Domain:

```text
api.yourdomain.com
```

Copy the CNAME value Railway provides. In your DNS provider, add:

```text
api.yourdomain.com CNAME [railway value]
```

Wait for SSL to provision, usually less than five minutes.

## Step 7 - Set Up Stripe Webhook

In Stripe Dashboard -> Webhooks -> Add endpoint:

```text
https://api.yourdomain.com/api/v1/billing/webhook
```

Events to listen to:

```text
checkout.session.completed
customer.subscription.updated
customer.subscription.deleted
invoice.payment_failed
invoice.payment_succeeded
customer.subscription.paused
```

Copy the webhook signing secret and set it as `STRIPE_WEBHOOK_SECRET` in Railway.
