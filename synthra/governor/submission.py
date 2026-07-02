"""Submission queue persisting approved candidates to SQLite."""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from synthra.memory import DatabaseManager


class QueuedCandidate(BaseModel):
    """Represents an alpha candidate queued for submission."""

    model_config = ConfigDict(
        frozen=True,
        strict=True,
    )

    candidate_id: str
    campaign_id: str
    hypothesis_id: str
    expression: str
    metrics: Dict[str, Any]
    lineage: Optional[Dict[str, Any]] = None
    generation: int = 0
    reason_selected: str = "approved"
    queued_at: datetime = Field(default_factory=datetime.utcnow)


class SubmissionQueue:
    """Handles persistence of candidate queue records to SQLite database."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        """Initialize database schemas for submission queue."""
        self.db_manager = db_manager
        self._init_table()

    def _init_table(self) -> None:
        """Create the submission queue table if it does not exist."""
        with self.db_manager.transaction() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS submission_queue (
                    candidate_id TEXT PRIMARY KEY,
                    campaign_id TEXT NOT NULL,
                    hypothesis_id TEXT NOT NULL,
                    expression TEXT NOT NULL,
                    metrics TEXT NOT NULL,
                    lineage TEXT,
                    generation INTEGER NOT NULL,
                    reason_selected TEXT NOT NULL,
                    queued_at TEXT NOT NULL
                );
            """)

    def enqueue(self, candidate: QueuedCandidate) -> None:
        """Add a candidate to the SQLite submission queue."""
        with self.db_manager.transaction() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO submission_queue (
                    candidate_id, campaign_id, hypothesis_id, expression,
                    metrics, lineage, generation, reason_selected, queued_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
                (
                    candidate.candidate_id,
                    candidate.campaign_id,
                    candidate.hypothesis_id,
                    candidate.expression,
                    json.dumps(candidate.metrics),
                    json.dumps(candidate.lineage) if candidate.lineage else None,
                    candidate.generation,
                    candidate.reason_selected,
                    candidate.queued_at.isoformat(),
                ),
            )

    def dequeue(self) -> Optional[QueuedCandidate]:
        """Remove and return the oldest queued candidate (FIFO)."""
        with self.db_manager.transaction() as conn:
            row = conn.execute(
                "SELECT * FROM submission_queue ORDER BY queued_at ASC LIMIT 1;"
            ).fetchone()
            if not row:
                return None

            candidate = QueuedCandidate(
                candidate_id=row["candidate_id"],
                campaign_id=row["campaign_id"],
                hypothesis_id=row["hypothesis_id"],
                expression=row["expression"],
                metrics=json.loads(row["metrics"]),
                lineage=json.loads(row["lineage"]) if row["lineage"] else None,
                generation=row["generation"],
                reason_selected=row["reason_selected"],
                queued_at=datetime.fromisoformat(row["queued_at"]),
            )

            conn.execute(
                "DELETE FROM submission_queue WHERE candidate_id = ?;",
                (row["candidate_id"],),
            )
            return candidate

    def get_all(self) -> List[QueuedCandidate]:
        """Query and return all currently enqueued candidates."""
        with self.db_manager.connection() as conn:
            rows = conn.execute(
                "SELECT * FROM submission_queue ORDER BY queued_at ASC;"
            ).fetchall()
            candidates = []
            for row in rows:
                candidates.append(
                    QueuedCandidate(
                        candidate_id=row["candidate_id"],
                        campaign_id=row["campaign_id"],
                        hypothesis_id=row["hypothesis_id"],
                        expression=row["expression"],
                        metrics=json.loads(row["metrics"]),
                        lineage=json.loads(row["lineage"]) if row["lineage"] else None,
                        generation=row["generation"],
                        reason_selected=row["reason_selected"],
                        queued_at=datetime.fromisoformat(row["queued_at"]),
                    )
                )
            return candidates

    def size(self) -> int:
        """Return the current number of enqueued candidates."""
        with self.db_manager.connection() as conn:
            row = conn.execute("SELECT COUNT(*) FROM submission_queue;").fetchone()
            return int(row[0]) if row else 0
