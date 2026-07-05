"""Scorer subsystem computing expected future value scores for expressions."""

from typing import List, Optional

from synthra.core.domain import SimulationResult, SimulationRequest
from synthra.learning.feedback import LearningRecord
from synthra.learning.similarity import jaccard_similarity
from synthra.memory import DatabaseManager


class ExpressionScorer:
    """Computes expected future value for a strategy candidate."""

    def __init__(
        self,
        history: Optional[List[LearningRecord]] = None,
        db_manager: Optional[DatabaseManager] = None,
    ) -> None:
        """Initialize with historical strategy learning logs."""
        self.history = history or []
        self.db_manager = db_manager

    def _refresh_history_from_db(self) -> None:
        """Query and populate self.history from SQLite dynamically."""
        if not self.db_manager:
            return
        try:
            from synthra.learning.repository import LearningRepository
            repo = LearningRepository(self.db_manager)
            self.history = repo.get_all_records()
        except Exception:
            pass

    def score_expression(self, expression: str, result: SimulationResult) -> float:
        """Calculate score combining performance, novelty, and similarity penalty.

        Expected Future Value = Performance + Novelty_Premium - Similarity_Penalty
        """
        self._refresh_history_from_db()

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

    def get_operator_score(self, operator: str) -> float:
        """Calculate the average Sharpe for learning records containing this operator."""
        self._refresh_history_from_db()
        if not self.history:
            return 0.0
        matching = [
            r.sharpe
            for r in self.history
            if any(op.lower() == operator.lower() for op in r.operators)
        ]
        return sum(matching) / len(matching) if matching else 0.0

    def get_dataset_score(self, dataset: str) -> float:
        """Calculate the average Sharpe for learning records containing this dataset."""
        self._refresh_history_from_db()
        if not self.history:
            return 0.0
        matching = [
            r.sharpe
            for r in self.history
            if any(d.lower() == dataset.lower() for d in r.datasets)
        ]
        return sum(matching) / len(matching) if matching else 0.0

    def get_mutation_score(self, mutation_type: str) -> float:
        """Calculate the average Sharpe for mutated expressions of this mutation type."""
        if not self.db_manager:
            return 0.0
        try:
            with self.db_manager.connection() as conn:
                row = conn.execute(
                    """
                    SELECT AVG(lr.sharpe)
                    FROM expression_lineages el
                    JOIN learning_records lr ON el.expression = lr.expression
                    WHERE el.mutation_type = ?
                    """,
                    (mutation_type,),
                ).fetchone()
                if row and row[0] is not None:
                    return float(row[0])
        except Exception:
            pass
        return 0.0

    def rank_mutations(
        self,
        requests: List[SimulationRequest],
        dataset_name: str,
        operators: List[str],
    ) -> List[SimulationRequest]:
        """Rank and sort mutation requests based on historical operator, dataset, and mutation type performance.

        Returns requests sorted in descending order of score.
        """
        scored_requests = []
        for req in requests:
            mutation_type = "parameter_tuning"
            if self.db_manager:
                try:
                    with self.db_manager.connection() as conn:
                        row = conn.execute(
                            "SELECT mutation_type FROM expression_lineages WHERE expression = ? LIMIT 1",
                            (req.expression,),
                        ).fetchone()
                        if row and row[0]:
                            mutation_type = row[0]
                except Exception:
                    pass

            op_score = sum(self.get_operator_score(op) for op in operators) / len(operators) if operators else 0.0
            ds_score = self.get_dataset_score(dataset_name)
            mut_score = self.get_mutation_score(mutation_type)

            total_score = op_score * 0.3 + ds_score * 0.3 + mut_score * 0.4
            scored_requests.append((req, total_score))

        scored_requests.sort(key=lambda x: x[1], reverse=True)
        return [x[0] for x in scored_requests]
