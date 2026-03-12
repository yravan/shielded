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

    if settings.KALSHI_API_KEY:
        clients.append(KalshiClient())

    if settings.METACULUS_API_KEY:
        clients.append(MetaculusClient())

    return clients
