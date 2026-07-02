"""Unit tests for the Hypothesis Generator subsystem."""

from synthra.research.hypothesis import HypothesisGenerator, MockLLMProvider
from synthra.research.planner import ResearchTask


def test_hypothesis_generation_and_mapping(mock_llm: MockLLMProvider) -> None:
    """Verify structured hypotheses are generated and mapped to domain."""
    generator = HypothesisGenerator(llm_provider=mock_llm)
    task = ResearchTask(
        id="TSK-0001-01",
        campaign_id="CMP-0001",
        objective="Analyze pv data",
        target_variable="returns",
        priority=5,
        status="pending",
        assigned_datasets=["pv"],
        assigned_operators=["ts_mean"],
    )

    structured = generator.generate_hypothesis(task)
    assert structured.target_variable == "returns"
    assert "pv" in structured.datasets
    assert "ts_mean" in structured.operators
    assert len(structured.rationale) >= 10
    assert len(structured.expected_market_behavior) >= 10

    # Test conversion to domain model
    domain_model = generator.to_domain(
        structured, campaign_id="CMP-0001", hypothesis_id="HYP-0001"
    )
    assert domain_model.id == "HYP-0001"
    assert domain_model.campaign_id == "CMP-0001"
    assert domain_model.rationale == structured.rationale
    assert domain_model.target_variable == structured.target_variable
    assert domain_model.datasets == structured.datasets
    assert domain_model.operators == structured.operators
