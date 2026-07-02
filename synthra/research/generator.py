"""Expression Generator subsystem to formulate compilable Fast Expressions."""

from typing import List
from pydantic import BaseModel, Field

from synthra.core.catalog import DatasetCatalog
from synthra.core.domain import Hypothesis, Region, SimulationRequest, Universe
from synthra.research.hypothesis import ILLMProvider
from synthra.research.validator import Validator


class GeneratedExpressionResponse(BaseModel):
    """Structured response containing candidate Fast Expressions."""

    expressions: List[str] = Field(..., min_length=1)


class ExpressionGenerator:
    """Expression Generator translating hypotheses rationales into code."""

    def __init__(
        self,
        llm_provider: ILLMProvider,
        catalog: DatasetCatalog,
        validator: Validator,
    ) -> None:
        """Initialize with LLM, catalog, and validator dependencies."""
        self.llm_provider = llm_provider
        self.catalog = catalog
        self.validator = validator

    def generate_expressions_for_dataset(
        self,
        hypothesis: Hypothesis,
        dataset_name: str,
        region: Region,
        universe: Universe,
    ) -> List[SimulationRequest]:
        """Convert a hypothesis context into validated simulation requests.

        Args:
            hypothesis: Target domain hypothesis.
            dataset_name: The target dataset to generate expressions for.
            region: Trading region constraint.
            universe: Universe sizing constraint.
        """
        from synthra.research.prompts import (
            EXPRESSION_SYSTEM_PROMPT,
            EXPRESSION_USER_PROMPT,
        )

        ds = self.catalog.get_dataset(dataset_name)
        if not ds:
            return []

        user_prompt = EXPRESSION_USER_PROMPT.format(
            dataset_name=dataset_name,
            rationale=hypothesis.rationale,
            target_variable=hypothesis.target_variable,
            fields=", ".join(ds.fields),
            operators=", ".join(hypothesis.operators),
        )

        # Generate structured candidate expressions
        structured = self.llm_provider.generate_structured(
            system_prompt=EXPRESSION_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=GeneratedExpressionResponse,
        )

        valid_requests: List[SimulationRequest] = []

        for expr in structured.expressions:
            # Create a candidate request
            candidate = SimulationRequest(
                expression=expr,
                region=Region(region),
                universe=Universe(universe),
                delay=1,
                decay=0,
                neutralization="SUBINDUSTRY",
            )
            # Validate the expression against the target dataset schema
            if self.validator.validate_request(candidate, dataset_name):
                valid_requests.append(candidate)

        return valid_requests
