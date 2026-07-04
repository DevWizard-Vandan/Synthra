"""Unit tests for the WorldQuant execution client."""

from dataclasses import dataclass, field
from typing import Mapping

import pytest

from pydantic import SecretStr
from synthra.core.domain import Region, SimulationRequest, Universe
from synthra.execution import (
    ExecutionAuthenticationError,
    ExecutionRateLimitError,
    HttpResponse,
    SimulationHandle,
    WorldQuantCredentials,
    WorldQuantExecutionClient,
    WorldQuantExecutionConfig,
)
from synthra.execution.transport import JsonObject


@dataclass
class RecordedRequest:
    """Captured transport call for assertions."""

    method: str
    url: str
    headers: Mapping[str, str]
    json_body: JsonObject | None
    timeout_seconds: float


@dataclass
class FakeTransport:
    """Deterministic transport returning queued responses."""

    responses: list[HttpResponse]
    requests: list[RecordedRequest] = field(default_factory=list)

    def request(
        self,
        method: str,
        url: str,
        headers: Mapping[str, str],
        json_body: JsonObject | None,
        timeout_seconds: float,
    ) -> HttpResponse:
        """Record request arguments and return the next fake response."""
        self.requests.append(
            RecordedRequest(
                method=method,
                url=url,
                headers=headers,
                json_body=json_body,
                timeout_seconds=timeout_seconds,
            )
        )
        return self.responses.pop(0)


def make_client(transport: FakeTransport) -> WorldQuantExecutionClient:
    """Build a client with test-safe configuration."""
    creds = WorldQuantCredentials(username="user", password=SecretStr("secret"))
    return WorldQuantExecutionClient(
        credentials=creds,
        config=WorldQuantExecutionConfig(api_base_url="https://brain.example.test"),
        transport=transport,
    )


def auth_response() -> HttpResponse:
    """Build a successful authentication response."""
    return HttpResponse(
        status_code=201,
        headers={},
        body=b'{"access_token":"session-token"}',
    )


def submit_response() -> HttpResponse:
    """Build a successful simulation submission response."""
    return HttpResponse(
        status_code=202,
        headers={"Location": "https://brain.example.test/simulations/SIM-1"},
        body=b'{"id":"SIM-1","status":"running"}',
    )


def test_authenticate_stores_bearer_token() -> None:
    """Authentication stores bearer credentials for later requests."""
    transport = FakeTransport(
        responses=[
            HttpResponse(
                status_code=201,
                headers={},
                body=b'{"access_token":"session-token"}',
            )
        ]
    )
    client = make_client(transport)

    client.authenticate()

    assert transport.requests[0].method == "POST"
    assert transport.requests[0].url == "https://brain.example.test/authentication"
    assert transport.requests[0].headers["Authorization"].startswith("Basic ")


def test_authenticate_rejects_invalid_credentials() -> None:
    """Authentication raises a narrow error for rejected credentials."""
    transport = FakeTransport(
        responses=[HttpResponse(status_code=401, headers={}, body=b"{}")]
    )
    client = make_client(transport)

    with pytest.raises(ExecutionAuthenticationError):
        client.authenticate()


def test_submit_simulation_authenticates_and_returns_handle() -> None:
    """Submitting a simulation sends a domain request and returns a handle."""
    transport = FakeTransport(
        responses=[
            HttpResponse(
                status_code=201,
                headers={"Set-Cookie": "session=abc"},
                body=b"{}",
            ),
            HttpResponse(
                status_code=202,
                headers={"Location": "https://brain.example.test/simulations/SIM-1"},
                body=b'{"id":"SIM-1","status":"running"}',
            ),
        ]
    )
    client = make_client(transport)
    request = SimulationRequest(
        expression="ts_rank(close, 20)",
        region=Region.US,
        universe=Universe.TOP3000,
    )

    handle = client.submit_simulation(request)

    assert handle == SimulationHandle(
        id="SIM-1",
        status="running",
        location="https://brain.example.test/simulations/SIM-1",
    )
    submit_request = transport.requests[1]
    assert submit_request.method == "POST"
    assert submit_request.headers["Cookie"] == "session=abc"
    assert submit_request.json_body is not None
    assert submit_request.json_body["expression"] == "ts_rank(close, 20)"
    assert submit_request.json_body["region"] == "US"


def test_submit_simulation_raises_rate_limit_after_retry() -> None:
    """Rate limiting is retried and then surfaced as a narrow exception."""
    transport = FakeTransport(
        responses=[
            HttpResponse(
                status_code=201,
                headers={},
                body=b'{"token":"session-token"}',
            ),
            HttpResponse(status_code=429, headers={}, body=b"{}"),
            HttpResponse(status_code=429, headers={}, body=b"{}"),
            HttpResponse(status_code=429, headers={}, body=b"{}"),
        ]
    )
    client = make_client(transport)

    with pytest.raises(ExecutionRateLimitError):
        client.submit_simulation(
            SimulationRequest(
                expression="ts_rank(close, 20)",
                region=Region.US,
                universe=Universe.TOP3000,
            )
        )


def test_get_simulation_returns_json_payload() -> None:
    """Simulation status lookup returns parsed platform payloads."""
    transport = FakeTransport(
        responses=[
            HttpResponse(
                status_code=201,
                headers={},
                body=b'{"access_token":"session-token"}',
            ),
            HttpResponse(
                status_code=200,
                headers={},
                body=b'{"id":"SIM-1","status":"complete"}',
            ),
        ]
    )
    client = make_client(transport)

    payload = client.get_simulation(
        SimulationHandle(
            id="SIM-1",
            status="running",
            location="https://brain.example.test/simulations/SIM-1",
        )
    )

    assert payload["id"] == "SIM-1"
    assert payload["status"] == "complete"


def test_client_automatic_session_refresh_on_401() -> None:
    """A 401 response on submission triggers re-authentication."""
    transport = FakeTransport(
        responses=[
            auth_response(),  # initial authenticate()
            HttpResponse(
                status_code=401, headers={}, body=b"{}"
            ),  # first submit fails with 401
            auth_response(),  # automatic re-auth
            submit_response(),  # retried submit succeeds
        ]
    )
    client = make_client(transport)
    request = SimulationRequest(
        expression="ts_rank(close, 20)",
        region=Region.US,
        universe=Universe.TOP3000,
    )

    handle = client.submit_simulation(request)
    assert handle.id == "SIM-1"
    # Verify we authenticated twice
    assert len(transport.requests) == 4
    assert transport.requests[0].url.endswith("/authentication")
    assert transport.requests[1].url.endswith("/simulations")
    assert transport.requests[2].url.endswith("/authentication")
    assert transport.requests[3].url.endswith("/simulations")


def test_client_retry_exponential_backoff(monkeypatch: pytest.MonkeyPatch) -> None:
    """Request retries sleep exponentially on transient failures."""
    sleep_times = []

    def mock_sleep(seconds: float) -> None:
        sleep_times.append(seconds)

    monkeypatch.setattr("time.sleep", mock_sleep)

    transport = FakeTransport(
        responses=[
            HttpResponse(status_code=429, headers={}, body=b"{}"),
            HttpResponse(status_code=500, headers={}, body=b"{}"),
            HttpResponse(
                status_code=201,
                headers={},
                body=b'{"access_token":"session-token"}',
            ),
        ]
    )
    client = make_client(transport)
    client.authenticate()

    assert len(transport.requests) == 3
    # First retry backoff: 0.5 * 2^0 = 0.5s
    # Second retry backoff: 0.5 * 2^1 = 1.0s
    assert sleep_times == [0.5, 1.0]
