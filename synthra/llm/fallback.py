"""LLM provider wrapper executing fallback route logic across multiple models."""

import logging
from typing import Any, Dict, List, Optional
from synthra.llm.base import LLMProvider
from synthra.llm.models import LLMRequest, LLMResponse, ProviderHealth

logger = logging.getLogger(__name__)


class FallbackLLMProvider(LLMProvider):
    """Wrapper that tries a list of LLM providers sequentially until one succeeds."""

    def __init__(self, providers: List[LLMProvider]) -> None:
        """Initialize fallback wrapper with list of ordered providers."""
        self.providers = providers

    def generate(self, request: LLMRequest) -> LLMResponse:
        """Execute text completion sequentially across providers."""
        errors = []
        for provider in self.providers:
            model_name = getattr(provider, "model", "unknown")
            try:
                logger.info("Attempting generation using LLM provider model: %s", model_name)
                return provider.generate(request)
            except Exception as e:
                logger.warning(
                    "LLM provider '%s' failed: %s. Trying fallback...",
                    model_name,
                    e,
                )
                errors.append(f"{model_name}: {e}")
        raise RuntimeError(f"All LLM providers failed: {'; '.join(errors)}")

    def chat(
        self, messages: List[Dict[str, str]], config: Optional[Any] = None
    ) -> LLMResponse:
        """Execute chat interaction sequentially across providers."""
        errors = []
        for provider in self.providers:
            model_name = getattr(provider, "model", "unknown")
            try:
                logger.info("Attempting chat using LLM provider model: %s", model_name)
                return provider.chat(messages, config)
            except Exception as e:
                logger.warning(
                    "LLM provider '%s' failed: %s. Trying fallback...",
                    model_name,
                    e,
                )
                errors.append(f"{model_name}: {e}")
        raise RuntimeError(f"All LLM providers failed: {'; '.join(errors)}")

    def health(self) -> ProviderHealth:
        """Check status of primary configured provider."""
        if self.providers:
            return self.providers[0].health()
        return ProviderHealth(status="unhealthy", latency_ms=0.0)

    def count_tokens(self, text: str) -> int:
        """Count tokens using primary provider."""
        if self.providers:
            return self.providers[0].count_tokens(text)
        return len(text) // 4

    def supports_json(self) -> bool:
        """Check JSON support constraint based on active model settings."""
        # For structured outputs, we check if the first (best available) provider supports it.
        if self.providers:
            return self.providers[0].supports_json()
        return False

    def supports_streaming(self) -> bool:
        """Check streaming capability."""
        if self.providers:
            return self.providers[0].supports_streaming()
        return False
