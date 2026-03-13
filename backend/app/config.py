from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://shielded:shielded@localhost:5432/shielded"
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    FRONTEND_URL: str = "http://localhost:3000"
    POLYMARKET_API_URL: str = "https://clob.polymarket.com"
    POLYMARKET_GAMMA_API_URL: str = "https://gamma-api.polymarket.com"
    KALSHI_API_URL: str = "https://api.elections.kalshi.com/trade-api/v2"
    KALSHI_API_KEY: str = ""
    KALSHI_KEY_ID: str = ""
    METACULUS_API_URL: str = "https://www.metaculus.com/api2"
    METACULUS_API_KEY: str = ""
    POLL_INTERVAL_SECONDS: int = 300
    ENABLE_LIVE_POLLING: bool = False
    CLERK_SECRET_KEY: str = ""
    CLERK_PUBLISHABLE_KEY: str = ""
    CLERK_JWT_ISSUER: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
