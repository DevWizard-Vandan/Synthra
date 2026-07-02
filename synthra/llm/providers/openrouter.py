"""OpenRouter API provider adapter leveraging OpenAI compatibility."""

from typing import Any, Dict, List, Optional

from synthra.llm.models import LLMRequest, LLMResponse
from synthra.llm.providers.openai import OpenAIProvider


class OpenRouterProvider(OpenAIProvider):
    """Adapter for OpenRouter completions utilising the OpenAI client package."""

    def __init__(
        self,
        api_key: str,
        model: str = "meta-llama/llama-3-8b-instruct:free",
        api_base: Optional[str] = None,
        timeout_seconds: int = 120,
    ) -> None:
        """Initialize OpenRouter with its standard base URL endpoint."""
        actual_base = api_base or "https://openrouter.ai/api/v1"
        super().__init__(
            api_key=api_key,
            model=model,
            api_base=actual_base,
            timeout_seconds=timeout_seconds,
        )

    def generate(self, request: LLMRequest) -> LLMResponse:
        """Execute text generation and mark provider source as openrouter."""
        response = super().generate(request)
        return response.model_copy(update={"provider": "openrouter"})

    def chat(
        self, messages: List[Dict[str, str]], config: Optional[Any] = None
    ) -> LLMResponse:
        """Execute chat interaction and mark provider source as openrouter."""
        response = super().chat(messages, config)
        return response.model_copy(update={"provider": "openrouter"})
