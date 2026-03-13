"""Test Polymarket token resolution and price history for all 3 event types.

Usage: cd backend && uv run python -m playground.test_polymarket_prices
"""

import asyncio
import json
import sys
from datetime import datetime

import httpx

from app.config import settings


# ---------------------------------------------------------------------------
# Classification helpers
# ---------------------------------------------------------------------------

def _classify_event(event: dict) -> str:
    """Returns 'binary', 'qualitative', or 'quantitative'.

    Uses API-provided estimateValue/cantEstimate fields for classification.
    Falls back to checking lowerBound/upperBound on individual markets.
    """
    markets = event.get("markets", [])
    if len(markets) <= 1:
        return "binary"

    # Event-level: use estimateValue field from Gamma API
    if event.get("estimateValue") and not event.get("cantEstimate"):
        return "quantitative"

    # Market-level fallback: check for lowerBound/upperBound
    with_bounds = sum(
        1 for m in markets
        if m.get("lowerBound") is not None or m.get("upperBound") is not None
    )
    if with_bounds == len(markets):
        return "quantitative"

    return "qualitative"


def _parse_clob_token_ids(raw) -> list[str]:
    """Parse clobTokenIds from JSON string or list."""
    if raw is None:
        return []
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return []
    return raw if isinstance(raw, list) else []


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

def _print_header(text: str):
    print(f"\n{'=' * 70}")
    print(f"  {text}")
    print(f"{'=' * 70}")


def _print_event_meta(event: dict):
    print(f"  Title:       {event.get('title')}")
    print(f"  Slug:        {event.get('slug')}")
    print(f"  Volume:      {event.get('volume')}")
    tags = event.get("tags", [])
    tag_labels = [t.get("label", "") for t in tags if isinstance(t, dict)]
    if tag_labels:
        print(f"  Tags:        {', '.join(tag_labels)}")
    markets = event.get("markets", [])
    print(f"  Markets:     {len(markets)}")


def _print_price_history(history: list, label: str = ""):
    if label:
        print(f"\n  --- Price history: {label} ---")
    print(f"  Data points: {len(history)}")
    if not history:
        print("  (no data)")
        return
    print(f"  First: t={history[0].get('t')}  p={history[0].get('p')}")
    print(f"  Last:  t={history[-1].get('t')}  p={history[-1].get('p')}")
    print(f"\n  All {len(history)} points:")
    last_p = None
    for pt in history:
        ts = pt.get("t")
        dt = datetime.fromtimestamp(int(ts)).strftime("%Y-%m-%d %H:%M") if ts else "?"
        p = pt.get("p")
        tag = ""
        if p is not None:
            last_p = p
        elif last_p is not None:
            p = last_p
            tag = " [ffill]"
        else:
            p = "?"
        print(f"    {dt} | p={p}{tag}")


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------

async def _resolve_token_id(client: httpx.AsyncClient, clob_url: str, market: dict) -> str | None:
    """Resolve the Yes token ID for a market. Tries clobTokenIds first, then CLOB API."""
    # Method A: direct from Gamma clobTokenIds
    clob_tokens = _parse_clob_token_ids(market.get("clobTokenIds"))
    if clob_tokens:
        return clob_tokens[0]

    # Method B: CLOB /markets/{condition_id}
    condition_id = market.get("conditionId")
    if not condition_id:
        return None
    try:
        resp = await client.get(f"{clob_url}/markets/{condition_id}")
        resp.raise_for_status()
        tokens = resp.json().get("tokens", [])
        if tokens:
            return tokens[0].get("token_id")
    except httpx.HTTPStatusError:
        pass
    return None


async def _fetch_price_history(
    client: httpx.AsyncClient, clob_url: str, token_id: str,
    interval: str = "max", fidelity: int = 60,
) -> list:
    """Fetch price history for a single token."""
    url = f"{clob_url}/prices-history"
    params = {"market": token_id, "interval": interval, "fidelity": fidelity}
    resp = await client.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()
    history = data.get("history", data) if isinstance(data, dict) else data
    return history if isinstance(history, list) else []


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

async def _discover_events(
    client: httpx.AsyncClient, gamma_url: str,
) -> dict[str, dict]:
    """Paginate through Gamma events to find one of each type."""
    found: dict[str, dict] = {}
    needed = {"binary", "qualitative", "quantitative"}
    offset = 0
    total_seen = 0

    while needed and total_seen < 200:
        url = f"{gamma_url}/events"
        params = {"limit": 100, "active": "true", "closed": "false", "offset": offset}
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        raw = resp.json()
        events = raw if isinstance(raw, list) else raw.get("events", raw.get("data", []))

        for ev in events:
            total_seen += 1
            etype = _classify_event(ev)
            if etype in needed:
                found[etype] = ev
                needed.discard(etype)
                print(f"  Found {etype:15s} → {ev.get('slug', '')[:40]} — {ev.get('title', '')[:50]}")
                if not needed:
                    break

        if not events or len(events) < 100:
            break
        offset += 100

    print(f"  Scanned {total_seen} events total")
    return found


# ---------------------------------------------------------------------------
# Test sections
# ---------------------------------------------------------------------------

async def _test_binary(client, gamma_url, clob_url, event):
    _print_header("[BINARY] Single-market event")
    _print_event_meta(event)

    markets = event.get("markets", [])
    if not markets:
        print("  ERROR: No markets in event")
        return

    market = markets[0]
    condition_id = market.get("conditionId")
    print(f"\n  Condition ID:   {condition_id}")
    print(f"  Last price:     {market.get('lastTradePrice')}")

    # Token resolution comparison
    clob_tokens = _parse_clob_token_ids(market.get("clobTokenIds"))
    token_a = clob_tokens[0] if clob_tokens else None
    print(f"\n  Token resolution:")
    print(f"    Method A (Gamma clobTokenIds): {token_a}")

    try:
        resp = await client.get(f"{clob_url}/markets/{condition_id}")
        resp.raise_for_status()
        clob_market = resp.json()
        tokens = clob_market.get("tokens", [])
        token_b = tokens[0].get("token_id") if tokens else None
        print(f"    Method B (CLOB /markets):     {token_b}")
        match = token_a == token_b
        print(f"    Match: {'YES' if match else 'NO'}")
    except httpx.HTTPStatusError as e:
        print(f"    Method B: HTTP {e.response.status_code}")
        token_b = None

    token_id = token_a or token_b
    if not token_id:
        print("  ERROR: Could not resolve token_id")
        return

    # Price history across intervals
    for interval in ["max", "1d", "1w", "1m"]:
        try:
            history = await _fetch_price_history(client, clob_url, token_id, interval=interval)
            _print_price_history(history, f"interval={interval}")
        except httpx.HTTPStatusError as e:
            print(f"\n  --- Price history: interval={interval} ---")
            print(f"  HTTP {e.response.status_code}: {e.response.text[:300]}")


async def _test_qualitative(client, gamma_url, clob_url, event):
    _print_header("[QUALITATIVE MULTI-MARKET] Text outcome labels")
    _print_event_meta(event)

    markets = event.get("markets", [])
    print(f"\n  Market overview:")
    for m in markets:
        label = m.get("groupItemTitle", "")
        closed = bool(m.get("closed", False))
        status = " [CLOSED]" if closed else ""
        print(f"    {m.get('conditionId', '')[:20]}...  label={label!r:30s}  price={m.get('lastTradePrice')}{status}")

    # Filter out closed markets before fetching price history
    active_markets = [m for m in markets if not m.get("closed", False)]
    if not active_markets:
        print("  All markets are closed, skipping price history")
        return

    # Price history for first 2 active markets across intervals
    for m in active_markets[:2]:
        token_id = await _resolve_token_id(client, clob_url, m)
        label = m.get("groupItemTitle", m.get("question", "?"))
        if not token_id:
            print(f"\n  --- {label} ---")
            print("  Could not resolve token_id, skipping")
            continue
        for interval in ["max", "1d", "1w", "1m"]:
            try:
                history = await _fetch_price_history(client, clob_url, token_id, interval=interval)
                _print_price_history(history, f"{label} (interval={interval})")
            except httpx.HTTPStatusError as e:
                print(f"\n  --- {label} (interval={interval}) ---")
                print(f"  HTTP {e.response.status_code}: {e.response.text[:300]}")


async def _test_quantitative(client, gamma_url, clob_url, event):
    _print_header("[QUANTITATIVE MULTI-MARKET] Numeric outcome labels")
    _print_event_meta(event)

    markets = event.get("markets", [])

    # Show event-level EV fields
    print(f"\n  estimateValue:   {event.get('estimateValue')}")
    print(f"  cantEstimate:    {event.get('cantEstimate')}")
    print(f"  estimatedValue:  {event.get('estimatedValue')}")

    print(f"\n  Market overview:")
    for m in markets:
        label = m.get("groupItemTitle", "")
        closed = bool(m.get("closed", False))
        status = " [CLOSED]" if closed else ""
        lower = m.get("lowerBound")
        upper = m.get("upperBound")
        if lower is not None and upper is not None:
            parsed = f"{float(lower):,.2f}-{float(upper):,.2f}"
        elif lower is not None:
            parsed = f">{float(lower):,.2f}"
        elif upper is not None:
            parsed = f"<{float(upper):,.2f}"
        else:
            parsed = "N/A"
        print(f"    {m.get('conditionId', '')[:20]}...  label={label!r:30s}  bounds={parsed:>16s}  prob={m.get('lastTradePrice')}{status}")

    # Filter out closed markets before fetching price history
    active_markets = [m for m in markets if not m.get("closed", False)]
    if not active_markets:
        print("  All markets are closed, skipping price history")
        return

    # Price history for first 2 active markets across intervals
    for m in active_markets[:2]:
        token_id = await _resolve_token_id(client, clob_url, m)
        label = m.get("groupItemTitle", m.get("question", "?"))
        if not token_id:
            print(f"\n  --- {label} ---")
            print("  Could not resolve token_id, skipping")
            continue
        for interval in ["max", "1d", "1w", "1m"]:
            try:
                history = await _fetch_price_history(client, clob_url, token_id, interval=interval)
                _print_price_history(history, f"{label} (interval={interval})")
            except httpx.HTTPStatusError as e:
                print(f"\n  --- {label} (interval={interval}) ---")
                print(f"  HTTP {e.response.status_code}: {e.response.text[:300]}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main():
    gamma_url = settings.POLYMARKET_GAMMA_API_URL
    clob_url = settings.POLYMARKET_API_URL

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Step 1: Discover events
        _print_header("DISCOVERING EVENTS (up to 200)")
        found = await _discover_events(client, gamma_url)

        if not found:
            print("ERROR: No events found")
            sys.exit(1)

        # Step 2: Test each type
        if "binary" in found:
            await _test_binary(client, gamma_url, clob_url, found["binary"])
        else:
            print("\n  [BINARY] — not found, skipping")

        if "qualitative" in found:
            await _test_qualitative(client, gamma_url, clob_url, found["qualitative"])
        else:
            print("\n  [QUALITATIVE MULTI-MARKET] — not found, skipping")

        if "quantitative" in found:
            await _test_quantitative(client, gamma_url, clob_url, found["quantitative"])
        else:
            print("\n  [QUANTITATIVE MULTI-MARKET] — not found among scanned events, skipping")

    print(f"\n{'=' * 70}")
    print("  DONE")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    asyncio.run(main())
