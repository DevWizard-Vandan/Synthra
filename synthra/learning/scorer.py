"""Scorer subsystem computing expected future value scores for expressions."""

from typing import List

from synthra.core.domain import SimulationResult
from synthra.learning.feedback import LearningRecord
from synthra.learning.similarity import jaccard_similarity


class ExpressionScorer:
    """Computes expected future value for a strategy candidate."""

    def __init__(self, history: List[LearningRecord]) -> None:
        """Initialize with historical strategy learning logs."""
        self.history = history

    def score_expression(self, expression: str, result: SimulationResult) -> float:
        """Calculate score combining performance, novelty, and similarity penalty.

        Expected Future Value = Performance + Novelty_Premium - Similarity_Penalty
        """
        # 1. Base performance metrics
        performance = (
            result.sharpe * 1.5
            + result.fitness * 1.0
            + result.margin * 0.5
            + result.coverage * 0.5
            - result.turnover * 0.5
        )

        # 2. Historical Success weight
        # Calculate matching success rates for shared operators or datasets
        historical_premium = 0.0
        used_datasets = {d.lower() for d in getattr(result, "datasets", [])}
        if self.history and used_datasets:
            successful_runs = [r for r in self.history if r.success]
            matching_dataset_runs = [
                r
                for r in successful_runs
                if any(d.lower() in used_datasets for d in r.datasets)
            ]
            if matching_dataset_runs:
                historical_premium = 0.2  # Bonus if datasets have historical success

        # 3. Novelty vs. Similarity Penalty
        max_similarity = 0.0
        for rec in self.history:
            sim = jaccard_similarity(expression, rec.expression)
            if sim > max_similarity:
                max_similarity = sim

        novelty = 1.0 - max_similarity
        novelty_premium = novelty * 0.5

        # Penalty escalates as similarity approaches identity (1.0)
        similarity_penalty = 0.0
        if max_similarity > 0.7:
            similarity_penalty = max_similarity * 2.0

        score = performance + historical_premium + novelty_premium - similarity_penalty
        return score
