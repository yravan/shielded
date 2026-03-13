from app.config import settings
from app.ingestion.base import BaseMarketClient
from app.ingestion.kalshi import KalshiClient
from app.ingestion.metaculus import MetaculusClient
from app.ingestion.polymarket import PolymarketClient


def get_enabled_clients() -> list[BaseMarketClient]:
    """Return list of market clients that are configured and enabled."""
    clients: list[BaseMarketClient] = []

    # Polymarket is always enabled (public API, no auth required)
    clients.append(PolymarketClient())

    if settings.KALSHI_API_KEY and settings.KALSHI_KEY_ID:
        clients.append(KalshiClient())

    if settings.METACULUS_API_KEY:
        clients.append(MetaculusClient())

    return clients


def get_client_for_source(source: str) -> BaseMarketClient | None:
    """Return the matching market client for a given source name."""
    for client in get_enabled_clients():
        if client.source_name == source:
            return client
    return None
