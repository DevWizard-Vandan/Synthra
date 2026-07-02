"""Exhaustive offline tests for the LLM Provider Layer."""

import time
from unittest.mock import MagicMock, patch
import pytest
from pydantic import BaseModel, SecretStr

from synthra.core.config import LLMConfig, LLMProviderConfig, LLMProviderSecrets
from synthra.llm import (
    AuthenticationError,
    GenerationConfig,
    GenerationError,
    LLMCache,
    LLMRequest,
    LLMResponse,
    ProviderManager,
    RateLimitError,
    StructuredLLMBridge,
    TimeoutError,
    TokenUsage,
)
from synthra.llm.providers.openai import OpenAIProvider
from synthra.llm.providers.anthropic import AnthropicProvider
from synthra.llm.providers.ollama import OllamaProvider

# ---------------------------------------------------------------------------
# Caching Tests
# ---------------------------------------------------------------------------


def test_cache_set_get_clear_ttl() -> None:
    """Verify in-memory cache behaves correctly under TTL and clearance."""
    cache = LLMCache(default_ttl_seconds=2)
    config = GenerationConfig(temperature=0.0)

    response = LLMResponse(
        text="Cached response content",
        model="gpt-4o",
        provider="openai",
        usage=TokenUsage(prompt_tokens=10, completion_tokens=10, total_tokens=20),
    )

    # Put in cache
    cache.set(
        provider="openai",
        model="gpt-4o",
        prompt="hello",
        system_prompt=None,
        config=config,
        response=response,
    )

    # Get from cache - should exist
    cached = cache.get(
        provider="openai",
        model="gpt-4o",
        prompt="hello",
        system_prompt=None,
        config=config,
    )
    assert cached is not None
    assert cached.text == "Cached response content"
    assert cached.cached is True

    # Check non-existent prompt
    assert (
        cache.get(
            provider="openai",
            model="gpt-4o",
            prompt="different",
            system_prompt=None,
            config=config,
        )
        is None
    )

    # Clear cache
    cache.clear()
    assert (
        cache.get(
            provider="openai",
            model="gpt-4o",
            prompt="hello",
            system_prompt=None,
            config=config,
        )
        is None
    )

    # Test TTL expiration using mock time
    cache.set(
        provider="openai",
        model="gpt-4o",
        prompt="hello",
        system_prompt=None,
        config=config,
        response=response,
        ttl_seconds=1,
    )
    with patch("time.time", return_value=time.time() + 2):
        assert (
            cache.get(
                provider="openai",
                model="gpt-4o",
                prompt="hello",
                system_prompt=None,
                config=config,
            )
            is None
        )


# ---------------------------------------------------------------------------
# Provider Selection and Registration Tests
# ---------------------------------------------------------------------------


def test_provider_manager_selection_and_fallback() -> None:
    """Verify manual provider registration, default fallback, and lookup errors."""
    manager = ProviderManager(config=None)

    mock_openai = MagicMock(spec=OpenAIProvider)
    mock_anthropic = MagicMock(spec=AnthropicProvider)

    # Register
    manager.register_provider("openai", mock_openai, make_default=True)
    manager.register_provider("anthropic", mock_anthropic)

    assert manager.get_default_provider() is mock_openai
    assert manager.get_provider("openai") is mock_openai
    assert manager.get_provider("anthropic") is mock_anthropic

    # Case insensitivity check
    assert manager.get_provider("OpEnAi") is mock_openai

    # Unregistered lookup check
    with pytest.raises(KeyError):
        manager.get_provider("google")


# ---------------------------------------------------------------------------
# Configuration Loading Tests
# ---------------------------------------------------------------------------


def test_configuration_loading_and_instantiation() -> None:
    """Verify that manager loads configurations and registers enabled adapters."""
    # Build a mock config structure
    providers = {
        "openai": LLMProviderConfig(
            model="gpt-4o",
            enabled=True,
            timeout_seconds=60,
            secrets=LLMProviderSecrets(api_key=SecretStr("sk-openai")),
        ),
        "anthropic": LLMProviderConfig(
            model="claude-3-5",
            enabled=False,  # Should skip loading this one
            timeout_seconds=60,
            secrets=LLMProviderSecrets(api_key=SecretStr("sk-anthropic")),
        ),
    }
    llm_config = LLMConfig(providers=providers)

    with patch("synthra.llm.providers.openai.OpenAIProvider._get_client"):
        manager = ProviderManager(config=llm_config)
        assert "openai" in manager.available_models()
        assert "anthropic" not in manager.available_models()
        assert manager.available_models()["openai"] == "gpt-4o"


# ---------------------------------------------------------------------------
# Exception Mapping Tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw_exception, expected_exception",
    [
        (Exception("RateLimitError occurred"), RateLimitError),
        (Exception("AuthenticationError occurred 401"), AuthenticationError),
        (Exception("Timeout occurred"), TimeoutError),
        (Exception("BadRequest occurred"), GenerationError),
    ],
)
def test_openai_exception_mapping(
    raw_exception: Exception, expected_exception: type
) -> None:
    """Verify that provider maps SDK errors to standard SYNTHRA LLM exception types."""
    provider = OpenAIProvider(api_key="mock", model="gpt-4o")

    # Mock client and call completions endpoint
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = raw_exception
    provider._client = mock_client

    request = LLMRequest(prompt="hello")
    with pytest.raises(expected_exception):
        provider.generate(request)


# ---------------------------------------------------------------------------
# Structured LLM Bridge Tests
# ---------------------------------------------------------------------------


class MockStructuredOutput(BaseModel):
    """Pydantic model used to test structured JSON output parsing."""

    rationale: str
    target: str


def test_structured_llm_bridge_parsing() -> None:
    """Verify bridge adapts unstructured string response and parses JSON to Pydantic."""
    mock_provider = MagicMock(spec=OpenAIProvider)
    mock_provider.supports_json.return_value = True

    # Setup provider to return JSON text block
    mock_provider.generate.return_value = LLMResponse(
        text='{"rationale": "momentum indicator", "target": "returns"}',
        model="gpt-4o",
        provider="openai",
    )

    bridge = StructuredLLMBridge(provider=mock_provider)
    result = bridge.generate_structured(
        system_prompt="system",
        user_prompt="user",
        response_model=MockStructuredOutput,
    )

    assert isinstance(result, MockStructuredOutput)
    assert result.rationale == "momentum indicator"
    assert result.target == "returns"


# ---------------------------------------------------------------------------
# Ollama Rest API Tests
# ---------------------------------------------------------------------------


def test_ollama_provider_makes_requests() -> None:
    """Verify Ollama adapter correctly formats HTTP post payloads and maps results."""
    provider = OllamaProvider(model="llama3", api_base="http://localhost:11434")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "response": "Llama completed response.",
        "prompt_eval_count": 5,
        "eval_count": 10,
    }

    # Mock httpx Client
    with patch("httpx.Client.post", return_value=mock_response) as mock_post:
        request = LLMRequest(prompt="ping")
        res = provider.generate(request)

        assert res.text == "Llama completed response."
        assert res.usage.prompt_tokens == 5
        assert res.usage.completion_tokens == 10
        assert res.usage.total_tokens == 15

        mock_post.assert_called_once()
