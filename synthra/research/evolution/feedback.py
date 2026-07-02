from typing import Any, Dict


class EvolutionFeedback:
    """Logs and tracks accepted/rejected mutations and performance success rates."""

    def __init__(self) -> None:
        """Initialize counters for mutation metrics."""
        self.accepted_mutations = 0
        self.rejected_mutations = 0
        self.improved_metrics = 0
        self.failed_metrics = 0

    def record_mutation_feedback(
        self, parent_sharpe: float, child_sharpe: float, success: bool
    ) -> None:
        """Record outcome of a mutation step to compile statistical feedback."""
        if success:
            self.accepted_mutations += 1
        else:
            self.rejected_mutations += 1

        if child_sharpe > parent_sharpe:
            self.improved_metrics += 1
        else:
            self.failed_metrics += 1


class EvolutionStats:
    """Holder for current generation mutation statistics."""

    def __init__(self) -> None:
        """Initialize stats container."""
        self.mutation_statistics: Dict[str, Any] = {}
        self.selection_statistics: Dict[str, Any] = {}
