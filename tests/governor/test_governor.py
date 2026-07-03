"""Exhaustive offline tests for the Governor and Campaign Scheduler."""

import time
from datetime import datetime
from unittest.mock import MagicMock
import pytest

from synthra.core.catalog import DatasetCatalog
from synthra.core.domain import (
    Campaign,
    CampaignStatus,
    Region,
    SimulationResult,
    Universe,
)
from synthra.execution.runner import SimulationRunner
from synthra.governor import (
    CampaignEvent,
    Event,
    CampaignEventBus,
    CampaignQueue,
    CampaignScheduler,
    CampaignState,
    Governor,
    InvalidStateTransition,
    validate_transition,
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

# ---------------------------------------------------------------------------
# State Machine Tests
# ---------------------------------------------------------------------------


def test_state_machine_valid_transitions() -> None:
    """Verify that allowed state transitions pass validation successfully."""
    # draft -> queued
    validate_transition(CampaignState.DRAFT, CampaignState.QUEUED)
    # queued -> running
    validate_transition(CampaignState.QUEUED, CampaignState.RUNNING)
    # running -> paused
    validate_transition(CampaignState.RUNNING, CampaignState.PAUSED)
    # paused -> running
    validate_transition(CampaignState.PAUSED, CampaignState.RUNNING)
    # running -> completed
    validate_transition(CampaignState.RUNNING, CampaignState.COMPLETED)


def test_state_machine_invalid_transitions() -> None:
    """Verify that disallowed transitions raise InvalidStateTransition."""
    # draft -> completed (cannot jump states directly)
    with pytest.raises(InvalidStateTransition):
        validate_transition(CampaignState.DRAFT, CampaignState.COMPLETED)

    # completed -> running (terminal state)
    with pytest.raises(InvalidStateTransition):
        validate_transition(CampaignState.COMPLETED, CampaignState.RUNNING)


# ---------------------------------------------------------------------------
# Queue Ordering Tests
# ---------------------------------------------------------------------------


def test_campaign_queue_ordering() -> None:
    """Verify priority queue order and FIFO override for identical priorities."""
    queue = CampaignQueue()

    c1 = Campaign(
        id="CMP-0001",
        name="C1",
        region=Region.US,
        universe=Universe.TOP2000,
        budget_limit=10.0,
    )
    c2 = Campaign(
        id="CMP-0002",
        name="C2",
        region=Region.US,
        universe=Universe.TOP2000,
        budget_limit=10.0,
    )
    c3 = Campaign(
        id="CMP-0003",
        name="C3",
        region=Region.US,
        universe=Universe.TOP2000,
        budget_limit=10.0,
    )

    # Enqueue in arbitrary order with different priorities
    queue.enqueue(c1, priority=1)
    queue.enqueue(c2, priority=10)  # Highest
    queue.enqueue(c3, priority=5)

    # Dequeue B (priority 10), then C (5), then A (1)
    res2 = queue.dequeue()
    assert res2 is not None and res2[0].id == "CMP-0002"

    res3 = queue.dequeue()
    assert res3 is not None and res3[0].id == "CMP-0003"

    res1 = queue.dequeue()
    assert res1 is not None and res1[0].id == "CMP-0001"


def test_campaign_queue_fifo_fallback() -> None:
    """Verify FIFO ordering when priorities are identical."""
    queue = CampaignQueue()

    c1 = Campaign(
        id="CMP-0001",
        name="C1",
        region=Region.US,
        universe=Universe.TOP2000,
        budget_limit=10.0,
    )
    c2 = Campaign(
        id="CMP-0002",
        name="C2",
        region=Region.US,
        universe=Universe.TOP2000,
        budget_limit=10.0,
    )

    queue.enqueue(c1, priority=2)
    time.sleep(0.01)  # ensure timestamp gap
    queue.enqueue(c2, priority=2)

    res1 = queue.dequeue()
    assert res1 is not None and res1[0].id == "CMP-0001"

    res2 = queue.dequeue()
    assert res2 is not None and res2[0].id == "CMP-0002"


# ---------------------------------------------------------------------------
# Event Bus and Emission Tests
# ---------------------------------------------------------------------------


def test_event_bus_publishing() -> None:
    """Verify EventBus registers subscribers and broadcasts events correctly."""
    bus = CampaignEventBus()
    events_received = []

    def listener(event: Event) -> None:
        events_received.append(event)

    bus.subscribe(listener)

    ev = CampaignEvent(campaign_id="CMP-0001")
    bus.publish(ev)

    assert len(events_received) == 1
    assert events_received[0].campaign_id == "CMP-0001"  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# Scheduler Pause, Resume, Cancel & Recovery Tests
# ---------------------------------------------------------------------------


def test_scheduler_lifecycle_and_control(
    db_manager: DatabaseManager, catalog: DatasetCatalog
) -> None:
    """Verify pause, resume, cancel transitions and SQLite state synchronization."""
    queue = CampaignQueue()
    progress = MagicMock()
    bus = CampaignEventBus()
    orch = MagicMock(spec=ResearchOrchestrator)

    scheduler = CampaignScheduler(
        queue=queue,
        orchestrator=orch,
        progress_tracker=progress,
        event_bus=bus,
        db_manager=db_manager,
    )

    c1 = Campaign(
        id="CMP-0001",
        name="Trend",
        region=Region.US,
        universe=Universe.TOP2000,
        budget_limit=100.0,
    )

    # Enqueue -> state is QUEUED
    scheduler.enqueue_campaign(c1, priority=5)
    assert scheduler.get_campaign_state("CMP-0001") == CampaignState.QUEUED
    assert queue.size() == 1

    # Pause -> state is PAUSED, removed from queue
    scheduler.pause_campaign("CMP-0001")
    assert scheduler.get_campaign_state("CMP-0001") == CampaignState.PAUSED
    assert queue.size() == 0

    # Resume -> state is QUEUED, added back to queue
    scheduler.resume_campaign("CMP-0001")
    assert scheduler.get_campaign_state("CMP-0001") == CampaignState.QUEUED
    assert queue.size() == 1

    # Cancel -> state is CANCELLED, removed from queue
    scheduler.cancel_campaign("CMP-0001")
    assert scheduler.get_campaign_state("CMP-0001") == CampaignState.CANCELLED
    assert queue.size() == 0


def test_scheduler_recovery(db_manager: DatabaseManager) -> None:
    """Verify recovery on startup restores queued/running campaigns to active queue."""
    queue = CampaignQueue()
    progress = MagicMock()
    bus = CampaignEventBus()
    orch = MagicMock(spec=ResearchOrchestrator)

    c1 = Campaign(
        id="CMP-0001",
        name="C1",
        region=Region.US,
        universe=Universe.TOP2000,
        budget_limit=10.0,
    )
    c2 = Campaign(
        id="CMP-0002",
        name="C2",
        region=Region.US,
        universe=Universe.TOP2000,
        budget_limit=10.0,
    )

    scheduler = CampaignScheduler(
        queue=queue,
        orchestrator=orch,
        progress_tracker=progress,
        event_bus=bus,
        db_manager=db_manager,
    )

    # Setup database state manually representing a crash during RUNNING/QUEUED states
    with db_manager.transaction() as conn:
        CampaignRepository(conn).save(c1)
        CampaignRepository(conn).save(c2)
        conn.execute(
            "INSERT INTO campaign_states (campaign_id, state, priority) "
            "VALUES (?, ?, ?)",
            ("CMP-0001", CampaignState.RUNNING.value, 5),
        )
        conn.execute(
            "INSERT INTO campaign_states (campaign_id, state, priority) "
            "VALUES (?, ?, ?)",
            ("CMP-0002", CampaignState.QUEUED.value, 1),
        )

    # Recover
    scheduler.recover_campaigns()

    assert queue.size() == 2
    # Statuses reset back to QUEUED
    assert scheduler.get_campaign_state("CMP-0001") == CampaignState.QUEUED
    assert scheduler.get_campaign_state("CMP-0002") == CampaignState.QUEUED


# ---------------------------------------------------------------------------
# Retry and Backoff Tests
# ---------------------------------------------------------------------------


def test_scheduler_retry_backoff(db_manager: DatabaseManager) -> None:
    """Verify scheduler schedules backoff for failed campaign state."""
    queue = CampaignQueue()
    progress = MagicMock()
    bus = CampaignEventBus()
    orch = MagicMock(spec=ResearchOrchestrator)

    scheduler = CampaignScheduler(
        queue=queue,
        orchestrator=orch,
        progress_tracker=progress,
        event_bus=bus,
        db_manager=db_manager,
        max_retries=2,
        initial_backoff_seconds=1.0,
    )

    c1 = Campaign(
        id="CMP-0001",
        name="C1",
        region=Region.US,
        universe=Universe.TOP2000,
        budget_limit=10.0,
    )
    scheduler.enqueue_campaign(c1, priority=1)

    # Emulate campaign failing
    scheduler.update_campaign_state("CMP-0001", CampaignState.FAILED)

    # Verify retry_at is set in the database
    with db_manager.connection() as conn:
        row = conn.execute("SELECT retry_at, failures FROM campaign_states").fetchone()
        assert row is not None
        assert row["retry_at"] > 0.0
        assert row["failures"] == 0  # Starts at 0, incremented when monitor re-enqueues


# ---------------------------------------------------------------------------
# Complete Governor Loop Test
# ---------------------------------------------------------------------------


def test_governor_autonomous_loop(
    db_manager: DatabaseManager, catalog: DatasetCatalog
) -> None:
    """Verify complete governor orchestration loop using workers."""
    # 1. Setup learning subsystems
    tracker = HistoryTracker(db_manager=db_manager)
    feedback_gen = FeedbackGenerator()
    learning_repo = LearningRepository(db_manager=db_manager)
    scorer = ExpressionScorer(history=[])

    # 2. Setup research subsystems
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
    )

    # 3. Setup Governor with 1 worker
    gov = Governor(
        orchestrator=orch,
        db_manager=db_manager,
        num_workers=1,
    )

    c1 = Campaign(
        id="CMP-0001",
        name="Governor Integrated test",
        region=Region.US,
        universe=Universe.TOP2000,
        budget_limit=100.0,
        status=CampaignStatus.ACTIVE,
        created_at=datetime.utcnow(),
    )

    gov.start()
    try:
        gov.enqueue_campaign(c1, priority=5)

        # Wait for the worker to process the campaign (run loop dequeues it)
        timeout = 5.0
        start_time = time.time()
        while time.time() - start_time < timeout:
            state = gov.get_campaign_state("CMP-0001")
            if state == CampaignState.COMPLETED:
                break
            time.sleep(0.1)

        # Check final state
        assert gov.get_campaign_state("CMP-0001") == CampaignState.COMPLETED

        # Check progress details
        progress = gov.get_campaign_progress("CMP-0001")
        assert progress is not None
        assert progress.completed_simulations > 0
        assert progress.successful_simulations > 0
        assert progress.current_best_sharpe == 1.8

    finally:
        gov.stop()
