"""Tests for the telemetry and Governor status endpoints in FastAPI."""

from typing import Generator
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi.testclient import TestClient
from synthra.governor.events import WorkerIdle


def _make_mock_state_with_governor() -> MagicMock:
    """Return a fully-configured mock ServiceState with a Governor."""
    state = MagicMock()
    state.is_ready = True
    state.campaign_count.return_value = 5
    state.simulations_executed.return_value = 10
    state.initialize = AsyncMock()
    state.shutdown = AsyncMock()

    # Mock Governor
    gov = MagicMock()

    # Telemetry
    gov.telemetry.get_metrics.return_value = {
        "running_workers": 2,
        "queued_jobs": 1,
        "completed_jobs": 3,
        "failed_jobs": 0,
        "campaigns_running": 1,
        "campaigns_completed": 3,
        "simulations_running": 1,
        "simulations_completed": 10,
        "accepted_candidates": 2,
        "rejected_candidates": 4,
        "mutations_generated": 15,
        "average_simulation_time": 4.5,
        "uptime": 120.5,
    }

    # Event History
    gov.telemetry.get_events.return_value = [WorkerIdle(worker_name="Worker-1")]

    # Workers
    w1 = MagicMock()
    w1.worker_id = 1
    w1.is_alive.return_value = True

    w2 = MagicMock()
    w2.worker_id = 2
    w2.is_alive.return_value = False

    gov.scheduler._workers = [w1, w2]
    gov.scheduler.num_workers = 2
    gov.scheduler.max_retries = 3
    gov.scheduler.initial_backoff = 2.0
    gov.scheduler._running = True

    # Queue
    campaign = MagicMock()
    campaign.id = "CMP-0001"
    campaign.name = "Test Queue Campaign"

    gov.queue.size.return_value = 1
    gov.queue._campaigns = {"CMP-0001": (campaign, 5)}

    # Submission Queue (Candidates)
    cand = MagicMock()
    cand.candidate_id = "CAND-0001"
    cand.campaign_id = "CMP-0001"
    cand.hypothesis_id = "HYP-0001"
    cand.expression = "close/open"
    cand.metrics = {"sharpe": 1.5}
    cand.generation = 1

    gov.submission_queue.size.return_value = 1
    gov.submission_queue.get_all.return_value = [cand]

    # DB connection for campaigns query
    conn = MagicMock()
    cursor = MagicMock()
    cursor.fetchall.return_value = [
        (
            "CMP-0001",
            "Test Queue Campaign",
            "US",
            "TOP2000",
            100.0,
            10.0,
            5,
            20,
            "ACTIVE",
            "RUNNING",
        )
    ]
    conn.execute.return_value = cursor
    gov.db_manager.connection.return_value.__enter__.return_value = conn

    state.governor = gov
    return state


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    """Provide a TestClient with mocked ServiceState and Governor."""
    mock_state = _make_mock_state_with_governor()

    with patch("synthra.api.app.ServiceState.get_instance", return_value=mock_state):
        from synthra.api.app import create_app

        application = create_app()
        with TestClient(application, raise_server_exceptions=True) as tc:
            yield tc


def test_get_metrics(client: TestClient) -> None:
    """GET /metrics returns the telemetry metrics."""
    response = client.get("/metrics")
    assert response.status_code == 200
    metrics = response.json()
    assert metrics["running_workers"] == 2
    assert metrics["queued_jobs"] == 1
    assert metrics["average_simulation_time"] == 4.5


def test_get_workers(client: TestClient) -> None:
    """GET /workers returns the status of active worker threads."""
    response = client.get("/workers")
    assert response.status_code == 200
    workers = response.json()
    assert len(workers) == 2
    assert workers[0]["worker_id"] == 1
    assert workers[0]["is_alive"] is True
    assert workers[1]["worker_id"] == 2
    assert workers[1]["is_alive"] is False


def test_get_campaigns(client: TestClient) -> None:
    """GET /campaigns returns the list of all campaigns with state."""
    response = client.get("/campaigns")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    campaigns = body["campaigns"]
    assert campaigns[0]["id"] == "CMP-0001"
    assert campaigns[0]["state"] == "RUNNING"


def test_get_queue(client: TestClient) -> None:
    """GET /queue returns campaigns currently in the queue."""
    response = client.get("/queue")
    assert response.status_code == 200
    queue = response.json()
    assert len(queue) == 1
    assert queue[0]["id"] == "CMP-0001"
    assert queue[0]["priority"] == 5


def test_get_candidates(client: TestClient) -> None:
    """GET /candidates returns alpha candidates enqueued for submission."""
    response = client.get("/candidates")
    assert response.status_code == 200
    candidates = response.json()
    assert len(candidates) == 1
    assert candidates[0]["candidate_id"] == "CAND-0001"
    assert candidates[0]["metrics"]["sharpe"] == 1.5


def test_get_events(client: TestClient) -> None:
    """GET /events returns recent events."""
    response = client.get("/events")
    assert response.status_code == 200
    events = response.json()
    assert len(events) == 1
    assert events[0]["event_type"] == "WorkerIdle"
    assert events[0]["worker_name"] == "Worker-1"


def test_get_system(client: TestClient) -> None:
    """GET /system returns system stats."""
    response = client.get("/system")
    assert response.status_code == 200
    system = response.json()
    assert system["database_backend"] == "sqlite"
    assert system["campaign_count"] == 5
    assert system["simulations_executed"] == 10


def test_get_governor(client: TestClient) -> None:
    """GET /governor returns governor stats and configuration."""
    response = client.get("/governor")
    assert response.status_code == 200
    governor = response.json()
    assert governor["status"] == "running"
    assert governor["worker_count"] == 2
    assert governor["max_retries"] == 3


def test_events_stream(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """GET /events/stream returns event-stream media type."""
    from typing import Any, AsyncGenerator
    from fastapi import Request

    async def mock_sse_generator(
        request: Request, event_bus: Any
    ) -> AsyncGenerator[str, None]:
        yield ": connection established\n\n"

    monkeypatch.setattr("synthra.api.routers.status.sse_generator", mock_sse_generator)

    with client.stream("GET", "/events/stream") as response:
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
