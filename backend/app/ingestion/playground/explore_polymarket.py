"""Fetch Polymarket events and print structured analysis.

Usage: cd backend && uv run python -m playground.explore_polymarket
"""

import asyncio
import json
import sys
from pathlib import Path

import httpx

from app.config import settings


async def main():
    gamma_url = settings.POLYMARKET_GAMMA_API_URL

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Fetch events
        url = f"{gamma_url}/events"
        params = {"limit": 5, "active": "true", "closed": "false"}
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

        # Print raw JSON
        print("=" * 80)
        print("RAW RESPONSE (first 5 events)")
        print("=" * 80)
        raw_events = data if isinstance(data, list) else data.get("events", data.get("data", []))
        print(json.dumps(raw_events[:2], indent=2)[:5000])
        print("... (truncated)\n")

        total_markets = 0

        for i, ev in enumerate(raw_events):
            print(f"\n{'─' * 60}")
            print(f"EVENT {i + 1}")
            print(f"  id:            {ev.get('id')}")
            print(f"  title:         {ev.get('title')}")
            print(f"  slug:          {ev.get('slug')}")
            print(f"  category:      {ev.get('category')}")
            print(f"  subcategory:   {ev.get('subcategory')}")
            print(f"  endDate:       {ev.get('endDate')}")
            print(f"  volume:        {ev.get('volume')}")
            print(f"  liquidity:     {ev.get('liquidity')}")
            print(f"  openInterest:  {ev.get('openInterest')}")
            print(f"  image:         {ev.get('image')}")

            markets = ev.get("markets", [])
            print(f"  markets count: {len(markets)}")
            total_markets += len(markets)

            for j, mkt in enumerate(markets):
                # Parse clobTokenIds (JSON string)
                clob_raw = mkt.get("clobTokenIds", "[]")
                try:
                    clob_tokens = json.loads(clob_raw) if isinstance(clob_raw, str) else clob_raw
                except (json.JSONDecodeError, TypeError):
                    clob_tokens = []

                # Parse outcomePrices (JSON string)
                prices_raw = mkt.get("outcomePrices", "[]")
                try:
                    outcome_prices = json.loads(prices_raw) if isinstance(prices_raw, str) else prices_raw
                except (json.JSONDecodeError, TypeError):
                    outcome_prices = []

                print(f"\n  MARKET {j + 1}:")
                print(f"    conditionId:       {mkt.get('conditionId')}")
                print(f"    question:          {mkt.get('question')}")
                print(f"    clobTokenIds:      {clob_tokens}")
                print(f"    outcomePrices:     {outcome_prices}")
                print(f"    lastTradePrice:    {mkt.get('lastTradePrice')}")
                print(f"    bestBid:           {mkt.get('bestBid')}")
                print(f"    bestAsk:           {mkt.get('bestAsk')}")
                print(f"    spread:            {mkt.get('spread')}")
                print(f"    volumeNum:         {mkt.get('volumeNum')}")
                print(f"    volume24hr:        {mkt.get('volume24hr')}")
                print(f"    oneDayPriceChange: {mkt.get('oneDayPriceChange')}")
                print(f"    active:            {mkt.get('active')}")
                print(f"    closed:            {mkt.get('closed')}")
                print(f"    endDate:           {mkt.get('endDate')}")

                # Verify: is clobTokenIds[0] already the right token?
                if clob_tokens:
                    print(f"    YES token (clob):  {clob_tokens[0][:30]}...")

        print(f"\n{'=' * 80}")
        print("SUMMARY")
        print(f"  Total events:  {len(raw_events)}")
        print(f"  Total markets: {total_markets}")
        print(f"{'=' * 80}")

        # Optionally save to file
        if "--save" in sys.argv:
            out = Path("playground/polymarket_events_raw.json")
            out.write_text(json.dumps(raw_events, indent=2))
            print(f"\nSaved raw response to {out}")


if __name__ == "__main__":
    asyncio.run(main())
