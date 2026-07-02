"""Ollama local model API provider adapter using direct HTTP requests."""

import time
from typing import Any, Dict, List, Optional

import httpx

from synthra.llm.base import LLMProvider
from synthra.llm.exceptions import (
    GenerationError,
    ProviderUnavailable,
    TimeoutError,
)
from synthra.llm.models import LLMRequest, LLMResponse, ProviderHealth, TokenUsage


class OllamaProvider(LLMProvider):
    """Adapter for interacting with local Ollama service instances."""

    def __init__(
        self,
        model: str = "llama3",
        api_base: Optional[str] = None,
        timeout_seconds: int = 60,
    ) -> None:
        """Initialize Ollama connection endpoint properties."""
        self.model = model
        self.api_base = (api_base or "http://localhost:11434").rstrip("/")
        self.timeout = timeout_seconds

    def generate(self, request: LLMRequest) -> LLMResponse:
        """Submit generation request to local Ollama generate endpoint."""
        url = f"{self.api_base}/api/generate"
        payload = {
            "model": self.model,
            "prompt": request.prompt,
            "system": request.system_prompt,
            "stream": False,
            "options": {
                "temperature": request.config.temperature,
                "top_p": request.config.top_p,
            },
        }
        if request.config.response_format == "json":
            payload["format"] = "json"

        try:
            with httpx.Client(timeout=self.timeout) as client:
                res = client.post(url, json=payload)
                if res.status_code != 200:
                    raise GenerationError(
                        f"Ollama returned HTTP status {res.status_code}: {res.text}"
                    )
                data = res.json()
                text = data.get("response", "")

                prompt_tokens = data.get("prompt_eval_count", 0)
                completion_tokens = data.get("eval_count", 0)
                usage = TokenUsage(
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=prompt_tokens + completion_tokens,
                )

                return LLMResponse(
                    text=text,
                    model=self.model,
                    provider="ollama",
                    usage=usage,
                    cached=False,
                )
        except httpx.TimeoutException as e:
            raise TimeoutError(f"Ollama request timed out: {e}")
        except httpx.RequestError as e:
            raise ProviderUnavailable(f"Ollama endpoint unreachable: {e}")
        except Exception as e:
            raise GenerationError(f"Ollama error: {e}")

    def chat(
        self, messages: List[Dict[str, str]], config: Optional[Any] = None
    ) -> LLMResponse:
        """Submit message history to Ollama chat endpoint."""
        url = f"{self.api_base}/api/chat"
        payload = {
            "model": self.model,
            "messages": [
                {"role": m["role"], "content": m["content"]} for m in messages
            ],
            "stream": False,
        }
        try:
            with httpx.Client(timeout=self.timeout) as client:
                res = client.post(url, json=payload)
                if res.status_code != 200:
                    raise GenerationError(f"Ollama chat error: {res.text}")
                data = res.json()
                msg = data.get("message", {})
                text = msg.get("content", "")

                prompt_tokens = data.get("prompt_eval_count", 0)
                completion_tokens = data.get("eval_count", 0)
                usage = TokenUsage(
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=prompt_tokens + completion_tokens,
                )

                return LLMResponse(
                    text=text,
                    model=self.model,
                    provider="ollama",
                    usage=usage,
                    cached=False,
                )
        except Exception as e:
            raise GenerationError(f"Ollama chat generation failed: {e}")

    def health(self) -> ProviderHealth:
        """Check Ollama service liveness by pinging its root API endpoint."""
        url = f"{self.api_base}/"
        start = time.perf_counter()
        try:
            with httpx.Client(timeout=2.0) as client:
                res = client.get(url)
                latency = (time.perf_counter() - start) * 1000.0
                if res.status_code == 200:
                    return ProviderHealth(status="healthy", latency_ms=latency)
                return ProviderHealth(
                    status="unhealthy",
                    latency_ms=latency,
                    error_message=f"HTTP status {res.status_code}",
                )
        except Exception as e:
            latency = (time.perf_counter() - start) * 1000.0
            return ProviderHealth(
                status="unhealthy",
                latency_ms=latency,
                error_message=str(e),
            )

    def count_tokens(self, text: str) -> int:
        """Simple character fallback metric for Ollama inputs."""
        return len(text) // 4

    def supports_json(self) -> bool:
        """Ollama supports output format constraints."""
        return True

    def supports_streaming(self) -> bool:
        """Ollama supports token-level generation streaming."""
        return True
