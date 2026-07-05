"""Status router — detailed runtime information about the running service."""

import time
from typing import Any, AsyncGenerator, Dict, List
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
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


class WorkerInfo(BaseModel):
    """Details about an active worker thread."""

    worker_id: int
    is_alive: bool
    name: str


class QueueCampaignInfo(BaseModel):
    """Details about a campaign in the execution queue."""

    id: str
    name: str
    priority: int


class CandidateInfo(BaseModel):
    """Details about an accepted alpha candidate in the submission queue."""

    candidate_id: str
    campaign_id: str
    hypothesis_id: str
    expression: str
    metrics: Dict[str, Any]
    generation: int


class SystemInfo(BaseModel):
    """System-wide configuration, DB stats, and queue metrics."""

    database_backend: str
    campaign_count: int
    simulations_executed: int
    active_workers: int
    queue_sizes: Dict[str, int]


class GovernorInfo(BaseModel):
    """Settings and state of the central Governor."""

    status: str
    worker_count: int
    max_retries: int
    initial_backoff: float


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


@router.get("/metrics")
async def metrics(request: Request) -> Dict[str, Any]:
    """Get system-level telemetry and metrics."""
    service = getattr(request.app.state, "service", None)
    if not service or not service.governor:
        return {}
    metrics_dict: Dict[str, Any] = service.governor.telemetry.get_metrics()

    db_manager = service.governor.db_manager
    db_metrics = {}
    try:
        with db_manager.connection() as conn:
            # 1. Performance stats
            row = conn.execute(
                "SELECT AVG(sharpe), AVG(fitness), AVG(margin), AVG(turnover), AVG(coverage) FROM learning_records"
            ).fetchone()
            if row:
                db_metrics["avg_sharpe"] = round(row[0], 4) if row[0] is not None else 0.0
                db_metrics["avg_fitness"] = round(row[1], 4) if row[1] is not None else 0.0
                db_metrics["avg_margin"] = round(row[2], 4) if row[2] is not None else 0.0
                db_metrics["avg_turnover"] = round(row[3], 4) if row[3] is not None else 0.0
                db_metrics["avg_coverage"] = round(row[4], 4) if row[4] is not None else 0.0

            # 2. Best Sharpe ever
            row = conn.execute("SELECT MAX(sharpe) FROM learning_records").fetchone()
            db_metrics["best_sharpe_ever"] = round(row[0], 4) if row and row[0] is not None else 0.0

            # 3. Best Sharpe today
            row = conn.execute(
                "SELECT MAX(sharpe) FROM learning_records WHERE date(created_at) = date('now')"
            ).fetchone()
            db_metrics["best_sharpe_today"] = round(row[0], 4) if row and row[0] is not None else 0.0

            # 4. Total expressions & acceptance rate
            total_sims_row = conn.execute("SELECT COUNT(*) FROM simulation_logs WHERE status = 'completed'").fetchone()
            total_sims = total_sims_row[0] if total_sims_row else 0
            candidates_row = conn.execute("SELECT COUNT(*) FROM alpha_candidates").fetchone()
            total_candidates = candidates_row[0] if candidates_row else 0
            
            db_metrics["acceptance_rate"] = (
                round(total_candidates / total_sims, 4) if total_sims > 0 else 0.0
            )

            # 5. Last hypothesis
            row = conn.execute("SELECT rationale, target_variable FROM hypotheses ORDER BY created_at DESC LIMIT 1").fetchone()
            if row:
                db_metrics["current_hypothesis_rationale"] = row[0]
                db_metrics["current_hypothesis_target"] = row[1]
            else:
                db_metrics["current_hypothesis_rationale"] = "Generating first research campaign hypothesis..."
                db_metrics["current_hypothesis_target"] = "None"

            # 6. Max evolution generation
            row = conn.execute("SELECT MAX(generation) FROM expression_lineages").fetchone()
            db_metrics["max_generation"] = row[0] if row and row[0] is not None else 0

            # 7. Mutation stats
            rows = conn.execute("SELECT mutation_type, COUNT(*) FROM expression_lineages GROUP BY mutation_type").fetchall()
            mutation_stats = {r[0]: r[1] for r in rows if r[0]}
            db_metrics["mutation_stats"] = mutation_stats

            # 8. Operator & Dataset usage
            import json
            rows = conn.execute("SELECT operators, datasets FROM learning_records").fetchall()
            op_counts = {}
            ds_counts = {}
            for r in rows:
                try:
                    ops = json.loads(r[0])
                    for op in ops:
                        op_counts[op] = op_counts.get(op, 0) + 1
                except Exception:
                    pass
                try:
                    ds = json.loads(r[1])
                    for d in ds:
                        ds_counts[d] = ds_counts.get(d, 0) + 1
                except Exception:
                    pass
            db_metrics["operator_usage"] = op_counts
            db_metrics["dataset_usage"] = ds_counts
            
            # 9. Submitted today
            row = conn.execute(
                "SELECT COUNT(*) FROM alpha_candidates WHERE is_submitted = 1 AND date(submitted_at) = date('now')"
            ).fetchone()
            db_metrics["submitted_today"] = row[0] if row else 0

    except Exception as e:
        db_metrics["db_metrics_error"] = str(e)

    metrics_dict.update(db_metrics)
    return metrics_dict


@router.get("/workers", response_model=List[WorkerInfo])
async def get_workers(request: Request) -> List[WorkerInfo]:
    """Get information about running worker threads."""
    service = getattr(request.app.state, "service", None)
    if not service or not service.governor:
        return []
    gov = service.governor
    return [
        WorkerInfo(
            worker_id=w.worker_id,
            is_alive=w.is_alive(),
            name=f"CampaignWorker-{w.worker_id}",
        )
        for w in gov.scheduler._workers
    ]


@router.get("/queue", response_model=List[QueueCampaignInfo])
async def get_queue(request: Request) -> List[QueueCampaignInfo]:
    """Get campaigns currently in the scheduler queue."""
    service = getattr(request.app.state, "service", None)
    if not service or not service.governor:
        return []
    gov = service.governor
    with gov.queue._lock:
        items = list(gov.queue._campaigns.values())
    return [
        QueueCampaignInfo(
            id=campaign.id,
            name=campaign.name,
            priority=priority,
        )
        for campaign, priority in items
    ]


@router.get("/candidates", response_model=List[CandidateInfo])
async def get_candidates(request: Request) -> List[CandidateInfo]:
    """Get alpha candidates enqueued in the submission queue."""
    service = getattr(request.app.state, "service", None)
    if not service or not service.governor:
        return []
    gov = service.governor
    queued_cands = []
    for cand in gov.submission_queue.get_all():
        queued_cands.append(
            CandidateInfo(
                candidate_id=cand.candidate_id,
                campaign_id=cand.campaign_id,
                hypothesis_id=cand.hypothesis_id,
                expression=cand.expression,
                metrics=cand.metrics,
                generation=cand.generation,
            )
        )
    return queued_cands


@router.get("/events")
async def get_events(request: Request) -> List[Dict[str, Any]]:
    """Get recent events from the rolling event history log."""
    service = getattr(request.app.state, "service", None)
    if not service or not service.governor:
        return []
    events = service.governor.telemetry.get_events()
    return [
        {
            "event_type": event.__class__.__name__,
            **event.model_dump(),
        }
        for event in events
    ]


@router.get("/system", response_model=SystemInfo)
async def get_system(request: Request) -> SystemInfo:
    """Get system health and environment state information."""
    service = getattr(request.app.state, "service", None)
    if not service:
        return SystemInfo(
            database_backend="sqlite",
            campaign_count=0,
            simulations_executed=0,
            active_workers=0,
            queue_sizes={},
        )
    gov = service.governor
    active_workers = len([w for w in gov.scheduler._workers if w.is_alive()])
    campaign_queue_size = gov.queue.size()
    submission_queue_size = gov.submission_queue.size()
    return SystemInfo(
        database_backend="sqlite",
        campaign_count=service.campaign_count(),
        simulations_executed=service.simulations_executed(),
        active_workers=active_workers,
        queue_sizes={
            "campaign_queue": campaign_queue_size,
            "submission_queue": submission_queue_size,
        },
    )


@router.get("/governor", response_model=GovernorInfo)
async def get_governor(request: Request) -> GovernorInfo:
    """Get governor runtime state and settings configuration."""
    service = getattr(request.app.state, "service", None)
    if not service or not service.governor:
        return GovernorInfo(
            status="stopped",
            worker_count=0,
            max_retries=0,
            initial_backoff=0.0,
        )
    gov = service.governor
    status = "running" if gov.scheduler._running else "stopped"
    return GovernorInfo(
        status=status,
        worker_count=gov.scheduler.num_workers,
        max_retries=gov.scheduler.max_retries,
        initial_backoff=gov.scheduler.initial_backoff,
    )


async def sse_generator(request: Request, event_bus: Any) -> AsyncGenerator[str, None]:
    """Generator for streaming live events via SSE."""
    import asyncio

    queue: asyncio.Queue[Any] = asyncio.Queue()

    def listener(event: Any) -> None:
        try:
            loop.call_soon_threadsafe(queue.put_nowait, event)
        except Exception:
            pass

    loop = asyncio.get_running_loop()
    event_bus.subscribe(listener)

    # Yield connection established comment immediately to flush headers
    yield ": connection established\n\n"

    try:
        while True:
            if await request.is_disconnected():
                break
            try:
                event = await asyncio.wait_for(queue.get(), timeout=1.0)
                evt_name = event.__class__.__name__
                evt_data = event.model_dump_json()
                yield f"event: {evt_name}\ndata: {evt_data}\n\n"
            except asyncio.TimeoutError:
                yield ": keep-alive\n\n"
    finally:
        event_bus.unsubscribe(listener)


@router.get("/events/stream")
async def event_stream(request: Request) -> StreamingResponse:
    """Stream live events using Server-Sent Events (SSE)."""
    service = getattr(request.app.state, "service", None)
    if not service or not service.governor:

        async def empty_generator() -> AsyncGenerator[str, None]:
            yield "data: {}\n\n"

        return StreamingResponse(empty_generator(), media_type="text/event-stream")

    return StreamingResponse(
        sse_generator(request, service.governor.event_bus),
        media_type="text/event-stream",
    )
