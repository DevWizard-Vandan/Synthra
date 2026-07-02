"""Unit test suite for SYNTHRA Configuration Manager (SPEC-0001)."""

import os
import time
import pytest
from pathlib import Path
from pydantic import ValidationError
from synthra.core.config.exceptions import (
    ConfigurationFileMissing,
    ConfigurationValidationError,
    SecretMissingError,
    UnsupportedConfigurationVersion,
)
from synthra.core.config.manager import ConfigurationManager
from synthra.core.config.models import ApplicationConfig


@pytest.fixture(autouse=True)
def clean_env():
    """Ensures a clean environment before each test runs."""
    old_env = dict(os.environ)
    # Remove any SYNTHRA_ prefixed keys
    for key in list(os.environ.keys()):
        if key.startswith("SYNTHRA_"):
            del os.environ[key]
    yield
    # Restore env
    os.environ.clear()
    os.environ.update(old_env)


def write_toml(path: Path, content: str) -> Path:
    """Helper to write configuration text to a file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def get_valid_base_toml() -> str:
    """Returns valid default configuration text."""
    return """
[app]
name = "Synthra"
env = "development"
schema_version = 1

[runtime]
concurrency_pool_size = 4
thread_timeout_seconds = 30.0

[logging]
level = "INFO"
format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

[storage]
backend = "memory"
connection_string = ":memory:"
timeout_ms = 5000
retry_limit = 3

[llm]
[llm.providers.openai]
model = "gpt-4o"
enabled = true
timeout_seconds = 60
secrets = { api_key = "default-key" }

[paths]
data_dir = "data"
output_dir = "output"

[monitoring]
pulse_interval_seconds = 10
metrics_enabled = true
"""


# TC-001: Empty paths array or invalid targets passed to manager loop.
def test_tc001_empty_or_invalid_paths(tmp_path):
    # Empty paths array
    with pytest.raises(ConfigurationFileMissing) as exc_info:
        ConfigurationManager.bootstrap_configuration([], {})
    assert "No configuration source files provided" in str(exc_info.value)

    # Non-existent file
    missing_file = tmp_path / "non_existent.toml"
    with pytest.raises(ConfigurationFileMissing) as exc_info:
        ConfigurationManager.bootstrap_configuration([missing_file], {})
    assert "Configuration file missing or unreachable" in str(exc_info.value)

    # Target path is a directory
    directory_path = tmp_path / "config_dir"
    directory_path.mkdir()
    with pytest.raises(ConfigurationFileMissing) as exc_info:
        ConfigurationManager.bootstrap_configuration([directory_path], {})
    assert "Configuration file missing or unreachable" in str(exc_info.value)


# TC-002: Invalid primitive schema type parameter entry.
def test_tc002_invalid_type_entry(tmp_path):
    base_file = write_toml(tmp_path / "base.toml", get_valid_base_toml())

    # Overriding with invalid type (string for integer) under strict mode
    override_toml = """
[runtime]
concurrency_pool_size = "abc"
"""
    override_file = write_toml(tmp_path / "override.toml", override_toml)

    with pytest.raises(ConfigurationValidationError) as exc_info:
        ConfigurationManager.bootstrap_configuration([base_file, override_file], {})
    assert "concurrency_pool_size" in str(exc_info.value)


# TC-003: Injection of unmapped tracking parameters outside schema constraints.
def test_tc003_extra_unmapped_parameters(tmp_path):
    base_file = write_toml(tmp_path / "base.toml", get_valid_base_toml())

    # Override adding an unmapped parameter (extra="forbid")
    override_toml = """
[runtime]
unmapped_parameter = 100
"""
    override_file = write_toml(tmp_path / "override.toml", override_toml)

    with pytest.raises(ConfigurationValidationError) as exc_info:
        ConfigurationManager.bootstrap_configuration([base_file, override_file], {})
    assert "Extra inputs are not permitted" in str(exc_info.value)


# TC-004: Target mapping missing mandatory environment variables (api_key).
def test_tc004_missing_or_empty_secrets(tmp_path):
    # Base configuration with empty key placeholder
    base_toml = """
[app]
env = "development"
schema_version = 1

[runtime]
concurrency_pool_size = 4
thread_timeout_seconds = 30.0

[logging]
level = "INFO"

[storage]
backend = "memory"
connection_string = ":memory:"

[llm]
[llm.providers.openai]
model = "gpt-4o"
secrets = { api_key = "" }

[paths]
data_dir = "data"
output_dir = "output"

[monitoring]
pulse_interval_seconds = 10
metrics_enabled = true
"""
    base_file = write_toml(tmp_path / "base.toml", base_toml)

    # 1. Bootstrapping with empty key should raise SecretMissingError
    with pytest.raises(SecretMissingError) as exc_info:
        ConfigurationManager.bootstrap_configuration([base_file], {})
    assert "API key is empty" in str(exc_info.value)

    # 2. Bootstrapping with missing secrets block should raise SecretMissingError
    no_secret_toml = base_toml.replace('secrets = { api_key = "" }', "")
    no_secret_file = write_toml(tmp_path / "no_secret.toml", no_secret_toml)
    with pytest.raises(SecretMissingError) as exc_info:
        ConfigurationManager.bootstrap_configuration([no_secret_file], {})
    assert "API key missing" in str(exc_info.value)

    # 3. Supplying environment variable should resolve the missing secret
    os.environ["SYNTHRA_LLM_PROVIDERS_OPENAI_SECRETS_API_KEY"] = "sk-proj-testkey"
    config = ConfigurationManager.bootstrap_configuration([base_file], {})
    assert (
        config.llm.providers["openai"].secrets.api_key.get_secret_value()
        == "sk-proj-testkey"
    )


# TC-005: Top-level schema version parameter is incremented out of bounds.
def test_tc005_unsupported_version(tmp_path):
    base_toml = get_valid_base_toml()
    # Replace version with 99
    invalid_version_toml = base_toml.replace(
        "schema_version = 1", "schema_version = 99"
    )
    base_file = write_toml(tmp_path / "base.toml", invalid_version_toml)

    with pytest.raises(UnsupportedConfigurationVersion) as exc_info:
        ConfigurationManager.bootstrap_configuration([base_file], {})
    assert "Unsupported configuration version: 99" in str(exc_info.value)


# TC-006: Flawless structural inputs and configuration files sheet.
def test_tc006_flawless_bootstrap(tmp_path):
    base_file = write_toml(tmp_path / "base.toml", get_valid_base_toml())

    # Run bootstrap
    config = ConfigurationManager.bootstrap_configuration([base_file], {})

    # Assert type
    assert isinstance(config, ApplicationConfig)
    assert config.app.name == "Synthra"
    assert config.app.env == "development"
    assert config.runtime.concurrency_pool_size == 4

    # Assert summary is generated
    assert ConfigurationManager.summary is not None
    summary = ConfigurationManager.summary
    assert summary.environment == "development"
    assert summary.schema_version == 1
    assert "base.toml" in summary.loaded_files[0]
    assert summary.storage_backend == "memory"
    assert "openai" in summary.providers_loaded
    assert len(summary.configuration_hash) == 64  # SHA-256 hash length


# TC-007: Post-instantiation code write mutation request execution.
def test_tc007_immutability(tmp_path):
    base_file = write_toml(tmp_path / "base.toml", get_valid_base_toml())
    config = ConfigurationManager.bootstrap_configuration([base_file], {})

    # Assert model config frozen prevents mutations
    with pytest.raises(ValidationError):
        config.runtime.concurrency_pool_size = 10


# TC-008: Serialization lookup verification pass.
def test_tc008_serialization_masking(tmp_path):
    base_file = write_toml(tmp_path / "base.toml", get_valid_base_toml())
    config = ConfigurationManager.bootstrap_configuration([base_file], {})

    # Serialize
    json_str = config.model_dump_json()

    # Assert secret is masked
    assert "default-key" not in json_str
    assert "**********" in json_str


# TC-009: Malformed TOML syntax verification.
def test_tc009_malformed_toml(tmp_path):
    base_file = write_toml(tmp_path / "base.toml", "[app\nname = ")
    with pytest.raises(ConfigurationValidationError) as exc_info:
        ConfigurationManager.bootstrap_configuration([base_file], {})
    assert "Failed to parse TOML" in str(exc_info.value)


# TC-010: Environment override precedence over TOML values.
def test_tc010_env_precedence(tmp_path):
    base_file = write_toml(tmp_path / "base.toml", get_valid_base_toml())

    # Set override env variables
    os.environ["SYNTHRA_RUNTIME_CONCURRENCY_POOL_SIZE"] = "16"
    os.environ["SYNTHRA_APP_ENV"] = "production"

    config = ConfigurationManager.bootstrap_configuration([base_file], {})
    assert config.runtime.concurrency_pool_size == 16
    assert config.app.env == "production"


# TC-011: Verify Loaded At timestamp presence and properties.
def test_tc011_loaded_at_timestamp(tmp_path):
    base_file = write_toml(tmp_path / "base.toml", get_valid_base_toml())

    # Bootstrap first time
    ConfigurationManager.bootstrap_configuration([base_file], {})
    summary1 = ConfigurationManager.summary
    assert summary1 is not None
    assert summary1.loaded_at.endswith("Z")

    # Small delay
    time.sleep(1.0)

    # Bootstrap second time
    ConfigurationManager.bootstrap_configuration([base_file], {})
    summary2 = ConfigurationManager.summary
    assert summary2 is not None

    # Verify loaded_at changed but configuration_hash remained identical
    assert summary1.loaded_at != summary2.loaded_at
    assert summary1.configuration_hash == summary2.configuration_hash
