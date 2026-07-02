"""Evolution strategies managing candidate selection routines."""

import random
from typing import Any, List, Tuple


class EvolutionStrategies:
    """Encapsulates evolution candidate selection algorithms."""

    @staticmethod
    def select_elitism(candidates: List[Tuple[Any, float]], k: int) -> List[Any]:
        """Elitism: select the top k candidates by score."""
        sorted_cands = sorted(candidates, key=lambda x: x[1], reverse=True)
        return [c for c, _ in sorted_cands[:k]]

    @staticmethod
    def select_tournament(
        candidates: List[Tuple[Any, float]], k: int, tournament_size: int = 3
    ) -> List[Any]:
        """Tournament selection: run local tournaments to select candidates."""
        if not candidates:
            return []
        selected = []
        for _ in range(k):
            tournament = random.sample(
                candidates, min(tournament_size, len(candidates))
            )
            winner = max(tournament, key=lambda x: x[1])
            selected.append(winner[0])
        return selected

    @staticmethod
    def select_epsilon_greedy(
        candidates: List[Tuple[Any, float]], k: int, epsilon: float = 0.2
    ) -> List[Any]:
        """Epsilon-greedy selection combining exploitation and random exploration."""
        if not candidates:
            return []
        selected = []
        sorted_cands = sorted(candidates, key=lambda x: x[1], reverse=True)

        for _ in range(k):
            if random.random() < epsilon:
                selected.append(random.choice(candidates)[0])
            else:
                for cand, _ in sorted_cands:
                    if cand not in selected:
                        selected.append(cand)
                        break
                else:
                    selected.append(random.choice(candidates)[0])
        return selected

    @staticmethod
    def select_beam_search(
        candidates: List[Tuple[Any, float]], beam_width: int
    ) -> List[Any]:
        """Beam search: keeps only the top beam_width candidates."""
        return EvolutionStrategies.select_elitism(candidates, beam_width)
