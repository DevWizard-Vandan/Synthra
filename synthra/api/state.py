"""Service state container holding initialized subsystems and running Governor."""

import logging
from pathlib import Path
from typing import Optional

from synthra.core.catalog import DatasetCatalog
from synthra.memory import DatabaseManager
from synthra.governor import Governor
from synthra.research.planner import Planner
from synthra.research.hypothesis import HypothesisGenerator
from synthra.research.generator import ExpressionGenerator
from synthra.research.validator import Validator
from synthra.research.mutator import MutationEngine
from synthra.research.evolution.lineage import LineageTracker
from synthra.research.evolution.selection import SelectionEngine
from synthra.research.ranking import CandidateRanker
from synthra.execution.runner import SimulationRunner
from synthra.learning.feedback import FeedbackGenerator
from synthra.learning.repository import LearningRepository
from synthra.learning.history import HistoryTracker
from synthra.learning.scorer import ExpressionScorer
from synthra.research.orchestrator import ResearchOrchestrator

logger = logging.getLogger(__name__)

_DEFAULT_DB_PATH = "data/synthra.db"


class ServiceState:
    """Singleton holding initialized subsystem references and background runner."""

    _instance: Optional["ServiceState"] = None

    def __init__(self) -> None:
        self._db_manager: Optional[DatabaseManager] = None
        self._catalog: Optional[DatasetCatalog] = None
        self._orchestrator: Optional[ResearchOrchestrator] = None
        self._governor: Optional[Governor] = None
        self._ready: bool = False

    @classmethod
    def get_instance(cls) -> "ServiceState":
        """Return the singleton ServiceState instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def initialize(self) -> None:
        """Initialize all subsystems in dependency order and start Governor."""
        logger.info("Initializing SQLite memory layer")
        self._db_manager = DatabaseManager(_DEFAULT_DB_PATH)

        logger.info("Initializing Dataset Catalog")
        catalog_path = Path("config/catalog.toml")
        self._catalog = DatasetCatalog(toml_path=catalog_path)

        logger.info("Initializing Research Pipeline subsystems")
        # Load LLM provider
        from synthra.research.hypothesis import ILLMProvider
        llm_bridge: ILLMProvider
        try:
            from synthra.llm import ProviderManager, StructuredLLMBridge

            llm_manager = ProviderManager()
            prov = llm_manager.get_default_provider()
            llm_bridge = StructuredLLMBridge(prov)
        except Exception:
            from synthra.research.hypothesis import MockLLMProvider

            llm_bridge = MockLLMProvider()

        planner = Planner(self._catalog)
        hypothesis_gen = HypothesisGenerator(llm_bridge)
        validator = Validator(self._catalog)
        expression_gen = ExpressionGenerator(llm_bridge, self._catalog, validator)

        # Lineage
        lineage_tracker = LineageTracker(self._db_manager)
        mutation_eng = MutationEngine(self._catalog, lineage_tracker=lineage_tracker)

        import os
        from pydantic import SecretStr
        from synthra.execution.client import WorldQuantExecutionClient
        from synthra.execution.models import WorldQuantCredentials

        wq_user = os.environ.get("WQ_USERNAME") or os.environ.get("BRAIN_USERNAME") or "mock"
        wq_pass = os.environ.get("WQ_PASSWORD") or os.environ.get("BRAIN_PASSWORD") or "mock"

        client = WorldQuantExecutionClient(
            credentials=WorldQuantCredentials(
                username=wq_user,
                password=SecretStr(wq_pass)
            )
        )
        simulation_run = SimulationRunner(client)
        ranker = CandidateRanker()

        feedback_gen = FeedbackGenerator()
        learning_repo = LearningRepository(self._db_manager)
        history_track = HistoryTracker(self._db_manager)
        scorer = ExpressionScorer(history=[])
        selection_eng = SelectionEngine()

        self._orchestrator = ResearchOrchestrator(
            planner=planner,
            hypothesis_generator=hypothesis_gen,
            expression_generator=expression_gen,
            validator=validator,
            mutation_engine=mutation_eng,
            simulation_runner=simulation_run,
            ranker=ranker,
            feedback_generator=feedback_gen,
            learning_repository=learning_repo,
            history_tracker=history_track,
            scorer=scorer,
            db_manager=self._db_manager,
            selection_engine=selection_eng,
        )

        logger.info("Initializing Governor service")
        self._governor = Governor(
            orchestrator=self._orchestrator,
            db_manager=self._db_manager,
            num_workers=2,
        )
        self._governor.start()

        self._ready = True
        logger.info("All subsystems initialized and Governor running")

    async def shutdown(self) -> None:
        """Graceful shutdown of subsystems."""
        self._ready = False
        if self._governor:
            logger.info("Stopping Governor service")
            self._governor.stop()
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
    def orchestrator(self) -> ResearchOrchestrator:
        """Return the initialized ResearchOrchestrator."""
        if self._orchestrator is None:
            raise RuntimeError("ResearchOrchestrator not initialized")
        return self._orchestrator

    @property
    def governor(self) -> Governor:
        """Return the running Governor instance."""
        if self._governor is None:
            raise RuntimeError("Governor not initialized")
        return self._governor

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
