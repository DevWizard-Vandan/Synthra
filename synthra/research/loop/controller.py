"""Controller modules for the autonomous research loop."""

import logging
from typing import List, Optional, Tuple

from synthra.core.catalog import DatasetCatalog
from synthra.core.domain import SimulationResult
from synthra.learning import FeedbackGenerator, LearningRepository
from synthra.memory import CampaignRepository, DatabaseManager
from synthra.research.loop.evaluator import LoopEvaluator
from synthra.research.loop.executor import LoopExecutor
from synthra.research.loop.generator import (
    ExpressionSynthesizer,
    LoopHypothesisGenerator,
)
from synthra.research.loop.planner import LoopPlanner

logger = logging.getLogger(__name__)


def _get_next_hypothesis_id(db_manager: DatabaseManager) -> str:
    """Generate the next available hypothesis ID following 'HYP-XXXX'."""
    with db_manager.connection() as conn:
        row = conn.execute(
            "SELECT id FROM hypotheses ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if row and row[0]:
            try:
                num = int(row[0].split("-")[1])
                return f"HYP-{num + 1:04d}"
            except Exception:
                pass
        return "HYP-0001"


def _get_next_experiment_id(db_manager: DatabaseManager) -> str:
    """Generate the next available experiment ID following 'EXP-XXXX'."""
    with db_manager.connection() as conn:
        row = conn.execute(
            "SELECT id FROM experiments ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if row and row[0]:
            try:
                num = int(row[0].split("-")[1])
                return f"EXP-{num + 1:04d}"
            except Exception:
                pass
        return "EXP-0001"


class LoopController:
    """Coordinates the entire autonomous research loop execution."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        catalog: DatasetCatalog,
        hypothesis_generator: LoopHypothesisGenerator,
        planner: LoopPlanner,
        synthesizer: ExpressionSynthesizer,
        executor: LoopExecutor,
        learning_repository: Optional[LearningRepository] = None,
        feedback_generator: Optional[FeedbackGenerator] = None,
    ) -> None:
        """Initialize the controller with required pipeline components."""
        self.db_manager = db_manager
        self.catalog = catalog
        self.hypothesis_generator = hypothesis_generator
        self.planner = planner
        self.synthesizer = synthesizer
        self.executor = executor
        self.learning_repo = learning_repository or LearningRepository(db_manager)
        self.feedback_gen = feedback_generator or FeedbackGenerator()

    def run_loop(
        self, campaign_id: str, generations: int = 3
    ) -> List[Tuple[str, SimulationResult, float]]:
        """Run the complete end-to-end autonomous research loop for N generations."""
        with self.db_manager.connection() as conn:
            campaign = CampaignRepository(conn).get_by_id(campaign_id)
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")

        simulated_candidates: List[Tuple[str, SimulationResult]] = []

        for gen in range(generations):
            logger.info("Starting generation %d for campaign %s", gen, campaign_id)

            # 1. Generate Hypothesis
            hyp_id = _get_next_hypothesis_id(self.db_manager)
            hypothesis = self.hypothesis_generator.generate_hypothesis(
                campaign_id, hyp_id
            )
            self.executor.history_tracker.record_hypothesis(hypothesis)

            # 2. Plan Task
            task_id = f"TSK-{campaign_id.split('-')[1]}-{gen + 1:02d}"
            task = self.planner.plan_hypothesis(hypothesis, task_id)
            # The research loop controller converts hypotheses to structured plans/tasks
            logger.info("Created task %s: %s", task.id, task.objective)

            # 3. Synthesize Expressions
            requests = self.synthesizer.synthesize_candidates(
                hypothesis, campaign.region, campaign.universe
            )

            # 4. Execute Simulations
            gen_results = []
            for req in requests:
                exp_id = _get_next_experiment_id(self.db_manager)
                result, error = self.executor.execute_simulation(
                    req, campaign_id, hyp_id, exp_id
                )
                if result:
                    gen_results.append((req, result))
                    simulated_candidates.append((req.expression, result))

                    # 5. Evolution Feedback: generate and store learning record
                    record = self.feedback_gen.generate_record(
                        req, result, hypothesis.datasets, hypothesis.operators
                    )
                    self.learning_repo.add_record(record)

            # 6. Mutate Candidates
            if gen_results:
                mutated_requests = self.synthesizer.mutate_candidates(
                    [r[0] for r in gen_results],
                    gen_results,
                    hypothesis.datasets[0],
                )

                # 7. Execute Mutation Simulations
                for mut_req in mutated_requests:
                    exp_id = _get_next_experiment_id(self.db_manager)
                    result, error = self.executor.execute_simulation(
                        mut_req, campaign_id, hyp_id, exp_id
                    )
                    if result:
                        simulated_candidates.append((mut_req.expression, result))

                        # Evolution Feedback for mutations
                        record = self.feedback_gen.generate_record(
                            mut_req,
                            result,
                            hypothesis.datasets,
                            hypothesis.operators,
                        )
                        self.learning_repo.add_record(record)

        # 8. Evaluate and Rank Candidates
        existing_exprs = [c[0] for c in simulated_candidates]
        evaluator = LoopEvaluator(existing_expressions=existing_exprs)
        ranked = evaluator.rank_candidates(simulated_candidates)

        return ranked
