"""
FastAPI application entry point.

Configures the app with lifespan management (database init/close),
router registration, structured logging, and CORS middleware.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings
from app.dependencies import set_repo, set_settings
from app.routers import agent_status, health, trmnl
from app.storage.sqlite import SqliteStatusRepository

logger = structlog.get_logger()


def configure_logging(log_level: str) -> None:
    """
    Configure structlog for JSON-formatted structured logging.

    Args:
        log_level: Logging level string (DEBUG, INFO, etc.).
    """
    import logging

    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, log_level.upper(), logging.INFO),
    )
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper(), logging.INFO),
        ),
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manage application lifecycle — initialize and teardown resources.

    On startup: loads settings, configures logging, initializes the
    database, and registers singletons for dependency injection.

    On shutdown: closes the database connection.

    Args:
        app: The FastAPI application instance.
    """
    # ─── Startup ──────────────────────────────────────────────
    settings = Settings()
    configure_logging(settings.log_level)

    logger.info(
        "app_starting",
        environment=settings.environment,
        database_url=settings.database_url,
    )

    # Initialize storage
    repo = SqliteStatusRepository(settings.get_db_path())
    await repo.initialize()

    # Register singletons
    set_settings(settings)
    set_repo(repo)

    logger.info("app_started")
    yield

    # ─── Shutdown ─────────────────────────────────────────────
    await repo.close()
    logger.info("app_stopped")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        Configured FastAPI instance with all routers and middleware.
    """
    app = FastAPI(
        title="OpenClaw Agent Status Board",
        description=(
            "Lightweight status-aggregation service for OpenClaw agents, "
            "optimized for TRMNL e-ink display."
        ),
        version="1.0.0",
        lifespan=lifespan,
    )

    # ─── CORS (permissive for dev, lock down in prod) ─────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ─── Register routers ─────────────────────────────────────
    app.include_router(health.router)
    app.include_router(agent_status.router)
    app.include_router(trmnl.router)

    return app


# Module-level app instance for uvicorn
app = create_app()
