"""Selection Engine managing candidate scoring and filtering."""

from synthra.core.domain import SimulationResult


class SelectionEngine:
    """Evaluates candidates using scores with stability/complexity penalties."""

    def __init__(
        self,
        complexity_penalty_weight: float = 0.05,
        correlation_penalty_weight: float = 0.2,
    ) -> None:
        """Initialize selection engine weights."""
        self.complexity_penalty_weight = complexity_penalty_weight
        self.correlation_penalty_weight = correlation_penalty_weight

    def calculate_score(
        self,
        expression: str,
        result: SimulationResult,
        drawdown: float = 0.05,
        stability: float = 0.8,
        correlation: float = 0.0,
        complexity: int = 1,
        duplicate_penalty: float = 0.0,
        budget_penalty: float = 0.0,
    ) -> float:
        """Compute the overall selection score including penalties."""
        base_score = (
            result.sharpe * 1.5
            + result.fitness * 1.0
            + result.coverage * 0.5
            + result.margin * 0.5
            - result.turnover * 0.5
            - drawdown * 1.0
            + stability * 0.5
        )

        complexity_penalty = complexity * self.complexity_penalty_weight
        correlation_penalty = correlation * self.correlation_penalty_weight

        total_score = (
            base_score
            - complexity_penalty
            - correlation_penalty
            - duplicate_penalty
            - budget_penalty
        )
        return total_score
