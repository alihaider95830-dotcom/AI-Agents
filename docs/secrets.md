## GitHub Actions Secrets

`PRODUCTION_API_URL`  
URL of the deployed Railway API, for example `https://api.yourdomain.com`.

`PRODUCTION_FRONTEND_URL`  
URL of the deployed Vercel frontend, for example `https://yourdomain.com`.

`PRODUCTION_ADMIN_KEY`  
The `ADMIN_API_KEY` value from Railway.

## Railway Environment Variables

Set these shared variables on all three Railway services:

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

Use `ENVIRONMENT=production` and comma-separated `ALLOWED_HOSTS`, for example `api.yourdomain.com,your-service.up.railway.app`.

## Railway Per-Service Variables

```text
studio-api:    MODE=api, PORT=8000, UVICORN_WORKERS=2
studio-worker: MODE=worker, CELERY_CONCURRENCY=2
studio-beat:   MODE=beat
```

Only one `studio-beat` service should exist. Running more than one beat scheduler can duplicate periodic tasks.

## Vercel Environment Variables

```text
NEXT_PUBLIC_API_URL
NEXT_PUBLIC_SUPABASE_URL
NEXT_PUBLIC_SUPABASE_ANON_KEY
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY
```

## Supabase Auth Settings

```text
Site URL: https://yourdomain.com
Redirect URLs:
  https://yourdomain.com/auth/callback
  https://yourdomain.com/dashboard
  http://localhost:3000/auth/callback
```

## Stripe Webhook Settings

Endpoint URL:

```text
https://api.yourdomain.com/api/v1/billing/webhook
```

Events:

```text
checkout.session.completed
customer.subscription.updated
customer.subscription.deleted
invoice.payment_failed
invoice.payment_succeeded
customer.subscription.paused
```

All secrets must be set as environment variables. Never commit `.env`, `.env.production`, or any file containing real API keys.
