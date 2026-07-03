"""Evaluator modules for the autonomous research loop."""

from typing import List, Optional, Tuple

from synthra.core.catalog import tokenize_expression
from synthra.core.domain import SimulationResult
from synthra.learning.similarity import jaccard_similarity
from synthra.research.evolution.novelty import NoveltyDetector


class LoopEvaluator:
    """Evaluates candidate expressions based on performance and metrics."""

    def __init__(self, existing_expressions: Optional[List[str]] = None) -> None:
        """Initialize loop evaluator and novelty detector."""
        # Use import here or parameter default typing if needed
        # Standardize typing with Optional to avoid mypy name resolution issues
        self.existing_expressions = existing_expressions or []
        self.novelty_detector = NoveltyDetector()
        for expr in self.existing_expressions:
            self.novelty_detector.add_expression(expr)

    def evaluate_candidate(self, expression: str, result: SimulationResult) -> float:
        """Compute a selection score for a candidate expression."""
        # 1. Performance metrics
        sharpe = result.sharpe
        fitness = result.fitness
        margin = result.margin
        turnover = result.turnover
        coverage = result.coverage

        # 2. Novelty
        is_novel = self.novelty_detector.is_novel(expression)
        novelty_score = 1.0 if is_novel else 0.0

        # 3. Complexity penalty
        try:
            token_count = len(tokenize_expression(expression))
        except Exception:
            token_count = len(expression.split())
        complexity_penalty = -0.05 * token_count

        # 4. Correlation/Similarity penalty
        max_sim = 0.0
        for existing in self.existing_expressions:
            sim = jaccard_similarity(expression, existing)
            if sim > max_sim:
                max_sim = sim
        correlation_penalty = -0.5 * max_sim

        # 5. Selection Score calculation
        selection_score = (
            1.0 * sharpe
            + 1.0 * fitness
            + 0.5 * margin
            - 0.5 * turnover
            + 0.5 * coverage
            + 1.0 * novelty_score
            + correlation_penalty
            + complexity_penalty
        )
        return selection_score

    def rank_candidates(
        self, candidates: List[Tuple[str, SimulationResult]]
    ) -> List[Tuple[str, SimulationResult, float]]:
        """Score and sort candidate alpha strategies."""
        scored = []
        for expr, res in candidates:
            score = self.evaluate_candidate(expr, res)
            scored.append((expr, res, score))
        return sorted(scored, key=lambda x: x[2], reverse=True)
