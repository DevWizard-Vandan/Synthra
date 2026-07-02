"""Orchestrator subsystem executing the complete autonomous research loop."""

import logging
from datetime import datetime
from typing import List, Optional

from synthra.core.domain import (
    AlphaCandidate,
    Campaign,
    Experiment,
    ExperimentStatus,
    Hypothesis,
)
from synthra.execution.runner import SimulationRunner
from synthra.learning.feedback import FeedbackGenerator, LearningRecord
from synthra.learning.history import HistoryTracker
from synthra.learning.repository import LearningRepository
from synthra.learning.scorer import ExpressionScorer
from synthra.learning.selector import HypothesisSelector
from synthra.research.generator import ExpressionGenerator
from synthra.research.hypothesis import HypothesisGenerator
from synthra.research.mutator import MutationEngine
from synthra.research.planner import Planner
from synthra.research.ranking import CandidateRanker
from synthra.research.validator import Validator

logger = logging.getLogger(__name__)


class ResearchOrchestrator:
    """Orchestrator executing the complete autonomous alpha generation loop."""

    def __init__(
        self,
        planner: Planner,
        hypothesis_generator: HypothesisGenerator,
        expression_generator: ExpressionGenerator,
        validator: Validator,
        mutation_engine: MutationEngine,
        simulation_runner: SimulationRunner,
        ranker: CandidateRanker,
        feedback_generator: Optional[FeedbackGenerator] = None,
        learning_repository: Optional[LearningRepository] = None,
        history_tracker: Optional[HistoryTracker] = None,
        selector: Optional[HypothesisSelector] = None,
        scorer: Optional[ExpressionScorer] = None,
    ) -> None:
        """Initialize orchestrator with all pipeline and learning subsystems."""
        self.planner = planner
        self.hypothesis_generator = hypothesis_generator
        self.expression_generator = expression_generator
        self.validator = validator
        self.mutation_engine = mutation_engine
        self.simulation_runner = simulation_runner
        self.ranker = ranker

        # Learning Engine dependencies
        self.feedback_generator = feedback_generator
        self.learning_repository = learning_repository
        self.history_tracker = history_tracker
        self.selector = selector or HypothesisSelector()
        self.scorer = scorer

    def execute_campaign(
        self, campaign: Campaign, max_hypotheses_per_task: int = 1
    ) -> List[AlphaCandidate]:
        """Run the complete research loop for a Campaign.

        Planner -> Hypothesis -> Expressions -> Validation -> Simulation ->
        Mutation -> Simulation -> Learning Feedback -> Ranking -> Candidate List.
        """
        logger.info("Starting execution for campaign %s", campaign.id)

        # Record campaign in history
        if self.history_tracker:
            self.history_tracker.record_campaign(campaign)

        # 1. Decompose campaign into tasks
        tasks = self.planner.plan_campaign(campaign)
        logger.info("Decomposed campaign into %d tasks", len(tasks))

        hypotheses: List[Hypothesis] = []
        all_candidates: List[AlphaCandidate] = []

        hyp_counter = 1
        exp_counter = 1
        cand_counter = 1

        for task in tasks:
            # 2. Generate structured hypotheses
            for _ in range(max_hypotheses_per_task):
                hyp_id = f"HYP-{hyp_counter:04d}"
                structured_hyp = self.hypothesis_generator.generate_hypothesis(task)
                hyp = self.hypothesis_generator.to_domain(
                    structured_hyp, campaign.id, hyp_id
                )
                hypotheses.append(hyp)
                hyp_counter += 1

                # Record hypothesis in history
                if self.history_tracker:
                    self.history_tracker.record_hypothesis(hyp)

                hypothesis_records: List[LearningRecord] = []

                # 3. Generate candidate expressions for each assigned dataset
                for dataset_name in hyp.datasets:
                    requests = (
                        self.expression_generator.generate_expressions_for_dataset(
                            hyp,
                            dataset_name,
                            region=campaign.region,
                            universe=campaign.universe,
                        )
                    )

                    # 4. Simulate and optimize (Mutate)
                    for req in requests:
                        try:
                            # Base Simulation Run
                            logger.info(
                                "Simulating base expression: %s", req.expression
                            )

                            # Record pending base experiment
                            exp_id = f"EXP-{exp_counter:04d}"
                            exp_counter += 1
                            base_exp = Experiment(
                                id=exp_id,
                                campaign_id=campaign.id,
                                hypothesis_id=hyp.id,
                                expression=req.expression,
                                request=req,
                                status=ExperimentStatus.PENDING,
                                created_at=datetime.utcnow(),
                            )
                            if self.history_tracker:
                                self.history_tracker.record_experiment(base_exp)

                            result = self.simulation_runner.run(req)

                            # Update base experiment to completed
                            completed_base_exp = base_exp.model_copy(
                                update={
                                    "status": ExperimentStatus.COMPLETED,
                                    "result": result,
                                    "finished_at": datetime.utcnow(),
                                }
                            )
                            if self.history_tracker:
                                self.history_tracker.record_experiment(
                                    completed_base_exp
                                )

                            # Save learning record feedback
                            if self.feedback_generator and self.learning_repository:
                                rec = self.feedback_generator.generate_record(
                                    req,
                                    result,
                                    datasets=[dataset_name],
                                    operators=hyp.operators,
                                )
                                self.learning_repository.add_record(rec)
                                hypothesis_records.append(rec)

                            cand_id = f"AST-{cand_counter:04d}"
                            candidate = AlphaCandidate(
                                id=cand_id,
                                experiment_id=exp_id,
                                hypothesis_id=hyp.id,
                                campaign_id=campaign.id,
                                expression=req.expression,
                                result=result,
                                is_submitted=False,
                            )
                            all_candidates.append(candidate)
                            cand_counter += 1

                            # 5. Evaluate if we should proceed with mutations
                            decision = self.selector.evaluate_hypothesis(
                                hypothesis_records
                            )
                            if decision == "retire":
                                logger.info(
                                    "Hypothesis %s retired early based on performance.",
                                    hyp.id,
                                )
                                continue

                            # Mutate to generate improved variants
                            mutated_reqs = self.mutation_engine.mutate_request(
                                req, result, dataset_name
                            )

                            # Limit mutation count based on evaluation decision
                            mutation_limit = 2 if decision == "mutate" else 1

                            for mut_req in mutated_reqs[:mutation_limit]:
                                # Validate mutated request
                                if self.validator.validate_request(
                                    mut_req, dataset_name
                                ):
                                    try:
                                        logger.info(
                                            "Simulating mutated expression: %s",
                                            mut_req.expression,
                                        )

                                        # Record pending mutated experiment
                                        mut_exp_id = f"EXP-{exp_counter:04d}"
                                        exp_counter += 1
                                        mut_exp = Experiment(
                                            id=mut_exp_id,
                                            campaign_id=campaign.id,
                                            hypothesis_id=hyp.id,
                                            expression=mut_req.expression,
                                            request=mut_req,
                                            status=ExperimentStatus.PENDING,
                                            created_at=datetime.utcnow(),
                                        )
                                        if self.history_tracker:
                                            self.history_tracker.record_experiment(
                                                mut_exp
                                            )

                                        mut_result = self.simulation_runner.run(mut_req)

                                        # Update mutated experiment to completed
                                        completed_mut_exp = mut_exp.model_copy(
                                            update={
                                                "status": ExperimentStatus.COMPLETED,
                                                "result": mut_result,
                                                "finished_at": datetime.utcnow(),
                                            }
                                        )
                                        if self.history_tracker:
                                            self.history_tracker.record_experiment(
                                                completed_mut_exp
                                            )

                                        # Save learning record feedback
                                        if (
                                            self.feedback_generator
                                            and self.learning_repository
                                        ):
                                            mut_rec = (
                                                self.feedback_generator.generate_record(
                                                    mut_req,
                                                    mut_result,
                                                    datasets=[dataset_name],
                                                    operators=hyp.operators,
                                                )
                                            )
                                            self.learning_repository.add_record(mut_rec)
                                            hypothesis_records.append(mut_rec)

                                        mut_cand_id = f"AST-{cand_counter:04d}"
                                        mut_candidate = AlphaCandidate(
                                            id=mut_cand_id,
                                            experiment_id=mut_exp_id,
                                            hypothesis_id=hyp.id,
                                            campaign_id=campaign.id,
                                            expression=mut_req.expression,
                                            result=mut_result,
                                            is_submitted=False,
                                        )
                                        all_candidates.append(mut_candidate)
                                        cand_counter += 1
                                    except Exception as e:
                                        logger.error(
                                            "Mutated simulation failed: %s",
                                            e,
                                        )

                        except Exception as e:
                            logger.error("Simulation of base expression failed: %s", e)

        # 6. Score and rank all successfully simulated candidates
        if self.scorer:
            # Score each candidate using the Expected Future Value Scorer
            scored_candidates = []
            for cand in all_candidates:
                score = self.scorer.score_expression(cand.expression, cand.result)
                scored_candidates.append((cand, score))

            # Sort descending by EFV score
            sorted_scored = sorted(scored_candidates, key=lambda x: x[1], reverse=True)
            return [candidate for candidate, _ in sorted_scored]
        else:
            # Standard metrics ranking fallback
            ranked_scored = self.ranker.rank_candidates(all_candidates)
            return [candidate for candidate, _ in ranked_scored]
