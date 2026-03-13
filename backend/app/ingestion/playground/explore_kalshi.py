"""Fetch Kalshi events and print structured analysis of the response format.

Usage: cd backend && uv run python -m playground.explore_kalshi
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


async def main():
    if not settings.KALSHI_API_KEY or not settings.KALSHI_KEY_ID:
        print("ERROR: KALSHI_API_KEY and KALSHI_KEY_ID must be set in .env")
        sys.exit(1)

    private_key = _load_private_key()
    base = settings.KALSHI_API_URL

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Fetch events
        url = f"{base}/events"
        params = {"limit": 5, "status": "open", "with_nested_markets": "true"}
        headers = _signed_headers(private_key, "GET", url)
        resp = await client.get(url, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()

        # Print raw JSON
        print("=" * 80)
        print("RAW RESPONSE (first 5 events)")
        print("=" * 80)
        print(json.dumps(data, indent=2)[:5000])
        print("... (truncated)\n")

        events = data.get("events", [])
        cursor = data.get("cursor")
        categories_seen = set()
        market_types_seen = set()
        total_markets = 0

        for i, ev in enumerate(events):
            print(f"\n{'─' * 60}")
            print(f"EVENT {i + 1}")
            print(f"  event_ticker:      {ev.get('event_ticker')}")
            print(f"  series_ticker:     {ev.get('series_ticker')}")
            print(f"  title:             {ev.get('title')}")
            print(f"  sub_title:         {ev.get('sub_title')}")
            print(f"  category:          {ev.get('category')}")
            print(f"  mutually_exclusive:{ev.get('mutually_exclusive')}")
            print(f"  strike_date:       {ev.get('strike_date')}")
            print(f"  strike_period:     {ev.get('strike_period')}")

            cat = ev.get("category", "")
            if cat:
                categories_seen.add(cat)

            markets = ev.get("markets", [])
            print(f"  markets count:     {len(markets)}")
            total_markets += len(markets)

            for j, mkt in enumerate(markets):
                mt = mkt.get("market_type", "")
                market_types_seen.add(mt)
                print(f"\n  MARKET {j + 1}:")
                print(f"    ticker:              {mkt.get('ticker')}")
                print(f"    market_type:         {mt}")
                print(f"    yes_sub_title:       {mkt.get('yes_sub_title')}")
                print(f"    no_sub_title:        {mkt.get('no_sub_title')}")
                print(f"    last_price_dollars:  {mkt.get('last_price_dollars')}")
                print(f"    yes_bid_dollars:     {mkt.get('yes_bid_dollars')}")
                print(f"    yes_ask_dollars:     {mkt.get('yes_ask_dollars')}")
                print(f"    volume_fp:           {mkt.get('volume_fp')}")
                print(f"    volume_24h_fp:       {mkt.get('volume_24h_fp')}")
                print(f"    open_interest_fp:    {mkt.get('open_interest_fp')}")
                print(f"    status:              {mkt.get('status')}")
                print(f"    close_time:          {mkt.get('close_time')}")

        print(f"\n{'=' * 80}")
        print("SUMMARY")
        print(f"  Total events:      {len(events)}")
        print(f"  Total markets:     {total_markets}")
        print(f"  Next cursor:       {cursor}")
        print(f"  Categories seen:   {sorted(categories_seen)}")
        print(f"  Market types seen: {sorted(market_types_seen)}")
        print(f"{'=' * 80}")

        # Optionally save to file
        if "--save" in sys.argv:
            out = Path("playground/kalshi_events_raw.json")
            out.write_text(json.dumps(data, indent=2))
            print(f"\nSaved raw response to {out}")


if __name__ == "__main__":
    asyncio.run(main())
