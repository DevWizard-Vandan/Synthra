"""Unit and integration tests for the autonomous research loop."""

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
from synthra.research.loop import (
    LoopHypothesisGenerator,
    ExpressionSynthesizer,
    LoopPlanner,
    LoopExecutor,
    LoopEvaluator,
    LoopController,
)


def test_loop_pipeline(
    tmp_path: Path, catalog: Any, validator: Any, mock_llm: Any
) -> None:
    """Verify end-to-end execution, evaluation, mapping, and database writes."""
    db_file = tmp_path / "test_loop.db"
    db_manager = DatabaseManager(str(db_file))

    # Setup history, learning repo
    history_tracker = HistoryTracker(db_manager=db_manager)
    learning_repo = LearningRepository(db_manager=db_manager)

    # Prepopulate campaign
    with db_manager.transaction() as conn:
        c = Campaign(
            id="CMP-0005",
            name="Autonomous loop test",
            region=Region.US,
            universe=Universe.TOP2000,
            budget_limit=100.0,
            status=CampaignStatus.ACTIVE,
            created_at=datetime.utcnow(),
            target_alpha_count=1,
        )
        CampaignRepository(conn).save(c)

    # Setup mock simulation runner
    mock_runner = MagicMock(spec=SimulationRunner)
    mock_runner.run.return_value = SimulationResult(
        sharpe=2.1,
        fitness=1.8,
        margin=0.07,
        turnover=0.03,
        coverage=0.99,
        simulated_at=datetime.utcnow(),
    )

    # Instantiate loop components
    hypothesis_gen = LoopHypothesisGenerator(catalog=catalog, seed=42)
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

    controller = LoopController(
        db_manager=db_manager,
        catalog=catalog,
        hypothesis_generator=hypothesis_gen,
        planner=planner,
        synthesizer=synthesizer,
        executor=executor,
        learning_repository=learning_repo,
    )

    # Run the loop for 2 generations
    ranked = controller.run_loop(campaign_id="CMP-0005", generations=2)

    # Verify campaign execution outputs
    assert len(ranked) > 0
    expr, res, score = ranked[0]
    assert expr != ""
    assert res.sharpe == 2.1
    assert score > 0.0

    # Verify repository writes
    with db_manager.connection() as conn:
        hyps = conn.execute("SELECT id FROM hypotheses").fetchall()
        assert len(hyps) >= 2

        exps = conn.execute("SELECT id, status FROM experiments").fetchall()
        assert len(exps) > 0
        assert all(row["status"] == "completed" for row in exps)

        records = learning_repo.get_all_records()
        assert len(records) > 0

    # Verify deterministic output with fixed seed
    generator_1 = LoopHypothesisGenerator(catalog=catalog, seed=42)
    generator_2 = LoopHypothesisGenerator(catalog=catalog, seed=42)
    hyp_1a = generator_1.generate_hypothesis("CMP-0005", "HYP-0001")
    hyp_1b = generator_2.generate_hypothesis("CMP-0005", "HYP-0001")
    assert hyp_1a.datasets == hyp_1b.datasets
    assert hyp_1a.operators == hyp_1b.operators


def test_evaluator_scoring_logic() -> None:
    """Verify loop evaluator computes correct selection scores and ranking."""
    evaluator = LoopEvaluator(existing_expressions=["ts_mean(close, 10)"])
    result = SimulationResult(
        sharpe=1.5,
        fitness=1.2,
        margin=0.05,
        turnover=0.04,
        coverage=0.95,
        simulated_at=datetime.utcnow(),
    )
    score_novel = evaluator.evaluate_candidate("rank(volume)", result)
    score_dup = evaluator.evaluate_candidate("ts_mean(close, 10)", result)

    # The novel expression should have a significantly higher score than duplicate
    assert score_novel > score_dup
