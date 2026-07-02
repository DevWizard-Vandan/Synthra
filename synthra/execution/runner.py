"""Simulation runner built on top of the WorldQuant execution client."""

import logging
import time
from collections.abc import Callable, Mapping

from synthra.core.domain import SimulationRequest, SimulationResult
from synthra.execution.client import WorldQuantExecutionClient
from synthra.execution.exceptions import (
    SimulationFailedError,
    SimulationResultMappingError,
    SimulationTimeoutError,
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
    ) -> None:
        """Initialize the runner with injected client and timing dependencies.

        Args:
            client: Execution client used for submission and status lookups.
            config: Polling and timeout controls.
            sleeper: Sleep function, injected by tests to avoid real delays.
            monotonic_clock: Monotonic time source, injected by timeout tests.
        """
        self._client = client
        self._config = config or SimulationRunnerConfig()
        self._sleep = sleeper or time.sleep
        self._monotonic = monotonic_clock or time.monotonic

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
        handle = self._client.submit_simulation(request)
        deadline = self._monotonic() + self._config.timeout_seconds
        interval_seconds = self._config.polling_interval_seconds

        while True:
            payload = self._client.get_simulation(handle)
            status = self._status(payload)

            if status in COMPLETED_STATUSES:
                return self._map_result(payload)
            if status in FAILED_STATUSES:
                message = self._failure_message(payload)
                raise SimulationFailedError(
                    f"Simulation {handle.id} failed with status '{status}': {message}"
                )
            if self._monotonic() >= deadline:
                raise SimulationTimeoutError(
                    f"Simulation {handle.id} did not complete within "
                    f"{self._config.timeout_seconds} seconds."
                )

            self._sleep(interval_seconds)
            interval_seconds = min(
                interval_seconds * self._config.backoff_multiplier,
                self._config.max_polling_interval_seconds,
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
