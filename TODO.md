# Shielded — Production Hardening TODO

## Security
- [ ] Add security headers (CSP, HSTS, X-Frame-Options) via middleware
- [ ] Add rate limiting to API endpoints (especially auth and lookup)
- [ ] Remove dev-mode auth bypass (`CLERK_SECRET_KEY` not set → allow all) or gate behind `DEBUG` flag
- [ ] Rotate any committed secrets and move to proper secret management
- [ ] Validate and sanitize all user input (company names, tickers, search queries)
- [ ] Add CSRF protection for state-changing endpoints

## Error Handling
- [ ] Add global exception handler in FastAPI (return structured error responses)
- [ ] Add React error boundaries for dashboard sections (not just the top-level one)
- [ ] Integrate error tracking (Sentry or similar) for both backend and frontend
- [ ] Handle API timeout / network errors gracefully in frontend hooks

## Testing
- [ ] Backend: API endpoint tests (pytest + httpx async client)
- [ ] Backend: Service/calculator unit tests
- [ ] Frontend: Component tests (Vitest + Testing Library)
- [ ] E2E tests (Playwright) for critical flows: sign-in → onboarding → track event → view dashboard
- [ ] Load testing for event polling and concurrent user access

## Observability
- [ ] Add structured request logging middleware (request ID, duration, status)
- [ ] Add Prometheus metrics endpoint (request count, latency histograms, DB pool usage)
- [ ] Add distributed tracing (OpenTelemetry)
- [ ] Set up alerting for ingestion staleness (>15 min without poll)
- [ ] Dashboard for Celery task health and failure rates

## Performance
- [ ] Frontend: code splitting / lazy loading for dashboard sections
- [ ] Frontend: image optimization (next/image for any added images)
- [ ] Backend: add database indexes for common query patterns (events by category+status)
- [ ] Backend: optimize N+1 queries in exposure endpoint
- [ ] Consider connection pooling with PgBouncer in production
- [ ] Add Redis caching for user's tracked events list

## SEO & Marketing
- [ ] Add Open Graph meta tags for marketing pages
- [ ] Generate sitemap.xml
- [ ] Add robots.txt
- [ ] Add structured data (JSON-LD) for the marketing page

## Deployment
- [ ] Frontend: create production Dockerfile
- [ ] Set up staging environment
- [ ] CI/CD: add deployment step (currently only lint/test)
- [ ] Add health check endpoints for container orchestration
- [ ] Configure auto-scaling for API and Celery workers
- [ ] Set up database backups and point-in-time recovery

## Mock Data Cleanup
- [ ] Gate mock data behind `NEXT_PUBLIC_USE_MOCKS=true` only (currently default)
- [ ] Remove or reduce mock data in production builds
- [ ] Add seed data command that populates DB with demo events for new deployments

## UX Enhancements
- [ ] Ticker search autocomplete: show all matching tickers when typing (e.g. "G" → GOOG, GS, GM, etc.) with dropdown results

## Data Model Enhancements
- [ ] Support multiple companies per user (change 1:1 to 1:many)
- [ ] Add user preferences table (notification settings, theme, etc.)
- [ ] Add audit log for tracking changes to company profiles
- [ ] Add event categories/tags as a separate table for flexible filtering
