"""Event models and event bus for broadcasting scheduler and campaign actions."""

from datetime import datetime
from typing import Callable, List
from pydantic import BaseModel, ConfigDict, Field


class CampaignEvent(BaseModel):
    """Base event model for all broadcasted campaign actions."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
    )

    campaign_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class CampaignStarted(CampaignEvent):
    """Broadcasted when a campaign transitions to the running state."""

    pass


class CampaignPaused(CampaignEvent):
    """Broadcasted when an active campaign is paused."""

    pass


class CampaignResumed(CampaignEvent):
    """Broadcasted when a paused campaign is resumed."""

    pass


class CampaignCompleted(CampaignEvent):
    """Broadcasted when a campaign completes successfully."""

    pass


class CampaignCancelled(CampaignEvent):
    """Broadcasted when a campaign is manually cancelled."""

    pass


class SimulationStarted(CampaignEvent):
    """Broadcasted when a new expression backtest simulation begins."""

    expression: str
    dataset: str


class SimulationCompleted(CampaignEvent):
    """Broadcasted when a simulation backtest finishes successfully."""

    expression: str
    sharpe: float
    fitness: float


class SimulationFailed(CampaignEvent):
    """Broadcasted when a simulation backtest encounters an error."""

    expression: str
    error_message: str


class HypothesisGenerated(CampaignEvent):
    """Broadcasted when a new hypothesis is successfully generated."""

    hypothesis_id: str
    rationale: str


class CandidateApproved(CampaignEvent):
    """Broadcasted when an alpha candidate passes selection thresholds."""

    candidate_id: str
    expression: str
    sharpe: float


class CandidateRejected(CampaignEvent):
    """Broadcasted when an alpha candidate is rejected by selectors."""

    expression: str
    reason: str


class LearningRecorded(CampaignEvent):
    """Broadcasted when feedback is persisted to the learning repo."""

    expression: str
    success: bool
    sharpe: float


class CampaignEventBus:
    """Thread-safe event bus for registering listeners and publishing events."""

    def __init__(self) -> None:
        """Initialize event bus with empty list of listeners."""
        self._listeners: List[Callable[[CampaignEvent], None]] = []

    def subscribe(self, listener: Callable[[CampaignEvent], None]) -> None:
        """Register a callback function to listen for published events."""
        self._listeners.append(listener)

    def publish(self, event: CampaignEvent) -> None:
        """Broadcast an event to all registered listener callbacks."""
        for listener in self._listeners:
            try:
                listener(event)
            except Exception:
                # Keep event distribution isolated from listener callback bugs
                pass
