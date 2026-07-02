"""Unit tests for the Mutation Engine subsystem."""

from datetime import datetime

from synthra.core.catalog import DatasetCatalog
from synthra.core.domain import Region, SimulationRequest, SimulationResult, Universe
from synthra.research.mutator import MutationEngine


def test_mutation_engine_generates_variants(catalog: DatasetCatalog) -> None:
    """Verify that mutation engine produces diverse mutated variants."""
    mutator = MutationEngine(catalog=catalog)
    req = SimulationRequest(
        expression="ts_mean(close, 20) / open",
        region=Region.US,
        universe=Universe.TOP2000,
        delay=1,
        decay=0,
        neutralization="SUBINDUSTRY",
    )
    res = SimulationResult(
        sharpe=1.2,
        fitness=1.5,
        margin=0.05,
        turnover=0.1,
        coverage=0.95,
        simulated_at=datetime.utcnow(),
    )

    mutations = mutator.mutate_request(req, res, "pv")
    assert len(mutations) > 0

    expressions = [m.expression for m in mutations]
    neutralizations = [m.neutralization for m in mutations]
    delays = [m.delay for m in mutations]

    # Verify lookback / parameter mutations occurred
    assert any("15" in expr or "25" in expr or "30" in expr for expr in expressions)

    # Verify operator substitution occurred (e.g. ts_mean -> ts_sum or others)
    assert any("ts_sum" in expr or "ts_std_dev" in expr for expr in expressions)

    # Verify dataset field substitution occurred (e.g. open -> vwap, etc.)
    assert any(
        "vwap" in expr or "volume" in expr or "high" in expr for expr in expressions
    )

    # Verify neutralization mutation occurred
    assert "INDUSTRY" in neutralizations

    # Verify delay mutation occurred
    assert 2 in delays

    # Verify rank wrapping mutation occurred
    assert any("rank(ts_mean(" in expr for expr in expressions)
