"""Orchestration control loop and data wrapper gateway."""

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from synthra.core.config.exceptions import (
    ConfigurationFileMissing,
    SecretMissingError,
)
from synthra.core.config.loader import ConfigurationLoader
from synthra.core.config.models import ApplicationConfig, ConfigurationSummary
from synthra.core.config.parser import ConfigurationParser
from synthra.core.config.resolver import ConfigurationResolver
from synthra.core.config.validator import ConfigurationValidator


class ConfigurationManager:
    """Orchestration control loop and data wrapper gateway."""

    # Class attributes to store the latest initialized configuration state
    config: Optional[ApplicationConfig] = None
    summary: Optional[ConfigurationSummary] = None

    @staticmethod
    def _exclude_secrets(data: Any) -> Any:
        """Recursively walks a primitive structure and redacts key secrets."""
        if isinstance(data, dict):
            cleaned = {}
            for k, v in data.items():
                if k == "api_key":
                    cleaned[k] = ""
                elif k == "secrets" and isinstance(v, dict) and "api_key" in v:
                    cleaned[k] = {**v, "api_key": ""}
                else:
                    cleaned[k] = ConfigurationManager._exclude_secrets(v)
            return cleaned
        elif isinstance(data, list):
            return [ConfigurationManager._exclude_secrets(item) for item in data]
        return data

    @staticmethod
    def _calculate_hash(raw_data: Dict[str, Any]) -> str:
        """Computes deterministic SHA-256 hash of the sanitized configuration dict."""
        cleaned = ConfigurationManager._exclude_secrets(raw_data)

        def sort_dict(d: Any) -> Any:
            if isinstance(d, dict):
                return {k: sort_dict(d[k]) for k in sorted(d.keys())}
            if isinstance(d, list):
                return [sort_dict(x) for x in d]
            return d

        sorted_data = sort_dict(cleaned)
        serialized = json.dumps(sorted_data, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    @classmethod
    def bootstrap_configuration(
        cls,
        ordered_source_files: List[Path],
        bootstrap_overrides: Dict[str, Any],
    ) -> ApplicationConfig:
        """Orchestrates configuration instantiation via dependency ingestion rules.

        Args:
            ordered_source_files: List of paths to load TOML configuration sheets from.
            bootstrap_overrides: Ephemeral dictionary of runtime overrides.

        Returns:
            The frozen, validated ApplicationConfig instance.

        Raises:
            ConfigurationFileMissing: If file list is empty or lookups fail.
            SecretMissingError: If credentials or keys are empty.
            ConfigurationValidationError: If schema verification fails.
        """
        if not ordered_source_files:
            raise ConfigurationFileMissing("No configuration source files provided.")

        file_payloads: List[Dict[str, Any]] = []

        # 1. Load and parse TOML files
        for file_path in ordered_source_files:
            raw_bytes = ConfigurationLoader.load_bytes(file_path)
            parsed_dict = ConfigurationParser.parse_toml(raw_bytes)
            file_payloads.append(parsed_dict)

        # 2. Resolve cascade (files -> environment -> overrides)
        env_vars = dict(os.environ)
        merged_data = ConfigurationResolver.resolve_cascade(
            file_payloads, env_vars, bootstrap_overrides
        )

        # 3. Fail fast if secrets are missing or empty strings
        llm_data = merged_data.get("llm")
        if isinstance(llm_data, dict):
            providers = llm_data.get("providers")
            if isinstance(providers, dict):
                for provider_name, provider_conf in providers.items():
                    if isinstance(provider_conf, dict):
                        secrets = provider_conf.get("secrets")
                        if (
                            not secrets
                            or not isinstance(secrets, dict)
                            or "api_key" not in secrets
                        ):
                            raise SecretMissingError(
                                f"Mandatory API key missing for provider "
                                f"'{provider_name}'."
                            )
                        api_key_val = secrets.get("api_key")
                        if api_key_val is None:
                            raise SecretMissingError(
                                f"Mandatory API key missing for provider "
                                f"'{provider_name}'."
                            )
                        # Extract string value if it is already wrapped or just a string
                        val_str = (
                            api_key_val.get_secret_value()
                            if hasattr(api_key_val, "get_secret_value")
                            else str(api_key_val)
                        )
                        if not val_str.strip():
                            raise SecretMissingError(
                                f"API key is empty for provider '{provider_name}'."
                            )

        # 4. Validate schema
        config_instance = ConfigurationValidator.validate_schema(merged_data)

        # 5. Compile summary and calculate hash
        config_hash = cls._calculate_hash(merged_data)
        summary_instance = ConfigurationSummary(
            environment=config_instance.app.env,
            schema_version=config_instance.app.schema_version,
            loaded_files=[str(f) for f in ordered_source_files],
            storage_backend=config_instance.storage.backend,
            providers_loaded=list(config_instance.llm.providers.keys()),
            configuration_hash=config_hash,
            loaded_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        )

        # Cache class properties
        cls.config = config_instance
        cls.summary = summary_instance

        return config_instance
