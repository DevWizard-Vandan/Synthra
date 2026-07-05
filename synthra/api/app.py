import os
import logging
import time
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from synthra.api.routers import health, status, campaigns, auth
from synthra.api.state import ServiceState

logger = logging.getLogger(__name__)

_START_TIME: float = 0.0


class SPAStaticFiles(StaticFiles):
    """Custom StaticFiles subclass supporting SPA routing fallback to index.html."""

    async def get_response(self, path: str, scope: Any) -> Any:
        # Check if the path is an API path (normalizing path separators for cross-platform compatibility)
        clean_path = path.replace("\\", "/").lstrip("/")
        if clean_path.startswith("api/") or clean_path == "api":
            raise HTTPException(status_code=404, detail="Not Found")

        try:
            response = await super().get_response(path, scope)
            if response.status_code == 404:
                html_path = os.path.join(self.directory, path + ".html")
                if os.path.isfile(html_path):
                    return FileResponse(html_path)
                return FileResponse(os.path.join(self.directory, "index.html"))
            return response
        except (HTTPException, StarletteHTTPException) as ex:
            if ex.status_code == 404:
                html_path = os.path.join(self.directory, path + ".html")
                if os.path.isfile(html_path):
                    return FileResponse(html_path)
                return FileResponse(os.path.join(self.directory, "index.html"))
            raise ex
        except Exception:
            return FileResponse(os.path.join(self.directory, "index.html"))


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

    # Prefix-level router registration (production frontend)
    application.include_router(health.router, prefix="/api")
    application.include_router(status.router, prefix="/api")
    application.include_router(campaigns.router, prefix="/api")
    application.include_router(auth.router, prefix="/api")

    @application.get("/api", tags=["root"])
    async def root_api() -> dict[str, str]:
        """Root API endpoint returning service identity."""
        return {
            "service": "Synthra",
            "version": "0.1.0",
            "status": "running",
        }

    # Mount Next.js static exported HTML
    root_dir = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    frontend_out = os.path.join(root_dir, "frontend", "out")
    if os.path.exists(frontend_out):
        application.mount(
            "/", SPAStaticFiles(directory=frontend_out, html=True), name="static"
        )

    return application


app = create_app()
