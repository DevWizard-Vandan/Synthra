"""Provider Manager managing model configurations and provider selection."""

import logging
from typing import Dict, Optional

from synthra.core.config import ConfigurationManager, LLMConfig
from synthra.llm.base import LLMProvider
from synthra.llm.models import ProviderHealth
from synthra.llm.providers.anthropic import AnthropicProvider
from synthra.llm.providers.google import GoogleProvider
from synthra.llm.providers.ollama import OllamaProvider
from synthra.llm.providers.openai import OpenAIProvider
from synthra.llm.providers.openrouter import OpenRouterProvider

logger = logging.getLogger(__name__)


class ProviderManager:
    """Manager to load, instantiate, and route calls to LLM providers."""

    def __init__(self, config: Optional[LLMConfig] = None) -> None:
        """Initialize ProviderManager, optionally loading from injected config."""
        self._providers: Dict[str, LLMProvider] = {}
        self._default_provider_name: Optional[str] = None

        llm_config = config
        if llm_config is None:
            try:
                app_config = ConfigurationManager.config
                if app_config is not None:
                    llm_config = app_config.llm
            except Exception:
                logger.warning(
                    "ConfigurationManager not initialized; "
                    "running with empty providers."
                )

        if llm_config:
            self._load_providers(llm_config)

    def _load_providers(self, llm_config: LLMConfig) -> None:
        """Instantiate enabled providers from configuration settings."""
        for name, p_config in llm_config.providers.items():
            if not p_config.enabled:
                continue

            api_key = ""
            if p_config.secrets and p_config.secrets.api_key:
                api_key = p_config.secrets.api_key.get_secret_value()

            try:
                provider: Optional[LLMProvider] = None
                normalized_name = name.lower()

                if normalized_name == "openai":
                    provider = OpenAIProvider(
                        api_key=api_key,
                        model=p_config.model,
                        api_base=p_config.api_base,
                        timeout_seconds=p_config.timeout_seconds,
                    )
                elif normalized_name == "anthropic":
                    provider = AnthropicProvider(
                        api_key=api_key,
                        model=p_config.model,
                        api_base=p_config.api_base,
                        timeout_seconds=p_config.timeout_seconds,
                    )
                elif normalized_name in ("google", "gemini"):
                    provider = GoogleProvider(
                        api_key=api_key,
                        model=p_config.model,
                        api_base=p_config.api_base,
                        timeout_seconds=p_config.timeout_seconds,
                    )
                elif normalized_name == "openrouter":
                    provider = OpenRouterProvider(
                        api_key=api_key,
                        model=p_config.model,
                        api_base=p_config.api_base,
                        timeout_seconds=p_config.timeout_seconds,
                    )
                elif normalized_name == "ollama":
                    provider = OllamaProvider(
                        model=p_config.model,
                        api_base=p_config.api_base,
                        timeout_seconds=p_config.timeout_seconds,
                    )

                if provider:
                    self._providers[normalized_name] = provider
                    if self._default_provider_name is None:
                        self._default_provider_name = normalized_name
            except Exception as e:
                logger.error("Graceful skip. Failed to load provider '%s': %s", name, e)

    def register_provider(
        self, name: str, provider: LLMProvider, make_default: bool = False
    ) -> None:
        """Manually inject a custom provider, primarily for mocks and test overrides."""
        normalized_name = name.lower()
        self._providers[normalized_name] = provider
        if make_default or self._default_provider_name is None:
            self._default_provider_name = normalized_name

    def get_provider(self, name: str) -> LLMProvider:
        """Retrieve an instantiated provider by its normalized identifier key."""
        normalized_name = name.lower()
        if normalized_name not in self._providers:
            raise KeyError(f"LLM provider '{name}' is not configured or enabled.")
        return self._providers[normalized_name]

    def get_default_provider(self) -> LLMProvider:
        """Return the default/fallback active provider."""
        if not self._default_provider_name:
            raise RuntimeError("No active LLM providers configured.")
        return self._providers[self._default_provider_name]

    def health_check(self) -> Dict[str, ProviderHealth]:
        """Perform parallel latency status checks on all active connections."""
        results: Dict[str, ProviderHealth] = {}
        for name, provider in self._providers.items():
            results[name] = provider.health()
        return results

    def available_models(self) -> Dict[str, str]:
        """Map active provider name keys to their active execution models."""
        models: Dict[str, str] = {}
        for name, provider in self._providers.items():
            # Extract model parameter safely from adapter properties
            model_attr = getattr(provider, "model", "unknown")
            models[name] = model_attr
        return models
