"""Exhaustive offline tests for the Research Evolution Engine."""

from datetime import datetime
from pathlib import Path

from synthra.core.catalog import DatasetCatalog
from synthra.core.domain import Region, SimulationRequest, SimulationResult, Universe
from synthra.memory import DatabaseManager
from synthra.research.evolution import (
    AdaptiveExplorer,
    CampaignEvolutionStats,
    EvolutionFeedback,
    EvolutionStrategies,
    LineageNode,
    LineageTracker,
    NoveltyDetector,
    SelectionEngine,
)
from synthra.research.mutator import MutationEngine

# ---------------------------------------------------------------------------
# Mutation Correctness Tests
# ---------------------------------------------------------------------------


def test_mutation_engine_advanced_strategies(catalog: DatasetCatalog) -> None:
    """Verify that MutationEngine yields nested, scale, and winsorize variants."""
    mutator = MutationEngine(catalog=catalog)
    req = SimulationRequest(
        expression="ts_mean(close, 20)",
        region=Region.US,
        universe=Universe.TOP2000,
        delay=1,
        decay=0,
        neutralization="SUBINDUSTRY",
    )
    res = SimulationResult(
        sharpe=1.5,
        fitness=2.0,
        margin=0.06,
        turnover=0.1,
        coverage=0.95,
        simulated_at=datetime.utcnow(),
    )

    mutations = mutator.mutate_request(req, res, dataset_name="pv")
    expressions = [m.expression for m in mutations]

    # Verify winsorization wrapper mutation
    assert any("winsorize(" in expr for expr in expressions)

    # Verify scale wrapper mutation
    assert any("scale(" in expr for expr in expressions)

    # Verify window tuning parameter adjustments (e.g. 20 -> 15 or 25)
    assert any("25" in expr or "15" in expr for expr in expressions)

    # Verify nested expression wrapping (e.g. ts_delta(ts_mean(...)))
    assert any("ts_delta(ts_mean(" in expr for expr in expressions)


# ---------------------------------------------------------------------------
# Lineage Tests
# ---------------------------------------------------------------------------


def test_lineage_tracker_node_resolution(tmp_path: Path) -> None:
    """Verify LineageTracker records parent/child relationships and generation."""
    db_file = tmp_path / "test_lineage.db"
    db_manager = DatabaseManager(str(db_file))
    tracker = LineageTracker(db_manager=db_manager)

    parent_expr = "ts_mean(close, 20)"
    child_expr = "rank(ts_mean(close, 20))"

    # Record parent node
    parent_node = LineageNode(
        expression=parent_expr,
        parent_id=None,
        generation=0,
        mutation_type=None,
        campaign_id="CMP-0001",
        hypothesis_id="HYP-0001",
        origin="generated",
    )
    tracker.record_node(parent_node)

    # Record child node
    child_node = LineageNode(
        expression=child_expr,
        parent_id=parent_expr,
        generation=parent_node.generation + 1,
        mutation_type="ranking_insertion",
        campaign_id="CMP-0001",
        hypothesis_id="HYP-0001",
        origin="mutated",
    )
    tracker.record_node(child_node)

    # Assert recovery
    recovered_child = tracker.get_node(child_expr)
    assert recovered_child is not None
    assert recovered_child.parent_id == parent_expr
    assert recovered_child.generation == 1
    assert recovered_child.mutation_type == "ranking_insertion"


# ---------------------------------------------------------------------------
# Novelty Detection Tests
# ---------------------------------------------------------------------------


def test_novelty_detector_rules() -> None:
    """Verify duplicate, AST equivalence, and fingerprint collision checks."""
    detector = NoveltyDetector()

    expr1 = "ts_mean(close, 20) / open"
    expr2 = "ts_mean(close, 10) / open"  # AST equivalent (numbers ignored)
    expr3 = "rank(ts_sum(volume, 5))"  # structurally novel

    detector.add_expression(expr1)

    # 1. Exact string duplicate -> Not novel
    assert not detector.is_novel(expr1)

    # 2. AST equivalent expression (different lookback window only) -> Not novel
    assert not detector.is_novel(expr2)

    # 3. Structurally diverse expression -> Novel
    assert detector.is_novel(expr3)


# ---------------------------------------------------------------------------
# Selection Engine Tests
# ---------------------------------------------------------------------------


def test_selection_engine_scores() -> None:
    """Verify that SelectionEngine factors complexity and stability into total score."""
    engine = SelectionEngine(
        complexity_penalty_weight=0.1,
        correlation_penalty_weight=0.5,
    )

    res = SimulationResult(
        sharpe=1.5,
        fitness=2.0,
        margin=0.06,
        turnover=0.1,
        coverage=0.95,
        simulated_at=datetime.utcnow(),
    )

    # Base candidate score
    score_simple = engine.calculate_score(
        expression="close",
        result=res,
        complexity=1,
        correlation=0.1,
    )

    # High complexity & high correlation candidate score
    score_complex = engine.calculate_score(
        expression="delay(ts_std_dev(ts_mean(close, 20), 5), 1)",
        result=res,
        complexity=5,
        correlation=0.8,
    )

    # Simple expression should score higher due to complexity/correlation penalties
    assert score_simple > score_complex


# ---------------------------------------------------------------------------
# Evolution Strategies Tests
# ---------------------------------------------------------------------------


def test_evolution_strategies_selections() -> None:
    """Verify elitism, tournament, and epsilon-greedy search select correctly."""
    candidates = [
        ("A", 1.0),
        ("B", 2.5),  # Best
        ("C", 1.8),
        ("D", 0.5),
    ]

    # Elitism selects top k
    elite = EvolutionStrategies.select_elitism(candidates, k=2)
    assert "B" in elite
    assert "C" in elite
    assert len(elite) == 2

    # Tournament selection
    tournament = EvolutionStrategies.select_tournament(
        candidates, k=1, tournament_size=3
    )
    assert len(tournament) == 1
    assert tournament[0] in {"A", "B", "C", "D"}

    # Epsilon-greedy selection
    egreedy = EvolutionStrategies.select_epsilon_greedy(candidates, k=2, epsilon=0.0)
    # Epsilon 0.0 forces purely greedy exploit -> picks best A/B/C/D
    assert egreedy[0] == "B"


# ---------------------------------------------------------------------------
# Adaptive Exploration Tests
# ---------------------------------------------------------------------------


def test_adaptive_explorer_stagnation() -> None:
    """Verify AdaptiveExplorer shifts search configs if Sharpe progress stagnates."""
    explorer = AdaptiveExplorer(stagnation_limit=2)

    # Round 1: Improvement -> no stagnation
    explorer.update(1.2)
    assert explorer.stagnation_count == 0
    assert explorer.epsilon == 0.1

    # Round 2: Stagnates
    explorer.update(1.2)
    assert explorer.stagnation_count == 1

    # Round 3: Stagnates beyond limit -> triggers adaptation
    explorer.update(1.2)
    assert explorer.stagnation_count == 2
    # Epsilon search rate increases
    assert explorer.epsilon > 0.1
    # Advanced operators are added to mutation active list
    assert "nested" in explorer.active_mutation_operators


# ---------------------------------------------------------------------------
# Feedback & Stats Tests
# ---------------------------------------------------------------------------


def test_evolution_feedback_metrics() -> None:
    """Verify recording of success/failure feedback stats."""
    feedback = EvolutionFeedback()

    # Success mutation with improved metrics
    feedback.record_mutation_feedback(parent_sharpe=1.0, child_sharpe=1.5, success=True)
    # Failing mutation with reduced metrics
    feedback.record_mutation_feedback(
        parent_sharpe=1.2, child_sharpe=0.8, success=False
    )

    assert feedback.accepted_mutations == 1
    assert feedback.rejected_mutations == 1
    assert feedback.improved_metrics == 1
    assert feedback.failed_metrics == 1


def test_campaign_evolution_statistics() -> None:
    """Verify campaign evolution stats aggregations and success rate."""
    stats = CampaignEvolutionStats()

    stats.record_mutation(
        mutation_type="parameter_tuning", success=True, improvement=0.2
    )
    stats.record_mutation(mutation_type="operator_replacement", success=False)

    assert stats.mutation_attempts == 2
    assert stats.mutation_successes == 1
    assert stats.mutation_success_rate == 0.5
    assert stats.average_improvement == 0.2
