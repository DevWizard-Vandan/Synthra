"""Campaign statistics manager to monitor evolutionary optimization progress."""

from typing import Dict, List


class CampaignEvolutionStats:
    """Aggregates and tracks metrics over generations for campaign analysis."""

    def __init__(self) -> None:
        """Initialize stats fields."""
        self.generations = 0
        self.mutation_attempts = 0
        self.mutation_successes = 0
        self.improvements: List[float] = []
        self.best_lineage: List[str] = []
        self.mutation_frequencies: Dict[str, int] = {}
        self.top_operators: Dict[str, int] = {}
        self.top_datasets: Dict[str, int] = {}

    @property
    def mutation_success_rate(self) -> float:
        """Calculate mutation success rate."""
        if self.mutation_attempts == 0:
            return 0.0
        return self.mutation_successes / self.mutation_attempts

    @property
    def average_improvement(self) -> float:
        """Compute the average improvement of candidate Sharpe metrics."""
        if not self.improvements:
            return 0.0
        return sum(self.improvements) / len(self.improvements)

    def record_mutation(
        self, mutation_type: str, success: bool, improvement: float = 0.0
    ) -> None:
        """Record a mutation attempt, its success outcome, and improvement."""
        self.mutation_attempts += 1
        if success:
            self.mutation_successes += 1
            if improvement > 0.0:
                self.improvements.append(improvement)

        freq = self.mutation_frequencies.get(mutation_type, 0)
        self.mutation_frequencies[mutation_type] = freq + 1
