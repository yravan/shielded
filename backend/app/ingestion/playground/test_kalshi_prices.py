"""Test Kalshi candlestick and forecast percentile fetching for all 3 event types.

Usage: cd backend && uv run python -m playground.test_kalshi_prices
"""

import asyncio
import base64
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import httpx
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

from app.config import settings

PERIOD_DAILY = 1440
PERIOD_HOURLY = 60


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

def _load_private_key():
    key_path = Path(settings.KALSHI_API_KEY)
    if not key_path.is_absolute():
        key_path = Path(__file__).resolve().parents[1] / key_path
    return serialization.load_pem_private_key(key_path.read_bytes(), password=None)


def _sign_request(private_key, timestamp_ms: int, method: str, path: str) -> str:
    message = f"{timestamp_ms}{method}{path}".encode()
    signature = private_key.sign(
        message,
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
        hashes.SHA256(),
    )
    return base64.b64encode(signature).decode()


def _signed_headers(private_key, method: str, url: str) -> dict:
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
# Classification helpers
# ---------------------------------------------------------------------------

_NUMERIC_STRIKE_TYPES = {
    "greater", "greater_or_equal", "less", "less_or_equal",
    "between", "functional", "structured",
}


def _classify_event(event: dict) -> str:
    """Returns 'binary', 'qualitative', or 'quantitative' using API strike_type."""
    markets = event.get("markets", [])
    if len(markets) <= 1:
        return "binary"
    numeric = sum(
        1 for m in markets
        if m.get("strike_type", "") in _NUMERIC_STRIKE_TYPES
    )
    if numeric == len(markets):
        return "quantitative"
    return "qualitative"


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

def _print_header(text: str):
    print(f"\n{'=' * 70}")
    print(f"  {text}")
    print(f"{'=' * 70}")


def _print_event_meta(event: dict):
    print(f"  Title:          {event.get('title')}")
    print(f"  Event ticker:   {event.get('event_ticker')}")
    print(f"  Series ticker:  {event.get('series_ticker')}")
    print(f"  Category:       {event.get('category')}")
    markets = event.get("markets", [])
    print(f"  Markets:        {len(markets)}")


def _print_candlesticks(candlesticks: list, label: str = ""):
    if label:
        print(f"\n  --- Candlesticks: {label} ---")
    print(f"  Data points: {len(candlesticks)}")
    if not candlesticks:
        print("  (no data)")
        return
    print(f"\n  Raw (first 3):")
    print(json.dumps(candlesticks[:3], indent=2))
    print(f"\n  Parsed (all {len(candlesticks)} points):")
    last_close = None
    for c in candlesticks:
        ts = c.get("end_period_ts")
        price = c.get("price", {})
        close = price.get("close_dollars")
        vol = c.get("volume_fp", "?")
        dt = datetime.fromtimestamp(ts).strftime("%Y-%m-%d") if ts else "?"
        tag = ""
        if close is not None:
            last_close = close
        elif last_close is not None:
            close = last_close
            tag = " [ffill]"
        else:
            close = "?"
        print(f"    {dt} | close={close} | vol={vol}{tag}")


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------

async def _fetch_candlesticks(
    client: httpx.AsyncClient, private_key, base: str,
    series_ticker: str, market_ticker: str,
    start_ts: int, end_ts: int,
    period_interval: int = PERIOD_DAILY,
) -> list:
    """Fetch candlesticks for a single market."""
    url = f"{base}/series/{series_ticker}/markets/{market_ticker}/candlesticks"
    params = {"start_ts": start_ts, "end_ts": end_ts, "period_interval": period_interval}
    headers = _signed_headers(private_key, "GET", url)
    resp = await client.get(url, headers=headers, params=params)
    resp.raise_for_status()
    return resp.json().get("candlesticks", [])


async def _fetch_forecast_percentiles(
    client: httpx.AsyncClient, private_key, base: str,
    series_ticker: str, event_ticker: str,
    start_ts: int, end_ts: int,
) -> list:
    """Fetch forecast percentile history for a quantitative event."""
    url = f"{base}/series/{series_ticker}/events/{event_ticker}/forecast_percentile_history"
    params = {
        "percentiles": "2500,5000,7500",
        "start_ts": start_ts,
        "end_ts": end_ts,
        "period_interval": PERIOD_DAILY,
    }
    headers = _signed_headers(private_key, "GET", url)
    resp = await client.get(url, headers=headers, params=params)
    resp.raise_for_status()
    return resp.json().get("forecast_history", [])


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

async def _discover_events(
    client: httpx.AsyncClient, private_key, base: str,
) -> dict[str, dict]:
    """Paginate through events to find one of each type: binary, qualitative, quantitative."""
    found: dict[str, dict] = {}
    needed = {"binary", "qualitative", "quantitative"}
    cursor = None
    total_seen = 0

    while needed and total_seen < 200:
        url = f"{base}/events"
        params: dict = {
            "limit": 100,
            "status": "open",
            "with_nested_markets": "true",
        }
        if cursor:
            params["cursor"] = cursor
        headers = _signed_headers(private_key, "GET", url)
        resp = await client.get(url, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()
        events = data.get("events", [])
        cursor = data.get("cursor")

        for ev in events:
            total_seen += 1
            etype = _classify_event(ev)
            if etype in needed:
                found[etype] = ev
                needed.discard(etype)
                print(f"  Found {etype:15s} → {ev.get('event_ticker')} — {ev.get('title', '')[:60]}")
                if not needed:
                    break

        if not events or not cursor:
            break

    print(f"  Scanned {total_seen} events total")
    return found


# ---------------------------------------------------------------------------
# Test sections
# ---------------------------------------------------------------------------

async def _test_binary(client, private_key, base, event, start_ts, end_ts):
    _print_header("[BINARY] Single-market event")
    _print_event_meta(event)

    markets = event.get("markets", [])
    if not markets:
        print("  ERROR: No markets in event")
        return

    market = markets[0]
    ticker = market["ticker"]
    series_ticker = event.get("series_ticker", "")
    print(f"\n  Market ticker:  {ticker}")
    print(f"  Last price:     {market.get('last_price_dollars')}")

    # Interval loop: (label, window_seconds, period_interval)
    intervals = [
        ("1d-hourly", 1 * 24 * 3600, PERIOD_HOURLY),
        ("1w-daily",  7 * 24 * 3600, PERIOD_DAILY),
        ("1m-daily", 30 * 24 * 3600, PERIOD_DAILY),
    ]
    for label, window, period in intervals:
        interval_start = end_ts - window
        try:
            candlesticks = await _fetch_candlesticks(
                client, private_key, base, series_ticker, ticker, interval_start, end_ts,
                period_interval=period,
            )
            _print_candlesticks(candlesticks, f"{ticker} ({label})")
        except httpx.HTTPStatusError as e:
            print(f"\n  --- Candlesticks: {ticker} ({label}) ---")
            print(f"  HTTP {e.response.status_code}: {e.response.text[:300]}")


async def _test_qualitative(client, private_key, base, event, start_ts, end_ts):
    _print_header("[QUALITATIVE MULTI-MARKET] Text outcome labels")
    _print_event_meta(event)

    markets = event.get("markets", [])
    print(f"\n  Market overview:")
    for m in markets:
        print(f"    {m['ticker']:40s}  yes_sub_title={m.get('yes_sub_title', '')!r:30s}  last_price={m.get('last_price_dollars')}")

    series_ticker = event.get("series_ticker", "")
    intervals = [
        ("1d-hourly", 1 * 24 * 3600, PERIOD_HOURLY),
        ("1w-daily",  7 * 24 * 3600, PERIOD_DAILY),
        ("1m-daily", 30 * 24 * 3600, PERIOD_DAILY),
    ]
    for m in markets[:2]:
        ticker = m["ticker"]
        for label, window, period in intervals:
            interval_start = end_ts - window
            try:
                candlesticks = await _fetch_candlesticks(
                    client, private_key, base, series_ticker, ticker, interval_start, end_ts,
                    period_interval=period,
                )
                _print_candlesticks(candlesticks, f"{ticker} ({label})")
            except httpx.HTTPStatusError as e:
                print(f"\n  --- Candlesticks: {ticker} ({label}) ---")
                print(f"  HTTP {e.response.status_code}: {e.response.text[:300]}")


async def _test_quantitative(client, private_key, base, event, start_ts, end_ts):
    _print_header("[QUANTITATIVE MULTI-MARKET] Numeric outcome labels")
    _print_event_meta(event)

    markets = event.get("markets", [])
    print(f"\n  Market overview:")
    for m in markets:
        label = m.get("yes_sub_title", "")
        strike_type = m.get("strike_type", "")
        floor = m.get("floor_strike")
        cap = m.get("cap_strike")
        # Use API strike fields for display
        if floor is not None and cap is not None:
            parsed = f"{float(floor):,.2f}-{float(cap):,.2f}"
        elif floor is not None:
            parsed = f">{float(floor):,.2f}"
        elif cap is not None:
            parsed = f"<{float(cap):,.2f}"
        else:
            parsed = "N/A"
        print(f"    {m['ticker']:40s}  label={label!r:30s}  strike={strike_type:10s}  value={parsed:>16s}  prob={m.get('last_price_dollars')}")

    series_ticker = event.get("series_ticker", "")
    event_ticker = event.get("event_ticker", "")

    # Candlesticks for first 2 markets across intervals
    intervals = [
        ("1d-hourly", 1 * 24 * 3600, PERIOD_HOURLY),
        ("1w-daily",  7 * 24 * 3600, PERIOD_DAILY),
        ("1m-daily", 30 * 24 * 3600, PERIOD_DAILY),
    ]
    for m in markets[:2]:
        ticker = m["ticker"]
        for label, window, period in intervals:
            interval_start = end_ts - window
            try:
                candlesticks = await _fetch_candlesticks(
                    client, private_key, base, series_ticker, ticker, interval_start, end_ts,
                    period_interval=period,
                )
                _print_candlesticks(candlesticks, f"{ticker} ({label})")
            except httpx.HTTPStatusError as e:
                print(f"\n  --- Candlesticks: {ticker} ({label}) ---")
                print(f"  HTTP {e.response.status_code}: {e.response.text[:300]}")

    # Forecast percentile history (EV timeseries)
    print(f"\n  --- Forecast Percentile History (EV timeseries) ---")
    try:
        history = await _fetch_forecast_percentiles(
            client, private_key, base, series_ticker, event_ticker, start_ts, end_ts
        )
        print(f"  Data points: {len(history)}")
        if history:
            print(f"\n  Raw (first 3):")
            print(json.dumps(history[:3], indent=2))
            print(f"\n  Parsed (all {len(history)} points):")
            for h in history:
                ts = h.get("end_period_ts")
                dt = datetime.fromtimestamp(ts).strftime("%Y-%m-%d") if ts else "?"
                pv = h.get("percentile_values", {})
                print(f"    {dt} | raw={pv.get('raw')} | processed={pv.get('processed')} | formatted={pv.get('formatted')}")
        else:
            print("  (no data returned)")
    except httpx.HTTPStatusError as e:
        print(f"  HTTP {e.response.status_code}: {e.response.text[:500]}")
        print("  (Forecast percentiles may not be available for this event)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main():
    if not settings.KALSHI_API_KEY or not settings.KALSHI_KEY_ID:
        print("ERROR: KALSHI_API_KEY and KALSHI_KEY_ID must be set in .env")
        sys.exit(1)

    private_key = _load_private_key()
    base = settings.KALSHI_API_URL

    end_ts = int(time.time())
    start_ts = end_ts - (30 * 24 * 3600)

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Step 1: Discover events
        _print_header("DISCOVERING EVENTS (up to 200)")
        found = await _discover_events(client, private_key, base)

        if not found:
            print("ERROR: No events found")
            sys.exit(1)

        # Step 2: Test each type
        if "binary" in found:
            await _test_binary(client, private_key, base, found["binary"], start_ts, end_ts)
        else:
            print("\n  [BINARY] — not found, skipping")

        if "qualitative" in found:
            await _test_qualitative(client, private_key, base, found["qualitative"], start_ts, end_ts)
        else:
            print("\n  [QUALITATIVE MULTI-MARKET] — not found, skipping")

        if "quantitative" in found:
            await _test_quantitative(client, private_key, base, found["quantitative"], start_ts, end_ts)
        else:
            print("\n  [QUANTITATIVE MULTI-MARKET] — not found among scanned events, skipping")

    print(f"\n{'=' * 70}")
    print("  DONE")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    asyncio.run(main())
