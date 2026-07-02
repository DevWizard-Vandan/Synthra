"""Selector subsystem to decide mutation, regeneration, or retirement status."""

from typing import List

from synthra.learning.feedback import LearningRecord


class HypothesisSelector:
    """Evaluates hypothesis historical backtest success to guide action routing."""

    def __init__(
        self,
        retire_sharpe_threshold: float = 0.5,
        mutate_sharpe_threshold: float = 1.2,
    ) -> None:
        """Initialize selector threshold boundaries."""
        self.retire_threshold = retire_sharpe_threshold
        self.mutate_threshold = mutate_sharpe_threshold

    def evaluate_hypothesis(self, records: List[LearningRecord]) -> str:
        """Determine appropriate action for a hypothesis context.

        Returns one of: "mutate", "regenerate", or "retire".
        """
        if not records:
            return "regenerate"

        # Calculate average performance indicators
        avg_sharpe = sum(r.sharpe for r in records) / len(records)
        success_rate = sum(1 for r in records if r.success) / len(records)

        # Retire rules: if overall Sharpe is extremely weak or success rate is zero
        if avg_sharpe < self.retire_threshold or success_rate == 0.0:
            return "retire"

        # Mutate rules: if overall Sharpe is strong, mutate to optimize parameters
        if avg_sharpe >= self.mutate_threshold:
            return "mutate"

        # Default fallback: regenerate (tweak operators/formulations)
        return "regenerate"
