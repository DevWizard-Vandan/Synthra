"""Exception hierarchy for the SYNTHRA LLM Provider Layer."""


class LLMError(Exception):
    """Base exception for all language model integration errors."""

    pass


class ProviderUnavailable(LLMError):
    """Raised when a configured provider is offline, missing SDK, or unreachable."""

    pass


class AuthenticationError(LLMError):
    """Raised when authorization checks or API credentials validation fail."""

    pass


class RateLimitError(LLMError):
    """Raised when the provider rejects requests due to rate limits."""

    pass


class GenerationError(LLMError):
    """Raised when text generation fails (e.g. content policy violations)."""

    pass


class TimeoutError(LLMError):
    """Raised when a generation request times out."""

    pass
