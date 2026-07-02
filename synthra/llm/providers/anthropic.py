"""Anthropic Claude API provider adapter with lazy SDK loading."""

import time
from typing import Any, Dict, List, NoReturn, Optional

from synthra.llm.base import LLMProvider
from synthra.llm.exceptions import (
    AuthenticationError,
    GenerationError,
    ProviderUnavailable,
    RateLimitError,
    TimeoutError,
)
from synthra.llm.models import LLMRequest, LLMResponse, ProviderHealth, TokenUsage


class AnthropicProvider(LLMProvider):
    """Adapter for interacting with Anthropic Claude completion and message APIs."""

    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-5-sonnet-20241022",
        api_base: Optional[str] = None,
        timeout_seconds: int = 120,
    ) -> None:
        """Initialize Anthropic provider credentials and configuration."""
        self.api_key = api_key
        self.model = model
        self.api_base = api_base
        self.timeout = timeout_seconds
        self._client: Any = None

    def _get_client(self) -> Any:
        """Lazily initialize the Anthropic API client."""
        if self._client is not None:
            return self._client
        try:
            import anthropic  # type: ignore
        except ImportError:
            raise ProviderUnavailable("Anthropic SDK is not installed.")

        try:
            self._client = anthropic.Anthropic(
                api_key=self.api_key,
                base_url=self.api_base,
                timeout=self.timeout,
            )
            return self._client
        except Exception as e:
            raise AuthenticationError(f"Anthropic auth setup failed: {e}")

    def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response utilizing Anthropic Messages API."""
        client = self._get_client()
        system_prompt = request.system_prompt or ""

        try:
            # Prepare configuration params
            max_tokens = request.config.max_tokens or 4096

            response = client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": request.prompt}],
                temperature=request.config.temperature,
                top_p=request.config.top_p,
            )

            text = ""
            if response.content and len(response.content) > 0:
                text = response.content[0].text

            usage_raw = getattr(response, "usage", None)
            usage = TokenUsage(
                prompt_tokens=getattr(usage_raw, "input_tokens", 0),
                completion_tokens=getattr(usage_raw, "output_tokens", 0),
                total_tokens=(
                    getattr(usage_raw, "input_tokens", 0)
                    + getattr(usage_raw, "output_tokens", 0)
                ),
            )

            return LLMResponse(
                text=text,
                model=self.model,
                provider="anthropic",
                usage=usage,
                cached=False,
            )
        except Exception as e:
            self._handle_exception(e)

    def chat(
        self, messages: List[Dict[str, str]], config: Optional[Any] = None
    ) -> LLMResponse:
        """Submit message history to Anthropic messages endpoint."""
        client = self._get_client()
        try:
            response = client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[
                    {"role": m["role"], "content": m["content"]} for m in messages
                ],
            )
            text = ""
            if response.content and len(response.content) > 0:
                text = response.content[0].text
            usage_raw = getattr(response, "usage", None)
            usage = TokenUsage(
                prompt_tokens=getattr(usage_raw, "input_tokens", 0),
                completion_tokens=getattr(usage_raw, "output_tokens", 0),
                total_tokens=(
                    getattr(usage_raw, "input_tokens", 0)
                    + getattr(usage_raw, "output_tokens", 0)
                ),
            )
            return LLMResponse(
                text=text,
                model=self.model,
                provider="anthropic",
                usage=usage,
                cached=False,
            )
        except Exception as e:
            self._handle_exception(e)

    def health(self) -> ProviderHealth:
        """Verify connection liveness by hitting a minimal test message request."""
        client = self._get_client()
        start = time.perf_counter()
        try:
            # Send a ultra-short test ping
            client.messages.create(
                model=self.model,
                max_tokens=1,
                messages=[{"role": "user", "content": "ping"}],
            )
            latency = (time.perf_counter() - start) * 1000.0
            return ProviderHealth(status="healthy", latency_ms=latency)
        except Exception as e:
            latency = (time.perf_counter() - start) * 1000.0
            return ProviderHealth(
                status="unhealthy",
                latency_ms=latency,
                error_message=str(e),
            )

    def count_tokens(self, text: str) -> int:
        """Estimate token size for input text."""
        # Standard character count estimate (4 chars = 1 token)
        return len(text) // 4

    def supports_json(self) -> bool:
        """Claude supports structured JSON outputs through prompting rules."""
        return True

    def supports_streaming(self) -> bool:
        """Anthropic supports chunked token streaming endpoints."""
        return True

    def _handle_exception(self, e: Exception) -> NoReturn:
        """Map Anthropic errors to unified exceptions."""
        err_type = type(e).__name__
        err_msg = str(e)

        if "RateLimit" in err_type or "429" in err_msg:
            raise RateLimitError(f"Anthropic rate limit: {e}")
        elif "Authentication" in err_type or "401" in err_msg:
            raise AuthenticationError(f"Anthropic credentials: {e}")
        elif "Timeout" in err_type:
            raise TimeoutError(f"Anthropic timeout: {e}")
        raise GenerationError(f"Anthropic generation error: {e}")
