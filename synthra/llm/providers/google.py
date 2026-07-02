"""Google Gemini API provider adapter with lazy SDK loading."""

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


class GoogleProvider(LLMProvider):
    """Adapter for Google Gemini generative model APIs."""

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-1.5-flash",
        api_base: Optional[str] = None,
        timeout_seconds: int = 120,
    ) -> None:
        """Initialize Google Gemini adapter params."""
        self.api_key = api_key
        self.model = model
        self.api_base = api_base
        self.timeout = timeout_seconds
        self._client: Any = None

    def _get_client(self) -> Any:
        """Lazily initialize Google generativeai library setup."""
        if self._client is not None:
            return self._client
        try:
            import google.generativeai as genai  # type: ignore
        except ImportError:
            raise ProviderUnavailable("Google GenerativeAI SDK is not installed.")

        try:
            genai.configure(api_key=self.api_key)
            self._client = genai.GenerativeModel(self.model)
            return self._client
        except Exception as e:
            raise AuthenticationError(f"Google setup failed: {e}")

    def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response via GenerativeModel."""
        model_client = self._get_client()
        try:
            import google.generativeai as genai
        except ImportError:
            raise ProviderUnavailable("Google GenerativeAI SDK is not installed.")

            # Construct configuration
        config = genai.types.GenerationConfig(
            temperature=request.config.temperature,
            max_output_tokens=request.config.max_tokens,
            top_p=request.config.top_p,
            response_mime_type=(
                "application/json"
                if request.config.response_format == "json"
                else "text/plain"
            ),
        )

        try:
            # Construct contents
            contents = []
            if request.system_prompt:
                # Pass system instructions safely via client config or prepend
                # to contents if dynamic configuration is unsupported.
                contents.append(f"System instructions: {request.system_prompt}")
            contents.append(request.prompt)

            response = model_client.generate_content(
                contents,
                generation_config=config,
            )

            text = response.text or ""

            # Token usage details
            usage = TokenUsage(
                prompt_tokens=self.count_tokens(request.prompt),
                completion_tokens=self.count_tokens(text),
                total_tokens=self.count_tokens(request.prompt)
                + self.count_tokens(text),
            )

            return LLMResponse(
                text=text,
                model=self.model,
                provider="google",
                usage=usage,
                cached=False,
            )
        except Exception as e:
            self._handle_exception(e)

    def chat(
        self, messages: List[Dict[str, str]], config: Optional[Any] = None
    ) -> LLMResponse:
        """Submit message history to Gemini API."""
        model_client = self._get_client()
        try:
            # Simple conversion to Gemini content blocks
            prompt_str = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
            response = model_client.generate_content(prompt_str)
            text = response.text or ""
            usage = TokenUsage(
                prompt_tokens=self.count_tokens(prompt_str),
                completion_tokens=self.count_tokens(text),
                total_tokens=self.count_tokens(prompt_str) + self.count_tokens(text),
            )
            return LLMResponse(
                text=text,
                model=self.model,
                provider="google",
                usage=usage,
                cached=False,
            )
        except Exception as e:
            self._handle_exception(e)

    def health(self) -> ProviderHealth:
        """Check availability by querying token count endpoint."""
        model_client = self._get_client()
        start = time.perf_counter()
        try:
            # Query token count as latency test
            model_client.count_tokens("liveness ping")
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
        """Estimate token count for Gemini inputs."""
        try:
            model_client = self._get_client()
            return int(model_client.count_tokens(text).total_tokens)
        except Exception:
            return len(text) // 4

    def supports_json(self) -> bool:
        """Gemini supports structured JSON output via application/json mime type."""
        return True

    def supports_streaming(self) -> bool:
        """Gemini supports stream-generate content APIs."""
        return True

    def _handle_exception(self, e: Exception) -> NoReturn:
        """Map Gemini errors to unified models."""
        err_msg = str(e)
        if "Quota" in err_msg or "429" in err_msg:
            raise RateLimitError(f"Google Gemini rate limit: {e}")
        elif "API key" in err_msg or "401" in err_msg or "403" in err_msg:
            raise AuthenticationError(f"Google credentials fail: {e}")
        elif "deadline" in err_msg.lower() or "timeout" in err_msg.lower():
            raise TimeoutError(f"Google Gemini timeout: {e}")
        raise GenerationError(f"Google Gemini error: {e}")
