# Changelog

All notable changes to Shielded are documented here.

---

## 2026-03-13 — Explore Page Fixes & Geopolitical Relevance Filter

### Added
- **Geopolitical relevance filter at ingestion** — Both Polymarket and Kalshi now filter events at fetch time using keyword/tag matching against ~80 geopolitical, trade, regulatory, conflict, climate, and economic terms. Polymarket dropped from ~8,100 to ~3,200 events; Kalshi from ~1,800 to ~930. Filter defined in `ingestion/base.py:is_event_relevant()`, applied in both `polymarket.py` and `kalshi.py` `fetch_events_page()`.
- **"Track All" button on multimarket cards** — `ParentEventCard` now has a Track All/Tracked button that tracks/untracks all child markets. Shows "Tracked" state when all children are tracked.

### Fixed
- **Filter expired/resolved child markets** — Closed (`is_closed`) and resolved (`probability >= 0.99`) child markets are now stripped from parent events in `tasks/discovery.py` before Redis cache and Postgres upsert. Kalshi `NormalizedMarket` now sets `is_closed` based on market `status` and `close_time`.
- **"Event not found" on multimarket click** — Moved `cache.set_all_events()` to after `session.commit()` in `tasks/discovery.py`. Previously Redis was populated before Postgres commit, creating a window where events appeared on explore with `UUID(int=0)` and returned 404 on click-through.
- **Interleave Kalshi and Polymarket events** — `explore_events()` now shuffles the event list when using default "updated" sort instead of appending sources sequentially.

### Changed
- **Compact multimarket cards** — Removed sparklines and `useEventHistory` hook calls from `ChildMarketRow` (eliminates N extra API calls per parent card on explore). Child titles now strip redundant parent title prefix. Card spacing tightened (`gap-2` → `gap-1.5`, child row padding reduced).

---

## 2026-03-13

### Removed
- **Quantitative event classification** — dropped entirely. `forecast_percentile_history` returns 400 for all numeric-strike events with `mutually_exclusive=False`. Events are now classified as **binary** (1 market) or **qualitative** (2+ markets) only.
- `is_quantitative_event()` from `ingestion/ev.py`
- `fetch_forecast_percentiles()` from `ingestion/kalshi.py`
- Forecast percentile polling block from `tasks/polling.py`
- Kalshi EV computation from `tasks/discovery.py` (now a no-op for Kalshi; Polymarket EV stays)
- Percentile fetching from `scripts/fetch_fixtures.py`
- `tests/test_ev.py` (tested the removed function)
- **Multivariate event ingestion** — Kalshi's `/events/multivariate` endpoint returns combo/parlay sub-markets (e.g., Oscar parlay permutations), not top-level multivariate events. Irrelevant to geopolitical risk analysis and stalled the fixture pipeline.
- `KalshiClient.fetch_multivariate_events_page()`
- `KalshiClient.fetch_all_events()` override (base class version used instead)
- Multivariate fixture fetching in `scripts/fetch_fixtures.py`
- Multivariate fixture files (`_multivariate_events.json`, `mv_*.json`)

### Fixed
- **Kalshi price history staircase** — switched from last-trade price to bid/ask midpoint for candlestick pricing, matching Kalshi's own chart. Falls back to trade close for candles with no bid/ask data.
- **Kalshi child market 404s** — progressive event ticker resolution: for deeply-nested child tickers (e.g. `KXNEWPOPE-70-PPAR`), progressively strips trailing segments to find the parent event and resolve `series_ticker`.
- **Removed forward-fill from price history** — both Kalshi and Polymarket `fetch_prices()` now return only real API data points. Forward-fill created fake flat segments in low-liquidity markets (e.g. 16-day staircase at $0.595). Charts now connect real data points with diagonal lines, matching Kalshi's own chart behavior.
- **Verify script y-axis** — auto-scaled y-axis to data range with padding instead of hardcoded 0–1, matching Kalshi's chart style.

### Changed
- `classify_kalshi_event()` simplified: binary if <=1 market, qualitative otherwise (removed `_NUMERIC_STRIKE_TYPES`, `"mixed"`, `"quantitative"` buckets)
- `api-reference.md` updated: `forecast_percentile_history` and `candlesticks/batch` moved from "Currently Used" to "Available for Future Use"

### Deferred
- **Polymarket midpoint pricing** — `/prices-history` only returns last-trade price. `POST /midpoints`, `POST /spreads`, and `GET /book` are current-snapshot-only (no historical data). Using last-trade for now since PM markets are more liquid. Future option: poll orderbook on Celery interval to build midpoint history over time.
