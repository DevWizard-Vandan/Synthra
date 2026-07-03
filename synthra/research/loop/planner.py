"""Planner modules for the autonomous research loop."""

from synthra.core.domain import Hypothesis
from synthra.research.planner import ResearchTask


class LoopPlanner:
    """Converts a Hypothesis into a structured ResearchTask plan."""

    def __init__(self) -> None:
        """Initialize the planner."""
        pass

    def plan_hypothesis(self, hypothesis: Hypothesis, task_id: str) -> ResearchTask:
        """Convert a hypothesis into a structured ResearchTask."""
        return ResearchTask(
            id=task_id,
            campaign_id=hypothesis.campaign_id,
            objective=f"Evaluate hypothesis: {hypothesis.rationale}",
            target_variable=hypothesis.target_variable,
            priority=3,
            status="pending",
            assigned_datasets=hypothesis.datasets,
            assigned_operators=hypothesis.operators,
        )
