"""Mutation Engine generating optimized expression variants."""

import re
from typing import List, Set, Tuple

from synthra.core.catalog import DatasetCatalog
from synthra.core.domain import SimulationRequest, SimulationResult


class MutationEngine:
    """Mutation Engine to optimize and explore candidate Fast Expressions."""

    def __init__(self, catalog: DatasetCatalog) -> None:
        """Initialize with the shared DatasetCatalog dependency."""
        self.catalog = catalog

    def mutate_request(
        self,
        request: SimulationRequest,
        result: SimulationResult,
        dataset_name: str,
    ) -> List[SimulationRequest]:
        """Generate improved/altered variants of a simulation request.

        Args:
            request: Source simulation request.
            result: Result of the source simulation (used to guide optimization).
            dataset_name: Active dataset name.
        """
        mutated_requests: List[SimulationRequest] = []
        expression = request.expression

        # 1. Parameter / Window / Lookback mutations
        numbers = re.findall(r"\b\d+\b", expression)
        for num in set(numbers):
            val = int(num)
            # Try window step sizing shifts
            for diff in [-5, 5, 10]:
                new_val = val + diff
                if new_val > 0:
                    new_expr = re.sub(rf"\b{num}\b", str(new_val), expression)
                    if new_expr != expression:
                        mutated_requests.append(
                            request.model_copy(update={"expression": new_expr})
                        )

        # 2. Operator substitution (replace with matching arity variants)
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
                        mutated_requests.append(
                            request.model_copy(update={"expression": new_expr})
                        )

        # 3. Dataset / Field substitution (swap variable/field with other fields)
        ds = self.catalog.get_dataset(dataset_name)
        if ds:
            for field in ds.fields:
                if field in expression:
                    for rep_field in ds.fields:
                        if rep_field != field:
                            new_expr = re.sub(rf"\b{field}\b", rep_field, expression)
                            mutated_requests.append(
                                request.model_copy(update={"expression": new_expr})
                            )

        # 4. Neutralization changes
        alt_neutralization = (
            "INDUSTRY" if request.neutralization == "SUBINDUSTRY" else "SUBINDUSTRY"
        )
        mutated_requests.append(
            request.model_copy(update={"neutralization": alt_neutralization})
        )

        # 5. Delay changes
        new_delay = 2 if request.delay == 1 else 1
        mutated_requests.append(request.model_copy(update={"delay": new_delay}))

        # 6. Ranking mutations (wrap expression in cross-sectional rank if not ranked)
        if not expression.startswith("rank("):
            mutated_requests.append(
                request.model_copy(update={"expression": f"rank({expression})"})
            )

        # Deduplicate results
        unique_mutations: List[SimulationRequest] = []
        seen: Set[Tuple[str, str, int, int]] = set()

        for req in mutated_requests:
            key = (req.expression, req.neutralization, req.delay, req.decay)
            if key not in seen:
                seen.add(key)
                unique_mutations.append(req)

        return unique_mutations
