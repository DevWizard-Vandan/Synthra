"""Module specific exception tree for SYNTHRA Configuration Manager."""


class ConfigurationError(Exception):
    """Base exception for all system configuration structural errors."""

    pass


class ConfigurationFileMissing(ConfigurationError):
    """Raised if raw configuration resource lookups fail on disk."""

    pass


class ConfigurationValidationError(ConfigurationError):
    """Raised when Pydantic parsing verification metrics break."""

    pass


class ConfigurationVersionMismatch(ConfigurationError):
    """Base category for configuration schema version errors.

    Note: The Configuration Manager does NOT perform data translation; schema migrations
    MUST be managed by a separate, dedicated external orchestrator or migration script.
    """

    pass


class UnsupportedConfigurationVersion(ConfigurationVersionMismatch):
    """Raised if the top-level schema version integer is completely unrecognized."""

    pass


class ConfigurationMigrationRequired(ConfigurationVersionMismatch):
    """Raised if schema values require upstream legacy conversion prior to loading."""

    pass


class SecretMissingError(ConfigurationError):
    """Raised when required env keys or secret tokens evaluate to empty strings."""

    pass
