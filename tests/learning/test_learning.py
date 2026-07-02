"""Exhaustive offline tests for the Learning & Knowledge Engine."""

from datetime import datetime
from unittest.mock import MagicMock


from synthra.core.catalog import DatasetCatalog
from synthra.core.domain import (
    AlphaCandidate,
    Campaign,
    CampaignStatus,
    Experiment,
    Hypothesis,
    HypothesisStatus,
    Region,
    SimulationRequest,
    SimulationResult,
    Universe,
)
from synthra.execution.runner import SimulationRunner
from synthra.learning import (
    ExpressionScorer,
    FeedbackGenerator,
    HistoryTracker,
    HypothesisSelector,
    LearningRecord,
    LearningRepository,
    ResultAnalyzer,
    jaccard_similarity,
    normalize_expression,
)
from synthra.memory import (
    AlphaCandidateRepository,
    CampaignRepository,
    DatabaseManager,
    ExperimentRepository,
    HypothesisRepository,
)
from synthra.research.generator import ExpressionGenerator
from synthra.research.hypothesis import HypothesisGenerator, MockLLMProvider
from synthra.research.mutator import MutationEngine
from synthra.research.orchestrator import ResearchOrchestrator
from synthra.research.planner import Planner
from synthra.research.ranking import CandidateRanker
from synthra.research.validator import Validator

# ---------------------------------------------------------------------------
# Result Analyzer Tests
# ---------------------------------------------------------------------------


def test_result_analyzer_classifies_metrics() -> None:
    """Verify that ResultAnalyzer correctly identifies success/failure reasons."""
    analyzer = ResultAnalyzer()

    # Case 1: Bad stats
    fail_res = SimulationResult(
        sharpe=0.2,
        fitness=0.1,
        margin=-0.02,
        turnover=0.85,
        coverage=0.75,
        simulated_at=datetime.utcnow(),
    )
    failures, successes = analyzer.analyze(fail_res)
    assert "weak Sharpe" in failures
    assert "poor fitness" in failures
    assert "negative margin" in failures
    assert "turnover too high" in failures
    assert "coverage too low" in failures
    assert len(successes) == 0

    # Case 2: Good stats
    pass_res = SimulationResult(
        sharpe=1.8,
        fitness=2.2,
        margin=0.08,
        turnover=0.03,
        coverage=0.98,
        simulated_at=datetime.utcnow(),
    )
    failures, successes = analyzer.analyze(pass_res)
    assert len(failures) == 0
    assert "strong Sharpe" in successes
    assert "excellent fitness" in successes
    assert "high coverage" in successes
    assert "low turnover" in successes


# ---------------------------------------------------------------------------
# Similarity Detection Tests
# ---------------------------------------------------------------------------


def test_expression_normalization() -> None:
    """Verify expression normalizer removes spacing, cased characters, and numbers."""
    expr1 = "ts_mean(close, 20) / open"
    expr2 = "TS_MEAN(  close, 5  ) / open"

    assert normalize_expression(expr1) == "ts_mean(close,#)/open"
    assert normalize_expression(expr2) == "ts_mean(close,#)/open"


def test_jaccard_token_similarity() -> None:
    """Verify Jaccard token similarity behaves correctly over expressions."""
    expr1 = "ts_mean(close, 20) / open"
    expr2 = "ts_mean(close, 10) / open"
    expr3 = "rank(ts_sum(volume, 5))"

    # Minimal difference (only numbers are ignored in tokens) -> High similarity
    sim_12 = jaccard_similarity(expr1, expr2)
    assert sim_12 == 1.0

    # Complete difference -> Low similarity
    sim_13 = jaccard_similarity(expr1, expr3)
    assert sim_13 < 0.2


# ---------------------------------------------------------------------------
# Feedback Mapping Tests
# ---------------------------------------------------------------------------


def test_feedback_generator_creates_records() -> None:
    """Verify FeedbackGenerator maps backtest outcomes to a LearningRecord."""
    generator = FeedbackGenerator()
    req = SimulationRequest(
        expression="ts_mean(close, 20) / open",
        region=Region.US,
        universe=Universe.TOP2000,
        delay=1,
        decay=0,
        neutralization="SUBINDUSTRY",
    )
    res = SimulationResult(
        sharpe=1.5,
        fitness=1.8,
        margin=0.06,
        turnover=0.12,
        coverage=0.97,
        simulated_at=datetime.utcnow(),
    )

    record = generator.generate_record(
        req, res, datasets=["pv"], operators=["ts_mean", "delay"]
    )

    assert isinstance(record, LearningRecord)
    assert record.expression == req.expression
    assert record.datasets == ["pv"]
    assert record.operators == ["ts_mean", "delay"]
    assert record.delay == 1
    assert record.neutralization == "SUBINDUSTRY"
    assert record.universe == "TOP2000"
    assert record.region == "US"
    assert record.sharpe == 1.5
    assert record.fitness == 1.8
    assert record.success is True
    assert len(record.failure_reasons) == 0


# ---------------------------------------------------------------------------
# Selector Tests
# ---------------------------------------------------------------------------


def test_hypothesis_selector_decisions() -> None:
    """Verify HypothesisSelector evaluates records and routes actions correctly."""
    selector = HypothesisSelector()

    # Helper function to generate records
    def make_record(sharpe: float, success: bool) -> LearningRecord:
        return LearningRecord(
            expression="expr",
            datasets=["pv"],
            operators=["ts_mean"],
            delay=1,
            neutralization="SUBINDUSTRY",
            universe="TOP2000",
            region="US",
            sharpe=sharpe,
            fitness=1.0,
            margin=0.05,
            turnover=0.1,
            coverage=0.9,
            success=success,
        )

    # 1. Mutate decision (high Sharpe, successful)
    recs_mutate = [make_record(1.5, True), make_record(1.3, True)]
    assert selector.evaluate_hypothesis(recs_mutate) == "mutate"

    # 2. Retire decision (low Sharpe, failed)
    recs_retire = [make_record(0.2, False)]
    assert selector.evaluate_hypothesis(recs_retire) == "retire"

    # 3. Regenerate decision (moderate Sharpe, mixed success)
    recs_regen = [make_record(0.8, True), make_record(0.9, False)]
    assert selector.evaluate_hypothesis(recs_regen) == "regenerate"


# ---------------------------------------------------------------------------
# Scorer Tests
# ---------------------------------------------------------------------------


def test_expression_scorer_evaluation() -> None:
    """Verify Scorer scores expressions, penalizing similarity to history."""
    rec = LearningRecord(
        expression="ts_mean(close, 20) / open",
        datasets=["pv"],
        operators=["ts_mean"],
        delay=1,
        neutralization="SUBINDUSTRY",
        universe="TOP2000",
        region="US",
        sharpe=1.2,
        fitness=1.5,
        margin=0.05,
        turnover=0.10,
        coverage=0.95,
        success=True,
    )
    scorer = ExpressionScorer(history=[rec])

    res = SimulationResult(
        sharpe=1.4,
        fitness=1.6,
        margin=0.06,
        turnover=0.08,
        coverage=0.96,
        simulated_at=datetime.utcnow(),
    )

    # Score a novel expression (high novelty, no penalty)
    score_novel = scorer.score_expression("rank(ts_sum(volume, 5))", res)

    # Score a highly similar expression (low novelty, high similarity penalty)
    score_similar = scorer.score_expression("ts_mean(close, 10) / open", res)

    assert score_novel > score_similar


# ---------------------------------------------------------------------------
# History Tracker and Repository Tests
# ---------------------------------------------------------------------------


def test_history_tracker_saves_entities(
    db_manager: DatabaseManager,
    campaign_repo: CampaignRepository,
    hypothesis_repo: HypothesisRepository,
    experiment_repo: ExperimentRepository,
    candidate_repo: AlphaCandidateRepository,
) -> None:
    """Verify HistoryTracker persists Campaigns, Hypotheses, Experiments, Candidates."""
    tracker = HistoryTracker(db_manager=db_manager)

    campaign = Campaign(
        id="CMP-0001",
        name="Test",
        region=Region.US,
        universe=Universe.TOP2000,
        budget_limit=100.0,
    )
    tracker.record_campaign(campaign)
    assert campaign_repo.get_by_id("CMP-0001") is not None

    hypothesis = Hypothesis(
        id="HYP-0001",
        campaign_id="CMP-0001",
        rationale="Momentum signals are predictive in price-volume.",
        target_variable="returns",
        datasets=["pv"],
        operators=["ts_mean"],
        status=HypothesisStatus.DRAFT,
    )
    tracker.record_hypothesis(hypothesis)
    assert hypothesis_repo.get_by_id("HYP-0001") is not None

    req = SimulationRequest(
        expression="close",
        region=Region.US,
        universe=Universe.TOP2000,
    )
    experiment = Experiment(
        id="EXP-0001",
        campaign_id="CMP-0001",
        hypothesis_id="HYP-0001",
        expression="close",
        request=req,
    )
    tracker.record_experiment(experiment)
    assert experiment_repo.get_by_id("EXP-0001") is not None

    candidate = AlphaCandidate(
        id="AST-0001",
        experiment_id="EXP-0001",
        hypothesis_id="HYP-0001",
        campaign_id="CMP-0001",
        expression="close",
        result=SimulationResult(
            sharpe=1.0,
            fitness=1.0,
            margin=0.01,
            turnover=0.1,
            coverage=0.9,
            simulated_at=datetime.utcnow(),
        ),
    )
    tracker.record_candidate(candidate)
    assert candidate_repo.get_by_id("AST-0001") is not None


def test_learning_repository_persistence(db_manager: DatabaseManager) -> None:
    """Verify LearningRepository correctly inserts and queries LearningRecords."""
    repo = LearningRepository(db_manager=db_manager)
    record = LearningRecord(
        expression="ts_mean(close, 20)",
        datasets=["pv"],
        operators=["ts_mean"],
        delay=1,
        neutralization="SUBINDUSTRY",
        universe="TOP2000",
        region="US",
        sharpe=1.5,
        fitness=2.0,
        margin=0.05,
        turnover=0.04,
        coverage=0.98,
        success=True,
        failure_reasons=[],
        success_reasons=["strong Sharpe"],
    )

    repo.add_record(record)
    records = repo.get_all_records()
    assert len(records) == 1
    assert records[0].expression == "ts_mean(close, 20)"
    assert records[0].success_reasons == ["strong Sharpe"]


# ---------------------------------------------------------------------------
# Orchestrator Integration Test
# ---------------------------------------------------------------------------


def test_orchestrator_learning_integration(
    db_manager: DatabaseManager,
    campaign_repo: CampaignRepository,
    hypothesis_repo: HypothesisRepository,
    experiment_repo: ExperimentRepository,
    candidate_repo: AlphaCandidateRepository,
    catalog: DatasetCatalog,
) -> None:
    """Verify autonomous campaign loop with full history and learning integration."""
    validator = Validator(catalog=catalog)
    mock_llm = MockLLMProvider()

    tracker = HistoryTracker(db_manager=db_manager)
    feedback_gen = FeedbackGenerator()
    learning_repo = LearningRepository(db_manager=db_manager)

    # Scorer uses a mock/empty history
    scorer = ExpressionScorer(history=[])

    planner = Planner(catalog=catalog)
    hypothesis_gen = HypothesisGenerator(llm_provider=mock_llm)
    expression_gen = ExpressionGenerator(
        llm_provider=mock_llm, catalog=catalog, validator=validator
    )
    mutator = MutationEngine(catalog=catalog)
    ranker = CandidateRanker()

    # Mock SimulationRunner
    mock_sim_runner = MagicMock(spec=SimulationRunner)
    mock_sim_runner.run.return_value = SimulationResult(
        sharpe=1.6,
        fitness=2.2,
        margin=0.07,
        turnover=0.04,
        coverage=0.99,
        simulated_at=datetime.utcnow(),
    )

    orchestrator = ResearchOrchestrator(
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

    campaign = Campaign(
        id="CMP-0001",
        name="Momentum anomaly campaign",
        region=Region.US,
        universe=Universe.TOP2000,
        budget_limit=5000.0,
        status=CampaignStatus.ACTIVE,
        created_at=datetime.utcnow(),
    )

    candidates = orchestrator.execute_campaign(campaign, max_hypotheses_per_task=1)

    assert len(candidates) > 0
    # Ensure history tracker recorded entities
    assert campaign_repo.get_by_id("CMP-0001") is not None
    assert len(learning_repo.get_all_records()) > 0
