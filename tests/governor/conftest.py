"""Fixtures for testing the SYNTHRA Governor & Campaign Scheduler."""

import sqlite3
from pathlib import Path
from typing import Generator
import pytest

from synthra.core.catalog import DatasetCatalog
from synthra.memory import (
    AlphaCandidateRepository,
    CampaignRepository,
    DatabaseManager,
    ExperimentRepository,
    HypothesisRepository,
)


@pytest.fixture
def db_manager(tmp_path: Path) -> DatabaseManager:
    """Provide a DatabaseManager configured with transient file SQLite storage."""
    db_file = tmp_path / "test_governor.db"
    return DatabaseManager(str(db_file))


@pytest.fixture
def db_conn(db_manager: DatabaseManager) -> Generator[sqlite3.Connection, None, None]:
    """Provide a sqlite3 Connection that stays open during the test."""
    with db_manager.connection() as conn:
        yield conn


@pytest.fixture
def catalog() -> DatasetCatalog:
    """Provide a loaded DatasetCatalog instance."""
    toml_path = Path(__file__).parents[2] / "config" / "catalog.toml"
    return DatasetCatalog(toml_path=toml_path)


@pytest.fixture
def campaign_repo(db_conn: sqlite3.Connection) -> CampaignRepository:
    """Provide a CampaignRepository instance."""
    return CampaignRepository(db_conn)


@pytest.fixture
def hypothesis_repo(db_conn: sqlite3.Connection) -> HypothesisRepository:
    """Provide a HypothesisRepository instance."""
    return HypothesisRepository(db_conn)


@pytest.fixture
def experiment_repo(db_conn: sqlite3.Connection) -> ExperimentRepository:
    """Provide an ExperimentRepository instance."""
    return ExperimentRepository(db_conn)


@pytest.fixture
def candidate_repo(db_conn: sqlite3.Connection) -> AlphaCandidateRepository:
    """Provide an AlphaCandidateRepository instance."""
    return AlphaCandidateRepository(db_conn)
