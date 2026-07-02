"""Analyzer subsystem to evaluate simulation outcomes and list reasons."""

from typing import List, Tuple

from synthra.core.domain import SimulationResult


class ResultAnalyzer:
    """Analyzes backtest simulation metrics for success and failure indicators."""

    def __init__(
        self,
        min_sharpe: float = 1.0,
        min_fitness: float = 0.5,
        min_coverage: float = 0.8,
        max_turnover: float = 0.7,
        min_margin: float = 0.0,
    ) -> None:
        """Initialize thresholds for metrics evaluation."""
        self.min_sharpe = min_sharpe
        self.min_fitness = min_fitness
        self.min_coverage = min_coverage
        self.max_turnover = max_turnover
        self.min_margin = min_margin

    def analyze(self, result: SimulationResult) -> Tuple[List[str], List[str]]:
        """Return lists of failure and success reasons for a simulation result."""
        failure_reasons: List[str] = []
        success_reasons: List[str] = []

        # Sharpe evaluation
        if result.sharpe < self.min_sharpe:
            failure_reasons.append("weak Sharpe")
        elif result.sharpe >= 1.5:
            success_reasons.append("strong Sharpe")

        # Fitness evaluation
        if result.fitness < self.min_fitness:
            failure_reasons.append("poor fitness")
        elif result.fitness >= 2.0:
            success_reasons.append("excellent fitness")

        # Coverage evaluation
        if result.coverage < self.min_coverage:
            failure_reasons.append("coverage too low")
        elif result.coverage >= 0.95:
            success_reasons.append("high coverage")

        # Turnover evaluation
        if result.turnover > self.max_turnover:
            failure_reasons.append("turnover too high")
        elif result.turnover < 0.05:
            success_reasons.append("low turnover")

        # Margin evaluation
        if result.margin < self.min_margin:
            failure_reasons.append("negative margin")

        return failure_reasons, success_reasons
