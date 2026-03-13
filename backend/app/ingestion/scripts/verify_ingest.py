"""Standalone ingestion verification script.

Verifies the full pipeline: API → normalize → cache → read-back → graph.
Handles both binary (single-market) and multimarket (qualitative) events.

Usage:
    uv run python -m app.ingestion.scripts.verify_ingest --source kalshi --mode binary
    uv run python -m app.ingestion.scripts.verify_ingest --source polymarket --mode multi
    uv run python -m app.ingestion.scripts.verify_ingest --source kalshi --source-id KXELONMARS-99
    uv run python -m app.ingestion.scripts.verify_ingest --source polymarket --mode multi --skip-db --no-graph
"""

import argparse
import asyncio
import json
import random
import uuid
from dataclasses import asdict
from datetime import datetime, timezone

from app.ingestion.base import NormalizedEvent, PricePoint


def _banner(phase: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {phase}")
    print(f"{'='*60}")


def _print_event_summary(event: NormalizedEvent) -> None:
    """Pretty-print a NormalizedEvent summary table."""
    if event.is_parent and event.markets:
        print(f"\n  {'source_id':<40} {'title':<50}")
        print(f"  {'-'*40} {'-'*50}")
        print(f"  {event.source_id:<40} {event.title[:50]:<50}")
        print(f"\n  Child markets ({len(event.markets)}):")
        print(f"  {'outcome_label':<40} {'prob':>8} {'volume':>12}")
        print(f"  {'-'*40} {'-'*8} {'-'*12}")
        for m in event.markets:
            label = (m.outcome_label or m.title)[:40]
            vol = f"{m.volume:.0f}" if m.volume else "N/A"
            print(f"  {label:<40} {m.probability:>8.4f} {vol:>12}")
    else:
        print(f"\n  source_id:   {event.source_id}")
        print(f"  title:       {event.title[:80]}")
        print(f"  probability: {event.probability:.4f}")
        print(f"  volume:      {event.volume}")
        print(f"  category:    {event.category}")
        print(f"  region:      {event.region}")


async def phase1_fetch(source: str, mode: str, source_id: str | None):
    """Phase 1: Fetch & auto-select event."""
    _banner("Phase 1 — Fetch & auto-select event")

    if source == "kalshi":
        from app.ingestion.kalshi import KalshiClient
        client = KalshiClient()
    else:
        from app.ingestion.polymarket import PolymarketClient
        client = PolymarketClient()

    event: NormalizedEvent | None = None

    if source_id:
        # Fetch pages and find the specific event
        print(f"  Looking for source_id={source_id}...")
        for page_num in range(3):
            cursor = str(page_num * 100) if source == "polymarket" and page_num > 0 else (None if page_num == 0 else cursor_next)
            events, cursor_next = await client.fetch_events_page(
                None if page_num == 0 else cursor_next if page_num > 0 else None
            )
            for e in events:
                if e.source_id == source_id:
                    event = e
                    break
                for m in e.markets:
                    if m.source_id == source_id:
                        event = e
                        break
                if event:
                    break
            if event or not cursor_next:
                break
        if not event:
            print(f"  ERROR: Could not find event with source_id={source_id}")
            await client.close()
            return None, client
    else:
        # Auto-select based on mode
        print(f"  Auto-selecting {mode} event from {source}...")
        cursor_next = None
        for page_num in range(3):
            events, cursor_next = await client.fetch_events_page(
                None if page_num == 0 else cursor_next
            )
            print(f"  Page {page_num + 1}: {len(events)} events")
            for e in events:
                if mode == "binary" and not e.is_parent:
                    event = e
                    if random.random() > 0.9:
                        break
                elif mode == "multi" and e.is_parent and len(e.markets) >= 2:
                    event = e
                    if random.random() > 0.9:
                        break
            if event or not cursor_next:
                break

        if not event:
            print(f"  ERROR: No matching {mode} event found in first 3 pages")
            await client.close()
            return None, client

    print(f"  Selected: {event.title[:80]}")
    print(f"  source_id: {event.source_id}, is_parent: {event.is_parent}")
    return event, client


def phase2_display(event: NormalizedEvent):
    """Phase 2: Display normalized event."""
    _banner("Phase 2 — Normalized event data")

    print("\n  Full NormalizedEvent JSON:")
    print(json.dumps(asdict(event), indent=2, default=str))
    print("\n  Summary:")
    _print_event_summary(event)


async def phase3_cache_roundtrip(event: NormalizedEvent, source: str):
    """Phase 3: Cache round-trip."""
    _banner("Phase 3 — Cache round-trip (event)")

    try:
        import redis.asyncio as aioredis
        from app.cache import EventCache
        from app.config import settings

        redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        cache = EventCache(redis)

        # Write
        await cache.set_event(source, event.source_id, event)
        print(f"  Wrote event to cache: events:{source}:{event.source_id}")

        # Read back
        cached = await cache.get_event(source, event.source_id)
        if cached is None:
            print("  ERROR: Read back None from cache")
            await redis.aclose()
            return cache, redis

        # Compare
        original_dict = asdict(event)
        cached_dict = asdict(cached)
        if original_dict == cached_dict:
            print("  CACHE ROUND-TRIP: OK")
        else:
            print("  CACHE ROUND-TRIP: MISMATCH")
            # Find diffs
            for key in original_dict:
                if original_dict[key] != cached_dict.get(key):
                    print(f"    {key}: {original_dict[key]!r} → {cached_dict.get(key)!r}")

        return cache, redis
    except Exception as exc:
        print(f"  WARNING: Redis unavailable ({exc}), skipping cache verification")
        return None, None


async def phase4_db_upsert(event: NormalizedEvent, skip_db: bool):
    """Phase 4: DB upsert."""
    _banner("Phase 4 — DB upsert")

    if skip_db:
        print("  Skipped (--skip-db)")
        return

    try:
        from sqlalchemy import select
        from app.database import async_session
        from app.models.event import Event
        from app.tasks.discovery import _upsert_event_to_pg

        async with async_session() as session:
            if event.is_parent and event.markets:
                parent_db_id = await _upsert_event_to_pg(session, event)
                print(f"  Upserted parent: db_id={parent_db_id}")

                for market in event.markets:
                    child_event = NormalizedEvent(
                        source=event.source,
                        source_id=market.source_id,
                        source_url=event.source_url,
                        title=market.title,
                        description=event.description,
                        category=event.category,
                        region=event.region,
                        status="closed" if market.is_closed else event.status,
                        resolution_date=event.resolution_date,
                        probability=market.probability,
                        is_parent=False,
                        image_url=market.image_url or event.image_url,
                        tags=event.tags,
                        series_ticker=market.series_ticker or event.series_ticker,
                        volume=market.volume,
                    )
                    child_db_id = await _upsert_event_to_pg(session, child_event, parent_db_id)
                    print(f"  Upserted child: {market.outcome_label[:40]:<40} db_id={child_db_id}")
            else:
                db_id = await _upsert_event_to_pg(session, event)
                print(f"  Upserted: db_id={db_id}")

            await session.commit()

            # Read back and display
            print("\n  DB read-back:")
            result = await session.execute(
                select(Event).where(
                    Event.source == event.source,
                    Event.source_id == event.source_id,
                )
            )
            db_event = result.scalar_one_or_none()
            if db_event:
                print(f"    id:                  {db_event.id}")
                print(f"    title:               {db_event.title[:60]}")
                print(f"    source_id:           {db_event.source_id}")
                print(f"    current_probability: {db_event.current_probability}")
                print(f"    status:              {db_event.status}")

                if event.is_parent:
                    child_result = await session.execute(
                        select(Event).where(Event.parent_event_id == db_event.id)
                    )
                    children = child_result.scalars().all()
                    print(f"\n    Children ({len(children)}):")
                    for c in children:
                        print(f"      {c.source_id:<40} prob={c.current_probability:.4f} status={c.status}")
            else:
                print("    WARNING: Could not read back from DB")

    except Exception as exc:
        print(f"  WARNING: DB unavailable ({exc}), skipping DB upsert")


async def phase5_fetch_prices(event: NormalizedEvent, client):
    """Phase 5: Fetch price history."""
    _banner("Phase 5 — Fetch price history")

    all_prices: dict[str, list[PricePoint]] = {}

    try:
        if event.is_parent and event.markets:
            for market in event.markets:
                label = (market.outcome_label or market.title)[:40]
                print(f"  Fetching prices for: {label} ({market.source_id})...")
                points = await client.fetch_prices(market.source_id)
                all_prices[market.source_id] = points
                if points:
                    dates = [datetime.fromtimestamp(p.timestamp, tz=timezone.utc) for p in points]
                    print(f"    {len(points)} points, {dates[0].date()} → {dates[-1].date()}")
                else:
                    print(f"    WARNING: No price data returned")
        else:
            print(f"  Fetching prices for: {event.source_id}...")
            points = await client.fetch_prices(event.source_id)
            all_prices[event.source_id] = points
            if points:
                dates = [datetime.fromtimestamp(p.timestamp, tz=timezone.utc) for p in points]
                print(f"    {len(points)} points, {dates[0].date()} → {dates[-1].date()}")
            else:
                print(f"    WARNING: No price data returned")
    except Exception as exc:
        print(f"  ERROR fetching prices: {exc}")

    return all_prices


async def phase6_price_cache(
    all_prices: dict[str, list[PricePoint]], source: str, cache, redis
):
    """Phase 6: Price cache round-trip."""
    _banner("Phase 6 — Price cache round-trip")

    if cache is None:
        print("  Skipped (no Redis connection)")
        return

    try:
        for source_id, points in all_prices.items():
            if not points:
                print(f"  Skipped {source_id} (no price data)")
                continue

            await cache.set_history(source, source_id, points)
            cached_points = await cache.get_history(source, source_id)

            if cached_points is None:
                print(f"  {source_id}: ERROR — read back None")
                continue

            original = [asdict(p) for p in points]
            cached = [asdict(p) for p in cached_points]
            if original == cached:
                print(f"  {source_id}: CACHE ROUND-TRIP: OK ({len(points)} points)")
            else:
                print(f"  {source_id}: CACHE ROUND-TRIP: MISMATCH")
                print(f"    Original: {len(original)} points, Cached: {len(cached)} points")
    except Exception as exc:
        print(f"  WARNING: Price cache error ({exc})")


def phase7_graph(
    event: NormalizedEvent,
    all_prices: dict[str, list[PricePoint]],
    no_graph: bool,
):
    """Phase 7: Graph with matplotlib."""
    _banner("Phase 7 — Graph")

    if no_graph:
        print("  Skipped (--no-graph)")
        return

    # Check if we have any data to plot
    has_data = any(points for points in all_prices.values())
    if not has_data:
        print("  WARNING: No price data to graph, skipping")
        return

    try:
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
    except ImportError:
        print("  matplotlib not installed. Install with: uv add --dev matplotlib")
        return

    fig, ax = plt.subplots(figsize=(12, 6))

    if event.is_parent and event.markets:
        # Multi: one line per child market
        for market in event.markets:
            points = all_prices.get(market.source_id, [])
            if not points:
                continue
            dates = [datetime.fromtimestamp(p.timestamp, tz=timezone.utc) for p in points]
            probs = [p.probability for p in points]
            label = (market.outcome_label or market.title)[:40]
            line, = ax.plot(dates, probs, label=label, linewidth=1.5)
            # Annotate current probability at rightmost point
            ax.annotate(
                f"{probs[-1]:.2f}",
                xy=(dates[-1], probs[-1]),
                fontsize=8,
                color=line.get_color(),
                fontweight="bold",
            )
        ax.legend(loc="best", fontsize=8)
    else:
        # Binary: single line
        source_id = event.source_id
        points = all_prices.get(source_id, [])
        if points:
            dates = [datetime.fromtimestamp(p.timestamp, tz=timezone.utc) for p in points]
            probs = [p.probability for p in points]
            ax.plot(dates, probs, color="steelblue", linewidth=2, label="Probability")
            ax.annotate(
                f"{probs[-1]:.2f}",
                xy=(dates[-1], probs[-1]),
                fontsize=10,
                color="steelblue",
                fontweight="bold",
            )

            # Secondary y-axis for volume if available
            volumes = [p.volume for p in points if p.volume is not None]
            if volumes:
                ax2 = ax.twinx()
                vol_dates = [
                    datetime.fromtimestamp(p.timestamp, tz=timezone.utc)
                    for p in points
                    if p.volume is not None
                ]
                ax2.bar(vol_dates, volumes, alpha=0.2, color="gray", width=0.5, label="Volume")
                ax2.set_ylabel("Volume", color="gray")
                ax2.tick_params(axis="y", labelcolor="gray")

    ax.set_title(event.title[:80], fontsize=11)
    ax.set_ylabel("Probability")
    # Auto-scale y-axis to data range with padding, like Kalshi's charts
    all_probs = []
    for points in all_prices.values():
        all_probs.extend(p.probability for p in points)
    if all_probs:
        ymin, ymax = min(all_probs), max(all_probs)
        margin = max((ymax - ymin) * 0.1, 0.01)
        ax.set_ylim(max(0, ymin - margin), min(1, ymax + margin))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    fig.autofmt_xdate()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    print("  Displaying graph (close window to continue)...")
    plt.show()


async def main():
    parser = argparse.ArgumentParser(description="Verify ingestion pipeline end-to-end")
    parser.add_argument("--source", required=True, choices=["kalshi", "polymarket"])
    parser.add_argument("--mode", default="binary", choices=["binary", "multi"])
    parser.add_argument("--source-id", default=None, help="Explicit event source_id")
    parser.add_argument("--skip-db", action="store_true", help="Skip DB upsert")
    parser.add_argument("--no-graph", action="store_true", help="Skip matplotlib graph")
    args = parser.parse_args()

    print(f"Verifying ingestion: source={args.source}, mode={args.mode}")
    if args.source_id:
        print(f"  Explicit source_id: {args.source_id}")

    # Phase 1
    event, client = await phase1_fetch(args.source, args.mode, args.source_id)
    if event is None:
        await client.close()
        return

    # Phase 2
    phase2_display(event)

    # Phase 3
    cache, redis = await phase3_cache_roundtrip(event, args.source)

    # Phase 4
    await phase4_db_upsert(event, args.skip_db)

    # Phase 5
    all_prices = await phase5_fetch_prices(event, client)

    # Phase 6
    await phase6_price_cache(all_prices, args.source, cache, redis)

    # Cleanup
    await client.close()
    if redis:
        await redis.aclose()

    # Phase 7 (sync — matplotlib)
    phase7_graph(event, all_prices, args.no_graph)

    print(f"\n{'='*60}")
    print("  Verification complete!")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())
