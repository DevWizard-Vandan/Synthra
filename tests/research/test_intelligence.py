"""Offline unit and integration tests for the Research Intelligence Engine."""

from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

from synthra.core.domain import (
    Campaign,
    CampaignStatus,
    Region,
    SimulationResult,
    Universe,
)
from synthra.execution.runner import SimulationRunner
from synthra.learning import HistoryTracker, LearningRepository
from synthra.memory import CampaignRepository, DatabaseManager
from synthra.research.generator import ExpressionGenerator
from synthra.research.mutator import MutationEngine
from synthra.research.loop import LoopPlanner, LoopExecutor, ExpressionSynthesizer
from synthra.research.intelligence import (
    KnowledgeBase,
    ReasoningEngine,
    HypothesisRanker,
    IntelligenceResearcher,
    IntelligenceLoopController,
)


def test_intelligence_components(tmp_path: Path, catalog: Any) -> None:
    """Verify knowledge base retrieval, reasoning engine, templates, and ranking."""
    db_file = tmp_path / "test_intel.db"
    db_manager = DatabaseManager(str(db_file))

    # 1. Verify Knowledge Retrieval
    kb = KnowledgeBase(db_manager)
    entries = kb.get_entries()
    assert len(entries) == 13
    momentum = kb.get_entry("Momentum")
    assert momentum is not None
    assert momentum.concept == "Momentum"
    assert "ts_delta" in momentum.preferred_operators

    # 2. Verify Reasoning Engine and Template Generation
    campaign = Campaign(
        id="CMP-0010",
        name="Intelligence Test Campaign",
        region=Region.US,
        universe=Universe.TOP3000,
        budget_limit=100.0,
        status=CampaignStatus.ACTIVE,
        created_at=datetime.utcnow(),
        target_alpha_count=2,
    )
    engine = ReasoningEngine(catalog)
    paths = engine.formulate_reasoning_paths(campaign, kb)
    assert len(paths) > 0

    # Must have candidate expressions generated from templates
    first_path = paths[0]
    assert len(first_path.candidate_expressions) > 0
    assert first_path.required_dataset in [
        "pv",
        "fundamentals",
        "analyst",
        "sentiment",
    ]

    # 3. Verify Hypothesis Ranking
    ranker = HypothesisRanker(catalog)
    ranked = ranker.rank_paths(paths, campaign, kb)
    assert len(ranked) > 0
    assert ranked[0][1] >= ranked[-1][1]  # Ranked descending

    # 4. Verify Learning Updates and Deterministic behavior
    assert momentum.confidence == 0.5
    # Record success feedback
    kb.record_feedback("Momentum", "US", "TOP3000", success=True)
    m1 = kb.get_entry("Momentum")
    assert m1 is not None
    assert m1.confidence == 0.55
    # Record failure feedback
    kb.record_feedback("Momentum", "US", "TOP3000", success=False)
    m2 = kb.get_entry("Momentum")
    assert m2 is not None
    assert m2.confidence == 0.50


def test_intelligence_loop_integration(
    tmp_path: Path, catalog: Any, validator: Any, mock_llm: Any
) -> None:
    """Verify integration of intelligence controller with the full loop."""
    db_file = tmp_path / "test_intel_loop.db"
    db_manager = DatabaseManager(str(db_file))

    history_tracker = HistoryTracker(db_manager=db_manager)
    learning_repo = LearningRepository(db_manager=db_manager)

    with db_manager.transaction() as conn:
        c = Campaign(
            id="CMP-0011",
            name="Loop Intel test",
            region=Region.US,
            universe=Universe.TOP3000,
            budget_limit=100.0,
            status=CampaignStatus.ACTIVE,
            created_at=datetime.utcnow(),
            target_alpha_count=1,
        )
        CampaignRepository(conn).save(c)

    mock_runner = MagicMock(spec=SimulationRunner)
    mock_runner.run.return_value = SimulationResult(
        sharpe=2.5,
        fitness=2.0,
        margin=0.08,
        turnover=0.02,
        coverage=0.99,
        simulated_at=datetime.utcnow(),
    )

    researcher = IntelligenceResearcher(db_manager=db_manager, catalog=catalog)
    planner = LoopPlanner()
    validator.validate_request = MagicMock(return_value=True)
    expression_gen = ExpressionGenerator(
        llm_provider=mock_llm, catalog=catalog, validator=validator
    )
    mutator = MutationEngine(catalog=catalog)
    synthesizer = ExpressionSynthesizer(
        expression_generator=expression_gen,
        mutation_engine=mutator,
        validator=validator,
    )
    executor = LoopExecutor(
        runner=mock_runner,
        history_tracker=history_tracker,
        max_retries=2,
        initial_backoff=0.01,
    )

    controller = IntelligenceLoopController(
        db_manager=db_manager,
        catalog=catalog,
        hypothesis_generator=researcher,
        planner=planner,
        synthesizer=synthesizer,
        executor=executor,
        learning_repository=learning_repo,
    )

    # Run the loop for 1 generation
    ranked = controller.run_loop(campaign_id="CMP-0011", generations=1)
    assert len(ranked) > 0

    # Verify learning updates processed successfully
    with db_manager.connection() as conn:
        rows = conn.execute(
            "SELECT concept, confidence FROM research_knowledge;"
        ).fetchall()
        assert len(rows) > 0
        assert any(r["confidence"] > 0.5 for r in rows)
