"""FastAPI application factory and service bootstrap for SYNTHRA."""

import logging
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from synthra.api.routers import health, status, campaigns
from synthra.api.state import ServiceState

logger = logging.getLogger(__name__)

_START_TIME: float = 0.0


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Handle startup and shutdown lifecycle events."""
    global _START_TIME
    _START_TIME = time.time()

    logger.info("SYNTHRA service starting up")

    # Initialize service state (config, memory, catalog)
    state = ServiceState.get_instance()
    await state.initialize()

    app.state.service = state
    app.state.start_time = _START_TIME

    logger.info("SYNTHRA service ready")
    yield

    logger.info("SYNTHRA service shutting down")
    await state.shutdown()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    application = FastAPI(
        title="Synthra",
        description=("Autonomous quantitative research platform for WorldQuant BRAIN."),
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    application.include_router(health.router)
    application.include_router(status.router)
    application.include_router(campaigns.router)

    @application.get("/", tags=["root"])
    async def root() -> dict[str, str]:
        """Root endpoint returning service identity."""
        return {
            "service": "Synthra",
            "version": "0.1.0",
            "status": "running",
        }

    return application


app = create_app()
