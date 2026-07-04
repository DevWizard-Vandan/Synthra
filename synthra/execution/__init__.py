"""Execution layer for official WorldQuant BRAIN API interactions."""

from synthra.execution.client import WorldQuantExecutionClient
from synthra.execution.exceptions import (
    AuthenticationError,
    ExecutionAuthenticationError,
    ExecutionClientError,
    ExecutionError,
    ExecutionRateLimitError,
    ExecutionServerError,
    ExecutionTransportError,
    RateLimitError,
    SimulationFailedError,
    SimulationResultMappingError,
    SimulationRunnerError,
    SimulationTimeoutError,
    TimeoutError,
    TransportError,
)
from synthra.execution.models import (
    SimulationHandle,
    SimulationRunnerConfig,
    WorldQuantCredentials,
    WorldQuantExecutionConfig,
)
from synthra.execution.runner import SimulationRunner
from synthra.execution.transport import HttpResponse, HttpTransport, UrllibHttpTransport

__all__ = [
    "AuthenticationError",
    "ExecutionAuthenticationError",
    "ExecutionClientError",
    "ExecutionError",
    "ExecutionRateLimitError",
    "ExecutionServerError",
    "ExecutionTransportError",
    "HttpResponse",
    "HttpTransport",
    "RateLimitError",
    "SimulationHandle",
    "SimulationFailedError",
    "SimulationResultMappingError",
    "SimulationRunner",
    "SimulationRunnerConfig",
    "SimulationRunnerError",
    "SimulationTimeoutError",
    "TimeoutError",
    "TransportError",
    "UrllibHttpTransport",
    "WorldQuantCredentials",
    "WorldQuantExecutionClient",
    "WorldQuantExecutionConfig",
]
