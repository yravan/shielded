# API Reference: Kalshi & Polymarket

Source of truth for the ingestion layer. Updated with corrections from real API exploration.

---

## Kalshi API

**Base URL**: `https://api.elections.kalshi.com/trade-api/v2`

### Authentication

RSA-PSS signed headers. Sign `{timestamp_ms}{METHOD}{path_without_query}` with SHA256.

Headers:
- `KALSHI-ACCESS-KEY` — API key ID
- `KALSHI-ACCESS-SIGNATURE` — base64-encoded RSA-PSS signature
- `KALSHI-ACCESS-TIMESTAMP` — millisecond timestamp used in signature

### Rate Limits

Basic tier: 20 reads/sec.

### GET /events — Event Discovery

**Params**: `limit` (max 200), `cursor`, `status` (open/closed/settled), `with_nested_markets` (bool), `series_ticker`, `min_close_ts`, `min_updated_ts`

**Response**: `{ events: EventData[], cursor: string }`

> **NOTE**: Excludes multivariate events (use `/events/multivariate` for those).

**EventData fields**:
| Field | Type | Notes |
|---|---|---|
| `event_ticker` | string | Primary identifier |
| `series_ticker` | string | Series grouping |
| `title` | string | |
| `sub_title` | string | |
| `category` | string | e.g. "World", "Climate and Weather", "Science and Technology" |
| `mutually_exclusive` | bool | |
| `strike_date` | string | **Always None in practice** |
| `strike_period` | string | Can be empty string |
| `markets` | Market[] | Only if `with_nested_markets=true` |

### Market Object

Nested in events (with `with_nested_markets=true`) or from `GET /markets/{ticker}`.

| Field | Type | Notes |
|---|---|---|
| `ticker` | string | Market identifier |
| `event_ticker` | string | Parent event |
| `market_type` | string | `binary` or `scalar` |
| `yes_sub_title` | string | **NOT** `subtitle` (deprecated, always empty) |
| `no_sub_title` | string | |
| `last_price_dollars` | string | FixedPointDollars: `"0.5600"` |
| `yes_bid_dollars` | string | FixedPointDollars |
| `yes_ask_dollars` | string | FixedPointDollars |
| `previous_price_dollars` | string | FixedPointDollars |
| `volume_fp` | string | FixedPointCount: `"1234.00"` |
| `volume_24h_fp` | string | FixedPointCount |
| `open_interest_fp` | string | FixedPointCount |
| `close_time` | string | ISO datetime |
| `open_time` | string | ISO datetime |
| `expected_expiration_time` | string | ISO datetime |
| `latest_expiration_time` | string | ISO datetime |
| `status` | string | initialized/inactive/active/closed/determined/finalized |
| `can_close_early` | bool | |
| `rules_primary` | string | Resolution rules |
| `notional_value_dollars` | string | FixedPointDollars |
| `liquidity_dollars` | string | FixedPointDollars |
| `settlement_timer_seconds` | int | |
| `price_ranges` | array | Price range objects |

> **NOTE**: `series_ticker` is **NOT available on market detail responses** (`GET /markets/{ticker}`). Only available on event-level responses. The `subtitle` field is deprecated and always empty — use `yes_sub_title` instead.

**FixedPointDollars**: String like `"0.5600"` — parse with `float()`.
**FixedPointCount**: String like `"1234.00"` — parse with `float()`.

### GET /markets — List Markets

**Params**: `event_ticker` (filter by single event), `tickers` (comma-separated), `status`, `limit` (max 1000), `cursor`

### GET /markets/{ticker} — Single Market Detail

Returns full Market object. **Does NOT include `series_ticker`.**

### GET /series/{series_ticker}/markets/{ticker}/candlesticks — Price History

**Params**: `start_ts` (unix seconds), `end_ts` (unix seconds), `period_interval` (1, 60, or 1440 minutes)

**Response** (corrected from real API):
```json
{
  "ticker": "...",
  "candlesticks": [
    {
      "end_period_ts": 1234567890,
      "price": {
        "open_dollars": "0.5600",
        "close_dollars": "0.5700",
        "high_dollars": "0.5900",
        "low_dollars": "0.5500",
        "mean_dollars": "0.5650",
        "previous_dollars": "0.5500"
      },
      "volume_fp": "100.00",
      "open_interest_fp": "500.00",
      "yes_ask": {
        "open_dollars": "0.5700",
        "close_dollars": "0.5800",
        "high_dollars": "0.6000",
        "low_dollars": "0.5600"
      },
      "yes_bid": {
        "open_dollars": "0.5500",
        "close_dollars": "0.5600",
        "high_dollars": "0.5800",
        "low_dollars": "0.5400"
      }
    }
  ]
}
```

> **CORRECTION**: Price fields use `*_dollars` suffix (`close_dollars`, NOT `close`). Candlesticks also include `yes_ask` and `yes_bid` OHLC objects (not documented).

### GET /historical/markets/{ticker}/candlesticks — Settled Market History

Same schema as above, for markets beyond the active cutoff.

### GET /series/{series}/events/{ticker}/candlesticks — Event-Level Candlesticks

Aggregated across all markets in the event.

**Response**: `{ market_tickers[], market_candlesticks[][], adjusted_end_ts }`

### GET /series/{series}/events/{ticker}/forecast_percentile_history — EV Timeseries

**Params**: `percentiles` (int array, 0-10000 representing 0.00%-100.00%), `start_ts`, `end_ts`, `period_interval` (0=5sec, 1, 60, 1440)

> **CORRECTION**: `percentiles` must be passed as repeated query params (`percentiles=2500&percentiles=5000`), NOT comma-separated. In httpx, pass as `params={"percentiles": [2500, 5000, 7500]}`.

**Response**:
```json
{
  "forecast_history": [
    {
      "event_ticker": "...",
      "end_period_ts": 1234567890,
      "percentile_values": {
        "raw": [4.0, 4.15, 4.35],
        "processed": [4.0, 4.15, 4.35],
        "formatted": ["4.00%", "4.15%", "4.35%"]
      }
    }
  ]
}
```

> **This gives us EV history directly from Kalshi** — much better than computing client-side.

---

## Polymarket APIs

### Gamma API — Event Discovery

**Base URL**: `https://gamma-api.polymarket.com`
**Auth**: None required.
**Rate limits**: 500 req/10s on `/events`, 300 req/10s on `/markets`.

### GET /events

**Params**: `limit`, `offset`, `active`, `closed`, `archived`, `featured`, `liquidity_min/max`, `volume_min/max`, `start_date_min/max`, `end_date_min/max`, `tag_id`, `order`, `ascending`

**Response**: Array of Event objects.

**Event fields**:
| Field | Type | Notes |
|---|---|---|
| `id` | string | Primary identifier |
| `ticker` | string | |
| `slug` | string | URL slug |
| `title` | string | |
| `subtitle` | string | |
| `description` | string | |
| `startDate` | string | ISO datetime |
| `endDate` | string | ISO datetime |
| `image` | string | URL |
| `icon` | string | URL |
| `active` | bool | |
| `closed` | bool | |
| `category` | string | **ALWAYS None** — use `tags[]` instead |
| `subcategory` | string | **ALWAYS None** — use `tags[]` instead |
| `volume` | number | |
| `volume24hr` | number | |
| `volume1wk` | number | |
| `volume1mo` | number | |
| `liquidity` | number | |
| `openInterest` | number | |
| `commentCount` | number | |
| `negRisk` | bool | Affects multi-market on-chain behavior |
| `tags` | Tag[] | **Real categorization data** |
| `markets` | Market[] | Nested |

**Tag object**: `{ id, label, slug, forceShow?, createdAt, updatedAt }`

> **CORRECTION**: `category` and `subcategory` are **ALWAYS `None`**. The `tags[]` array has the real categorization data. Tags are rich objects with `label` and `slug` fields. Example tags: "Politics", "Finance", "Crypto", "World", "Geopolitics", "France", "China".

### Market Object (Gamma)

| Field | Type | Notes |
|---|---|---|
| `conditionId` | string | On-chain condition identifier |
| `question` | string | Market question text |
| `questionID` | string | Hash used for resolution |
| `clobTokenIds` | string | **JSON string**: `"[\"token1\",\"token2\"]"`. Token[0]=Yes, Token[1]=No |
| `outcomePrices` | string | **JSON string** — can contain string numbers: `"[\"0\", \"1\"]"` |
| `lastTradePrice` | number | 0-1 |
| `bestBid` | number | |
| `bestAsk` | number | |
| `spread` | number | |
| `oneDayPriceChange` | number | |
| `oneWeekPriceChange` | number | |
| `oneMonthPriceChange` | number | |
| `volume` | string | String representation |
| `volumeNum` | number | Numeric volume — **use this, not `volume`** |
| `volume24hr` | number | |
| `volume1wk` | number | |
| `volume1mo` | number | |
| `liquidityNum` | number | |
| `endDate` | string | |
| `startDate` | string | |
| `createdAt` | string | |
| `updatedAt` | string | |
| `active` | bool | |
| `closed` | bool | **Can be true while parent event is active** |
| `image` | string | URL |
| `icon` | string | URL |
| `groupItemTitle` | string | Label for multi-market events (e.g., "December 31, 2025") |
| `negRisk` | bool | |

> **CORRECTION**: `outcomePrices` can contain string numbers (`"[\"0\", \"1\"]"`), not just numeric arrays. Must `float()` each element after `json.loads()`. Child markets can be `closed: true` while parent event is `active: true` (time-series events). `groupItemTitle` provides the market label for multi-market events.

### CLOB API — Price History

**Base URL**: `https://clob.polymarket.com`
**Auth**: None required for reads.
**Rate limits**: 1000 req/10s on `/prices-history`.

### GET /prices-history

**Params**:
- `market` (required) — **CLOB token ID**, NOT condition_id
- `startTs`, `endTs` — unix timestamps
- `interval` — `max`, `all`, `1m`, `1w`, `1d`, `6h`, `1h`
- `fidelity` — minutes, default 1

**Response**: `{ history: [{ t, p }] }` or direct array of `{ t, p }` points.

### Token Resolution

**Key insight**: The `clobTokenIds` field on Gamma market objects already contains the token IDs needed for `/prices-history`. No extra CLOB API call is needed.

```
clobTokenIds = "[\"token_yes\",\"token_no\"]"
json.loads(clobTokenIds)[0]  # Yes token → use for /prices-history
```

> **CORRECTION**: The Gamma `GET /markets?condition_id=X` endpoint is **unreliable** — it can return a completely wrong market. Use `clobTokenIds` from the nested event market objects directly. Zero extra API calls needed.

---

## Field Mapping: What We Want → How We Get It

### Per Event
| Our field | Kalshi source | Polymarket source |
|---|---|---|
| source_id (event) | `event_ticker` | `event.id` |
| title | `event.title` | `event.title` |
| description | `event.sub_title` | `event.description` |
| category | `event.category` (lowercase) | `tags[].label` → category mapping |
| region | keyword inference | `tags[].label` → region mapping, text fallback |
| source_url | `https://kalshi.com/events/{event_ticker}` | `https://polymarket.com/event/{slug}` |
| image_url | — | `event.image` |
| tags | — | `[tag.label for tag in event.tags]` |
| resolution_date | `market.close_time` | `event.endDate` |
| status | map from `market.status` | `active`/`closed` booleans |
| is_parent | `len(markets) > 1` | `len(markets) > 1` |
| mutually_exclusive | `event.mutually_exclusive` | infer from market count |
| volume | `float(market.volume_fp)` | `event.volume` |
| series_ticker | `event.series_ticker` | — |

### Per Market/Child
| Our field | Kalshi source | Polymarket source |
|---|---|---|
| source_id (market) | `market.ticker` | `market.conditionId` |
| title/question | `market.yes_sub_title` | `market.question` |
| probability | `float(market.last_price_dollars)` | `market.lastTradePrice` |
| outcome_label | `market.yes_sub_title` | `market.groupItemTitle` or `market.question` |
| outcome_value | parsed numeric from label | parsed numeric from label |
| volume | `float(market.volume_fp)` | `market.volumeNum` |
| clob_token_id | — | `json.loads(market.clobTokenIds)[0]` |
| series_ticker | `event.series_ticker` | — |
| is_closed | — | `market.closed` |
| group_item_title | — | `market.groupItemTitle` |

### Per Price Point
| Our field | Kalshi source | Polymarket source |
|---|---|---|
| timestamp | `candlestick.end_period_ts` | `point.t` |
| probability | `float(candlestick.price.close_dollars)` | `point.p` |
| volume | `float(candlestick.volume_fp)` | — |

### EV History
| Source | Method |
|---|---|
| Kalshi | Deferred — `forecast_percentile_history` returns 400 for numeric-strike events with `mutually_exclusive=False` |
| Polymarket | Computed client-side from children price histories |

---

## Available Endpoints — Full Inventory

> **Note:** This section replaces the memory-based reference. This document is the canonical endpoint inventory.

### Currently Used (15 total)

**Kalshi (8):**
1. `GET /events` — Event discovery with nested markets (excludes multivariate)
2. `GET /events/{event_ticker}` — Event detail for series_ticker resolution
3. `GET /markets/{ticker}` — Single market detail
4. `GET /series/{series}/markets/{ticker}/candlesticks` — Market price history
5. `GET /search/tags_by_categories` — Tag taxonomy
6. `GET /events/multivariate` — Compound/multivariate events (with `with_nested_markets=true`, `status=open`)
7. `GET /series` — Series listing

> **Removed:** `forecast_percentile_history` (returns 400 for numeric-strike events with `mutually_exclusive=False`), `GET /markets/candlesticks/batch` (unused in code).

**Polymarket (7):**
1. `GET /events` (Gamma) — Event discovery
2. `GET /markets/{conditionId}` (Gamma) — Market detail
3. `GET /markets/{conditionId}` (CLOB) — CLOB market detail
4. `GET /prices-history` (CLOB) — Price history by token ID
5. `GET /tags` (Gamma) — Tag taxonomy
6. `POST /midpoints` (CLOB) — Bulk midpoint prices
7. `POST /spreads` (CLOB) — Bulk bid-ask spreads

### Available for Future Use

**Kalshi:**
- `GET /markets` — List/filter markets (with event_ticker, tickers params)
- `GET /historical/markets/{ticker}/candlesticks` — Settled market history
- `GET /series/{series}/events/{event}/candlesticks` — Event-level aggregated candlesticks
- `GET /series/{series}/events/{event}/forecast_percentile_history` — EV timeseries (deferred: returns 400 for events with `mutually_exclusive=False`)
- `GET /markets/candlesticks/batch` — Batch candlesticks for multiple markets
- `GET /markets/{ticker}/orderbook` — Live orderbook
- `GET /exchange/schedule` — Exchange trading schedule
- `GET /portfolio/positions` — User portfolio positions (requires auth)

**Polymarket:**
- `GET /markets` (CLOB) — List/search markets
- `GET /book` (CLOB) — Orderbook for a token
- `GET /neg-risk` (CLOB) — Negative risk parameters
- `GET /sampling-simplified-markets` (CLOB) — Featured/simplified markets
- `GET /notifications/` (CLOB) — Market notifications
- `GET /tick-sizes` (CLOB) — Tick size configuration
