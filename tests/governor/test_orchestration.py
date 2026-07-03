"""Offline integration tests for the autonomous Research Orchestrator pipeline."""

import time
from datetime import datetime
from pathlib import Path
from typing import Any, List, Tuple
from unittest.mock import MagicMock
import pytest

from synthra.core.domain import (
    Campaign,
    CampaignStatus,
    Region,
    SimulationResult,
    Universe,
)
from synthra.execution.runner import SimulationRunner
from synthra.governor import (
    CampaignState,
    Governor,
)
from synthra.governor.events import (
    CampaignCheckpointed,
    CampaignRecovered,
    CandidateQueued,
)
from synthra.learning import (
    ExpressionScorer,
    FeedbackGenerator,
    HistoryTracker,
    LearningRepository,
)
from synthra.memory import CampaignRepository, DatabaseManager
from synthra.research.generator import ExpressionGenerator
from synthra.research.hypothesis import HypothesisGenerator, MockLLMProvider
from synthra.research.mutator import MutationEngine
from synthra.research.orchestrator import ResearchOrchestrator
from synthra.research.planner import Planner
from synthra.research.ranking import CandidateRanker
from synthra.research.validator import Validator


@pytest.fixture
def test_env(
    tmp_path: Path, catalog: Any
) -> Tuple[DatabaseManager, Governor, MagicMock]:
    """Fixture initializing a clean test database and orchestrator dependencies."""
    db_file = tmp_path / "test_orch.db"
    db_manager = DatabaseManager(str(db_file))

    # Setup history and learning
    tracker = HistoryTracker(db_manager=db_manager)
    feedback_gen = FeedbackGenerator()
    learning_repo = LearningRepository(db_manager=db_manager)
    scorer = ExpressionScorer(history=[])

    # Setup mock LLM & pipeline
    mock_llm = MockLLMProvider()
    validator = Validator(catalog=catalog)
    planner = Planner(catalog=catalog)
    hypothesis_gen = HypothesisGenerator(llm_provider=mock_llm)
    expression_gen = ExpressionGenerator(
        llm_provider=mock_llm, catalog=catalog, validator=validator
    )
    mutator = MutationEngine(catalog=catalog)
    ranker = CandidateRanker()

    mock_sim_runner = MagicMock(spec=SimulationRunner)
    mock_sim_runner.run.return_value = SimulationResult(
        sharpe=1.8,
        fitness=2.1,
        margin=0.08,
        turnover=0.04,
        coverage=0.98,
        simulated_at=datetime.utcnow(),
    )

    orch = ResearchOrchestrator(
        planner=planner,
        hypothesis_generator=hypothesis_gen,
        expression_generator=expression_gen,
        validator=validator,
        mutation_engine=mutator,
        simulation_runner=mock_sim_runner,
        ranker=ranker,
        feedback_generator=feedback_gen,
        learning_repository=learning_repo,
        history_tracker=tracker,
        scorer=scorer,
        db_manager=db_manager,
    )

    gov = Governor(
        orchestrator=orch,
        db_manager=db_manager,
        num_workers=1,
    )

    return db_manager, gov, mock_sim_runner


# ---------------------------------------------------------------------------
# Complete Pipeline & Candidate Queue Tests
# ---------------------------------------------------------------------------


def test_pipeline_and_candidate_queue(
    test_env: Tuple[DatabaseManager, Governor, MagicMock],
) -> None:
    """Verify campaign runs to completion, enqueuing candidates in SubmissionQueue."""
    db_manager, gov, _ = test_env

    # 1. Setup events logging
    captured_events: List[Any] = []
    gov.event_bus.subscribe(captured_events.append)

    c = Campaign(
        id="CMP-0001",
        name="Orch pipeline test",
        region=Region.US,
        universe=Universe.TOP2000,
        budget_limit=100.0,
        status=CampaignStatus.ACTIVE,
        created_at=datetime.utcnow(),
        target_alpha_count=1,
    )

    gov.start()
    try:
        gov.enqueue_campaign(c, priority=10)

        # Wait for completion
        time.sleep(1.0)
        assert gov.get_campaign_state("CMP-0001") == CampaignState.COMPLETED

        # Verify candidate enqueued
        sub_queue = gov.submission_queue
        assert sub_queue.size() > 0

        cand = sub_queue.dequeue()
        assert cand is not None
        assert cand.campaign_id == "CMP-0001"
        assert cand.metrics["sharpe"] == 1.8
        assert "passed selection" in cand.reason_selected

        # Verify event emission
        assert any(isinstance(e, CandidateQueued) for e in captured_events)
    finally:
        gov.stop()


# ---------------------------------------------------------------------------
# Checkpoint & Recovery Tests
# ---------------------------------------------------------------------------


def test_checkpoint_recovery_flow(
    test_env: Tuple[DatabaseManager, Governor, MagicMock],
) -> None:
    """Verify workers save campaign checkpoints and recover cleanly upon restart."""
    db_manager, gov, _ = test_env

    captured_events: List[Any] = []
    gov.event_bus.subscribe(captured_events.append)

    c = Campaign(
        id="CMP-0002",
        name="Checkpoint recovery test",
        region=Region.US,
        universe=Universe.TOP2000,
        budget_limit=100.0,
        status=CampaignStatus.ACTIVE,
        created_at=datetime.utcnow(),
        target_alpha_count=1,
    )

    # 1. Pre-populate database with checkpoint representing task_idx 2 completed
    with db_manager.transaction() as conn:
        CampaignRepository(conn).save(c)
        conn.execute(
            """
            INSERT OR REPLACE INTO campaign_checkpoints (
                campaign_id, task_index, generation, checkpoint_data
            ) VALUES (?, ?, ?, ?)
            """,
            ("CMP-0002", 2, 0, "{}"),
        )
        # Register campaign in states table as queued to simulate recovery restart
        conn.execute(
            """
            INSERT OR REPLACE INTO campaign_states (
                campaign_id, state, priority
            ) VALUES (?, ?, ?)
            """,
            ("CMP-0002", CampaignState.QUEUED.value, 5),
        )

    gov.start()
    try:
        # Trigger recovery explicitly
        gov.scheduler.recover_campaigns()

        # Wait for completion
        time.sleep(1.0)

        # Assert campaign completes
        assert gov.get_campaign_state("CMP-0002") == CampaignState.COMPLETED

        # Check that recover event was fired
        assert any(isinstance(e, CampaignRecovered) for e in captured_events)
        assert any(isinstance(e, CampaignCheckpointed) for e in captured_events)

    finally:
        gov.stop()


# ---------------------------------------------------------------------------
# Stop Conditions Tests
# ---------------------------------------------------------------------------


def test_max_simulations_stop_condition(
    test_env: Tuple[DatabaseManager, Governor, MagicMock],
) -> None:
    """Verify worker concludes campaign early when max simulations limit is hit."""
    db_manager, gov, _ = test_env

    c = Campaign(
        id="CMP-0003",
        name="Max sims limit test",
        region=Region.US,
        universe=Universe.TOP2000,
        budget_limit=100.0,
        status=CampaignStatus.ACTIVE,
        created_at=datetime.utcnow(),
        max_simulations=1,  # limit to 1 simulation
    )

    gov.start()
    try:
        gov.enqueue_campaign(c, priority=5)
        time.sleep(1.0)

        assert gov.get_campaign_state("CMP-0003") == CampaignState.COMPLETED
        progress = gov.progress_tracker.get_progress("CMP-0003")
        assert progress is not None
        assert progress.completed_simulations == 1
    finally:
        gov.stop()


def test_target_alpha_count_stop_condition(
    test_env: Tuple[DatabaseManager, Governor, MagicMock],
) -> None:
    """Verify worker concludes campaign early when target alpha count is met."""
    db_manager, gov, _ = test_env

    c = Campaign(
        id="CMP-0004",
        name="Target alpha limit test",
        region=Region.US,
        universe=Universe.TOP2000,
        budget_limit=100.0,
        status=CampaignStatus.ACTIVE,
        created_at=datetime.utcnow(),
        target_alpha_count=1,  # Stop after 1 approved alpha candidate
    )

    gov.start()
    try:
        gov.enqueue_campaign(c, priority=5)
        time.sleep(1.0)

        assert gov.get_campaign_state("CMP-0004") == CampaignState.COMPLETED
        progress = gov.progress_tracker.get_progress("CMP-0004")
        assert progress is not None
        assert progress.approved_candidates >= 1
    finally:
        gov.stop()
