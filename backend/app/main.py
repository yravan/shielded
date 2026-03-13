from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.logging import setup_logging

setup_logging()
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await logger.ainfo("Starting Shielded API")

    # Run database migrations
    try:
        from alembic import command
        from alembic.config import Config

        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        await logger.ainfo("Database migrations completed")
    except Exception as e:
        await logger.aerror("Failed to run database migrations", error=str(e))

    # Dispatch initial discovery task
    try:
        from app.tasks.discovery import discover_new_events
        discover_new_events.delay()
    except Exception as e:
        await logger.awarning("Failed to dispatch startup discovery task", error=str(e))

    yield
    await logger.ainfo("Shutting down Shielded API")


app = FastAPI(
    title="Shielded API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_URL,
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://127.0.2.2:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.router import router  # noqa: E402

app.include_router(router)
