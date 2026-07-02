"""Service state container holding initialized subsystems."""

import logging
from pathlib import Path
from typing import Optional

from synthra.core.catalog import DatasetCatalog
from synthra.memory import CampaignRepository, DatabaseManager

logger = logging.getLogger(__name__)

_DEFAULT_DB_PATH = "data/synthra.db"


class ServiceState:
    """Singleton holding initialized subsystem references."""

    _instance: Optional["ServiceState"] = None

    def __init__(self) -> None:
        self._db_manager: Optional[DatabaseManager] = None
        self._catalog: Optional[DatasetCatalog] = None
        self._campaign_repo: Optional[CampaignRepository] = None
        self._ready: bool = False

    @classmethod
    def get_instance(cls) -> "ServiceState":
        """Return the singleton ServiceState instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def initialize(self) -> None:
        """Initialize all subsystems in dependency order."""
        logger.info("Initializing SQLite memory layer")
        self._db_manager = DatabaseManager(_DEFAULT_DB_PATH)

        logger.info("Initializing Dataset Catalog")
        catalog_path = Path("config/catalog.toml")
        self._catalog = DatasetCatalog(toml_path=catalog_path)

        logger.info("Initializing repositories")
        self._ready = True
        logger.info("All subsystems initialized")

    async def shutdown(self) -> None:
        """Graceful shutdown of subsystems."""
        self._ready = False
        logger.info("ServiceState shutdown complete")

    @property
    def db_manager(self) -> DatabaseManager:
        """Return the initialized DatabaseManager."""
        if self._db_manager is None:
            raise RuntimeError("DatabaseManager not initialized")
        return self._db_manager

    @property
    def catalog(self) -> DatasetCatalog:
        """Return the initialized DatasetCatalog."""
        if self._catalog is None:
            raise RuntimeError("DatasetCatalog not initialized")
        return self._catalog

    @property
    def is_ready(self) -> bool:
        """Return True when all subsystems are initialized."""
        return self._ready

    def campaign_count(self) -> int:
        """Return the current number of campaigns stored in the database."""
        if self._db_manager is None:
            return 0
        try:
            with self._db_manager.connection() as conn:
                row = conn.execute("SELECT COUNT(*) FROM campaigns").fetchone()
                return int(row[0]) if row else 0
        except Exception:
            return 0

    def simulations_executed(self) -> int:
        """Return the current number of experiments in the database."""
        if self._db_manager is None:
            return 0
        try:
            with self._db_manager.connection() as conn:
                row = conn.execute("SELECT COUNT(*) FROM experiments").fetchone()
                return int(row[0]) if row else 0
        except Exception:
            return 0
