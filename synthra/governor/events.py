"""Event models and event bus for broadcasting scheduler and campaign actions."""

from datetime import datetime
from typing import Any, Callable, Dict, List
from pydantic import BaseModel, ConfigDict, Field


class Event(BaseModel):
    """Base event model for all broadcasted system and campaign events."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
    )

    timestamp: datetime = Field(default_factory=datetime.utcnow)


class CampaignEvent(Event):
    """Base event model for all broadcasted campaign actions."""

    campaign_id: str


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


class ExpressionGenerated(CampaignEvent):
    """Broadcasted when a new expression is generated."""

    expression: str


class CandidateQueued(CampaignEvent):
    """Broadcasted when a candidate is enqueued in the submission queue."""

    candidate_id: str
    expression: str


class MutationCreated(CampaignEvent):
    """Broadcasted when a mutation variant is created."""

    expression: str
    mutation_type: str


class LearningUpdated(CampaignEvent):
    """Broadcasted when the learning model receives updated metrics."""

    expression: str
    metrics: Dict[str, Any]


class CampaignCheckpointed(CampaignEvent):
    """Broadcasted when a campaign progress checkpoint is saved."""

    task_index: int
    generation: int


class CampaignRecovered(CampaignEvent):
    """Broadcasted when a campaign is successfully recovered from a checkpoint."""

    task_index: int
    generation: int


class CampaignFinished(CampaignEvent):
    """Broadcasted when a campaign concludes (completed, failed, or cancelled)."""

    status: str


class CandidateAccepted(CampaignEvent):
    """Broadcasted when an alpha candidate is accepted for submission."""

    candidate_id: str
    expression: str
    sharpe: float


class WorkerIdle(Event):
    """Broadcasted when a worker is idle and waiting for a job."""

    worker_name: str


class WorkerBusy(Event):
    """Broadcasted when a worker starts processing a campaign."""

    worker_name: str
    campaign_id: str


class GovernorStarted(Event):
    """Broadcasted when the governor begins running."""

    pass


class GovernorStopped(Event):
    """Broadcasted when the governor stops running."""

    pass


class CampaignEventBus:
    """Thread-safe event bus for registering listeners and publishing events."""

    def __init__(self) -> None:
        """Initialize event bus with empty list of listeners and a lock."""
        from threading import Lock

        self._lock = Lock()
        self._listeners: List[Callable[[Event], None]] = []

    def subscribe(self, listener: Callable[[Event], None]) -> None:
        """Register a callback function to listen for published events."""
        with self._lock:
            self._listeners.append(listener)

    def unsubscribe(self, listener: Callable[[Event], None]) -> None:
        """Remove a callback function from listening to events."""
        with self._lock:
            try:
                self._listeners.remove(listener)
            except ValueError:
                pass

    def publish(self, event: Event) -> None:
        """Broadcast an event to all registered listener callbacks."""
        with self._lock:
            listeners = list(self._listeners)
        for listener in listeners:
            try:
                listener(event)
            except Exception:
                # Keep event distribution isolated from listener callback bugs
                pass
