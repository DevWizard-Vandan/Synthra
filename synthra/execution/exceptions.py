"""Exception hierarchy for the SYNTHRA execution layer."""


class ExecutionError(Exception):
    """Base error for execution-layer failures."""


class ExecutionTransportError(ExecutionError):
    """Raised when HTTP transport fails before a structured response is available."""


class ExecutionAuthenticationError(ExecutionError):
    """Raised when authentication with the execution platform fails."""


class ExecutionClientError(ExecutionError):
    """Raised for non-retryable 4xx execution platform responses."""


class ExecutionRateLimitError(ExecutionClientError):
    """Raised when the platform rejects a request due to rate limiting."""


class ExecutionServerError(ExecutionError):
    """Raised when the platform returns a 5xx response after retries."""


class SimulationRunnerError(ExecutionError):
    """Base error for simulation runner failures."""


class SimulationTimeoutError(SimulationRunnerError):
    """Raised when a simulation does not complete within the configured timeout."""


class SimulationFailedError(SimulationRunnerError):
    """Raised when the platform reports a failed simulation terminal state."""


class SimulationResultMappingError(SimulationRunnerError):
    """Raised when a completed response cannot be mapped to SimulationResult."""
