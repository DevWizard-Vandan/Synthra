"""Simulation runner built on top of the WorldQuant execution client."""

import logging
import time
import uuid
import json
from collections.abc import Callable, Mapping
from datetime import datetime
from typing import Any

from synthra.core.domain import SimulationRequest, SimulationResult
from synthra.execution.client import WorldQuantExecutionClient
from synthra.execution.exceptions import (
    SimulationFailedError,
    SimulationResultMappingError,
    SimulationTimeoutError,
    SimulationRunnerError,
)
from synthra.execution.models import SimulationRunnerConfig
from synthra.execution.transport import JsonValue

logger = logging.getLogger(__name__)

COMPLETED_STATUSES = {"complete", "completed", "done", "success", "passed"}
FAILED_STATUSES = {"failed", "error", "cancelled", "canceled", "rejected"}


class SimulationRunner:
    """Submit a simulation request and poll until a terminal result is available."""

    def __init__(
        self,
        client: WorldQuantExecutionClient,
        config: SimulationRunnerConfig | None = None,
        sleeper: Callable[[float], None] | None = None,
        monotonic_clock: Callable[[], float] | None = None,
        db_manager: Any = None,
    ) -> None:
        """Initialize the runner with injected client and timing dependencies.

        Args:
            client: Execution client used for submission and status lookups.
            config: Polling and timeout controls.
            sleeper: Sleep function, injected by tests to avoid real delays.
            monotonic_clock: Monotonic time source, injected by timeout tests.
            db_manager: Optional DatabaseManager for SQL log persistence.
        """
        self._client = client
        self._config = config or SimulationRunnerConfig()
        self._sleep = sleeper or time.sleep
        self._monotonic = monotonic_clock or time.monotonic
        self._db_manager = db_manager

    def run(self, request: SimulationRequest) -> SimulationResult:
        """Submit and monitor a simulation request until it completes.

        Args:
            request: Domain simulation request.

        Returns:
            Mapped domain simulation result.

        Raises:
            SimulationTimeoutError: If timeout expires before completion.
            SimulationFailedError: If the platform returns a failed terminal state.
            SimulationResultMappingError: If completed payload lacks result metrics.
        """
        trace_id = f"TRC-{uuid.uuid4().hex[:8].upper()}"
        started_at = datetime.utcnow()

        # Before call: validate and log
        self._validate_payload(request)
        self._validate_expression(request.expression)
        logger.info(
            f"[Simulation] Trace ID: {trace_id} | "
            f"Submitting expression: '{request.expression}'"
        )

        # Persist request start immediately
        self._persist_state(
            trace_id=trace_id,
            expression=request.expression,
            raw_request=request.model_dump(mode="json"),
            status="submitted",
            started_at=started_at,
        )

        handle = None
        try:
            handle = self._client.submit_simulation(request)
            deadline = self._monotonic() + self._config.timeout_seconds
            interval_seconds = self._config.polling_interval_seconds

            while True:
                payload = self._client.get_simulation(handle)
                status = self._status(payload)

                # Validate response schema in client payload
                self._validate_response_schema(payload, status)

                if status in COMPLETED_STATUSES:
                    result = self._map_result(payload)
                    # Normalize values
                    metrics = {
                        "sharpe": result.sharpe,
                        "fitness": result.fitness,
                        "margin": result.margin,
                        "turnover": result.turnover,
                        "coverage": result.coverage,
                    }
                    self._persist_state(
                        trace_id=trace_id,
                        expression=request.expression,
                        raw_request=request.model_dump(mode="json"),
                        status="completed",
                        started_at=started_at,
                        finished_at=datetime.utcnow(),
                        raw_response=payload,
                        normalized_metrics=metrics,
                    )
                    return result

                if status in FAILED_STATUSES:
                    message = self._failure_message(payload)
                    self._persist_state(
                        trace_id=trace_id,
                        expression=request.expression,
                        raw_request=request.model_dump(mode="json"),
                        status="failed",
                        started_at=started_at,
                        finished_at=datetime.utcnow(),
                        raw_response=payload,
                        error_message=message,
                    )
                    raise SimulationFailedError(
                        f"Simulation {handle.id} failed with "
                        f"status '{status}': {message}"
                    )

                if self._monotonic() >= deadline:
                    msg = (
                        f"Simulation {handle.id} did not complete within "
                        f"{self._config.timeout_seconds} seconds."
                    )
                    self._persist_state(
                        trace_id=trace_id,
                        expression=request.expression,
                        raw_request=request.model_dump(mode="json"),
                        status="failed",
                        started_at=started_at,
                        finished_at=datetime.utcnow(),
                        raw_response=payload,
                        error_message=msg,
                    )
                    raise SimulationTimeoutError(msg)

                self._sleep(interval_seconds)
                interval_seconds = min(
                    interval_seconds * self._config.backoff_multiplier,
                    self._config.max_polling_interval_seconds,
                )

        except Exception as err:
            logger.error(
                f"[Simulation] Failed execution for trace {trace_id}: {str(err)}",
                exc_info=True,
            )
            # Update status to failed if not already stored as completed
            self._persist_state(
                trace_id=trace_id,
                expression=request.expression,
                raw_request=request.model_dump(mode="json"),
                status="failed",
                started_at=started_at,
                finished_at=datetime.utcnow(),
                error_message=str(err),
            )
            raise

    def _validate_payload(self, request: SimulationRequest) -> None:
        """Validate the SimulationRequest payload structure."""
        if not isinstance(request, SimulationRequest):
            raise SimulationRunnerError("Payload must be a SimulationRequest instance")

    def _validate_expression(self, expression: str) -> None:
        """Validate formatting/syntax of Fast Expression."""
        if not expression or not expression.strip():
            raise SimulationRunnerError("Expression must not be empty")

        # Balance check
        open_parens = 0
        for char in expression:
            if char == "(":
                open_parens += 1
            elif char == ")":
                open_parens -= 1
                if open_parens < 0:
                    raise SimulationRunnerError(
                        f"Mismatched parentheses in expression: {expression}"
                    )
        if open_parens != 0:
            raise SimulationRunnerError(
                f"Mismatched parentheses in expression: {expression}"
            )

    def _validate_response_schema(
        self, payload: Mapping[str, JsonValue], status: str
    ) -> None:
        """Validate structure/schema of the API response payload."""
        if not isinstance(payload, dict):
            raise SimulationResultMappingError(
                "API response payload must be a JSON object"
            )
        if status in COMPLETED_STATUSES:
            # Must contain result/metrics/results sub-dictionary
            metrics = self._metrics_payload(payload)
            if not isinstance(metrics, dict):
                raise SimulationResultMappingError(
                    "Completed payload lacks result dictionary"
                )

    def _persist_state(
        self,
        trace_id: str,
        expression: str,
        raw_request: dict[str, Any],
        status: str,
        started_at: datetime,
        finished_at: datetime | None = None,
        raw_response: Mapping[str, JsonValue] | None = None,
        normalized_metrics: dict[str, Any] | None = None,
        error_message: str | None = None,
    ) -> None:
        """Persist simulation metadata to log table."""
        if not self._db_manager:
            return

        duration = (finished_at - started_at).total_seconds() if finished_at else None

        with self._db_manager.transaction() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO simulation_logs (
                    trace_id, expression, raw_request, raw_response,
                    normalized_metrics, status, error_message,
                    started_at, finished_at, duration
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    trace_id,
                    expression,
                    json.dumps(raw_request),
                    json.dumps(raw_response) if raw_response is not None else None,
                    (
                        json.dumps(normalized_metrics)
                        if normalized_metrics is not None
                        else None
                    ),
                    status,
                    error_message,
                    started_at.isoformat(),
                    finished_at.isoformat() if finished_at is not None else None,
                    duration,
                ),
            )

    @staticmethod
    def _status(payload: Mapping[str, JsonValue]) -> str:
        """Extract normalized platform status from a poll payload."""
        value = payload.get("status")
        if isinstance(value, str) and value:
            return value.lower()
        return "unknown"

    @staticmethod
    def _failure_message(payload: Mapping[str, JsonValue]) -> str:
        """Extract a human-readable failure message from a platform payload."""
        for key in ("error", "message", "reason"):
            value = payload.get(key)
            if isinstance(value, str) and value:
                return value
        return "no failure message provided"

    @classmethod
    def _map_result(cls, payload: Mapping[str, JsonValue]) -> SimulationResult:
        """Map a completed platform payload into the domain SimulationResult."""
        metrics = cls._metrics_payload(payload)
        return SimulationResult(
            sharpe=cls._numeric_field(metrics, "sharpe"),
            fitness=cls._numeric_field(metrics, "fitness"),
            margin=cls._numeric_field(metrics, "margin"),
            turnover=cls._numeric_field(metrics, "turnover"),
            coverage=cls._numeric_field(metrics, "coverage"),
        )

    @staticmethod
    def _metrics_payload(payload: Mapping[str, JsonValue]) -> Mapping[str, JsonValue]:
        """Find the object containing result metrics in common response shapes."""
        for key in ("result", "results", "metrics"):
            value = payload.get(key)
            if isinstance(value, dict):
                return value
        return payload

    @staticmethod
    def _numeric_field(payload: Mapping[str, JsonValue], field: str) -> float:
        """Extract a numeric metric while rejecting bools and missing fields."""
        value = payload.get(field)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise SimulationResultMappingError(
                f"Completed simulation payload missing numeric '{field}' metric."
            )
        return float(value)
