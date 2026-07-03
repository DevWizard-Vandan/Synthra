"""Generator modules for the autonomous research loop."""

import random
from typing import Any, List, Optional

from synthra.core.catalog import DatasetCatalog
from synthra.core.domain import (
    Hypothesis,
    HypothesisStatus,
    Region,
    SimulationRequest,
    Universe,
)
from synthra.research.generator import ExpressionGenerator
from synthra.research.mutator import MutationEngine
from synthra.research.validator import Validator


class LoopHypothesisGenerator:
    """Produces hypotheses deterministically using an injected random seed."""

    def __init__(self, catalog: DatasetCatalog, seed: Optional[int] = 42) -> None:
        """Initialize hypothesis generator with catalog and optional seed."""
        self.catalog = catalog
        self.seed = seed
        self._rng = random.Random(seed)

    def generate_hypothesis(self, campaign_id: str, hypothesis_id: str) -> Hypothesis:
        """Deterministically generate a predictive hypothesis from catalog metadata."""
        datasets = list(self.catalog._dataset_metadata.keys())
        if not datasets:
            raise ValueError("No datasets available in catalog")

        operators = list(self.catalog._operator_metadata.keys())
        if not operators:
            raise ValueError("No operators available in catalog")

        dataset = self._rng.choice(datasets)
        selected_operators = self._rng.sample(operators, min(len(operators), 3))

        ops_str = ", ".join(selected_operators)
        rationale = (
            f"We hypothesize that predictive signals can be constructed from {dataset} "
            f"by applying operators such as {ops_str} to predict Close price returns."
        )

        return Hypothesis(
            id=hypothesis_id,
            campaign_id=campaign_id,
            rationale=rationale,
            target_variable="returns",
            datasets=[dataset],
            operators=selected_operators,
            status=HypothesisStatus.DRAFT,
        )


class ExpressionSynthesizer:
    """Uses existing modules to generate and validate candidate expressions."""

    def __init__(
        self,
        expression_generator: ExpressionGenerator,
        mutation_engine: MutationEngine,
        validator: Validator,
    ) -> None:
        """Initialize synthesizer with dependencies."""
        self.expression_generator = expression_generator
        self.mutation_engine = mutation_engine
        self.validator = validator

    def synthesize_candidates(
        self,
        hypothesis: Hypothesis,
        region: Region,
        universe: Universe,
    ) -> List[SimulationRequest]:
        """Formulate initial candidate expressions based on a hypothesis."""
        candidates: List[SimulationRequest] = []
        for dataset_name in hypothesis.datasets:
            initial_reqs = self.expression_generator.generate_expressions_for_dataset(
                hypothesis, dataset_name, region, universe
            )
            for req in initial_reqs:
                if self.validator.validate_request(req, dataset_name):
                    candidates.append(req)
        return candidates

    def mutate_candidates(
        self,
        requests: List[SimulationRequest],
        results: List[tuple[SimulationRequest, Any]],
        dataset_name: str,
    ) -> List[SimulationRequest]:
        """Apply mutation strategies on current expressions to form new variants."""
        mutated_reqs: List[SimulationRequest] = []
        for req, res in results:
            mutations = self.mutation_engine.mutate_request(req, res, dataset_name)
            for mut in mutations:
                if self.validator.validate_request(mut, dataset_name):
                    mutated_reqs.append(mut)
        return mutated_reqs
