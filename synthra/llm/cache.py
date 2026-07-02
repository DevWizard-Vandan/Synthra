"""In-memory cache for storing and reusing LLM responses with TTL constraints."""

import time
from typing import Any, Dict, Optional, Tuple

from synthra.llm.models import GenerationConfig, LLMResponse


class LLMCache:
    """Thread-safe TTL in-memory cache for mapping LLM requests to responses."""

    def __init__(self, default_ttl_seconds: int = 3600) -> None:
        """Initialize cache with a default TTL duration."""
        self.default_ttl = default_ttl_seconds
        # Structure: key -> (Response, Expiration timestamp)
        self._cache: Dict[Tuple[Any, ...], Tuple[LLMResponse, float]] = {}

    def _make_key(
        self,
        provider: str,
        model: str,
        prompt: str,
        system_prompt: Optional[str],
        config: GenerationConfig,
    ) -> Tuple[Any, ...]:
        """Construct a hashable tuple representing the request footprint."""
        config_tuple = (
            config.temperature,
            config.max_tokens,
            config.top_p,
            config.response_format,
        )
        return (provider, model, prompt, system_prompt, config_tuple)

    def get(
        self,
        provider: str,
        model: str,
        prompt: str,
        system_prompt: Optional[str],
        config: GenerationConfig,
    ) -> Optional[LLMResponse]:
        """Lookup cached response, filtering out expired cache keys."""
        key = self._make_key(provider, model, prompt, system_prompt, config)
        if key in self._cache:
            response, expiry = self._cache[key]
            if time.time() < expiry:
                # Return response copy marked as cached
                return response.model_copy(update={"cached": True})
            else:
                del self._cache[key]
        return None

    def set(
        self,
        provider: str,
        model: str,
        prompt: str,
        system_prompt: Optional[str],
        config: GenerationConfig,
        response: LLMResponse,
        ttl_seconds: Optional[int] = None,
    ) -> None:
        """Store a response in cache with a custom or default TTL."""
        key = self._make_key(provider, model, prompt, system_prompt, config)
        actual_ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        expiry = time.time() + actual_ttl

        # Ensure response is stored with cached=False so retrieves copy cleanly
        stored_response = response.model_copy(update={"cached": False})
        self._cache[key] = (stored_response, expiry)

    def clear(self) -> None:
        """Flush all cache entries."""
        self._cache.clear()
