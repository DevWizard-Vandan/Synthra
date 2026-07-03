"""Unit tests for SYNTHRA domain models."""

from datetime import datetime
from pathlib import Path
import pytest
from pydantic import ValidationError

from synthra.core.domain import (
    AlphaCandidate,
    Campaign,
    CampaignStatus,
    Dataset,
    Experiment,
    ExperimentStatus,
    Hypothesis,
    HypothesisStatus,
    Operator,
    Region,
    ResearchAsset,
    ResearchAssetType,
    SimulationRequest,
    SimulationResult,
    Universe,
)


def test_campaign_validation() -> None:
    """Tests that Campaign validates correct input and rejects invalid fields."""
    valid_campaign = Campaign(
        id="CMP-0001",
        name="Momentum Research",
        region=Region.US,
        universe=Universe.TOP3000,
        budget_limit=5000.0,
        budget_spent=150.0,
        status=CampaignStatus.ACTIVE,
        created_at=datetime(2026, 7, 2, 12, 0, 0),
    )
    assert valid_campaign.id == "CMP-0001"
    assert valid_campaign.name == "Momentum Research"
    assert valid_campaign.region == "US"  # use_enum_values serializes to string
    assert valid_campaign.universe == "TOP3000"
    assert valid_campaign.status == "active"

    # Test serialization outputs the enum values directly as strings
    data = valid_campaign.model_dump()
    assert data["region"] == "US"
    assert data["universe"] == "TOP3000"
    assert data["status"] == "active"

    # Test invalid Enum string value
    with pytest.raises(ValidationError):
        Campaign(
            id="CMP-0001",
            name="Momentum Research",
            region="INVALID_REGION",  # type: ignore
            universe=Universe.TOP3000,
            budget_limit=5000.0,
        )

    # Test invalid ID format
    with pytest.raises(ValidationError) as excinfo:
        Campaign(
            id="CMP-1",
            name="Momentum Research",
            region=Region.US,
            universe=Universe.TOP3000,
            budget_limit=5000.0,
        )
    assert "Campaign ID must match the format 'CMP-XXXX'" in str(excinfo.value)

    # Test budget limit constraint
    with pytest.raises(ValidationError):
        Campaign(
            id="CMP-0001",
            name="Momentum Research",
            region=Region.US,
            universe=Universe.TOP3000,
            budget_limit=-5.0,
        )

    # Test strict typing
    with pytest.raises(ValidationError):
        Campaign(
            id="CMP-0001",
            name=12345,  # type: ignore[arg-type]  # Invalid type under strict=True
            region=Region.US,
            universe=Universe.TOP3000,
            budget_limit=5000.0,
        )

    # Test immutability
    with pytest.raises(ValidationError):
        valid_campaign.status = CampaignStatus.CONCLUDED


def test_hypothesis_validation() -> None:
    """Tests Hypothesis creation and constraints validation."""
    valid_hyp = Hypothesis(
        id="HYP-0101",
        campaign_id="CMP-0001",
        rationale="Asset momentum based on 5-day cumulative returns should persist.",
        target_variable="returns_5d",
        datasets=["price_volume"],
        operators=["ts_sum", "delay"],
        status=HypothesisStatus.DRAFT,
    )
    assert valid_hyp.id == "HYP-0101"
    assert valid_hyp.campaign_id == "CMP-0001"
    assert valid_hyp.status == "draft"

    # Test invalid hypothesis ID
    with pytest.raises(ValidationError):
        Hypothesis(
            id="HYP-99",
            campaign_id="CMP-0001",
            rationale="Too short rationale string.",
            target_variable="returns_5d",
            datasets=["price_volume"],
            operators=["ts_sum"],
        )


def test_simulation_request_and_result() -> None:
    """Tests SimulationRequest and SimulationResult schemas."""
    req = SimulationRequest(
        expression="ts_rank(close, 20)",
        region=Region.US,
        universe=Universe.TOP3000,
        delay=1,
        decay=0,
        neutralization="SUBINDUSTRY",
    )
    assert req.expression == "ts_rank(close, 20)"
    assert req.region == "US"
    assert req.universe == "TOP3000"

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
        region=Region.US,
        universe=Universe.TOP3000,
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
        status=ExperimentStatus.COMPLETED,
        request=req,
        result=res,
    )

    assert exp.id == "EXP-0042"
    assert exp.status == "completed"
    assert exp.result is not None
    assert exp.result.sharpe == 1.45


def test_alpha_candidate_validation() -> None:
    """Tests AlphaCandidate creation, validation, and embedded metrics."""
    res = SimulationResult(
        sharpe=1.45,
        fitness=1.12,
        margin=0.08,
        turnover=0.45,
        coverage=0.92,
    )

    candidate = AlphaCandidate(
        id="AST-0001",
        experiment_id="EXP-0042",
        hypothesis_id="HYP-0101",
        campaign_id="CMP-0001",
        expression="ts_rank(close, 20)",
        result=res,
    )
    assert candidate.id == "AST-0001"
    assert candidate.result.sharpe == 1.45
    assert candidate.result.fitness == 1.12
    assert not candidate.is_submitted


def test_dataset_and_operator_metadata() -> None:
    """Tests Dataset and Operator catalog schemas."""
    dataset = Dataset(
        name="pv",
        region=Region.US,
        category="price_volume",
        description="Standard price volume dataset",
        fields=["open", "close", "volume"],
    )
    assert dataset.name == "pv"
    assert dataset.region == "US"

    op = Operator(
        name="ts_rank",
        category="time_series",
        signature="ts_rank(x, d)",
        description="Time series rank",
    )
    assert op.name == "ts_rank"


def test_research_asset_validation() -> None:
    """Tests ResearchAsset validation and asset type enums."""
    asset = ResearchAsset(
        id="AST-0002",
        campaign_id="CMP-0001",
        type=ResearchAssetType.REPORT,
        file_path=Path("outputs/reports/CMP-0001_final.pdf"),
        description="Final campaign summary PDF",
    )
    assert asset.id == "AST-0002"
    assert asset.type == "report"
