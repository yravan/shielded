"""Fetch live fixture data from Kalshi and Polymarket APIs.

Saves 50 events per source as individual JSON files:
  tests/fixtures/kalshi/{event_ticker}.json    — raw event from /events endpoint
  tests/fixtures/kalshi/{event_ticker}_markets/ — raw market detail per child market
  tests/fixtures/polymarket/{slug}.json        — raw event from Gamma /events endpoint
  tests/fixtures/polymarket/{slug}_markets/    — raw Gamma + CLOB market detail per child

All responses saved faithfully as returned by the API with no modification.

Usage: cd backend && uv run python app/ingestion/scripts/fetch_fixtures.py
"""

import asyncio
import base64
import json
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import httpx
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

# Add backend to path so we can import app.config
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from app.config import settings

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "tests" / "fixtures"
MAX_EVENTS = 50
MAX_CONCURRENT = 5  # max concurrent API requests per source
RETRY_BACKOFF = [0.5, 1.0, 2.0]  # retry delays for 429s


async def _request_with_retry(coro_factory):
    """Call coro_factory() up to len(RETRY_BACKOFF)+1 times, retrying on 429."""
    for attempt in range(len(RETRY_BACKOFF) + 1):
        resp = await coro_factory()
        if resp.status_code != 429:
            resp.raise_for_status()
            return resp
        if attempt < len(RETRY_BACKOFF):
            await asyncio.sleep(RETRY_BACKOFF[attempt])
    resp.raise_for_status()  # final 429 → raise
    return resp  # unreachable but keeps type checkers happy


# ---------------------------------------------------------------------------
# Kalshi auth helpers
# ---------------------------------------------------------------------------

def _load_kalshi_private_key():
    key_path = Path(settings.KALSHI_API_KEY)
    if not key_path.is_absolute():
        key_path = Path(__file__).resolve().parents[3] / key_path
    return serialization.load_pem_private_key(key_path.read_bytes(), password=None)


def _sign_request(private_key, timestamp_ms: int, method: str, path: str) -> str:
    message = f"{timestamp_ms}{method}{path}".encode()
    signature = private_key.sign(
        message,
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
        hashes.SHA256(),
    )
    return base64.b64encode(signature).decode()


def _kalshi_headers(private_key, method: str, url: str) -> dict:
    timestamp_ms = int(time.time() * 1000)
    path = urlparse(url).path
    sig = _sign_request(private_key, timestamp_ms, method.upper(), path)
    return {
        "KALSHI-ACCESS-KEY": settings.KALSHI_KEY_ID,
        "KALSHI-ACCESS-SIGNATURE": sig,
        "KALSHI-ACCESS-TIMESTAMP": str(timestamp_ms),
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


# ---------------------------------------------------------------------------
# Classification helpers (for display only — no data modification)
# ---------------------------------------------------------------------------

def classify_kalshi_event(event: dict) -> str:
    markets = event.get("markets", [])
    if len(markets) <= 1:
        return "binary"
    return "qualitative"


def classify_polymarket_event(event: dict) -> str:
    markets = event.get("markets", [])
    if len(markets) <= 1:
        return "binary"
    if event.get("estimateValue") and not event.get("cantEstimate"):
        return "quantitative"
    with_bounds = sum(
        1 for m in markets
        if m.get("lowerBound") is not None or m.get("upperBound") is not None
    )
    if with_bounds == len(markets):
        return "quantitative"
    return "qualitative"


# ---------------------------------------------------------------------------
# Kalshi fetching
# ---------------------------------------------------------------------------

async def _fetch_kalshi_event(sem, client, private_key, base, out_dir, event, index, total):
    """Fetch all detail data for a single Kalshi event concurrently."""
    event_ticker = event.get("event_ticker", f"unknown_{index}")

    # Save the raw event as-is from the /events endpoint
    out_path = out_dir / f"{event_ticker}.json"
    out_path.write_text(json.dumps(event, indent=2))

    api_markets = event.get("markets", [])
    if api_markets:
        mkt_dir = out_dir / f"{event_ticker}_markets"
        mkt_dir.mkdir(exist_ok=True)

        async def _fetch_market_detail(mkt):
            ticker = mkt.get("ticker", "")
            try:
                async with sem:
                    mkt_url = f"{base}/markets/{ticker}"
                    resp = await _request_with_retry(
                        lambda u=mkt_url: client.get(u, headers=_kalshi_headers(private_key, "GET", u))
                    )
                    mkt_detail = resp.json()
                (mkt_dir / f"{ticker}.json").write_text(json.dumps(mkt_detail, indent=2))
            except Exception as e:
                print(f"    WARN: Failed to fetch market detail {ticker}: {e}")

        async def _fetch_event_detail():
            try:
                async with sem:
                    evt_url = f"{base}/events/{event_ticker}"
                    resp = await _request_with_retry(
                        lambda u=evt_url: client.get(u, headers=_kalshi_headers(private_key, "GET", u))
                    )
                    evt_detail = resp.json()
                (mkt_dir / f"{event_ticker}_detail.json").write_text(json.dumps(evt_detail, indent=2))
            except Exception as e:
                print(f"    WARN: Failed to fetch event detail {event_ticker}: {e}")

        async def _fetch_candlesticks(mkt):
            ticker = mkt.get("ticker", "")
            series_ticker = event.get("series_ticker")
            if not series_ticker:
                return
            end_ts = int(time.time())
            start_ts_30d = end_ts - (30 * 24 * 3600)
            start_ts_1d = end_ts - (24 * 3600)
            # Daily candlesticks (30 days)
            try:
                async with sem:
                    candle_url = f"{base}/series/{series_ticker}/markets/{ticker}/candlesticks"
                    resp = await _request_with_retry(
                        lambda u=candle_url: client.get(u, headers=_kalshi_headers(private_key, "GET", u), params={
                            "period_interval": 1440,
                            "start_ts": start_ts_30d,
                            "end_ts": end_ts,
                        })
                    )
                    daily_data = resp.json()
                (mkt_dir / f"{ticker}_candlesticks_daily.json").write_text(json.dumps(daily_data, indent=2))
            except Exception as e:
                print(f"    WARN: Failed to fetch daily candlesticks {ticker}: {e}")
            # Hourly candlesticks (1 day)
            try:
                async with sem:
                    candle_url = f"{base}/series/{series_ticker}/markets/{ticker}/candlesticks"
                    resp = await _request_with_retry(
                        lambda u=candle_url: client.get(u, headers=_kalshi_headers(private_key, "GET", u), params={
                            "period_interval": 60,
                            "start_ts": start_ts_1d,
                            "end_ts": end_ts,
                        })
                    )
                    hourly_data = resp.json()
                (mkt_dir / f"{ticker}_candlesticks_hourly.json").write_text(json.dumps(hourly_data, indent=2))
            except Exception as e:
                print(f"    WARN: Failed to fetch hourly candlesticks {ticker}: {e}")

        # Gather all HTTP work for this event concurrently
        tasks = [_fetch_event_detail()]
        for mkt in api_markets:
            tasks.append(_fetch_market_detail(mkt))
            tasks.append(_fetch_candlesticks(mkt))
        await asyncio.gather(*tasks)

    etype = classify_kalshi_event(event)
    strike_types = set(m.get("strike_type", "") for m in api_markets if m.get("strike_type"))
    has_floor = any(m.get("floor_strike") is not None for m in api_markets)
    has_cap = any(m.get("cap_strike") is not None for m in api_markets)
    title = event.get("title", "")[:60]
    strikes_str = str(strike_types) if strike_types else "∅"
    print(f"  [{index+1:2d}/{total}] {etype:13s} | {event_ticker:30s} | strikes={strikes_str:30s} | floor={has_floor} cap={has_cap} | {title}")


async def fetch_kalshi_fixtures(client: httpx.AsyncClient):
    if not settings.KALSHI_API_KEY or not settings.KALSHI_KEY_ID:
        print("SKIP: KALSHI_API_KEY/KALSHI_KEY_ID not set, skipping Kalshi")
        return

    private_key = _load_kalshi_private_key()
    base = settings.KALSHI_API_URL
    out_dir = FIXTURES_DIR / "kalshi"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("\n=== KALSHI: Fetching events ===")
    events = []
    cursor = None

    while len(events) < MAX_EVENTS:
        url = f"{base}/events"
        params = {"limit": 100, "status": "open", "with_nested_markets": "true"}
        if cursor:
            params["cursor"] = cursor
        headers = _kalshi_headers(private_key, "GET", url)
        resp = await client.get(url, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()
        page_events = data.get("events", [])
        cursor = data.get("cursor")

        events.extend(page_events)
        print(f"  Fetched page: {len(page_events)} events (total: {len(events)})")

        if not page_events or not cursor:
            break

    events = events[:MAX_EVENTS]
    print(f"  Saving {len(events)} events...")

    sem = asyncio.Semaphore(MAX_CONCURRENT)
    await asyncio.gather(*[
        _fetch_kalshi_event(sem, client, private_key, base, out_dir, event, i, len(events))
        for i, event in enumerate(events)
    ])

    # -------------------------------------------------------------------
    # Kalshi global / taxonomy fetches
    # -------------------------------------------------------------------

    print("\n  --- Kalshi global fetches ---")

    # (f) Tags by categories
    try:
        tags_url = f"{base}/search/tags_by_categories"
        headers = _kalshi_headers(private_key, "GET", tags_url)
        resp = await client.get(tags_url, headers=headers)
        resp.raise_for_status()
        (out_dir / "_tags_by_categories.json").write_text(json.dumps(resp.json(), indent=2))
        print("  Saved _tags_by_categories.json")
    except Exception as e:
        print(f"  WARN: Failed to fetch tags_by_categories: {e}")

    # (h) Series listing
    try:
        series_url = f"{base}/series"
        headers = _kalshi_headers(private_key, "GET", series_url)
        resp = await client.get(series_url, headers=headers, params={"limit": 100})
        resp.raise_for_status()
        (out_dir / "_series.json").write_text(json.dumps(resp.json(), indent=2))
        print("  Saved _series.json")
    except Exception as e:
        print(f"  WARN: Failed to fetch series: {e}")

    print(f"  Done: {len(events)} Kalshi events saved to {out_dir}")


# ---------------------------------------------------------------------------
# Polymarket fetching
# ---------------------------------------------------------------------------

async def _fetch_polymarket_event(sem, client, gamma_url, clob_url, out_dir, event, index, total):
    """Fetch all detail data for a single Polymarket event concurrently."""
    slug = event.get("slug", f"unknown_{index}")
    safe_slug = slug.replace("/", "_")[:100]

    # Save the raw event as-is from the Gamma /events endpoint
    out_path = out_dir / f"{safe_slug}.json"
    out_path.write_text(json.dumps(event, indent=2))

    api_markets = event.get("markets", [])
    if api_markets:
        mkt_dir = out_dir / f"{safe_slug}_markets"
        mkt_dir.mkdir(exist_ok=True)

        async def _fetch_gamma_detail(mkt):
            condition_id = mkt.get("conditionId", "")
            short_id = condition_id[:16]
            try:
                async with sem:
                    resp = await _request_with_retry(
                        lambda cid=condition_id: client.get(f"{gamma_url}/markets/{cid}")
                    )
                    gamma_detail = resp.json()
                (mkt_dir / f"{short_id}_gamma.json").write_text(json.dumps(gamma_detail, indent=2))
            except Exception as e:
                if "404" not in str(e) and "422" not in str(e):
                    print(f"    WARN: Gamma market detail failed for {condition_id[:20]}...: {e}")

        async def _fetch_clob_detail(mkt):
            condition_id = mkt.get("conditionId", "")
            short_id = condition_id[:16]
            try:
                async with sem:
                    resp = await _request_with_retry(
                        lambda cid=condition_id: client.get(f"{clob_url}/markets/{cid}")
                    )
                    clob_detail = resp.json()
                (mkt_dir / f"{short_id}_clob.json").write_text(json.dumps(clob_detail, indent=2))
            except Exception:
                pass  # CLOB detail is best-effort

        async def _fetch_price_history(mkt):
            condition_id = mkt.get("conditionId", "")
            short_id = condition_id[:16]
            try:
                clob_token_ids_raw = mkt.get("clobTokenIds", "")
                if clob_token_ids_raw:
                    token_ids = json.loads(clob_token_ids_raw) if isinstance(clob_token_ids_raw, str) else clob_token_ids_raw
                    if token_ids:
                        token_id = token_ids[0]
                        async with sem:
                            prices_url = f"{clob_url}/prices-history"
                            resp = await _request_with_retry(
                                lambda tid=token_id: client.get(prices_url, params={
                                    "market": tid,
                                    "interval": "max",
                                    "fidelity": 60,
                                })
                            )
                            prices_data = resp.json()
                        (mkt_dir / f"{short_id}_prices.json").write_text(json.dumps(prices_data, indent=2))
            except Exception as e:
                print(f"    WARN: Failed to fetch price history for {condition_id[:20]}...: {e}")

        # Gather all HTTP work for this event concurrently
        tasks = []
        for mkt in api_markets:
            tasks.append(_fetch_gamma_detail(mkt))
            tasks.append(_fetch_clob_detail(mkt))
            tasks.append(_fetch_price_history(mkt))
        await asyncio.gather(*tasks)

    etype = classify_polymarket_event(event)
    has_ev = bool(event.get("estimateValue") and not event.get("cantEstimate"))
    est_val = event.get("estimatedValue")
    has_bounds = any(
        m.get("lowerBound") is not None or m.get("upperBound") is not None
        for m in api_markets
    )
    title = event.get("title", "")[:60]
    print(f"  [{index+1:2d}/{total}] {etype:13s} | {safe_slug:40s} | ev={has_ev} estVal={est_val!s:>10s} bounds={has_bounds} | {title}")


async def fetch_polymarket_fixtures(client: httpx.AsyncClient):
    gamma_url = settings.POLYMARKET_GAMMA_API_URL
    clob_url = settings.POLYMARKET_API_URL
    out_dir = FIXTURES_DIR / "polymarket"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("\n=== POLYMARKET: Fetching events ===")
    events = []
    offset = 0

    while len(events) < MAX_EVENTS:
        url = f"{gamma_url}/events"
        params = {"limit": 100, "active": "true", "closed": "false", "offset": offset}
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        raw = resp.json()
        page_events = raw if isinstance(raw, list) else raw.get("data", raw.get("events", []))

        events.extend(page_events)
        print(f"  Fetched page: {len(page_events)} events (total: {len(events)})")

        if not page_events or len(page_events) < 100:
            break
        offset += 100

    events = events[:MAX_EVENTS]
    print(f"  Saving {len(events)} events...")

    sem = asyncio.Semaphore(MAX_CONCURRENT)
    await asyncio.gather(*[
        _fetch_polymarket_event(sem, client, gamma_url, clob_url, out_dir, event, i, len(events))
        for i, event in enumerate(events)
    ])

    # -------------------------------------------------------------------
    # Polymarket global fetches
    # -------------------------------------------------------------------

    # Collect all token IDs from fetched events
    all_poly_token_ids = []
    for event in events:
        for mkt in event.get("markets", []):
            clob_token_ids_raw = mkt.get("clobTokenIds", "")
            try:
                if clob_token_ids_raw:
                    token_ids = json.loads(clob_token_ids_raw) if isinstance(clob_token_ids_raw, str) else clob_token_ids_raw
                    if token_ids:
                        all_poly_token_ids.append(token_ids[0])
            except Exception:
                pass

    print("\n  --- Polymarket global fetches ---")

    # (i) Full tag taxonomy
    try:
        resp = await client.get(f"{gamma_url}/tags")
        resp.raise_for_status()
        (out_dir / "_tags.json").write_text(json.dumps(resp.json(), indent=2))
        print("  Saved _tags.json")
    except Exception as e:
        print(f"  WARN: Failed to fetch Polymarket tags: {e}")

    # (j) Bulk midpoints
    if all_poly_token_ids:
        try:
            resp = await client.post(f"{clob_url}/midpoints", json={"token_ids": all_poly_token_ids})
            resp.raise_for_status()
            (out_dir / "_midpoints.json").write_text(json.dumps(resp.json(), indent=2))
            print("  Saved _midpoints.json")
        except Exception as e:
            print(f"  WARN: Failed to fetch bulk midpoints: {e}")

        # (k) Bulk spreads
        try:
            resp = await client.post(f"{clob_url}/spreads", json={"token_ids": all_poly_token_ids})
            resp.raise_for_status()
            (out_dir / "_spreads.json").write_text(json.dumps(resp.json(), indent=2))
            print("  Saved _spreads.json")
        except Exception as e:
            print(f"  WARN: Failed to fetch bulk spreads: {e}")

    print(f"  Done: {len(events)} Polymarket events saved to {out_dir}")


# ---------------------------------------------------------------------------
# Cleanup old fixtures
# ---------------------------------------------------------------------------

def cleanup_old_fixtures():
    """Remove old single-file fixtures."""
    old_files = [
        "kalshi_events_page.json",
        "kalshi_candlesticks.json",
        "kalshi_forecast_percentiles.json",
        "kalshi_market_detail.json",
        "polymarket_events_page.json",
        "polymarket_prices_history.json",
    ]
    print("\n=== Cleaning up old fixtures ===")
    for name in old_files:
        path = FIXTURES_DIR / name
        if path.exists():
            path.unlink()
            print(f"  Deleted: {name}")
        else:
            print(f"  Already gone: {name}")


# ---------------------------------------------------------------------------
# Summary analysis
# ---------------------------------------------------------------------------

def print_analysis():
    """Analyze fetched fixtures and print summary."""
    print("\n" + "=" * 70)
    print("  FIXTURE ANALYSIS")
    print("=" * 70)

    # Kalshi analysis
    kalshi_dir = FIXTURES_DIR / "kalshi"
    if kalshi_dir.exists():
        print("\n--- Kalshi ---")
        strike_types = {}
        qual_with_strikes = []
        total = 0
        type_counts = {"binary": 0, "qualitative": 0}

        for f in sorted(kalshi_dir.glob("*.json")):
            if f.name.startswith("_"):
                continue
            data = json.loads(f.read_text())
            total += 1
            etype = classify_kalshi_event(data)
            type_counts[etype] = type_counts.get(etype, 0) + 1

            for m in data.get("markets", []):
                st = m.get("strike_type", "")
                if st:
                    strike_types[st] = strike_types.get(st, 0) + 1

                if etype == "qualitative" and (m.get("floor_strike") is not None or m.get("cap_strike") is not None):
                    qual_with_strikes.append((data.get("event_ticker"), m.get("ticker"), st, m.get("floor_strike"), m.get("cap_strike")))

        print(f"  Total events: {total}")
        print(f"  By type: {type_counts}")
        print(f"  strike_type values: {dict(sorted(strike_types.items(), key=lambda x: -x[1]))}")
        if qual_with_strikes:
            print(f"  WARN: Qualitative events with floor/cap strikes:")
            for item in qual_with_strikes:
                print(f"    {item}")
        else:
            print(f"  OK: No qualitative events have floor_strike/cap_strike")

    # Polymarket analysis
    pm_dir = FIXTURES_DIR / "polymarket"
    if pm_dir.exists():
        print("\n--- Polymarket ---")
        total = 0
        type_counts = {"binary": 0, "qualitative": 0, "quantitative": 0}
        events_with_bounds = 0
        events_with_ev = 0

        for f in sorted(pm_dir.glob("*.json")):
            if f.name.startswith("_"):
                continue
            data = json.loads(f.read_text())
            total += 1
            etype = classify_polymarket_event(data)
            type_counts[etype] = type_counts.get(etype, 0) + 1

            if data.get("estimateValue") and not data.get("cantEstimate"):
                events_with_ev += 1

            has_bounds = any(
                m.get("lowerBound") is not None or m.get("upperBound") is not None
                for m in data.get("markets", [])
            )
            if has_bounds:
                events_with_bounds += 1

        print(f"  Total events: {total}")
        print(f"  By type: {type_counts}")
        print(f"  Events with estimateValue: {events_with_ev}")
        print(f"  Events with lowerBound/upperBound: {events_with_bounds}")

        print(f"\n  Quantitative event details:")
        for f in sorted(pm_dir.glob("*.json")):
            if f.name.startswith("_"):
                continue
            data = json.loads(f.read_text())
            if classify_polymarket_event(data) == "quantitative":
                markets = data.get("markets", [])
                bounds_info = []
                for m in markets[:3]:
                    lb = m.get("lowerBound")
                    ub = m.get("upperBound")
                    bounds_info.append(f"[{lb}-{ub}]")
                print(f"    {f.stem[:40]:40s} | ev={data.get('estimatedValue')!s:>10s} | bounds: {' '.join(bounds_info)}")

    print("\n" + "=" * 70)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main():
    print("Fetching live fixtures from Kalshi and Polymarket APIs...")
    print(f"Output: {FIXTURES_DIR}")

    async with httpx.AsyncClient(timeout=30.0) as client:
        await asyncio.gather(
            fetch_kalshi_fixtures(client),
            fetch_polymarket_fixtures(client),
        )

    cleanup_old_fixtures()
    print_analysis()

    print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
