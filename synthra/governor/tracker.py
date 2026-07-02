"""Progress tracker monitoring live campaign stats and performance metrics."""

from datetime import datetime
from threading import Lock
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field


class CampaignProgress(BaseModel):
    """Data container representing live metrics and states for a campaign."""

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        strict=True,
    )

    campaign_id: str
    started_at: Optional[datetime] = None
    concluded_at: Optional[datetime] = None
    current_stage: str = Field(default="queued")
    queue_size: int = Field(default=0)
    completed_simulations: int = Field(default=0)
    successful_simulations: int = Field(default=0)
    failed_simulations: int = Field(default=0)
    generated_hypotheses: int = Field(default=0)
    generated_expressions: int = Field(default=0)
    generated_candidates: int = Field(default=0)
    approved_candidates: int = Field(default=0)
    submitted_candidates: int = Field(default=0)
    current_best_sharpe: float = Field(default=0.0)
    current_best_fitness: float = Field(default=0.0)
    current_best_score: float = Field(default=0.0)

    @property
    def uptime(self) -> float:
        """Calculate total running duration in seconds."""
        if not self.started_at:
            return 0.0
        end_time = self.concluded_at or datetime.utcnow()
        return (end_time - self.started_at).total_seconds()


class CampaignProgressTracker:
    """Thread-safe manager for tracking progress across active campaigns."""

    def __init__(self) -> None:
        """Initialize progress tracker with lock and storage."""
        self._lock = Lock()
        self._progress_records: Dict[str, CampaignProgress] = {}

    def init_campaign(self, campaign_id: str) -> None:
        """Initialize progress logging structure for a campaign."""
        with self._lock:
            self._progress_records[campaign_id] = CampaignProgress(
                campaign_id=campaign_id
            )

    def get_progress(self, campaign_id: str) -> Optional[CampaignProgress]:
        """Retrieve progress record for a campaign."""
        with self._lock:
            return self._progress_records.get(campaign_id)

    def update_metrics(self, campaign_id: str, **kwargs: Any) -> None:
        """Update metrics attributes of a campaign's progress record."""
        with self._lock:
            record = self._progress_records.get(campaign_id)
            if not record:
                record = CampaignProgress(campaign_id=campaign_id)
                self._progress_records[campaign_id] = record

            # Update fields safely
            for key, val in kwargs.items():
                if hasattr(record, key):
                    setattr(record, key, val)
