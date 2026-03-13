# Shielded — Pre-Deployment Testing Plan

> **Target:** Complete all sections before client deployment.
> **How to use:** Work through each section top-to-bottom, checking off items as you go.

---

## Table of Contents

1. [Environment Setup](#1-environment-setup)
2. [Backend API Testing](#2-backend-api-testing)
3. [Authentication Testing](#3-authentication-testing)
4. [Frontend Page-by-Page Testing](#4-frontend-page-by-page-testing)
5. [Data Flow / End-to-End Testing](#5-data-flow--end-to-end-testing)
6. [Background Tasks (Celery)](#6-background-tasks-celery)
7. [Edge Cases & Error Handling](#7-edge-cases--error-handling)
8. [Cross-Browser & Responsive Testing](#8-cross-browser--responsive-testing)
9. [Performance Basics](#9-performance-basics)
10. [Security Checklist](#10-security-checklist)
11. [Pre-Launch Go/No-Go](#11-pre-launch-gono-go)

---

## 1. Environment Setup

Verify all services are running and configured before testing.

### Services

- [ ] PostgreSQL is running and `shielded` database exists
- [ ] Redis is running on port 6379
- [ ] Backend (`uvicorn`) starts without errors on port 8000
- [ ] Celery worker starts without errors
- [ ] Celery Beat scheduler starts without errors
- [ ] Frontend (`next dev` or `next start`) starts without errors on port 3000

### Environment Variables — Backend

- [ ] `DATABASE_URL` points to correct PostgreSQL instance
- [ ] `REDIS_URL` points to correct Redis instance
- [ ] `CELERY_BROKER_URL` points to correct Redis DB
- [ ] `FRONTEND_URL` matches actual frontend URL (CORS)
- [ ] `CLERK_SECRET_KEY` is set to **production** Clerk key
- [ ] `CLERK_PUBLISHABLE_KEY` is set to **production** Clerk key
- [ ] `CLERK_JWT_ISSUER` matches your Clerk instance
- [ ] `POLYMARKET_API_URL` is set (default: `https://clob.polymarket.com`)
- [ ] `KALSHI_API_KEY` path points to valid PEM file (if using Kalshi)
- [ ] `KALSHI_KEY_ID` is set (if using Kalshi)
- [ ] `METACULUS_API_KEY` is set (if using Metaculus)
- [ ] `POLL_INTERVAL_SECONDS` is set to desired value (default: 300)
- [ ] `ENABLE_LIVE_POLLING` is `true`

### Environment Variables — Frontend

- [ ] `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` is set to **production** key
- [ ] `CLERK_SECRET_KEY` is set to **production** key
- [ ] `NEXT_PUBLIC_API_URL` points to backend URL
- [ ] `NEXT_PUBLIC_USE_MOCKS` is `false` (⚠️ **critical** — must not be `true` in production)

### Database

- [ ] All Alembic migrations applied: `alembic upgrade head`
- [ ] Verify tables exist: `users`, `companies`, `events`, `user_tracked_events`, `exposures`, `probability_history`, `hedge_analyses`

---

## 2. Backend API Testing

Test every endpoint. Use curl, Postman, or httpie. Replace `$TOKEN` with a valid Clerk JWT.

### Health Endpoints (No Auth)

- [ ] **`GET /api/health`** → returns `{"status": "ok"}`
- [ ] **`GET /api/health/detailed`** → returns database, Redis, and ingestion statuses; all should be healthy

### Events — Explore (Auth Required)

- [ ] **`GET /api/explore/events`** → returns paginated list of all events
- [ ] **`GET /api/explore/events?search=tariff`** → results contain "tariff" in title/description
- [ ] **`GET /api/explore/events?category=trade`** → only trade-category events
- [ ] **`GET /api/explore/events?region=Asia-Pacific`** → only Asia-Pacific events
- [ ] **`GET /api/explore/events?status=active`** → only active events
- [ ] **`GET /api/explore/events?sort=probability`** → sorted by probability descending
- [ ] **`GET /api/explore/events?page=2&page_size=5`** → correct pagination

### Events — Tracked (Auth Required)

- [ ] **`GET /api/events`** → returns only user's tracked events
- [ ] **`GET /api/events?all=true`** → returns all events
- [ ] **`GET /api/events?category=conflict`** → filtered by category
- [ ] **`GET /api/events/{event_id}`** → returns single event with all fields populated
- [ ] **`GET /api/events/{event_id}/history?hours=24`** → returns probability history array
- [ ] **`GET /api/events/{event_id}/history?hours=168&bucket_minutes=60`** → aggregated buckets

### Events — Tracking (Auth Required)

- [ ] **`POST /api/events/{event_id}/track`** → returns success, event appears in `GET /api/events`
- [ ] **`POST /api/events/{event_id}/track`** (duplicate) → returns appropriate error or idempotent success
- [ ] **`DELETE /api/events/{event_id}/track`** → returns success, event disappears from tracked list
- [ ] **`DELETE /api/events/{event_id}/track`** (not tracked) → returns appropriate error

### Companies — My Companies (Auth Required)

- [ ] **`GET /api/my-companies`** → returns user's companies (may be empty initially)
- [ ] **`POST /api/my-companies`** with body `{"name": "Test Corp", "ticker": "TST", "sector": "Technology", "annual_revenue": 1000000, "operating_expense": 500000, "capital_expense": 200000}` → creates company
- [ ] **`GET /api/my-companies`** → now includes the created company
- [ ] **`PUT /api/my-companies/{company_id}`** with updated name → name changes
- [ ] **`DELETE /api/my-companies/{company_id}`** → company removed
- [ ] **`PUT /api/my-companies/{other_users_company_id}`** → returns 403 (ownership check)

### Companies — Backward Compat (Auth Required)

- [ ] **`GET /api/my-company`** → returns first company or appropriate empty response
- [ ] **`POST /api/my-company`** → creates or updates first company

### Companies — Public / Lookup

- [ ] **`GET /api/company-lookup/AAPL`** → returns Apple financials from yfinance
- [ ] **`GET /api/company-lookup/INVALIDTICKER`** → returns appropriate error
- [ ] **`GET /api/companies`** → returns all companies in system
- [ ] **`GET /api/companies/{company_id}`** → returns single company
- [ ] **`GET /api/companies/{company_id}/exposure`** → returns exposure array (may be empty)

### Impacts (Auth Required)

- [ ] **`GET /api/impacts/{company_id}/{event_id}`** → returns impact analysis object
- [ ] **`GET /api/impacts/{invalid_id}/{event_id}`** → returns 404 or appropriate error

### Hedge Analysis (Auth Required)

- [ ] **`GET /api/hedge-analysis?company_id={id}&event_id={id}`** → returns hedge comparison with PM cost, traditional cost, recommendation, savings
- [ ] **`GET /api/hedge-analysis`** (missing params) → returns 422 validation error

### Users (Auth Required)

- [ ] **`GET /api/me`** → returns current user info with `tracked_event_count` and `company_count`
- [ ] First call creates user record; subsequent calls return same user

---

## 3. Authentication Testing

### Clerk JWT Flow

- [ ] Backend rejects requests to protected endpoints with no `Authorization` header → 401/403
- [ ] Backend rejects requests with invalid/expired JWT → 401/403
- [ ] Backend accepts requests with valid Clerk JWT → 200
- [ ] Frontend redirects unauthenticated users to `/sign-in` for protected routes

### Dev Bypass Removal

> ⚠️ **CRITICAL** — The backend falls back to a dev user if `CLERK_SECRET_KEY` is not set.

- [ ] Confirm `CLERK_SECRET_KEY` **is set** in production environment
- [ ] With `CLERK_SECRET_KEY` set, unauthenticated requests are rejected (no dev user fallback)
- [ ] Test by temporarily unsetting `CLERK_SECRET_KEY` — verify dev bypass activates (then re-set it!)

### Protected Routes (Frontend Middleware)

- [ ] `/dashboard` → redirects to sign-in if not authenticated
- [ ] `/events` → redirects to sign-in if not authenticated
- [ ] `/events/[eventId]` → redirects to sign-in if not authenticated
- [ ] `/explore` → redirects to sign-in if not authenticated
- [ ] `/companies` → redirects to sign-in if not authenticated
- [ ] `/hedging` → redirects to sign-in if not authenticated
- [ ] `/settings` → redirects to sign-in if not authenticated
- [ ] `/onboarding` → redirects to sign-in if not authenticated
- [ ] `/` (marketing home) → accessible without auth
- [ ] `/sign-in` → accessible without auth
- [ ] `/sign-up` → accessible without auth

### Auth State Transitions

- [ ] Sign in → redirected to dashboard, all data loads
- [ ] Sign out → redirected to home page, protected routes inaccessible
- [ ] Token refresh → user stays logged in without page reload issues

---

## 4. Frontend Page-by-Page Testing

### Marketing Home (`/`)

- [ ] Page loads without errors
- [ ] Navigation links work (sign-in, sign-up, any anchor links)
- [ ] CTA buttons navigate correctly
- [ ] Marketing nav renders correctly

### Sign In (`/sign-in`)

- [ ] Clerk sign-in form renders
- [ ] Can sign in with valid credentials
- [ ] Error shown for invalid credentials
- [ ] Redirects to dashboard after successful sign-in

### Sign Up (`/sign-up`)

- [ ] Clerk sign-up form renders
- [ ] Can create new account
- [ ] Redirects appropriately after sign-up (onboarding or dashboard)

### Dashboard (`/dashboard`)

- [ ] Stats cards display: tracked events count, high-probability events count, companies count
- [ ] Tracked events cards render with title, probability, trend indicator
- [ ] Probability badges show correct color coding
- [ ] Clicking an event card navigates to `/events/[eventId]`
- [ ] Empty state displayed if no tracked events

### Events (`/events`)

- [ ] List of tracked events loads
- [ ] Category filter works
- [ ] Region filter works (if available)
- [ ] Event cards show: title, description, probability, source, trend
- [ ] Clicking event navigates to detail page
- [ ] Empty state if no tracked events with CTA to explore

### Event Detail (`/events/[eventId]`)

- [ ] Event title, description, category, region, source display correctly
- [ ] Probability badge shows current probability
- [ ] Trend indicator shows direction (up/down/flat) vs previous probability
- [ ] Probability chart renders with historical data
- [ ] Time selector (1h, 24h, 7d, 30d, etc.) changes chart range
- [ ] Financial impacts section renders if company selected
- [ ] Implied financials section renders correctly
- [ ] Source URL link works (opens external prediction market page)

### Explore (`/explore`)

- [ ] All events load with pagination
- [ ] Search bar filters events by keyword
- [ ] Category dropdown filters correctly
- [ ] Sort options work: by updated, by probability, by created
- [ ] "Track" button adds event to tracked list
- [ ] "Untrack" button removes event from tracked list
- [ ] Track/untrack state reflects immediately in UI
- [ ] Pagination controls work (next page, previous page)
- [ ] Loading skeletons appear while data is fetching

### Companies (`/companies`)

- [ ] List of user's companies displays
- [ ] Company cards show: name, ticker, sector, revenue
- [ ] Clicking company navigates to detail page
- [ ] Empty state with CTA to add first company

### Company Detail (`/companies/[companyId]`)

- [ ] Company info displays: name, ticker, sector, financials
- [ ] Exposure table shows company's event exposures
- [ ] Exposure entries show: event title, exposure type, direction, sensitivity, impact percentages

### Hedging (`/hedging`)

- [ ] Hedge recommendations load for each company-event pair
- [ ] Market comparison chart renders (PM cost vs traditional cost)
- [ ] Each recommendation shows: PM cost, PM payout, traditional instrument, traditional cost, savings %, recommendation
- [ ] Empty state if no exposures configured

### Settings (`/settings`)

- [ ] User profile info displays
- [ ] Company management section:
  - [ ] Add new company (form with name, ticker, sector, revenue fields)
  - [ ] Edit existing company
  - [ ] Delete company (with confirmation)
  - [ ] Ticker lookup auto-fills financials from yfinance
- [ ] Theme toggle works (light/dark)
- [ ] Data sources status shows which sources are connected
- [ ] Polling config displays current interval

### Onboarding (`/onboarding`)

- [ ] Flow renders for new users
- [ ] Can complete onboarding steps (company setup, etc.)
- [ ] Redirects to dashboard after completion

### Navigation & Layout

- [ ] Sidebar renders on all dashboard pages
- [ ] Active page highlighted in sidebar
- [ ] Sidebar links all navigate correctly: Dashboard, Events, Explore, Companies, Hedging, Settings
- [ ] Top bar renders with user info
- [ ] Sign out button works from top bar/sidebar

---

## 5. Data Flow / End-to-End Testing

Test complete data paths from external APIs through to the frontend.

### Event Discovery → Display

- [ ] Trigger `discover_new_events` task manually (via Celery CLI or admin endpoint)
- [ ] New events appear in database (`events` table)
- [ ] New events appear in `GET /api/explore/events`
- [ ] New events appear on `/explore` page in frontend
- [ ] Events have: title, description, category, region, source, source_id, probability

### Probability Updates → Chart

- [ ] Trigger `poll_all_markets` task manually
- [ ] `probability_history` table gets new records
- [ ] `events.current_probability` and `events.previous_probability` update
- [ ] `GET /api/events/{id}/history` returns updated history
- [ ] Probability chart on event detail page reflects new data points
- [ ] Trend indicator shows correct direction after update

### Company Setup → Exposure → Impact

- [ ] Create company via Settings page
- [ ] Company appears in `GET /api/my-companies`
- [ ] Exposure data populates for company-event pairs
- [ ] `GET /api/companies/{id}/exposure` returns exposures
- [ ] `GET /api/impacts/{company_id}/{event_id}` returns impact analysis
- [ ] Impact data renders on event detail page

### Hedge Analysis Flow

- [ ] With company and tracked events set up, go to `/hedging`
- [ ] Hedge analysis loads for each company-event exposure pair
- [ ] PM cost, traditional cost, and savings % are reasonable values
- [ ] Recommendation field shows actionable advice
- [ ] Trigger `recompute_hedges` task → hedging page data updates

### Redis Caching

- [ ] First call to `/api/companies/{id}/exposure` hits DB (check logs)
- [ ] Second call within 300s returns cached data (faster response, no DB hit in logs)
- [ ] Same for `/api/impacts/{company_id}/{event_id}` (300s cache)

---

## 6. Background Tasks (Celery)

### Task Execution

- [ ] `poll_all_markets` runs successfully and returns `{"updated": N}` where N > 0
- [ ] `discover_new_events` runs successfully and returns `{"new_events": N}`
- [ ] `recompute_hedges` runs successfully and returns `{"computed": N}`
- [ ] `backfill_history` runs without error

### Scheduled Execution (Celery Beat)

- [ ] Celery Beat is scheduling `poll_all_markets` at `POLL_INTERVAL_SECONDS` interval
- [ ] Verify by watching Celery worker logs for periodic task execution
- [ ] Events table shows `updated_at` timestamps advancing

### Error Resilience

- [ ] If Polymarket API is down, task logs error but doesn't crash; other sources still polled
- [ ] Circuit breaker activates after 5 failures (check logs for circuit breaker messages)
- [ ] Circuit breaker resets after 900s cooldown
- [ ] Retry logic: verify exponential backoff on transient failures (check logs)

### Data Integrity

- [ ] `poll_all_markets` updates `previous_probability` to old value before setting new `current_probability`
- [ ] `probability_history` records have correct `recorded_at` timestamps (from API, not just `now()`)
- [ ] No duplicate `probability_history` entries for same event + timestamp
- [ ] `discover_new_events` doesn't create duplicate events (unique constraint on `source` + `source_id`)

---

## 7. Edge Cases & Error Handling

### Empty States

- [ ] Dashboard with no tracked events → shows empty state message
- [ ] Events page with no tracked events → shows empty state with link to explore
- [ ] Companies page with no companies → shows empty state with CTA
- [ ] Hedging page with no companies or no exposures → shows appropriate message
- [ ] Explore with search yielding no results → shows "no results" message

### Invalid Inputs

- [ ] Event detail page with non-existent event ID → 404 or error page
- [ ] Company detail page with non-existent company ID → 404 or error page
- [ ] API calls with malformed UUIDs → 422 validation error
- [ ] Company creation with missing required fields → validation error shown in UI
- [ ] Ticker lookup with nonsense string → graceful error

### Network Failures

- [ ] Frontend handles API timeout gracefully (loading spinner, then error message)
- [ ] Frontend handles 500 errors with user-friendly message
- [ ] React Query retry behavior works (3 retries by default)
- [ ] Offline/disconnected state doesn't crash the app

### Concurrent Operations

- [ ] Two users tracking the same event simultaneously → no errors
- [ ] Tracking an event while `poll_all_markets` is running → no deadlock
- [ ] Creating a company while another request is in-flight → no duplicate creation

---

## 8. Cross-Browser & Responsive Testing

### Browsers

- [ ] Chrome (latest) — all pages functional
- [ ] Firefox (latest) — all pages functional
- [ ] Safari (latest) — all pages functional
- [ ] Edge (latest) — all pages functional

### Responsive Breakpoints

- [ ] **Mobile (375px)** — sidebar collapses, content readable, cards stack vertically
- [ ] **Tablet (768px)** — layout adjusts, charts readable
- [ ] **Desktop (1280px)** — full layout, sidebar visible, charts at full width
- [ ] **Wide (1920px)** — no horizontal scrolling, content doesn't stretch awkwardly

### Key Visual Checks

- [ ] Probability charts render correctly at all sizes
- [ ] Tables are scrollable on mobile (not cut off)
- [ ] Forms are usable on mobile (input fields, buttons accessible)
- [ ] Modals/dialogs don't overflow on small screens
- [ ] Dark mode renders correctly (no invisible text, good contrast)
- [ ] Light mode renders correctly

---

## 9. Performance Basics

### Page Load Times (Target: < 3s on 4G)

- [ ] Marketing home page
- [ ] Dashboard (with data)
- [ ] Events list page
- [ ] Event detail page (with chart)
- [ ] Explore page (first page load)
- [ ] Settings page

### API Response Times (Target: < 500ms)

- [ ] `GET /api/health` → < 100ms
- [ ] `GET /api/explore/events` → < 500ms
- [ ] `GET /api/events` → < 500ms
- [ ] `GET /api/events/{id}` → < 200ms
- [ ] `GET /api/events/{id}/history` → < 500ms
- [ ] `GET /api/companies/{id}/exposure` → < 500ms (< 50ms cached)
- [ ] `GET /api/impacts/{cid}/{eid}` → < 500ms (< 50ms cached)
- [ ] `GET /api/hedge-analysis` → < 1s
- [ ] `GET /api/me` → < 200ms

### Quick Checks

- [ ] No N+1 queries visible in backend logs (watch for repeated queries)
- [ ] Probability chart doesn't freeze with 7 days of minute-level data
- [ ] Explore page pagination doesn't reload entire dataset

---

## 10. Security Checklist

### Authentication & Authorization

- [ ] All protected endpoints return 401/403 without valid JWT
- [ ] Users cannot access other users' companies (ownership check on `PUT`/`DELETE /api/my-companies/{id}`)
- [ ] Users cannot see other users' tracked events
- [ ] `CLERK_SECRET_KEY` is set in production (dev bypass disabled)
- [ ] JWT issuer validation is active (`CLERK_JWT_ISSUER` configured)

### CORS

- [ ] `FRONTEND_URL` is set to the exact production frontend URL
- [ ] Requests from unauthorized origins are rejected
- [ ] No wildcard (`*`) CORS in production

### Secrets & Config

- [ ] `.env` files are in `.gitignore` and not committed
- [ ] No API keys, secrets, or credentials in source code
- [ ] `NEXT_PUBLIC_USE_MOCKS=false` in production
- [ ] Kalshi PEM key file is not in the repository
- [ ] No debug/development settings active in production

### Input Validation

- [ ] SQL injection: try `'; DROP TABLE events;--` in search field → no effect
- [ ] XSS: try `<script>alert('xss')</script>` in company name → escaped in output
- [ ] Path traversal: try `../../etc/passwd` in API parameters → rejected
- [ ] Oversized payloads: send very large body to POST endpoints → rejected or handled

### Headers & Transport

- [ ] HTTPS enforced in production (no HTTP)
- [ ] Sensitive headers not leaked in API responses
- [ ] Stack traces not exposed in production error responses (no debug mode)

---

## 11. Pre-Launch Go/No-Go

Final checklist before giving client access.

### Must-Have (Blockers)

- [ ] All Section 2 (API) tests pass
- [ ] All Section 3 (Auth) tests pass — especially dev bypass removal
- [ ] All Section 4 (Frontend) pages load without console errors
- [ ] All Section 5 (Data Flow) tests pass — data flows end-to-end
- [ ] Section 6 (Celery) tasks execute on schedule
- [ ] Section 10 (Security) — no critical findings

### Should-Have

- [ ] Section 7 (Edge Cases) — empty states handled
- [ ] Section 8 (Responsive) — works on mobile
- [ ] Section 9 (Performance) — all targets met

### Deployment

- [ ] Database migrations applied in production
- [ ] All environment variables set in production
- [ ] Celery worker and Beat running in production
- [ ] Redis accessible in production
- [ ] Frontend build succeeds (`next build` with no errors)
- [ ] Backend starts cleanly in production
- [ ] HTTPS/SSL configured
- [ ] Domain/DNS configured
- [ ] Initial `discover_new_events` run completed → events populated
- [ ] At least one `poll_all_markets` cycle completed → probabilities fresh

### Monitoring

- [ ] Backend logs accessible (stdout/file/service)
- [ ] Celery task logs accessible
- [ ] Error alerting configured (Sentry, or at minimum log monitoring)
- [ ] Know how to check if Celery tasks are stuck/failing

---

**Done?** If all "Must-Have" items are checked and no blockers remain, you're clear to deploy.
