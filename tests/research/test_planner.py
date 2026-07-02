"""Unit tests for the Planner subsystem."""

from datetime import datetime

from synthra.core.catalog import DatasetCatalog
from synthra.core.domain import Campaign, CampaignStatus, Region, Universe
from synthra.research.planner import Planner


def test_planner_decomposes_campaign(catalog: DatasetCatalog) -> None:
    """Verify that campaign context is correctly decomposed into research tasks."""
    planner = Planner(catalog=catalog)
    campaign = Campaign(
        id="CMP-0001",
        name="Test Momentum Campaign",
        region=Region.US,
        universe=Universe.TOP2000,
        budget_limit=1000.0,
        status=CampaignStatus.ACTIVE,
        created_at=datetime.utcnow(),
    )

    tasks = planner.plan_campaign(campaign)
    assert len(tasks) > 0

    for task in tasks:
        assert task.campaign_id == campaign.id
        assert task.id.startswith("TSK-0001-")
        assert len(task.assigned_datasets) == 1
        assert len(task.assigned_operators) > 0
        assert task.priority in (1, 2, 3, 4, 5)
        assert task.status == "pending"
