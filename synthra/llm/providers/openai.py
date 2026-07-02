"""OpenAI API provider adapter with lazy SDK loading."""

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


class OpenAIProvider(LLMProvider):
    """Adapter for interacting with OpenAI completions and chat models."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o",
        api_base: Optional[str] = None,
        timeout_seconds: int = 120,
    ) -> None:
        """Initialize OpenAI provider configuration details."""
        self.api_key = api_key
        self.model = model
        self.api_base = api_base
        self.timeout = timeout_seconds
        self._client: Any = None

    def _get_client(self) -> Any:
        """Lazily initialize the OpenAI API client wrapper."""
        if self._client is not None:
            return self._client
        try:
            import openai
        except ImportError:
            raise ProviderUnavailable("OpenAI SDK is not installed.")

        try:
            self._client = openai.OpenAI(
                api_key=self.api_key,
                base_url=self.api_base,
                timeout=self.timeout,
            )
            return self._client
        except Exception as e:
            raise AuthenticationError(f"OpenAI auth setup failed: {e}")

    def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response matching the request parameters."""
        client = self._get_client()
        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})

        try:
            response_format = None
            if request.config.response_format == "json":
                response_format = {"type": "json_object"}

            comp = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=request.config.temperature,
                max_tokens=request.config.max_tokens,
                top_p=request.config.top_p,
                response_format=response_format,
            )
            choice = comp.choices[0]
            text = choice.message.content or ""
            usage_raw = getattr(comp, "usage", None)

            usage = TokenUsage(
                prompt_tokens=getattr(usage_raw, "prompt_tokens", 0),
                completion_tokens=getattr(usage_raw, "completion_tokens", 0),
                total_tokens=getattr(usage_raw, "total_tokens", 0),
            )

            return LLMResponse(
                text=text,
                model=self.model,
                provider="openai",
                usage=usage,
                cached=False,
            )
        except Exception as e:
            self._handle_exception(e)

    def chat(
        self, messages: List[Dict[str, str]], config: Optional[Any] = None
    ) -> LLMResponse:
        """Submit message history for a chat interaction."""
        client = self._get_client()
        try:
            comp = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": m["role"], "content": m["content"]} for m in messages
                ],
            )
            choice = comp.choices[0]
            text = choice.message.content or ""
            usage_raw = getattr(comp, "usage", None)
            usage = TokenUsage(
                prompt_tokens=getattr(usage_raw, "prompt_tokens", 0),
                completion_tokens=getattr(usage_raw, "completion_tokens", 0),
                total_tokens=getattr(usage_raw, "total_tokens", 0),
            )
            return LLMResponse(
                text=text,
                model=self.model,
                provider="openai",
                usage=usage,
                cached=False,
            )
        except Exception as e:
            self._handle_exception(e)

    def health(self) -> ProviderHealth:
        """Perform a low-latency check on OpenAI availability."""
        client = self._get_client()
        start = time.perf_counter()
        try:
            # Quick models list check as liveness probe
            client.models.list()
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
        """Estimate token usage using tiktoken if available, else standard fallback."""
        try:
            import tiktoken

            encoding = tiktoken.encoding_for_model(self.model)
            return len(encoding.encode(text))
        except Exception:
            # Fallback rule: ~4 characters per token
            return len(text) // 4

    def supports_json(self) -> bool:
        """OpenAI models support structured JSON outputs."""
        return True

    def supports_streaming(self) -> bool:
        """OpenAI supports server-sent event completion streaming."""
        return True

    def _handle_exception(self, e: Exception) -> NoReturn:
        """Map provider-specific error conditions to unified exception types."""
        # Clean inspection without strict type import dependencies
        err_type = type(e).__name__
        err_msg = str(e)

        if "RateLimit" in err_type or "RateLimit" in err_msg or "429" in err_msg:
            raise RateLimitError(f"OpenAI rate limit: {e}")
        elif (
            "Authentication" in err_type
            or "Authentication" in err_msg
            or "APIConnection" in err_type
            or "APIConnection" in err_msg
            or "401" in err_msg
        ):
            raise AuthenticationError(f"OpenAI credentials error: {e}")
        elif "Timeout" in err_type or "Timeout" in err_msg:
            raise TimeoutError(f"OpenAI request timeout: {e}")
        elif "BadRequest" in err_type or "BadRequest" in err_msg or "400" in err_msg:
            raise GenerationError(f"OpenAI bad request: {e}")
        raise GenerationError(f"OpenAI generation failed: {e}")
