"""Ranking modules to prioritize alpha hypotheses before synthesis."""

from typing import List, Optional, Tuple

from synthra.core.catalog import DatasetCatalog
from synthra.core.domain import Campaign
from synthra.research.intelligence.knowledge import KnowledgeBase
from synthra.research.intelligence.reasoning import ReasoningPath


class HypothesisRanker:
    """HypothesisRanker prioritizing reasoning paths before expression generation."""

    def __init__(self, catalog: DatasetCatalog) -> None:
        """Initialize the hypothesis ranker with the shared DatasetCatalog."""
        self.catalog = catalog

    def rank_paths(
        self,
        paths: List[ReasoningPath],
        campaign: Campaign,
        knowledge_base: KnowledgeBase,
        existing_expressions: Optional[List[str]] = None,
    ) -> List[Tuple[ReasoningPath, float]]:
        """Score and sort reasoning paths in descending order of priority."""
        scored: List[Tuple[ReasoningPath, float]] = []
        existing = existing_expressions or []

        for path in paths:
            entry = knowledge_base.get_entry(path.concept)
            if not entry:
                continue

            # 1. Economic Plausibility
            plausibility = entry.confidence

            # 2. Dataset Availability
            ds = self.catalog.get_dataset(path.required_dataset)
            ds_avail = 1.0 if ds else 0.0

            # 3. Historical Novelty
            novelty = 1.0
            if path.candidate_expressions:
                num_new = sum(
                    1 for e in path.candidate_expressions if e not in existing
                )
                novelty = num_new / len(path.candidate_expressions)

            # 4. Estimated Robustness
            robustness = 0.5
            if any(w >= 60 for w in entry.preferred_lookback_windows):
                robustness = 0.8

            # 5. Estimated Complexity
            complexity = 1.0 - (0.02 * len(path.expression_blueprint))

            # 6. Estimated Turnover
            turnover_scores = {"low": 1.0, "medium": 0.7, "high": 0.4}
            turnover = turnover_scores.get(entry.expected_turnover, 0.5)

            # 7. Estimated Correlation
            # Penalize if this concept is already heavily represented in the campaign
            correlation = 1.0
            if any(path.concept.lower() in e.lower() for e in existing):
                correlation = 0.5

            # Calculate weighted sum priority score
            score = (
                1.5 * plausibility
                + 1.0 * ds_avail
                + 1.0 * novelty
                + 0.8 * robustness
                + 0.5 * complexity
                + 0.5 * turnover
                + 0.5 * correlation
            )
            scored.append((path, score))

        # Sort descending by priority score
        return sorted(scored, key=lambda x: x[1], reverse=True)
