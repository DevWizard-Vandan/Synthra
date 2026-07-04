"""Mutation Engine generating optimized expression variants with lineage tracking."""

import re
from typing import List, Optional, Set, Tuple

from synthra.core.catalog import DatasetCatalog
from synthra.core.domain import SimulationRequest, SimulationResult
from synthra.research.evolution.lineage import LineageNode, LineageTracker


class MutationEngine:
    """Mutation Engine to optimize and explore candidate Fast Expressions."""

    def __init__(
        self,
        catalog: DatasetCatalog,
        lineage_tracker: Optional[LineageTracker] = None,
    ) -> None:
        """Initialize with catalog and optional lineage tracker."""
        self.catalog = catalog
        self.lineage_tracker = lineage_tracker

    def _record_lineage(
        self,
        new_expr: str,
        parent_expr: str,
        mutation_type: str,
        campaign_id: str = "default",
        hypothesis_id: str = "default",
    ) -> None:
        """Helper to compute parent ID/gen and record lineage node."""
        if not self.lineage_tracker:
            return

        parent_node = self.lineage_tracker.get_node(parent_expr)
        generation = (parent_node.generation + 1) if parent_node else 1
        parent_id = parent_expr  # Use expression string directly as unique identifier

        node = LineageNode(
            expression=new_expr,
            parent_id=parent_id,
            generation=generation,
            mutation_type=mutation_type,
            campaign_id=campaign_id,
            hypothesis_id=hypothesis_id,
            origin="mutated",
        )
        self.lineage_tracker.record_node(node)

    def mutate_request(
        self,
        request: SimulationRequest,
        result: SimulationResult,
        dataset_name: str,
        campaign_id: str = "default",
        hypothesis_id: str = "default",
    ) -> List[SimulationRequest]:
        """Generate improved/altered variants of a simulation request.

        Supports operator replacement, parameter/decay/delay/neutralization tuning,
        scale/rank/winsorize wrapping, nesting, and dataset swaps.
        """
        mutated_requests: List[SimulationRequest] = []
        expression = request.expression

        # 1. Parameter / Window / Lookback mutations
        numbers = re.findall(r"\b\d+\b", expression)
        for num in set(numbers):
            val = int(num)
            for diff in [-5, 5, 10]:
                new_val = val + diff
                if new_val > 0:
                    new_expr = re.sub(rf"\b{num}\b", str(new_val), expression)
                    if new_expr != expression:
                        self._record_lineage(
                            new_expr,
                            expression,
                            "parameter_tuning",
                            campaign_id,
                            hypothesis_id,
                        )
                        mutated_requests.append(
                            request.model_copy(update={"expression": new_expr})
                        )

        # 2. Operator substitution
        operators_of_arity_2 = [
            "ts_mean",
            "ts_sum",
            "ts_rank",
            "ts_std_dev",
            "ts_max",
            "ts_min",
            "ts_delta",
            "delay",
        ]
        for op in operators_of_arity_2:
            if op in expression:
                for rep in operators_of_arity_2:
                    if rep != op:
                        new_expr = expression.replace(op, rep)
                        self._record_lineage(
                            new_expr,
                            expression,
                            "operator_replacement",
                            campaign_id,
                            hypothesis_id,
                        )
                        mutated_requests.append(
                            request.model_copy(update={"expression": new_expr})
                        )

        # 3. Dataset / Field substitution
        ds = self.catalog.get_dataset(dataset_name)
        if ds:
            for field in ds.fields:
                if field in expression:
                    for rep_field in ds.fields:
                        if rep_field != field:
                            new_expr = re.sub(rf"\b{field}\b", rep_field, expression)
                            self._record_lineage(
                                new_expr,
                                expression,
                                "field_replacement",
                                campaign_id,
                                hypothesis_id,
                            )
                            mutated_requests.append(
                                request.model_copy(update={"expression": new_expr})
                            )

        # 4. Neutralization changes
        alt_neutralization = (
            "INDUSTRY" if request.neutralization == "SUBINDUSTRY" else "SUBINDUSTRY"
        )
        self._record_lineage(
            expression,
            expression,
            "neutralization_tuning",
            campaign_id,
            hypothesis_id,
        )
        mutated_requests.append(
            request.model_copy(update={"neutralization": alt_neutralization})
        )

        # 5. Delay changes
        new_delay = 2 if request.delay == 1 else 1
        self._record_lineage(
            expression, expression, "delay_tuning", campaign_id, hypothesis_id
        )
        mutated_requests.append(request.model_copy(update={"delay": new_delay}))

        # 6. Decay changes
        new_decay = request.decay + 1 if request.decay < 5 else 0
        self._record_lineage(
            expression, expression, "decay_tuning", campaign_id, hypothesis_id
        )
        mutated_requests.append(request.model_copy(update={"decay": new_decay}))

        # 7. Ranking mutations
        if not expression.startswith("rank("):
            new_expr = f"rank({expression})"
            self._record_lineage(
                new_expr,
                expression,
                "ranking_insertion",
                campaign_id,
                hypothesis_id,
            )
            mutated_requests.append(request.model_copy(update={"expression": new_expr}))

        # 8. Normalization (scale) mutations
        if not expression.startswith("scale("):
            new_expr = f"scale({expression})"
            self._record_lineage(
                new_expr,
                expression,
                "normalization_insertion",
                campaign_id,
                hypothesis_id,
            )
            mutated_requests.append(request.model_copy(update={"expression": new_expr}))

        # 9. Winsorization mutations
        if not expression.startswith("winsorize("):
            new_expr = f"winsorize({expression})"
            self._record_lineage(
                new_expr,
                expression,
                "winsorization_insertion",
                campaign_id,
                hypothesis_id,
            )
            mutated_requests.append(request.model_copy(update={"expression": new_expr}))

        # 10. Nested expression mutations
        if "ts_mean" in expression:
            new_expr = f"ts_delta({expression}, 5)"
            self._record_lineage(
                new_expr,
                expression,
                "nested_expression_mutations",
                campaign_id,
                hypothesis_id,
            )
            mutated_requests.append(request.model_copy(update={"expression": new_expr}))

        # Deduplicate results
        unique_mutations: List[SimulationRequest] = []
        seen: Set[Tuple[str, str, int, int]] = set()

        for req in mutated_requests:
            key = (req.expression, req.neutralization, req.delay, req.decay)
            if key not in seen:
                seen.add(key)
                unique_mutations.append(req)

        return unique_mutations
