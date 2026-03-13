"""Save real API responses as test fixtures.

Usage: cd backend && uv run python -m playground.snapshot_responses
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

from app.config import settings

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "tests" / "fixtures"


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


def save_fixture(name: str, data):
    path = FIXTURES_DIR / name
    path.write_text(json.dumps(data, indent=2))
    print(f"  Saved: {path.relative_to(FIXTURES_DIR.parent.parent)}")


async def main():
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    base_kalshi = settings.KALSHI_API_URL
    gamma_url = settings.POLYMARKET_GAMMA_API_URL
    clob_url = settings.POLYMARKET_API_URL

    has_kalshi = bool(settings.KALSHI_API_KEY and settings.KALSHI_KEY_ID)
    private_key = _load_private_key() if has_kalshi else None

    async with httpx.AsyncClient(timeout=30.0) as client:
        # --- Kalshi ---
        if has_kalshi:
            print("\n=== KALSHI ===")

            # 1. Events page
            url = f"{base_kalshi}/events"
            params = {"limit": 10, "status": "open", "with_nested_markets": "true"}
            headers = _signed_headers(private_key, "GET", url)
            resp = await client.get(url, headers=headers, params=params)
            resp.raise_for_status()
            events_data = resp.json()
            save_fixture("kalshi_events_page.json", events_data)

            events = events_data.get("events", [])
            # Find a market ticker
            market_ticker = None
            series_ticker = None
            event_ticker = None
            for ev in events:
                for mkt in ev.get("markets", []):
                    market_ticker = mkt.get("ticker")
                    series_ticker = ev.get("series_ticker")
                    event_ticker = ev.get("event_ticker")
                    if market_ticker:
                        break
                if market_ticker:
                    break

            if market_ticker:
                # 2. Market detail
                url = f"{base_kalshi}/markets/{market_ticker}"
                headers = _signed_headers(private_key, "GET", url)
                resp = await client.get(url, headers=headers)
                resp.raise_for_status()
                save_fixture("kalshi_market_detail.json", resp.json())

                # 3. Candlesticks
                end_ts = int(time.time())
                start_ts = end_ts - (30 * 24 * 3600)
                url = f"{base_kalshi}/series/{series_ticker}/markets/{market_ticker}/candlesticks"
                params = {"start_ts": start_ts, "end_ts": end_ts, "period_interval": 1440}
                headers = _signed_headers(private_key, "GET", url)
                resp = await client.get(url, headers=headers, params=params)
                resp.raise_for_status()
                save_fixture("kalshi_candlesticks.json", resp.json())

                # 4. Forecast percentile history
                url = f"{base_kalshi}/series/{series_ticker}/events/{event_ticker}/forecast_percentile_history"
                params = {
                    "percentiles": "2500,5000,7500",
                    "start_ts": start_ts,
                    "end_ts": end_ts,
                    "period_interval": 1440,
                }
                headers = _signed_headers(private_key, "GET", url)
                try:
                    resp = await client.get(url, headers=headers, params=params)
                    resp.raise_for_status()
                    save_fixture("kalshi_forecast_percentiles.json", resp.json())
                except httpx.HTTPStatusError as e:
                    print(f"  Forecast percentiles: HTTP {e.response.status_code} (may not be available for this event)")
            else:
                print("  WARNING: No Kalshi market ticker found")
        else:
            print("\n=== KALSHI (skipped — no API keys) ===")

        # --- Polymarket ---
        print("\n=== POLYMARKET ===")

        # 5. Events page
        url = f"{gamma_url}/events"
        params = {"limit": 10, "active": "true", "closed": "false"}
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        pm_data = resp.json()
        save_fixture("polymarket_events_page.json", pm_data)

        # Find a token for price history
        pm_events = pm_data if isinstance(pm_data, list) else pm_data.get("events", [])
        token_id = None
        for ev in pm_events:
            for mkt in ev.get("markets", []):
                clob_raw = mkt.get("clobTokenIds", "[]")
                try:
                    clob_tokens = json.loads(clob_raw) if isinstance(clob_raw, str) else (clob_raw or [])
                except (json.JSONDecodeError, TypeError):
                    clob_tokens = []
                if clob_tokens:
                    token_id = clob_tokens[0]
                    break
            if token_id:
                break

        if token_id:
            # 6. Price history
            url = f"{clob_url}/prices-history"
            params = {"market": token_id, "interval": "max", "fidelity": 60}
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            save_fixture("polymarket_prices_history.json", resp.json())
        else:
            print("  WARNING: No Polymarket token_id found")

    print("\nDone! Fixtures saved to tests/fixtures/")


if __name__ == "__main__":
    asyncio.run(main())
