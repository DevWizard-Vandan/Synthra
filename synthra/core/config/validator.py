"""Pydantic schema validation wrapper."""

from typing import Any, Dict
from pydantic import ValidationError
from synthra.core.config.exceptions import (
    ConfigurationValidationError,
    UnsupportedConfigurationVersion,
)
from synthra.core.config.models import ApplicationConfig


class ConfigurationValidator:
    """Structural type checking and instantiation pass using Pydantic models."""

    @staticmethod
    def validate_schema(raw_data: Dict[str, Any]) -> ApplicationConfig:
        """Instantiates ApplicationConfig from raw data dictionary.

        Args:
            raw_data: Merged configuration primitive dictionary.

        Returns:
            An instantiated and validated ApplicationConfig model.

        Raises:
            UnsupportedConfigurationVersion: If the app version is missing or
                                             not supported (i.e. != 1).
            ConfigurationValidationError: If validation fails.
        """
        # Validate version first (fail fast on version mismatch)
        app_data = raw_data.get("app")
        if not isinstance(app_data, dict):
            raise ConfigurationValidationError(
                "Missing or invalid 'app' configuration section."
            )

        version = app_data.get("version")
        if version is None:
            raise UnsupportedConfigurationVersion(
                "Top-level config version is missing."
            )

        # Support only version = 1 currently
        if version != 1:
            raise UnsupportedConfigurationVersion(
                f"Unsupported configuration version: {version}. Expected: 1."
            )

        try:
            return ApplicationConfig(**raw_data)
        except ValidationError as err:
            raise ConfigurationValidationError(
                f"Configuration validation failed: {err}"
            ) from err
