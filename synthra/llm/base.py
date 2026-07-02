"""Abstract base interface defining the common contract for all LLM providers."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from synthra.llm.models import LLMRequest, LLMResponse, ProviderHealth


class LLMProvider(ABC):
    """Abstract interface defining required behaviors for language model clients."""

    @abstractmethod
    def generate(self, request: LLMRequest) -> LLMResponse:
        """Execute a text completion completion request."""
        pass

    @abstractmethod
    def chat(
        self, messages: List[Dict[str, str]], config: Optional[Any] = None
    ) -> LLMResponse:
        """Execute a multi-turn chat interaction."""
        pass

    @abstractmethod
    def health(self) -> ProviderHealth:
        """Check provider status and network connectivity latency."""
        pass

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Estimate token count for a text input block."""
        pass

    @abstractmethod
    def supports_json(self) -> bool:
        """Return True if the provider supports structured JSON output constraints."""
        pass

    @abstractmethod
    def supports_streaming(self) -> bool:
        """Return True if the provider supports token-level streaming responses."""
        pass
