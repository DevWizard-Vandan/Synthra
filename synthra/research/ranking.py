"""Ranking subsystem to score and sort alpha candidates."""

from typing import List, Tuple
from pydantic import BaseModel, Field

from synthra.core.domain import AlphaCandidate


class RankingWeights(BaseModel):
    """Configurable weights used to score candidate alpha strategies."""

    sharpe: float = Field(default=1.0)
    fitness: float = Field(default=1.0)
    margin: float = Field(default=0.5)
    turnover: float = Field(default=-0.5)  # Less turnover is better
    coverage: float = Field(default=0.5)
    correlation_penalty: float = Field(default=-0.5)


class CandidateRanker:
    """CandidateRanker scoring alpha candidates against performance weights."""

    def __init__(self, weights: RankingWeights | None = None) -> None:
        """Initialize with configurable ranking weights."""
        self.weights = weights or RankingWeights()

    def score_candidate(self, candidate: AlphaCandidate) -> float:
        """Compute a unified performance score for a candidate alpha."""
        res = candidate.result

        score = (
            self.weights.sharpe * res.sharpe
            + self.weights.fitness * res.fitness
            + self.weights.margin * res.margin
            + self.weights.turnover * res.turnover
            + self.weights.coverage * res.coverage
            # Placeholder correlation score: assume a baseline average of 0.0
            + self.weights.correlation_penalty * 0.0
        )
        return score

    def rank_candidates(
        self, candidates: List[AlphaCandidate]
    ) -> List[Tuple[AlphaCandidate, float]]:
        """Score, sort, and return candidates in descending order of performance."""
        scored = [(c, self.score_candidate(c)) for c in candidates]
        return sorted(scored, key=lambda x: x[1], reverse=True)
