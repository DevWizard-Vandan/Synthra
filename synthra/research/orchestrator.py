"""Orchestrator subsystem executing the complete autonomous research loop."""

import logging
from typing import List

from synthra.core.domain import (
    AlphaCandidate,
    Campaign,
    Hypothesis,
)
from synthra.execution.runner import SimulationRunner
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
    ) -> None:
        """Initialize orchestrator with all pipeline step subsystems."""
        self.planner = planner
        self.hypothesis_generator = hypothesis_generator
        self.expression_generator = expression_generator
        self.validator = validator
        self.mutation_engine = mutation_engine
        self.simulation_runner = simulation_runner
        self.ranker = ranker

    def execute_campaign(
        self, campaign: Campaign, max_hypotheses_per_task: int = 1
    ) -> List[AlphaCandidate]:
        """Run the complete research loop for a Campaign.

        Planner -> Hypothesis -> Expressions -> Validation -> Simulation ->
        Mutation -> Simulation -> Ranking -> Candidate List.
        """
        logger.info("Starting execution for campaign %s", campaign.id)

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
                            result = self.simulation_runner.run(req)

                            exp_id = f"EXP-{exp_counter:04d}"
                            exp_counter += 1

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

                            # 5. Mutate to generate improved variants
                            mutated_reqs = self.mutation_engine.mutate_request(
                                req, result, dataset_name
                            )
                            for mut_req in mutated_reqs[:2]:  # Limit to top 2 mutations
                                # Validate mutated request
                                if self.validator.validate_request(
                                    mut_req, dataset_name
                                ):
                                    try:
                                        logger.info(
                                            "Simulating mutated expression: %s",
                                            mut_req.expression,
                                        )
                                        mut_result = self.simulation_runner.run(mut_req)

                                        mut_exp_id = f"EXP-{exp_counter:04d}"
                                        exp_counter += 1

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

        # 6. Rank all successfully simulated candidates
        ranked_scored = self.ranker.rank_candidates(all_candidates)
        return [candidate for candidate, _ in ranked_scored]
