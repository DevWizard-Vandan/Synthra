"""Unit tests for SYNTHRA domain models."""

from datetime import datetime
from pathlib import Path
import pytest
from pydantic import ValidationError

from synthra.core.domain import (
    AlphaCandidate,
    Campaign,
    Dataset,
    Experiment,
    Hypothesis,
    Operator,
    ResearchAsset,
    SimulationRequest,
    SimulationResult,
)


def test_campaign_validation() -> None:
    """Tests that Campaign validates correct input and rejects invalid fields."""
    valid_campaign = Campaign(
        id="CMP-0001",
        name="Momentum Research",
        region="US",
        universe="TOP3000",
        budget_limit=5000.0,
        budget_spent=150.0,
        status="active",
        created_at=datetime(2026, 7, 2, 12, 0, 0),
    )
    assert valid_campaign.id == "CMP-0001"
    assert valid_campaign.name == "Momentum Research"
    assert valid_campaign.budget_spent == 150.0

    # Test invalid ID format
    with pytest.raises(ValidationError) as excinfo:
        Campaign(
            id="CMP-1",
            name="Momentum Research",
            region="US",
            universe="TOP3000",
            budget_limit=5000.0,
        )
    assert "Campaign ID must match the format 'CMP-XXXX'" in str(excinfo.value)

    # Test budget limit constraint
    with pytest.raises(ValidationError):
        Campaign(
            id="CMP-0001",
            name="Momentum Research",
            region="US",
            universe="TOP3000",
            budget_limit=-5.0,
        )

    # Test strict typing (name must be a string)
    with pytest.raises(ValidationError):
        Campaign(
            id="CMP-0001",
            name=12345,  # Invalid type under strict=True
            region="US",
            universe="TOP3000",
            budget_limit=5000.0,
        )

    # Test immutability
    with pytest.raises(ValidationError):
        # Enforced by pydantic frozen config
        valid_campaign.status = "concluded"  # type: ignore


def test_hypothesis_validation() -> None:
    """Tests Hypothesis creation and constraints validation."""
    valid_hyp = Hypothesis(
        id="HYP-0101",
        campaign_id="CMP-0001",
        rationale="Asset momentum based on 5-day cumulative returns should persist.",
        target_variable="returns_5d",
        datasets=["price_volume"],
        operators=["ts_sum", "delay"],
        status="draft",
    )
    assert valid_hyp.id == "HYP-0101"
    assert valid_hyp.campaign_id == "CMP-0001"

    # Test invalid hypothesis ID
    with pytest.raises(ValidationError):
        Hypothesis(
            id="HYP-99",
            campaign_id="CMP-0001",
            rationale="Too short.",
            target_variable="returns_5d",
            datasets=["price_volume"],
            operators=["ts_sum"],
        )

    # Test invalid campaign ID link
    with pytest.raises(ValidationError):
        Hypothesis(
            id="HYP-0101",
            campaign_id="CMP-INVALID",
            rationale="Some long rationale text for momentum.",
            target_variable="returns",
            datasets=["prices"],
            operators=["rank"],
        )


def test_simulation_request_and_result() -> None:
    """Tests SimulationRequest and SimulationResult schemas."""
    req = SimulationRequest(
        expression="ts_rank(close, 20)",
        region="US",
        universe="TOP3000",
        delay=1,
        decay=0,
        neutralization="SUBINDUSTRY",
    )
    assert req.expression == "ts_rank(close, 20)"
    assert req.delay == 1

    res = SimulationResult(
        sharpe=1.45,
        fitness=1.12,
        margin=0.08,
        turnover=0.45,
        coverage=0.92,
        simulated_at=datetime.utcnow(),
    )
    assert res.sharpe == 1.45
    assert res.coverage == 0.92


def test_experiment_validation() -> None:
    """Tests Experiment validation linking request and results."""
    req = SimulationRequest(
        expression="ts_rank(close, 20)",
        region="US",
        universe="TOP3000",
    )
    res = SimulationResult(
        sharpe=1.45,
        fitness=1.12,
        margin=0.08,
        turnover=0.45,
        coverage=0.92,
    )

    exp = Experiment(
        id="EXP-0042",
        campaign_id="CMP-0001",
        hypothesis_id="HYP-0101",
        expression="ts_rank(close, 20)",
        status="completed",
        request=req,
        result=res,
    )

    assert exp.id == "EXP-0042"
    assert exp.result is not None
    assert exp.result.sharpe == 1.45

    # Test validation of invalid IDs
    with pytest.raises(ValidationError):
        Experiment(
            id="EXP-42",
            campaign_id="CMP-0001",
            hypothesis_id="HYP-0101",
            expression="ts_rank(close, 20)",
            request=req,
        )


def test_alpha_candidate_validation() -> None:
    """Tests AlphaCandidate creation and field requirements."""
    candidate = AlphaCandidate(
        id="AST-0001",
        experiment_id="EXP-0042",
        hypothesis_id="HYP-0101",
        campaign_id="CMP-0001",
        expression="ts_rank(close, 20)",
        sharpe=1.45,
        fitness=1.12,
        turnover=0.45,
        margin=0.08,
    )
    assert candidate.id == "AST-0001"
    assert not candidate.is_submitted

    # Test validation error on extra fields
    with pytest.raises(ValidationError):
        AlphaCandidate(
            id="AST-0001",
            experiment_id="EXP-0042",
            hypothesis_id="HYP-0101",
            campaign_id="CMP-0001",
            expression="ts_rank(close, 20)",
            sharpe=1.45,
            fitness=1.12,
            turnover=0.45,
            margin=0.08,
            extra_field="forbidden",  # Extra field forbidden by config
        )


def test_dataset_and_operator_metadata() -> None:
    """Tests Dataset and Operator catalog schemas."""
    dataset = Dataset(
        name="pv",
        region="US",
        category="price_volume",
        description="Standard price volume dataset",
        fields=["open", "close", "volume"],
    )
    assert dataset.name == "pv"
    assert "close" in dataset.fields

    op = Operator(
        name="ts_rank",
        category="time_series",
        signature="ts_rank(x, d)",
        description="Time series rank",
    )
    assert op.name == "ts_rank"


def test_research_asset_validation() -> None:
    """Tests ResearchAsset path-mapping and validation logic."""
    asset = ResearchAsset(
        id="AST-0002",
        campaign_id="CMP-0001",
        type="report",
        file_path=Path("outputs/reports/CMP-0001_final.pdf"),
        description="Final campaign summary PDF",
    )
    assert asset.id == "AST-0002"
    assert isinstance(asset.file_path, Path)
