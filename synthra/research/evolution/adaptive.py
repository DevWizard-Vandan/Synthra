"""Adaptive exploration manager for stagnating research campaigns."""

from typing import Set


class AdaptiveExplorer:
    """Monitors campaign metrics stagnation and increases exploration."""

    def __init__(self, stagnation_limit: int = 3) -> None:
        """Initialize stagnation thresholds and default exploration configs."""
        self.stagnation_limit = stagnation_limit
        self.stagnation_count = 0
        self.best_sharpe = 0.0

        # Dynamic search parameters
        self.epsilon = 0.1
        self.mutation_diversity_scale = 1.0
        self.active_mutation_operators: Set[str] = {
            "parameter",
            "operator",
            "dataset",
        }

    def update(self, current_best_sharpe: float) -> None:
        """Analyze current Sharpe performance to scale exploration parameters."""
        if current_best_sharpe > self.best_sharpe:
            self.best_sharpe = current_best_sharpe
            self.stagnation_count = 0
            # Reset back to baseline parameters
            self.epsilon = 0.1
            self.mutation_diversity_scale = 1.0
            self.active_mutation_operators = {"parameter", "operator", "dataset"}
        else:
            self.stagnation_count += 1
            if self.stagnation_count >= self.stagnation_limit:
                # Stagnating: scale search diversity
                self.epsilon = min(self.epsilon + 0.15, 0.5)
                self.mutation_diversity_scale += 0.5
                self.active_mutation_operators.update(
                    ["nested", "ranking", "normalization"]
                )
