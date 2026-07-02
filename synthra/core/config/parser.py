"""Decoupled TOML text format parser."""

import tomllib
from typing import Any, Dict
from synthra.core.config.exceptions import ConfigurationValidationError


class ConfigurationParser:
    """Decoupled translation engine converting serialized byte strings to dict

    mappings.
    """

    @staticmethod
    def parse_toml(raw_bytes: bytes) -> Dict[str, Any]:
        """Converts raw byte structures into standard primitive Python

        dictionary objects using tomllib.

        Args:
            raw_bytes: The raw file bytes.

        Returns:
            A primitive Python dictionary of parsed options.

        Raises:
            ConfigurationValidationError: If TOML decoding fails due to syntax error.
        """
        try:
            content_str = raw_bytes.decode("utf-8")
            return tomllib.loads(content_str)
        except (tomllib.TOMLDecodeError, UnicodeDecodeError) as err:
            raise ConfigurationValidationError(
                f"Failed to parse TOML configuration data: {err}"
            ) from err
