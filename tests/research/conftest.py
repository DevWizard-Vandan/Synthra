"""Shared fixtures for testing the SYNTHRA Research Engine."""

from pathlib import Path
import pytest

from synthra.core.catalog import DatasetCatalog
from synthra.research.hypothesis import MockLLMProvider
from synthra.research.validator import Validator


@pytest.fixture
def catalog() -> DatasetCatalog:
    """Provide a loaded DatasetCatalog instance."""
    # Resolve catalog.toml relative to workspace root
    toml_path = Path(__file__).parents[2] / "config" / "catalog.toml"
    return DatasetCatalog(toml_path=toml_path)


@pytest.fixture
def validator(catalog: DatasetCatalog) -> Validator:
    """Provide a Validator instance."""
    return Validator(catalog=catalog)


@pytest.fixture
def mock_llm() -> MockLLMProvider:
    """Provide a MockLLMProvider instance."""
    return MockLLMProvider()
