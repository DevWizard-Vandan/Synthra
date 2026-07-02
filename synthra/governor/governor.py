"""Governor service exposing high-level campaign scheduling and control APIs."""

from typing import Optional

from synthra.core.domain import Campaign
from synthra.governor.events import CampaignEventBus
from synthra.governor.queue import CampaignQueue
from synthra.governor.scheduler import CampaignScheduler
from synthra.governor.state import CampaignState
from synthra.governor.tracker import CampaignProgress, CampaignProgressTracker
from synthra.memory import DatabaseManager
from synthra.research.orchestrator import ResearchOrchestrator


class Governor:
    """The root control service acting as the brain running SYNTHRA continuously."""

    def __init__(
        self,
        orchestrator: ResearchOrchestrator,
        db_manager: DatabaseManager,
        num_workers: int = 2,
        max_retries: int = 3,
        initial_backoff_seconds: float = 2.0,
    ) -> None:
        """Initialize governor with all necessary scheduling subsystems."""
        self.orchestrator = orchestrator
        self.db_manager = db_manager

        self.queue = CampaignQueue()
        self.progress_tracker = CampaignProgressTracker()
        self.event_bus = CampaignEventBus()

        self.scheduler = CampaignScheduler(
            queue=self.queue,
            orchestrator=self.orchestrator,
            progress_tracker=self.progress_tracker,
            event_bus=self.event_bus,
            db_manager=self.db_manager,
            num_workers=num_workers,
            max_retries=max_retries,
            initial_backoff_seconds=initial_backoff_seconds,
        )

    def start(self) -> None:
        """Start scheduler workers and recover interrupted campaigns."""
        self.scheduler.start()
        self.scheduler.recover_campaigns()

    def stop(self) -> None:
        """Stop scheduler workers and conclude execution threads."""
        self.scheduler.stop()

    def enqueue_campaign(self, campaign: Campaign, priority: int = 0) -> None:
        """Enroll a campaign into the scheduling queue."""
        self.scheduler.enqueue_campaign(campaign, priority)

    def pause_campaign(self, campaign_id: str) -> None:
        """Pause execution of a campaign."""
        self.scheduler.pause_campaign(campaign_id)

    def resume_campaign(self, campaign_id: str) -> None:
        """Resume execution of a paused campaign."""
        self.scheduler.resume_campaign(campaign_id)

    def cancel_campaign(self, campaign_id: str) -> None:
        """Cancel execution of a campaign."""
        self.scheduler.cancel_campaign(campaign_id)

    def get_campaign_state(self, campaign_id: str) -> CampaignState:
        """Retrieve current campaign state."""
        return self.scheduler.get_campaign_state(campaign_id)

    def get_campaign_progress(self, campaign_id: str) -> Optional[CampaignProgress]:
        """Retrieve current campaign progress metrics."""
        return self.progress_tracker.get_progress(campaign_id)
