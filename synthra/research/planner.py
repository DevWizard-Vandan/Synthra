"""Planner subsystem to decompose campaigns into research tasks."""

from typing import List
from pydantic import BaseModel, Field

from synthra.core.catalog import DatasetCatalog
from synthra.core.domain import Campaign


class ResearchTask(BaseModel):
    """Structured research task decomposed from a Campaign."""

    id: str = Field(..., description="Unique ID matching 'TSK-XXXX'")
    campaign_id: str = Field(..., description="Parent campaign ID")
    objective: str
    target_variable: str
    priority: int = Field(default=3, ge=1, le=5)
    status: str = "pending"
    assigned_datasets: List[str] = Field(default_factory=list)
    assigned_operators: List[str] = Field(default_factory=list)


class Planner:
    """Planner subsystem to analyze campaign constraints and generate tasks."""

    def __init__(self, catalog: DatasetCatalog) -> None:
        """Initialize the planner with the shared DatasetCatalog dependency."""
        self.catalog = catalog

    def plan_campaign(self, campaign: Campaign) -> List[ResearchTask]:
        """Decompose a campaign context into concrete, targeted research tasks.

        Uses the catalog to identify compatible datasets and operators, then
        decomposes them into actionable task units.
        """
        # Filter datasets compatible with this campaign's region and universe
        compatible_datasets = self.catalog.filter_datasets(
            region=campaign.region, universe=campaign.universe
        )

        tasks: List[ResearchTask] = []
        task_counter = 1

        for ds in compatible_datasets:
            # Assign priority based on dataset category
            priority = 3
            if ds.category == "market_data":
                priority = 5
            elif ds.category == "fundamentals":
                priority = 4

            # Decompose into tasks based on fields/targets
            # Every task targets "returns" if market_data, otherwise targets first field
            target_var = "returns" if "returns" in ds.fields else ds.fields[0]

            task_id = f"TSK-{campaign.id.split('-')[1]}-{task_counter:02d}"

            # Simple list of basic operators for this task
            operators = ["ts_mean", "ts_sum", "rank", "delay"]

            task = ResearchTask(
                id=task_id,
                campaign_id=campaign.id,
                objective=f"Analyze alpha predictive signals in dataset '{ds.name}'",
                target_variable=target_var,
                priority=priority,
                status="pending",
                assigned_datasets=[ds.name],
                assigned_operators=operators,
            )
            tasks.append(task)
            task_counter += 1

        return tasks
