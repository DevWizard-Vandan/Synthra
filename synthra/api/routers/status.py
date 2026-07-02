"""Status router — detailed runtime information about the running service."""

import time
from typing import Any, Dict, List
from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter(tags=["status"])

VERSION = "0.1.0"


class MemoryStatus(BaseModel):
    """Database memory status sub-schema."""

    backend: str
    campaign_count: int
    simulations_executed: int


class CandidateQueueInfo(BaseModel):
    """Details about candidates currently enqueued for submission."""

    size: int
    candidates: List[Dict[str, Any]]


class StatusResponse(BaseModel):
    """Runtime status response schema."""

    version: str
    uptime_seconds: float
    memory: MemoryStatus
    campaign_counts: Dict[str, int]
    active_workers: int
    queue_sizes: Dict[str, int]
    simulations: int
    candidate_queue: CandidateQueueInfo
    current_campaigns: List[str]
    governor_state: str


@router.get("/status", response_model=StatusResponse)
async def status(request: Request) -> StatusResponse:
    """Runtime status including uptime, workers, queue sizes, and candidates."""
    start_time: float = getattr(request.app.state, "start_time", time.time())
    uptime = round(time.time() - start_time, 2)

    service = getattr(request.app.state, "service", None)
    if not service:
        # Default empty fallback state
        return StatusResponse(
            version=VERSION,
            uptime_seconds=uptime,
            memory=MemoryStatus(
                backend="sqlite", campaign_count=0, simulations_executed=0
            ),
            campaign_counts={},
            active_workers=0,
            queue_sizes={},
            simulations=0,
            candidate_queue=CandidateQueueInfo(size=0, candidates=[]),
            current_campaigns=[],
            governor_state="stopped",
        )

    gov = service.governor
    active_workers = len([w for w in gov.scheduler._workers if w.is_alive()])
    campaign_queue_size = gov.queue.size()
    submission_queue_size = gov.submission_queue.size()
    governor_state = "running" if gov.scheduler._running else "stopped"

    # Get active/queued campaign IDs
    current_campaigns = [c.id for c in gov.queue.get_all()]

    # Candidate queue details
    queued_cands = []
    for cand in gov.submission_queue.get_all():
        queued_cands.append(
            {
                "candidate_id": cand.candidate_id,
                "campaign_id": cand.campaign_id,
                "hypothesis_id": cand.hypothesis_id,
                "expression": cand.expression,
                "metrics": cand.metrics,
                "generation": cand.generation,
            }
        )

    # Get state counts
    total_campaigns = service.campaign_count()
    campaign_counts = {
        "total": total_campaigns,
        "queued": 0,
        "running": 0,
        "completed": 0,
        "failed": 0,
        "paused": 0,
        "cancelled": 0,
    }
    with gov.db_manager.connection() as conn:
        rows = conn.execute(
            "SELECT state, COUNT(*) FROM campaign_states GROUP BY state"
        ).fetchall()
        for r in rows:
            state_key = r[0].lower()
            if state_key in campaign_counts:
                campaign_counts[state_key] = r[1]

    simulations_executed = service.simulations_executed()

    return StatusResponse(
        version=VERSION,
        uptime_seconds=uptime,
        memory=MemoryStatus(
            backend="sqlite",
            campaign_count=total_campaigns,
            simulations_executed=simulations_executed,
        ),
        campaign_counts=campaign_counts,
        active_workers=active_workers,
        queue_sizes={
            "campaign_queue": campaign_queue_size,
            "submission_queue": submission_queue_size,
        },
        simulations=simulations_executed,
        candidate_queue=CandidateQueueInfo(
            size=submission_queue_size, candidates=queued_cands
        ),
        current_campaigns=current_campaigns,
        governor_state=governor_state,
    )
