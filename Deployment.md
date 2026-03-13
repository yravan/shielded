# Deploying Shielded to Production

Stack: **Vercel** (frontend, free) + **Railway** (backend, ~$5/mo) + **Cloudflare** (domain/DNS, at-cost)

Estimated total cost: **~$5-15/month** + domain registration ($10-35/yr).

---

## Prerequisites

1. **Install CLIs:**
   ```bash
   npm i -g @railway/cli vercel
   railway login
   vercel login
   ```

2. **Accounts needed:**
   - [Railway](https://railway.app) — Hobby plan ($5/mo)
   - [Vercel](https://vercel.com) — Hobby (free)
   - [Cloudflare](https://cloudflare.com) — free account + domain registrar
   - [Clerk](https://clerk.com) — production instance

3. **Push all changes to `main`** before starting.

---

## 1. Purchase Domain (Cloudflare)

1. Go to **Cloudflare Dashboard → Registrar → Register Domain**
2. Search and purchase your domain (e.g. `shielded.app`)
3. Cloudflare automatically configures itself as the DNS provider

**Domain layout:**
| URL | Purpose |
|-----|---------|
| `shielded.app` | Frontend (Vercel) |
| `api.shielded.app` | Backend API (Railway) |

---

## 2. Railway Backend Setup

### 2.1 Create Project + Addons

1. **New Project** on Railway dashboard
2. **Add PostgreSQL** → click "New" → "Database" → "PostgreSQL"
3. **Add Redis** → click "New" → "Database" → "Redis"

### 2.2 Web Service (API)

1. Click "New" → "GitHub Repo" → select your repo
2. Configure:
   - **Root Directory:** `backend`
   - **Builder:** Dockerfile
   - Railway will auto-detect `railway.toml` settings:
     - Start command: `uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT`
     - Health check: `/api/health`

### 2.3 Worker Service (Celery Worker)

1. Click "New" → "GitHub Repo" → same repo
2. Configure:
   - **Root Directory:** `backend`
   - **Builder:** Dockerfile
   - **Start Command (override):** `uv run celery -A celery_app worker --loglevel=info --concurrency=2`
   - **Remove health check** (workers don't serve HTTP)

### 2.4 Beat Service (Celery Scheduler)

1. Click "New" → "GitHub Repo" → same repo
2. Configure:
   - **Root Directory:** `backend`
   - **Builder:** Dockerfile
   - **Start Command (override):** `uv run celery -A celery_app beat --loglevel=info`
   - **Remove health check**
   - **Never scale beyond 1 replica** — multiple beat instances = duplicate scheduled tasks

### 2.5 Environment Variables

Use **Railway shared variables** so all 3 services share the same config.

Go to project **Settings → Shared Variables** and add:

| Variable | Value |
|----------|-------|
| `DATABASE_URL` | `postgresql+asyncpg://${{Postgres.PGUSER}}:${{Postgres.PGPASSWORD}}@${{Postgres.PGHOST}}:${{Postgres.PGPORT}}/${{Postgres.PGDATABASE}}` |
| `REDIS_URL` | `${{Redis.REDIS_URL}}` |
| `CELERY_BROKER_URL` | `${{Redis.REDIS_URL}}` |
| `FRONTEND_URL` | `https://shielded.app` |
| `ENABLE_LIVE_POLLING` | `true` |
| `POLYMARKET_API_URL` | `https://clob.polymarket.com` |
| `KALSHI_API_URL` | `https://api.elections.kalshi.com/trade-api/v2` |
| `KALSHI_API_KEY` | *(your Kalshi API key PEM content)* |
| `KALSHI_KEY_ID` | *(your Kalshi key ID)* |
| `METACULUS_API_URL` | `https://www.metaculus.com/api2` |
| `METACULUS_API_KEY` | *(your Metaculus API key)* |
| `CLERK_SECRET_KEY` | `sk_live_...` *(set after Clerk production setup)* |
| `CLERK_PUBLISHABLE_KEY` | `pk_live_...` *(set after Clerk production setup)* |
| `CLERK_JWT_ISSUER` | *(from Clerk dashboard)* |
| `POLL_INTERVAL_SECONDS` | `300` |

> **Gotcha: `DATABASE_URL` format** — Railway's built-in `DATABASE_URL` uses `postgresql://` but our app requires `postgresql+asyncpg://`. You must construct it manually using the reference variables above.

> **Gotcha: `ENABLE_LIVE_POLLING`** — defaults to `false` in `config.py`. If you forget to set this, the poll and discover tasks won't be scheduled by Celery Beat (see `celery_app.py:18`).

### 2.6 Custom Domain

1. On the **Web service** (not worker/beat), go to **Settings → Networking → Custom Domain**
2. Add `api.shielded.app`
3. **Note the CNAME target** Railway provides (e.g. `your-project.up.railway.app`) — you'll need it for DNS

---

## 3. Vercel Frontend Setup

### 3.1 Import Project

1. Go to [vercel.com/new](https://vercel.com/new)
2. Import your GitHub repo
3. Configure:
   - **Root Directory:** `frontend`
   - **Framework Preset:** Next.js (auto-detected)
   - **Install Command:** `pnpm install --frozen-lockfile`

> **Gotcha: pnpm** — the project uses `pnpm-lock.yaml`. Vercel usually auto-detects this, but if you get install errors, explicitly set the install command above.

### 3.2 Environment Variables

Set these in **Vercel → Project Settings → Environment Variables:**

| Variable | Value |
|----------|-------|
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | `pk_live_...` |
| `CLERK_SECRET_KEY` | `sk_live_...` |
| `NEXT_PUBLIC_CLERK_SIGN_IN_URL` | `/sign-in` |
| `NEXT_PUBLIC_CLERK_SIGN_UP_URL` | `/sign-up` |
| `NEXT_PUBLIC_API_URL` | `https://api.shielded.app` |
| `NEXT_PUBLIC_USE_MOCKS` | `false` |

> **Gotcha: `NEXT_PUBLIC_` vars are baked in at build time.** Changing them requires a redeploy — they won't update at runtime.

### 3.3 Custom Domain

1. Go to **Vercel → Project Settings → Domains**
2. Add `shielded.app`
3. Vercel will tell you to point DNS to `cname.vercel-dns.com`
4. Optionally also add `www.shielded.app` (Vercel auto-redirects)

---

## 4. Cloudflare DNS Configuration

In **Cloudflare Dashboard → DNS → Records**, create three CNAME records:

| Type | Name | Content | Proxy Status |
|------|------|---------|-------------|
| CNAME | `@` | `cname.vercel-dns.com` | **DNS only** (gray cloud) |
| CNAME | `www` | `cname.vercel-dns.com` | **DNS only** (gray cloud) |
| CNAME | `api` | `<railway-cname-target>` | **DNS only** (gray cloud) |

Replace `<railway-cname-target>` with the CNAME from step 2.6.

> **Gotcha: DNS-only mode is required.** Cloudflare's proxy (orange cloud) breaks SSL certificate provisioning on both Vercel and Railway. Toggle the cloud icon to **gray** for all three records.

---

## 5. Database Migrations

From the `backend/` directory of your local repo:

```bash
cd backend

# Run all migrations
railway run uv run alembic upgrade head

# Verify migrations applied
railway run uv run alembic current
# Expected output: 004_multi_company (head)
```

---

## 6. Seed Initial Data

Trigger the discovery and hedge tasks to populate the database:

```bash
cd backend

# Discover events from Polymarket/Kalshi/Metaculus
railway run uv run python -c "
from app.tasks.discovery import discover_new_events
print(discover_new_events())
"

# Compute initial hedging recommendations
railway run uv run python -c "
from app.tasks.hedges import recompute_hedges
print(recompute_hedges())
"
```

Verify data exists:
```bash
curl https://api.shielded.app/api/health/detailed
# Should show: "active_events": <number > 0>
```

---

## 7. Configure Clerk for Production

1. **Create a production instance** in the [Clerk Dashboard](https://dashboard.clerk.com):
   - Either create a new production instance or switch your dev instance to production
2. **Add your production domain:** `shielded.app`
3. **Copy production keys:**
   - `pk_live_...` (publishable key)
   - `sk_live_...` (secret key)
   - JWT issuer URL
4. **Update environment variables:**
   - **Railway:** Update `CLERK_SECRET_KEY`, `CLERK_PUBLISHABLE_KEY`, `CLERK_JWT_ISSUER` in shared variables
   - **Vercel:** Update `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`, `CLERK_SECRET_KEY`
5. **Redeploy Vercel** — the publishable key is a `NEXT_PUBLIC_` build-time variable
6. **Set allowed origins** in Clerk:
   - `https://shielded.app`
   - `https://api.shielded.app`

---

## 8. Post-Deploy Verification

Run through this checklist:

```bash
# 1. API health
curl https://api.shielded.app/api/health
# → {"status": "ok", "version": "0.1.0"}

# 2. Detailed health (DB, Redis, ingestion)
curl https://api.shielded.app/api/health/detailed
# → database: ok, redis: ok, active_events: >0

# 3. CORS headers
curl -s -I -H "Origin: https://shielded.app" https://api.shielded.app/api/health \
  | grep -i access-control
# → Access-Control-Allow-Origin: https://shielded.app
```

Then manually verify:
- [ ] `https://shielded.app` loads the marketing page
- [ ] Sign-up and sign-in work via Clerk
- [ ] Dashboard loads and shows tracked events with probability data
- [ ] `/explore` page shows events from Polymarket/Kalshi/Metaculus
- [ ] Check Railway logs: worker and beat services show task execution
- [ ] Events update on the next poll cycle (~5 min)

---

## Cost Summary

| Service | Plan | Cost |
|---------|------|------|
| Vercel | Hobby | Free |
| Railway | Hobby (includes Postgres + Redis) | ~$5/mo |
| Cloudflare | Free account + domain | $10-35/yr |
| Clerk | Free tier (up to 10k MAU) | Free |
| **Total** | | **~$5-8/month** |

---

## Troubleshooting

**Railway deploy fails with "no matching manifest"**
- Ensure Root Directory is set to `backend` in Railway service settings

**`DATABASE_URL` connection errors**
- Verify you used `postgresql+asyncpg://` (not `postgresql://`)
- Check that reference variables (`${{Postgres.PGUSER}}` etc.) resolve correctly in Railway

**Frontend shows mock data instead of live data**
- Confirm `NEXT_PUBLIC_USE_MOCKS=false` is set
- Confirm `NEXT_PUBLIC_API_URL=https://api.shielded.app` is set
- Redeploy on Vercel (these are build-time vars)

**Celery tasks not running**
- Verify `ENABLE_LIVE_POLLING=true` is set on all 3 Railway services
- Check beat service logs for scheduled task registration
- Ensure beat is limited to exactly 1 replica

**SSL certificate errors on custom domain**
- Ensure Cloudflare DNS records use **DNS-only** mode (gray cloud, not orange)
- Wait 5-10 minutes for certificate provisioning after adding custom domains

**CORS errors in browser console**
- Verify `FRONTEND_URL=https://shielded.app` is set on Railway
- The CORS middleware reads this value at startup (`main.py:30`)
