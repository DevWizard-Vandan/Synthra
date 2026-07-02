"""Research Engine package for SYNTHRA.

Exposes the planner, hypothesis generator, expression generator, mutator,
validator, ranker, and orchestrator subsystems.
"""

from synthra.research.generator import ExpressionGenerator
from synthra.research.hypothesis import (
    HypothesisGenerator,
    ILLMProvider,
    MockLLMProvider,
    StructuredHypothesis,
)
from synthra.research.mutator import MutationEngine
from synthra.research.orchestrator import ResearchOrchestrator
from synthra.research.planner import Planner, ResearchTask
from synthra.research.ranking import CandidateRanker, RankingWeights
from synthra.research.validator import Validator

__all__ = [
    "ExpressionGenerator",
    "HypothesisGenerator",
    "ILLMProvider",
    "MockLLMProvider",
    "StructuredHypothesis",
    "MutationEngine",
    "ResearchOrchestrator",
    "Planner",
    "ResearchTask",
    "CandidateRanker",
    "RankingWeights",
    "Validator",
]
