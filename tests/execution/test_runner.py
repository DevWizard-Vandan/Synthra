"""Unit tests for the simulation runner."""

from dataclasses import dataclass, field
from typing import Mapping

import pytest

from pydantic import SecretStr
from synthra.core.domain import Region, SimulationRequest, SimulationResult, Universe
from synthra.execution import (
    HttpResponse,
    SimulationFailedError,
    SimulationResultMappingError,
    SimulationRunner,
    SimulationRunnerConfig,
    SimulationTimeoutError,
    WorldQuantCredentials,
    WorldQuantExecutionClient,
    WorldQuantExecutionConfig,
)
from synthra.execution.transport import JsonObject


@dataclass
class RecordedRequest:
    """Captured transport request."""

    method: str
    url: str
    headers: Mapping[str, str]
    json_body: JsonObject | None
    timeout_seconds: float


@dataclass
class FakeTransport:
    """Queue-backed fake transport for offline runner tests."""

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
        """Record the request and return the next queued response."""
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


@dataclass
class FakeClock:
    """Controllable monotonic clock used to avoid real test sleeps."""

    current: float = 0.0
    sleeps: list[float] = field(default_factory=list)

    def now(self) -> float:
        """Return the current fake monotonic time."""
        return self.current

    def sleep(self, seconds: float) -> None:
        """Advance fake time by the requested sleep interval."""
        self.sleeps.append(seconds)
        self.current += seconds


def make_client(transport: FakeTransport) -> WorldQuantExecutionClient:
    """Build a WorldQuant client with fake transport dependencies."""
    creds = WorldQuantCredentials(username="user", password=SecretStr("secret"))
    return WorldQuantExecutionClient(
        credentials=creds,
        config=WorldQuantExecutionConfig(api_base_url="https://brain.example.test"),
        transport=transport,
    )


def make_request() -> SimulationRequest:
    """Build a valid domain simulation request."""
    return SimulationRequest(
        expression="ts_rank(close, 20)",
        region=Region.US,
        universe=Universe.TOP3000,
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


def test_runner_submits_polls_and_maps_completed_result() -> None:
    """Runner returns SimulationResult after a completed poll payload."""
    transport = FakeTransport(
        responses=[
            auth_response(),
            submit_response(),
            HttpResponse(status_code=200, headers={}, body=b'{"status":"running"}'),
            HttpResponse(
                status_code=200,
                headers={},
                body=(
                    b'{"status":"complete","result":{"sharpe":1.2,'
                    b'"fitness":0.9,"margin":0.05,"turnover":0.3,'
                    b'"coverage":0.8}}'
                ),
            ),
        ]
    )
    clock = FakeClock()
    runner = SimulationRunner(
        client=make_client(transport),
        config=SimulationRunnerConfig(polling_interval_seconds=0.5),
        sleeper=clock.sleep,
        monotonic_clock=clock.now,
    )

    result = runner.run(make_request())

    assert isinstance(result, SimulationResult)
    assert result.sharpe == 1.2
    assert result.fitness == 0.9
    assert result.margin == 0.05
    assert result.turnover == 0.3
    assert result.coverage == 0.8
    assert clock.sleeps == [0.5]
    assert transport.requests[-1].method == "GET"


def test_runner_applies_exponential_backoff_between_polls() -> None:
    """Runner increases poll intervals using the configured backoff multiplier."""
    transport = FakeTransport(
        responses=[
            auth_response(),
            submit_response(),
            HttpResponse(status_code=200, headers={}, body=b'{"status":"running"}'),
            HttpResponse(status_code=200, headers={}, body=b'{"status":"running"}'),
            HttpResponse(
                status_code=200,
                headers={},
                body=(
                    b'{"status":"completed","sharpe":1,"fitness":2,'
                    b'"margin":3,"turnover":4,"coverage":5}'
                ),
            ),
        ]
    )
    clock = FakeClock()
    runner = SimulationRunner(
        client=make_client(transport),
        config=SimulationRunnerConfig(
            polling_interval_seconds=0.5,
            backoff_multiplier=2.0,
            max_polling_interval_seconds=10.0,
        ),
        sleeper=clock.sleep,
        monotonic_clock=clock.now,
    )

    runner.run(make_request())

    assert clock.sleeps == [0.5, 1.0]


def test_runner_times_out_when_simulation_never_completes() -> None:
    """Runner raises a typed timeout when polling exceeds the configured limit."""
    transport = FakeTransport(
        responses=[
            auth_response(),
            submit_response(),
            HttpResponse(status_code=200, headers={}, body=b'{"status":"running"}'),
            HttpResponse(status_code=200, headers={}, body=b'{"status":"running"}'),
            HttpResponse(status_code=200, headers={}, body=b'{"status":"running"}'),
        ]
    )
    clock = FakeClock()
    runner = SimulationRunner(
        client=make_client(transport),
        config=SimulationRunnerConfig(
            polling_interval_seconds=0.5,
            timeout_seconds=1.0,
            backoff_multiplier=2.0,
        ),
        sleeper=clock.sleep,
        monotonic_clock=clock.now,
    )

    with pytest.raises(SimulationTimeoutError):
        runner.run(make_request())

    assert clock.sleeps == [0.5, 1.0]


def test_runner_raises_failed_error_for_terminal_failure() -> None:
    """Runner preserves platform failure details in a typed exception."""
    transport = FakeTransport(
        responses=[
            auth_response(),
            submit_response(),
            HttpResponse(
                status_code=200,
                headers={},
                body=b'{"status":"failed","message":"expression invalid"}',
            ),
        ]
    )
    runner = SimulationRunner(client=make_client(transport), sleeper=lambda _: None)

    with pytest.raises(SimulationFailedError) as exc_info:
        runner.run(make_request())

    assert "expression invalid" in str(exc_info.value)


def test_runner_rejects_completed_payload_without_required_metrics() -> None:
    """Runner raises a mapping error when completed payloads lack metrics."""
    transport = FakeTransport(
        responses=[
            auth_response(),
            submit_response(),
            HttpResponse(
                status_code=200,
                headers={},
                body=b'{"status":"complete","result":{"sharpe":1.0}}',
            ),
        ]
    )
    runner = SimulationRunner(client=make_client(transport), sleeper=lambda _: None)

    with pytest.raises(SimulationResultMappingError):
        runner.run(make_request())


def test_runner_validates_expression_syntax() -> None:
    """SimulationRunner raises error if expression has mismatched parentheses."""
    from synthra.execution import SimulationRunnerError

    client = make_client(FakeTransport(responses=[]))
    runner = SimulationRunner(client=client, sleeper=lambda _: None)

    # Empty expression check directly
    with pytest.raises(SimulationRunnerError) as exc:
        runner._validate_expression("")
    assert "Expression must not be empty" in str(exc.value)

    # Mismatched parentheses
    req2 = SimulationRequest(
        expression="ts_rank(close, 20", region=Region.US, universe=Universe.TOP3000
    )
    with pytest.raises(SimulationRunnerError) as exc:
        runner.run(req2)
    assert "Mismatched parentheses" in str(exc.value)


def test_runner_persists_logs_to_database(tmp_path) -> None:
    """SimulationRunner records raw execution details to DB."""
    from synthra.memory import DatabaseManager

    db_file = tmp_path / "test_runner.db"
    db_mgr = DatabaseManager(str(db_file))

    transport = FakeTransport(
        responses=[
            auth_response(),
            submit_response(),
            HttpResponse(
                status_code=200,
                headers={},
                body=(
                    b'{"status":"complete","result":{"sharpe":1.2,'
                    b'"fitness":0.9,"margin":0.05,"turnover":0.3,'
                    b'"coverage":0.8}}'
                ),
            ),
        ]
    )
    runner = SimulationRunner(
        client=make_client(transport),
        sleeper=lambda _: None,
        db_manager=db_mgr,
    )

    req = make_request()
    result = runner.run(req)
    assert result.sharpe == 1.2

    # Query simulation_logs to check persistence
    with db_mgr.connection() as conn:
        row = conn.execute("SELECT * FROM simulation_logs").fetchone()
        assert row is not None
        assert row["expression"] == "ts_rank(close, 20)"
        assert row["status"] == "completed"
        assert row["raw_request"] is not None
        assert "USA" in row["raw_request"] or "US" in row["raw_request"]
        assert row["raw_response"] is not None
        assert "complete" in row["raw_response"]
        assert row["normalized_metrics"] is not None
        assert "1.2" in row["normalized_metrics"]
        assert row["started_at"] is not None
        assert row["finished_at"] is not None
        assert isinstance(row["duration"], float)
