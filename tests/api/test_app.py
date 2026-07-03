"""Tests for the FastAPI service layer."""

from typing import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_state() -> MagicMock:
    """Return a fully-configured mock ServiceState."""
    state = MagicMock()
    state.is_ready = True
    state.campaign_count.return_value = 0
    state.simulations_executed.return_value = 0
    state.initialize = AsyncMock()
    state.shutdown = AsyncMock()
    return state


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    """Provide a TestClient with mocked ServiceState initialization."""
    mock_state = _make_mock_state()

    with patch("synthra.api.app.ServiceState.get_instance", return_value=mock_state):
        from synthra.api.app import create_app

        application = create_app()
        with TestClient(application, raise_server_exceptions=True) as tc:
            yield tc


# ---------------------------------------------------------------------------
# Root
# ---------------------------------------------------------------------------


def test_root_returns_service_identity(client: TestClient) -> None:
    """GET / returns service name, version, and running status."""
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["service"] == "Synthra"
    assert body["version"] == "0.1.0"
    assert body["status"] == "running"


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


def test_health_returns_healthy(client: TestClient) -> None:
    """GET /health returns status=healthy."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_health_is_fast(client: TestClient) -> None:
    """GET /health must complete without touching state or DB."""
    import time

    start = time.perf_counter()
    response = client.get("/health")
    elapsed = time.perf_counter() - start

    assert response.status_code == 200
    # Must complete within 200 ms even on slow CI
    assert elapsed < 0.2


# ---------------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------------


def test_status_returns_expected_schema(client: TestClient) -> None:
    """GET /status returns version, uptime_seconds, and memory sub-object."""
    response = client.get("/status")
    assert response.status_code == 200
    body = response.json()

    assert body["version"] == "0.1.0"
    assert isinstance(body["uptime_seconds"], float)
    assert body["uptime_seconds"] >= 0

    mem = body["memory"]
    assert mem["backend"] == "sqlite"
    assert isinstance(mem["campaign_count"], int)
    assert isinstance(mem["simulations_executed"], int)


# ---------------------------------------------------------------------------
# Campaigns (stub)
# ---------------------------------------------------------------------------


def test_campaigns_list_returns_empty(client: TestClient) -> None:
    """GET /campaigns returns empty list and zero total."""
    response = client.get("/campaigns")
    assert response.status_code == 200
    body = response.json()
    assert body["campaigns"] == []
    assert body["total"] == 0


# ---------------------------------------------------------------------------
# Import sanity
# ---------------------------------------------------------------------------


def test_app_module_importable() -> None:
    """The app module must be importable from the expected path."""
    from synthra.api import app as app_module  # noqa: F401

    assert hasattr(app_module, "app")


def test_state_module_importable() -> None:
    """ServiceState must be importable from synthra.api.state."""
    from synthra.api.state import ServiceState  # noqa: F401

    assert ServiceState is not None
