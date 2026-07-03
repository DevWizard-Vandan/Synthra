"""Autonomous Researcher agent and intelligence loop controller."""

import logging
from typing import Any, List, Tuple

from synthra.core.catalog import DatasetCatalog
from synthra.core.domain import Hypothesis, HypothesisStatus, SimulationResult
from synthra.memory import CampaignRepository, DatabaseManager
from synthra.research.intelligence.knowledge import KnowledgeBase
from synthra.research.intelligence.ranking import HypothesisRanker
from synthra.research.intelligence.reasoning import ReasoningEngine
from synthra.research.loop import LoopController

logger = logging.getLogger(__name__)


class IntelligenceResearcher:
    """Quantitative researcher agent producing hypotheses using reasoning paths."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        catalog: DatasetCatalog,
    ) -> None:
        """Initialize the researcher with required sub-engines."""
        self.db_manager = db_manager
        self.catalog = catalog
        self.knowledge_base = KnowledgeBase(db_manager)
        self.reasoning_engine = ReasoningEngine(catalog)
        self.ranker = HypothesisRanker(catalog)

    def generate_hypothesis(self, campaign_id: str, hypothesis_id: str) -> Hypothesis:
        """Formulate a quantitative hypothesis from prioritized reasoning paths."""
        with self.db_manager.connection() as conn:
            campaign = CampaignRepository(conn).get_by_id(campaign_id)
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")

        # 1. Formulate reasoning paths
        paths = self.reasoning_engine.formulate_reasoning_paths(
            campaign, self.knowledge_base
        )
        if not paths:
            raise ValueError(
                f"No valid reasoning paths found for campaign {campaign_id}"
            )

        # Fetch existing expressions for novelty check
        existing_exprs: List[str] = []
        with self.db_manager.connection() as conn:
            rows = conn.execute("SELECT expression FROM experiments").fetchall()
            existing_exprs = [r["expression"] for r in rows]

        # 2. Rank hypotheses
        ranked = self.ranker.rank_paths(
            paths, campaign, self.knowledge_base, existing_expressions=existing_exprs
        )
        top_path, score = ranked[0]

        # Prefix rationale with the concept name for feedback tracking
        rationale = f"[Concept: {top_path.concept}] {top_path.thesis}"

        return Hypothesis(
            id=hypothesis_id,
            campaign_id=campaign_id,
            rationale=rationale,
            target_variable="returns",
            datasets=[top_path.required_dataset],
            operators=top_path.suitable_operators,
            status=HypothesisStatus.DRAFT,
        )

    def learn_from_result(
        self, hypothesis: Hypothesis, region: str, universe: str, success: bool
    ) -> None:
        """Process simulation feedback to update knowledge base confidence."""
        if hypothesis.rationale.startswith("[Concept:"):
            try:
                concept = (
                    hypothesis.rationale.split("]")[0].split("[Concept:")[1].strip()
                )
                self.knowledge_base.record_feedback(concept, region, universe, success)
                logger.info(
                    "Updated knowledge confidence for concept %s (%s, %s): success=%s",
                    concept,
                    region,
                    universe,
                    success,
                )
            except Exception as e:
                logger.error("Failed to parse concept name from rationale: %s", e)


class IntelligenceLoopController(LoopController):
    """LoopController integrating the IntelligenceResearcher and learning feedback."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        catalog: DatasetCatalog,
        hypothesis_generator: IntelligenceResearcher,
        planner: Any,
        synthesizer: Any,
        executor: Any,
        learning_repository: Any = None,
        feedback_generator: Any = None,
    ) -> None:
        """Initialize the intelligence loop controller."""
        super().__init__(
            db_manager=db_manager,
            catalog=catalog,
            hypothesis_generator=hypothesis_generator,  # type: ignore
            planner=planner,
            synthesizer=synthesizer,
            executor=executor,
            learning_repository=learning_repository,
            feedback_generator=feedback_generator,
        )
        self.intel_researcher = hypothesis_generator

    def run_loop(
        self, campaign_id: str, generations: int = 3
    ) -> List[Tuple[str, SimulationResult, float]]:
        """Run loop and apply reinforcement feedback to concepts."""
        ranked = super().run_loop(campaign_id, generations)

        # Retrieve executed experiments to apply reinforcement learning feedback
        with self.db_manager.connection() as conn:
            rows = conn.execute(
                """
                SELECT e.expression, e.result, h.rationale, c.region, c.universe
                FROM experiments e
                JOIN hypotheses h ON e.hypothesis_id = h.id
                JOIN campaigns c ON e.campaign_id = c.id
                WHERE e.campaign_id = ? AND e.status = 'completed';
                """,
                (campaign_id,),
            ).fetchall()

            for row in rows:
                result = SimulationResult.model_validate_json(row["result"])
                success = result.sharpe >= 1.0

                mock_hyp = Hypothesis(
                    id="HYP-0000",
                    campaign_id=campaign_id,
                    rationale=row["rationale"],
                    target_variable="returns",
                    datasets=["pv"],
                    operators=["ts_mean"],
                    status=HypothesisStatus.DRAFT,
                )
                self.intel_researcher.learn_from_result(
                    mock_hyp, row["region"], row["universe"], success
                )

        return ranked
