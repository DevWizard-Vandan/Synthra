"""History tracker persisting research entities using the DatabaseManager."""

from typing import List

from synthra.core.domain import AlphaCandidate, Campaign, Experiment, Hypothesis
from synthra.memory import (
    AlphaCandidateRepository,
    CampaignRepository,
    DatabaseManager,
    ExperimentRepository,
    HypothesisRepository,
)


class HistoryTracker:
    """Coordinates transactional persistence of campaigns, hypotheses, and runs."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        """Initialize history tracker with the DatabaseManager handler."""
        self.db_manager = db_manager

    def record_campaign(self, campaign: Campaign) -> None:
        """Persist or update campaign details."""
        with self.db_manager.transaction() as conn:
            CampaignRepository(conn).save(campaign)

    def record_hypothesis(self, hypothesis: Hypothesis) -> None:
        """Persist or update hypothesis details."""
        with self.db_manager.transaction() as conn:
            HypothesisRepository(conn).save(hypothesis)

    def record_experiment(self, experiment: Experiment) -> None:
        """Persist or update experiment execution runs."""
        with self.db_manager.transaction() as conn:
            ExperimentRepository(conn).save(experiment)

    def record_candidate(self, candidate: AlphaCandidate) -> None:
        """Persist or update alpha strategy candidates."""
        with self.db_manager.transaction() as conn:
            AlphaCandidateRepository(conn).save(candidate)

    def get_hypothesis_results(self, hypothesis_id: str) -> List[Experiment]:
        """Fetch all historical backtest experiment runs for a hypothesis."""
        with self.db_manager.connection() as conn:
            return ExperimentRepository(conn).list_by_hypothesis(hypothesis_id)
