# Vercel Setup Guide

## Step 1 - Deploy

```bash
cd studio/frontend
npx vercel --prod
```

Follow the prompts:

```text
Framework: Next.js
Root directory: studio/frontend
Install command: corepack enable && pnpm install --frozen-lockfile
Build command: pnpm build
Output directory: .next
```

## Step 2 - Environment Variables

In Vercel dashboard -> Project -> Settings -> Environment Variables, add these for Production:

```text
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
NEXT_PUBLIC_SUPABASE_URL=https://[ref].supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_...
```

## Step 3 - Custom Domain

In Vercel dashboard -> Project -> Settings -> Domains:

```text
yourdomain.com
www.yourdomain.com
```

Add the DNS records Vercel provides to your DNS provider. SSL is automatic.

## Step 4 - Update Supabase Auth

In Supabase dashboard -> Authentication -> URL Configuration:

```text
Site URL: https://yourdomain.com
```

Redirect URLs:

```text
https://yourdomain.com/auth/callback
https://yourdomain.com/dashboard
http://localhost:3000/auth/callback
```

Keep the localhost redirect for local development.

## Step 5 - Redeploy After Env Vars

```bash
cd studio/frontend
npx vercel --prod
```

If GitHub integration is connected, pushing to `main` can trigger production deploys.

## Step 6 - Replace Domain Placeholders

Before production launch, replace `yourdomain.com` in `studio/frontend/vercel.json` with the real frontend domain and `api.yourdomain.com` with the Railway API domain.
