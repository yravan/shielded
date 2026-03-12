from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://shielded:shielded@localhost:5432/shielded"
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    FRONTEND_URL: str = "http://localhost:3000"
    POLYMARKET_API_URL: str = "https://clob.polymarket.com"
    KALSHI_API_URL: str = "https://api.elections.kalshi.com/trade-api/v2"
    KALSHI_API_KEY: str = ""
    METACULUS_API_URL: str = "https://www.metaculus.com/api2"
    METACULUS_API_KEY: str = ""
    POLL_INTERVAL_SECONDS: int = 300
    ENABLE_LIVE_POLLING: bool = False

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
