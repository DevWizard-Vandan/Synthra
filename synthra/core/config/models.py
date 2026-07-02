"""Strongly typed Pydantic configuration models for SYNTHRA."""

from pathlib import Path
from pydantic import BaseModel, ConfigDict, Field, SecretStr
from typing import Dict, List, Literal, Optional

# Type Aliases for validation domains
EnvironmentName = Literal["development", "production", "local"]
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
StorageBackend = Literal["sqlite", "postgresql", "memory"]
ProviderRegistry = Dict[str, "LLMProviderConfig"]


class BaseConfigModel(BaseModel):
    """Base model enforcing post-validation immutability and strict schemas."""

    model_config = ConfigDict(
        frozen=True,  # Enforces absolute post-validation immutability
        extra="forbid",  # Fails validation instantly if unknown keys are passed
        strict=True,  # Disallows unsafe implicit type-coercion loops
        arbitrary_types_allowed=True,  # Allows native pathlib.Path type mappings
    )


class ApplicationSubConfig(BaseConfigModel):
    """General application attributes and version info."""

    name: str = Field(default="Synthra")
    env: EnvironmentName
    schema_version: int = Field(default=1)


class RuntimeConfig(BaseConfigModel):
    """Concurrency settings and thread controls."""

    concurrency_pool_size: int = Field(gt=0, le=64)
    thread_timeout_seconds: float = Field(default=30.0, gt=0.0)


class LoggingConfig(BaseConfigModel):
    """Telemetry logging levels and format layouts."""

    level: LogLevel
    format: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


class StorageConfig(BaseConfigModel):
    """Persistence parameters for local state caching."""

    backend: StorageBackend
    connection_string: str
    timeout_ms: int = Field(default=5000, ge=0)
    retry_limit: int = Field(default=3, ge=0)


class LLMProviderSecrets(BaseConfigModel):
    """Encapsulates sensitive provider authorization tokens."""

    api_key: SecretStr  # Wrapped to mask token printing in logs


class LLMProviderConfig(BaseConfigModel):
    """Configuration schema for a single LLM connection client."""

    model: str
    enabled: bool = Field(default=True)
    timeout_seconds: int = Field(default=120, gt=0)
    max_tokens: Optional[int] = Field(default=None, gt=0)
    api_base: Optional[str] = Field(default=None)
    secrets: LLMProviderSecrets


class LLMConfig(BaseConfigModel):
    """Dynamic mapping configuration for multi-provider support."""

    providers: ProviderRegistry


class PathConfig(BaseConfigModel):
    """Filesystem boundary controls."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=False,  # Allow coercion from string to Path
        arbitrary_types_allowed=True,
    )
    data_dir: Path
    output_dir: Path


class MonitoringConfig(BaseConfigModel):
    """Operational health monitoring triggers."""

    pulse_interval_seconds: int = Field(default=10, gt=0)
    metrics_enabled: bool = Field(default=True)


class ApplicationConfig(BaseConfigModel):
    """Top-level frozen configuration root injected into system components."""

    app: ApplicationSubConfig
    runtime: RuntimeConfig
    logging: LoggingConfig
    storage: StorageConfig
    llm: LLMConfig
    paths: PathConfig
    monitoring: MonitoringConfig


class ConfigurationSummary(BaseConfigModel):
    """Clean representation of system settings summary metadata."""

    environment: EnvironmentName
    schema_version: int
    loaded_files: List[str]
    storage_backend: StorageBackend
    providers_loaded: List[str]
    configuration_hash: str
    loaded_at: str  # ISO 8601 UTC timestamp of bootstrap trigger
