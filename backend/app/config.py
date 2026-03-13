from pydantic import model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://shielded:shielded@localhost:5432/shielded"
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = ""

    @model_validator(mode="after")
    def set_celery_broker(self) -> "Settings":
        if not self.CELERY_BROKER_URL:
            base = self.REDIS_URL.rsplit("/", 1)[0] if self.REDIS_URL.count("/") > 2 else self.REDIS_URL
            self.CELERY_BROKER_URL = f"{base}/1"
        return self
    FRONTEND_URL: str = "http://localhost:3000"
    POLYMARKET_API_URL: str = "https://clob.polymarket.com"
    POLYMARKET_GAMMA_API_URL: str = "https://gamma-api.polymarket.com"
    KALSHI_API_URL: str = "https://api.elections.kalshi.com/trade-api/v2"
    KALSHI_API_KEY: str = ""
    KALSHI_KEY_ID: str = ""
    KALSHI_PERIOD_INTERVAL: int = 60
    METACULUS_API_URL: str = "https://www.metaculus.com/api2"
    METACULUS_API_KEY: str = ""
    POLL_INTERVAL_SECONDS: int = 300
    ENABLE_LIVE_POLLING: bool = True
    CACHE_TTL_ALL_EVENTS: int = 7200  # 2h
    CACHE_TTL_SINGLE_EVENT: int = 900  # 15min
    CACHE_TTL_HISTORY: int = 300  # 5min
    CACHE_TTL_EXPLORE: int = 120  # 2min
    CACHE_TTL_TOKEN_MAP: int = 86400  # 24h
    CLERK_SECRET_KEY: str = ""
    CLERK_PUBLISHABLE_KEY: str = ""
    CLERK_JWT_ISSUER: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
