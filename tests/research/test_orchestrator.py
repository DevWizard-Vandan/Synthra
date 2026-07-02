"""Unit tests for the Research Orchestrator subsystem."""

from datetime import datetime
from unittest.mock import MagicMock

from synthra.core.catalog import DatasetCatalog
from synthra.core.domain import (
    Campaign,
    CampaignStatus,
    Region,
    SimulationResult,
    Universe,
)
from synthra.execution.runner import SimulationRunner
from synthra.research.generator import ExpressionGenerator
from synthra.research.hypothesis import HypothesisGenerator, MockLLMProvider
from synthra.research.mutator import MutationEngine
from synthra.research.orchestrator import ResearchOrchestrator
from synthra.research.planner import Planner
from synthra.research.ranking import CandidateRanker
from synthra.research.validator import Validator


def test_orchestrator_executes_autonomous_loop(
    catalog: DatasetCatalog, validator: Validator, mock_llm: MockLLMProvider
) -> None:
    """Verify that orchestrator executes the loop from Campaign to ranked candidates."""
    # 1. Initialize all subcomponents
    planner = Planner(catalog=catalog)
    hypothesis_gen = HypothesisGenerator(llm_provider=mock_llm)
    expression_gen = ExpressionGenerator(
        llm_provider=mock_llm, catalog=catalog, validator=validator
    )
    mutator = MutationEngine(catalog=catalog)
    ranker = CandidateRanker()

    # 2. Mock SimulationRunner
    mock_sim_runner = MagicMock(spec=SimulationRunner)
    mock_sim_runner.run.return_value = SimulationResult(
        sharpe=1.5,
        fitness=2.2,
        margin=0.07,
        turnover=0.04,
        coverage=0.99,
        simulated_at=datetime.utcnow(),
    )

    # 3. Create Orchestrator
    orchestrator = ResearchOrchestrator(
        planner=planner,
        hypothesis_generator=hypothesis_gen,
        expression_generator=expression_gen,
        validator=validator,
        mutation_engine=mutator,
        simulation_runner=mock_sim_runner,
        ranker=ranker,
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

    # 4. Run loop
    candidates = orchestrator.execute_campaign(campaign, max_hypotheses_per_task=1)

    # 5. Assert results
    # Since MockLLM yields 2 expressions and generates mutations, we expect candidates
    assert len(candidates) > 0
    assert mock_sim_runner.run.called is True

    # Validate that returned candidates are properly structured and ranked
    for i in range(len(candidates) - 1):
        score_curr = ranker.score_candidate(candidates[i])
        score_next = ranker.score_candidate(candidates[i + 1])
        assert score_curr >= score_next  # Properly ranked descending

    # Ensure all candidates are bound contextually to campaign/hypothesis/experiments
    for cand in candidates:
        assert cand.campaign_id == campaign.id
        assert cand.id.startswith("AST-")
        assert cand.experiment_id.startswith("EXP-")
        assert cand.hypothesis_id.startswith("HYP-")
        assert cand.expression != ""
