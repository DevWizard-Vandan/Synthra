"""Status router — runtime information about the running service."""

import time

from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter(tags=["status"])

VERSION = "0.1.0"


class MemoryStatus(BaseModel):
    """Database memory status sub-schema."""

    backend: str
    campaign_count: int
    simulations_executed: int


class StatusResponse(BaseModel):
    """Runtime status response schema."""

    version: str
    uptime_seconds: float
    memory: MemoryStatus


@router.get("/status", response_model=StatusResponse)
async def status(request: Request) -> StatusResponse:
    """Runtime status including uptime, version, and memory counters."""
    start_time: float = getattr(request.app.state, "start_time", time.time())
    uptime = round(time.time() - start_time, 2)

    service = getattr(request.app.state, "service", None)
    campaign_count = service.campaign_count() if service else 0
    simulations_executed = service.simulations_executed() if service else 0

    return StatusResponse(
        version=VERSION,
        uptime_seconds=uptime,
        memory=MemoryStatus(
            backend="sqlite",
            campaign_count=campaign_count,
            simulations_executed=simulations_executed,
        ),
    )
