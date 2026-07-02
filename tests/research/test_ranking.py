"""Unit tests for the Candidate Ranker subsystem."""

from datetime import datetime

from synthra.core.domain import AlphaCandidate, SimulationResult
from synthra.research.ranking import CandidateRanker, RankingWeights


def test_candidate_ranker_scores_and_sorts() -> None:
    """Verify that candidate ranker scores and sorts candidates in descending order."""
    ranker = CandidateRanker()

    cand1 = AlphaCandidate(
        id="AST-0001",
        experiment_id="EXP-0001",
        hypothesis_id="HYP-0001",
        campaign_id="CMP-0001",
        expression="ts_mean(close, 20) / open",
        result=SimulationResult(
            sharpe=1.5,
            fitness=2.0,
            margin=0.08,
            turnover=0.05,
            coverage=0.98,
            simulated_at=datetime.utcnow(),
        ),
    )

    cand2 = AlphaCandidate(
        id="AST-0002",
        experiment_id="EXP-0002",
        hypothesis_id="HYP-0001",
        campaign_id="CMP-0001",
        expression="ts_sum(volume, 5)",
        result=SimulationResult(
            sharpe=0.5,
            fitness=0.6,
            margin=0.02,
            turnover=0.3,
            coverage=0.90,
            simulated_at=datetime.utcnow(),
        ),
    )

    ranked = ranker.rank_candidates([cand2, cand1])
    assert len(ranked) == 2

    # cand1 has much higher Sharpe/Fitness and lower turnover, so it should rank first
    first_candidate, first_score = ranked[0]
    second_candidate, second_score = ranked[1]

    assert first_candidate.id == "AST-0001"
    assert second_candidate.id == "AST-0002"
    assert first_score > second_score


def test_custom_ranking_weights() -> None:
    """Verify that ranker respects custom/altered metric weighting."""
    # Alter weights to heavily penalize high turnover and prioritize margin
    weights = RankingWeights(sharpe=0.5, fitness=0.5, margin=2.0, turnover=-2.0)
    ranker = CandidateRanker(weights=weights)

    cand = AlphaCandidate(
        id="AST-0001",
        experiment_id="EXP-0001",
        hypothesis_id="HYP-0001",
        campaign_id="CMP-0001",
        expression="expr",
        result=SimulationResult(
            sharpe=1.0,
            fitness=1.0,
            margin=0.10,
            turnover=0.5,
            coverage=0.90,
            simulated_at=datetime.utcnow(),
        ),
    )

    # Score calculation: 0.5*1.0 + 0.5*1.0 + 2.0*0.10 - 2.0*0.5 + 0.5*0.90
    expected = 0.5 + 0.5 + 0.20 - 1.0 + 0.45
    assert abs(ranker.score_candidate(cand) - expected) < 1e-6
