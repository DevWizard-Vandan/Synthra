"""Research knowledge base and learning feedback loop definitions."""

from typing import Dict, List, Optional
from pydantic import BaseModel

from synthra.memory import DatabaseManager


class KnowledgeEntry(BaseModel):
    """Encapsulates economic rationale and empirical parameters for an alpha concept."""

    concept: str
    economic_rationale: str
    preferred_datasets: List[str]
    preferred_operators: List[str]
    preferred_lookback_windows: List[int]
    preferred_regions: List[str]
    preferred_universes: List[str]
    known_weaknesses: List[str]
    expected_turnover: str
    expected_decay: str
    preferred_neutralization: str
    confidence: float = 0.5
    successes: int = 0
    failures: int = 0


class KnowledgeBase:
    """Manages quantitative research knowledge and learning feedback loop."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        """Initialize knowledge base and synchronize with persistent storage."""
        self.db_manager = db_manager
        self._init_db()
        self._entries: Dict[str, KnowledgeEntry] = {}
        self._load_defaults()
        self._sync_with_db()

    def _init_db(self) -> None:
        """Ensure the research knowledge table exists in database state."""
        with self.db_manager.transaction() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS research_knowledge (
                    concept TEXT,
                    region TEXT,
                    universe TEXT,
                    confidence REAL,
                    successes INTEGER DEFAULT 0,
                    failures INTEGER DEFAULT 0,
                    PRIMARY KEY (concept, region, universe)
                );
            """)

    def _load_defaults(self) -> None:
        """Populate initial baseline researcher knowledge entries."""
        defaults = [
            KnowledgeEntry(
                concept="Momentum",
                economic_rationale=(
                    "Asset prices tend to persist in their recent direction."
                ),
                preferred_datasets=["pv"],
                preferred_operators=["ts_delta", "delay", "ts_mean"],
                preferred_lookback_windows=[20, 60, 120, 250],
                preferred_regions=["US", "EU", "AP"],
                preferred_universes=["TOP3000", "TOP2000"],
                known_weaknesses=["Momentum crashes during market inflection points."],
                expected_turnover="medium",
                expected_decay="medium",
                preferred_neutralization="SUBINDUSTRY",
            ),
            KnowledgeEntry(
                concept="Mean Reversion",
                economic_rationale=(
                    "Asset prices tend to revert to their historical mean."
                ),
                preferred_datasets=["pv"],
                preferred_operators=["ts_mean", "ts_std_dev", "ts_rank"],
                preferred_lookback_windows=[5, 10, 20],
                preferred_regions=["US", "EU", "AP"],
                preferred_universes=["TOP3000", "TOP2000"],
                known_weaknesses=["Susceptible to value traps and persistent trends."],
                expected_turnover="high",
                expected_decay="fast",
                preferred_neutralization="INDUSTRY",
            ),
            KnowledgeEntry(
                concept="Liquidity",
                economic_rationale="Illiquid assets require a risk premium.",
                preferred_datasets=["pv"],
                preferred_operators=["ts_mean", "rank"],
                preferred_lookback_windows=[20, 60],
                preferred_regions=["US", "EU"],
                preferred_universes=["TOP3000"],
                known_weaknesses=["Transaction costs can completely erode returns."],
                expected_turnover="low",
                expected_decay="slow",
                preferred_neutralization="SUBINDUSTRY",
            ),
            KnowledgeEntry(
                concept="Volatility",
                economic_rationale=(
                    "High volatility assets tend to underperform on a "
                    "risk-adjusted basis."
                ),
                preferred_datasets=["pv"],
                preferred_operators=["ts_std_dev", "ts_max", "ts_min"],
                preferred_lookback_windows=[20, 60],
                preferred_regions=["US", "EU"],
                preferred_universes=["TOP3000"],
                known_weaknesses=["Can underperform during sudden market rallies."],
                expected_turnover="medium",
                expected_decay="slow",
                preferred_neutralization="SUBINDUSTRY",
            ),
            KnowledgeEntry(
                concept="Quality",
                economic_rationale=(
                    "High-quality companies outperform low-quality peers."
                ),
                preferred_datasets=["fundamentals"],
                preferred_operators=["ts_mean", "rank"],
                preferred_lookback_windows=[4, 8, 12],
                preferred_regions=["US", "EU"],
                preferred_universes=["TOP3000", "TOP2000"],
                known_weaknesses=[
                    "Underperforms during junk rallies and credit expansions."
                ],
                expected_turnover="low",
                expected_decay="slow",
                preferred_neutralization="INDUSTRY",
            ),
            KnowledgeEntry(
                concept="Value",
                economic_rationale=(
                    "Cheap assets tend to outperform expensive assets "
                    "relative to fundamentals."
                ),
                preferred_datasets=["fundamentals"],
                preferred_operators=["ts_mean", "rank"],
                preferred_lookback_windows=[4, 12],
                preferred_regions=["US", "EU", "AP"],
                preferred_universes=["TOP3000", "TOP2000"],
                known_weaknesses=[
                    "Value traps where cheap assets remain cheap forever."
                ],
                expected_turnover="low",
                expected_decay="slow",
                preferred_neutralization="SUBINDUSTRY",
            ),
            KnowledgeEntry(
                concept="Growth",
                economic_rationale=(
                    "Companies showing strong growth metrics persist " "in expansion."
                ),
                preferred_datasets=["fundamentals"],
                preferred_operators=["ts_delta", "rank"],
                preferred_lookback_windows=[4, 8],
                preferred_regions=["US", "EU"],
                preferred_universes=["TOP3000"],
                known_weaknesses=[
                    "High growth stock multiples are sensitive to rate hikes."
                ],
                expected_turnover="medium",
                expected_decay="slow",
                preferred_neutralization="SUBINDUSTRY",
            ),
            KnowledgeEntry(
                concept="Analyst Revisions",
                economic_rationale=(
                    "Changes in analyst target prices carry " "predictive power."
                ),
                preferred_datasets=["analyst"],
                preferred_operators=["ts_delta", "ts_mean"],
                preferred_lookback_windows=[10, 30, 90],
                preferred_regions=["US", "EU", "AP"],
                preferred_universes=["TOP3000"],
                known_weaknesses=[
                    "Analysts can be slow to update forecasts behind price shifts."
                ],
                expected_turnover="medium",
                expected_decay="medium",
                preferred_neutralization="SUBINDUSTRY",
            ),
            KnowledgeEntry(
                concept="Earnings Drift",
                economic_rationale=(
                    "Post-earnings announcement drift represents slow "
                    "information digestion."
                ),
                preferred_datasets=["fundamentals", "analyst"],
                preferred_operators=["ts_delta", "delay"],
                preferred_lookback_windows=[1, 4],
                preferred_regions=["US", "EU"],
                preferred_universes=["TOP3000", "TOP2000"],
                known_weaknesses=["Earnings announcement days are highly volatile."],
                expected_turnover="medium",
                expected_decay="medium",
                preferred_neutralization="SUBINDUSTRY",
            ),
            KnowledgeEntry(
                concept="Risk Premia",
                economic_rationale=(
                    "Systematic risk exposure demands premium compensation."
                ),
                preferred_datasets=["pv"],
                preferred_operators=["ts_mean", "ts_std_dev"],
                preferred_lookback_windows=[60, 250],
                preferred_regions=["US", "EU", "AP"],
                preferred_universes=["TOP3000", "TOP2000"],
                known_weaknesses=["Can experience prolonged periods of drawdown."],
                expected_turnover="low",
                expected_decay="slow",
                preferred_neutralization="SUBINDUSTRY",
            ),
            KnowledgeEntry(
                concept="Seasonality",
                economic_rationale=(
                    "Calendar-based price trends persist due to " "structural flows."
                ),
                preferred_datasets=["pv"],
                preferred_operators=["delay", "ts_mean"],
                preferred_lookback_windows=[5, 20, 250],
                preferred_regions=["US", "EU", "AP"],
                preferred_universes=["TOP3000"],
                known_weaknesses=["Seasonal patterns can shift or break completely."],
                expected_turnover="high",
                expected_decay="fast",
                preferred_neutralization="INDUSTRY",
            ),
            KnowledgeEntry(
                concept="Volume Shock",
                economic_rationale=(
                    "Abnormal trading volume signals institutional " "repositioning."
                ),
                preferred_datasets=["pv"],
                preferred_operators=["ts_mean", "ts_std_dev"],
                preferred_lookback_windows=[5, 20],
                preferred_regions=["US", "EU", "AP"],
                preferred_universes=["TOP3000"],
                known_weaknesses=["Subject to high market noise and fake breakouts."],
                expected_turnover="high",
                expected_decay="fast",
                preferred_neutralization="SUBINDUSTRY",
            ),
            KnowledgeEntry(
                concept="News/Sentiment",
                economic_rationale=(
                    "Media coverage and sentiment drive short-term price "
                    "adjustments."
                ),
                preferred_datasets=["sentiment"],
                preferred_operators=["ts_mean", "decay"],
                preferred_lookback_windows=[1, 3, 5],
                preferred_regions=["US", "EU"],
                preferred_universes=["TOP3000"],
                known_weaknesses=["High noise-to-signal ratio and fast decay."],
                expected_turnover="high",
                expected_decay="fast",
                preferred_neutralization="SUBINDUSTRY",
            ),
        ]
        for entry in defaults:
            self._entries[entry.concept] = entry

    def _sync_with_db(self) -> None:
        """Load saved confidence, successes, and failures from the database."""
        with self.db_manager.connection() as conn:
            rows = conn.execute("""
                SELECT concept, region, universe, confidence, successes, failures
                FROM research_knowledge;
                """).fetchall()
            for row in rows:
                concept = row["concept"]
                if concept in self._entries:
                    self._entries[concept].confidence = row["confidence"]
                    self._entries[concept].successes = row["successes"]
                    self._entries[concept].failures = row["failures"]

    def get_entries(self) -> List[KnowledgeEntry]:
        """Return all current alpha concept entries in the knowledge base."""
        return list(self._entries.values())

    def get_entry(self, concept: str) -> Optional[KnowledgeEntry]:
        """Retrieve a specific alpha concept entry."""
        return self._entries.get(concept)

    def record_feedback(
        self, concept: str, region: str, universe: str, success: bool
    ) -> None:
        """Update confidence and success/failure statistics based on outcomes."""
        entry = self._entries.get(concept)
        if not entry:
            return

        with self.db_manager.connection() as conn:
            row = conn.execute(
                """
                SELECT confidence, successes, failures FROM research_knowledge
                WHERE concept = ? AND region = ? AND universe = ?;
                """,
                (concept, region, universe),
            ).fetchone()

        if row:
            confidence = row["confidence"]
            successes = row["successes"]
            failures = row["failures"]
        else:
            confidence = entry.confidence
            successes = 0
            failures = 0

        delta = 0.05
        if success:
            confidence = min(1.0, confidence + delta)
            successes += 1
        else:
            confidence = max(0.0, confidence - delta)
            failures += 1

        with self.db_manager.transaction() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO research_knowledge (
                    concept, region, universe, confidence, successes, failures
                ) VALUES (?, ?, ?, ?, ?, ?);
                """,
                (concept, region, universe, confidence, successes, failures),
            )

        entry.confidence = confidence
        entry.successes = successes
        entry.failures = failures
