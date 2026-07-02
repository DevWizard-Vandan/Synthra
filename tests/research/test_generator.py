"""Unit tests for the Expression Generator subsystem."""

from datetime import datetime

from synthra.core.catalog import DatasetCatalog
from synthra.core.domain import Hypothesis, HypothesisStatus, Region, Universe
from synthra.research.generator import ExpressionGenerator
from synthra.research.hypothesis import MockLLMProvider
from synthra.research.validator import Validator


def test_expression_generator_produces_valid_requests(
    mock_llm: MockLLMProvider, catalog: DatasetCatalog, validator: Validator
) -> None:
    """Verify that expression generator produces validated simulation requests."""
    generator = ExpressionGenerator(
        llm_provider=mock_llm, catalog=catalog, validator=validator
    )

    hypothesis = Hypothesis(
        id="HYP-0001",
        campaign_id="CMP-0001",
        rationale="Momentum anomalies exist in price-volume data.",
        target_variable="returns",
        datasets=["pv"],
        operators=["ts_mean", "delay"],
        status=HypothesisStatus.DRAFT,
        created_at=datetime.utcnow(),
    )

    requests = generator.generate_expressions_for_dataset(
        hypothesis,
        dataset_name="pv",
        region=Region.US,
        universe=Universe.TOP2000,
    )

    assert len(requests) > 0
    for req in requests:
        assert req.region == Region.US
        assert req.universe == Universe.TOP2000
        # The generated expressions are valid since MockLLM returns compilable ones
        assert validator.validate_request(req, "pv") is True
