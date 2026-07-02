"""Scheduler system managing active workers, retries, and state recovery."""

import logging
import time
from threading import Lock, Thread
from typing import List, Optional

from synthra.core.domain import Campaign
from synthra.governor.events import CampaignEventBus, CampaignPaused, CampaignResumed
from synthra.governor.exceptions import CampaignNotFoundError
from synthra.governor.queue import CampaignQueue
from synthra.governor.state import CampaignState, validate_transition
from synthra.governor.tracker import CampaignProgressTracker
from synthra.governor.worker import CampaignWorker
from synthra.governor.submission import SubmissionQueue
from synthra.memory import CampaignRepository, DatabaseManager
from synthra.research.orchestrator import ResearchOrchestrator

logger = logging.getLogger(__name__)


class CampaignScheduler:
    """Manages pool of campaign workers, retries, and crash recovery state."""

    def __init__(
        self,
        queue: CampaignQueue,
        orchestrator: ResearchOrchestrator,
        progress_tracker: CampaignProgressTracker,
        event_bus: CampaignEventBus,
        db_manager: DatabaseManager,
        num_workers: int = 2,
        max_retries: int = 3,
        initial_backoff_seconds: float = 2.0,
    ) -> None:
        """Initialize scheduler with thread safety and persistent schema."""
        self.queue = queue
        self.orchestrator = orchestrator
        self.progress_tracker = progress_tracker
        self.event_bus = event_bus
        self.db_manager = db_manager
        self.num_workers = num_workers
        self.max_retries = max_retries
        self.initial_backoff = initial_backoff_seconds
        self.submission_queue = SubmissionQueue(db_manager)

        self._workers: List[CampaignWorker] = []
        self._lock = Lock()
        self._running = False

        # Background monitor thread to process retries/backoffs
        self._monitor_thread: Optional[Thread] = None

        self._init_persistence()

    def _init_persistence(self) -> None:
        """Create scheduling states persistence tables."""
        with self.db_manager.transaction() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS campaign_states (
                    campaign_id TEXT PRIMARY KEY,
                    state TEXT NOT NULL,
                    priority INTEGER DEFAULT 0,
                    failures INTEGER DEFAULT 0,
                    retry_at REAL DEFAULT 0.0,
                    FOREIGN KEY(campaign_id) REFERENCES campaigns(id)
                );
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS campaign_checkpoints (
                    campaign_id TEXT PRIMARY KEY,
                    task_index INTEGER NOT NULL,
                    generation INTEGER NOT NULL,
                    checkpoint_data TEXT NOT NULL,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
            """)

    def start(self) -> None:
        """Start worker threads and retry monitor thread."""
        with self._lock:
            if self._running:
                return
            self._running = True

            # Start worker pool
            self._workers = []
            for i in range(self.num_workers):
                worker = CampaignWorker(
                    worker_id=i + 1,
                    queue=self.queue,
                    orchestrator=self.orchestrator,
                    progress_tracker=self.progress_tracker,
                    event_bus=self.event_bus,
                    update_state_cb=self.update_campaign_state,
                    get_state_cb=self.get_campaign_state,
                    submission_queue=self.submission_queue,
                )
                worker.start()
                self._workers.append(worker)

            # Start retry check monitor
            self._monitor_thread = Thread(target=self._monitor_loop, daemon=True)
            self._monitor_thread.start()
            logger.info("CampaignScheduler started with %d workers", self.num_workers)

    def stop(self) -> None:
        """Gracefully stop all worker and monitor threads."""
        with self._lock:
            if not self._running:
                return
            self._running = False

            # Signal workers to stop
            for worker in self._workers:
                worker.stop()

            # Wait for workers to finish
            for worker in self._workers:
                worker.join(timeout=1.0)

            self._workers = []
            logger.info("CampaignScheduler stopped")

    def enqueue_campaign(self, campaign: Campaign, priority: int = 0) -> None:
        """Enroll a campaign into the scheduler queue and update state."""
        # 1. Update state record in database
        with self.db_manager.transaction() as conn:
            cursor = conn.execute(
                "SELECT state, failures FROM campaign_states WHERE campaign_id = ?",
                (campaign.id,),
            )
            row = cursor.fetchone()

            if row:
                current_state = CampaignState(row["state"])
                validate_transition(current_state, CampaignState.QUEUED)
                conn.execute(
                    """
                    UPDATE campaign_states
                    SET state = ?, priority = ?, retry_at = 0.0
                    WHERE campaign_id = ?
                    """,
                    (CampaignState.QUEUED.value, priority, campaign.id),
                )
            else:
                # Save campaign first (to satisfy foreign key if it's not present)
                CampaignRepository(conn).save(campaign)
                conn.execute(
                    """
                    INSERT INTO campaign_states (
                        campaign_id, state, priority, failures, retry_at
                    ) VALUES (?, ?, ?, 0, 0.0)
                    """,
                    (campaign.id, CampaignState.QUEUED.value, priority),
                )

        # 2. Add to priority queue
        self.queue.enqueue(campaign, priority)
        self.progress_tracker.update_metrics(campaign.id, queue_size=self.queue.size())

    def pause_campaign(self, campaign_id: str) -> None:
        """Pause execution of a campaign."""
        with self.db_manager.transaction() as conn:
            cursor = conn.execute(
                "SELECT state FROM campaign_states WHERE campaign_id = ?",
                (campaign_id,),
            )
            row = cursor.fetchone()
            if not row:
                raise CampaignNotFoundError(f"Campaign {campaign_id} not registered")

            current_state = CampaignState(row["state"])
            validate_transition(current_state, CampaignState.PAUSED)
            conn.execute(
                "UPDATE campaign_states SET state = ? WHERE campaign_id = ?",
                (CampaignState.PAUSED.value, campaign_id),
            )

        # Remove from queue if present
        self.queue.remove(campaign_id)
        self.progress_tracker.update_metrics(campaign_id, queue_size=self.queue.size())
        self.event_bus.publish(CampaignPaused(campaign_id=campaign_id))

    def resume_campaign(self, campaign_id: str) -> None:
        """Resume execution of a paused campaign."""
        campaign: Optional[Campaign] = None
        priority = 0

        with self.db_manager.transaction() as conn:
            cursor = conn.execute(
                "SELECT state, priority FROM campaign_states WHERE campaign_id = ?",
                (campaign_id,),
            )
            row = cursor.fetchone()
            if not row:
                raise CampaignNotFoundError(f"Campaign {campaign_id} not registered")

            current_state = CampaignState(row["state"])
            validate_transition(current_state, CampaignState.QUEUED)
            priority = row["priority"]

            campaign = CampaignRepository(conn).get_by_id(campaign_id)
            if not campaign:
                raise CampaignNotFoundError(f"Campaign {campaign_id} not found in DB")

            conn.execute(
                "UPDATE campaign_states SET state = ? WHERE campaign_id = ?",
                (CampaignState.QUEUED.value, campaign_id),
            )

        # Re-enqueue
        self.queue.enqueue(campaign, priority)
        self.progress_tracker.update_metrics(campaign_id, queue_size=self.queue.size())
        self.event_bus.publish(CampaignResumed(campaign_id=campaign_id))

    def cancel_campaign(self, campaign_id: str) -> None:
        """Cancel execution of a campaign."""
        with self.db_manager.transaction() as conn:
            cursor = conn.execute(
                "SELECT state FROM campaign_states WHERE campaign_id = ?",
                (campaign_id,),
            )
            row = cursor.fetchone()
            if not row:
                raise CampaignNotFoundError(f"Campaign {campaign_id} not registered")

            current_state = CampaignState(row["state"])
            validate_transition(current_state, CampaignState.CANCELLED)
            conn.execute(
                "UPDATE campaign_states SET state = ? WHERE campaign_id = ?",
                (CampaignState.CANCELLED.value, campaign_id),
            )

        # Remove from queue if present
        self.queue.remove(campaign_id)
        self.progress_tracker.update_metrics(campaign_id, queue_size=self.queue.size())

    def get_campaign_state(self, campaign_id: str) -> CampaignState:
        """Retrieve current campaign state from the database."""
        with self.db_manager.connection() as conn:
            cursor = conn.execute(
                "SELECT state FROM campaign_states WHERE campaign_id = ?",
                (campaign_id,),
            )
            row = cursor.fetchone()
            if not row:
                return CampaignState.DRAFT
            return CampaignState(row["state"])

    def update_campaign_state(self, campaign_id: str, new_state: CampaignState) -> None:
        """Update campaign state in the database."""
        with self.db_manager.transaction() as conn:
            if new_state == CampaignState.FAILED:
                cursor = conn.execute(
                    "SELECT failures FROM campaign_states WHERE campaign_id = ?",
                    (campaign_id,),
                )
                row = cursor.fetchone()
                failures = row["failures"] if row else 0

                if failures < self.max_retries:
                    backoff = self.initial_backoff * (2**failures)
                    retry_at = time.time() + backoff
                    conn.execute(
                        """
                        UPDATE campaign_states
                        SET state = ?, retry_at = ?
                        WHERE campaign_id = ?
                        """,
                        (new_state.value, retry_at, campaign_id),
                    )
                    logger.info(
                        "Campaign %s failed. Scheduled retry in %f seconds.",
                        campaign_id,
                        backoff,
                    )
                    return

            conn.execute(
                "UPDATE campaign_states SET state = ? WHERE campaign_id = ?",
                (new_state.value, campaign_id),
            )

    def recover_campaigns(self) -> None:
        """Recover queued or interrupted campaigns from the database after a restart."""
        recovered_count = 0
        with self.db_manager.connection() as conn:
            # Re-enqueue campaigns that were running or queued
            cursor = conn.execute(
                """
                SELECT campaign_id, priority FROM campaign_states
                WHERE state IN (?, ?)
                """,
                (CampaignState.QUEUED.value, CampaignState.RUNNING.value),
            )
            rows = cursor.fetchall()

        for row in rows:
            campaign_id = row["campaign_id"]
            priority = row["priority"]
            with self.db_manager.connection() as conn:
                campaign = CampaignRepository(conn).get_by_id(campaign_id)

            if campaign:
                # Force status in db back to QUEUED
                self.update_campaign_state(campaign_id, CampaignState.QUEUED)
                self.queue.enqueue(campaign, priority)
                recovered_count += 1

        logger.info("Recovered %d campaigns from persistent storage", recovered_count)

    def _monitor_loop(self) -> None:
        """Background loop checking and re-queuing deferred failed campaigns."""
        while self._running:
            try:
                now = time.time()
                with self.db_manager.connection() as conn:
                    # Find failed campaigns that are ready for retry backoff
                    cursor = conn.execute(
                        """
                        SELECT campaign_id, priority, failures FROM campaign_states
                        WHERE state = ? AND retry_at > 0.0 AND retry_at <= ?
                        """,
                        (CampaignState.FAILED.value, now),
                    )
                    rows = cursor.fetchall()

                for row in rows:
                    campaign_id = row["campaign_id"]
                    priority = row["priority"]
                    failures = row["failures"]

                    if failures >= self.max_retries:
                        # Max retries reached
                        with self.db_manager.transaction() as conn:
                            conn.execute(
                                "UPDATE campaign_states "
                                "SET retry_at = 0.0 "
                                "WHERE campaign_id = ?",
                                (campaign_id,),
                            )
                        continue

                    # Re-enqueue campaign
                    with self.db_manager.connection() as conn:
                        campaign = CampaignRepository(conn).get_by_id(campaign_id)

                    if campaign:
                        logger.info(
                            "Retrying campaign %s (attempt %d)",
                            campaign_id,
                            failures + 1,
                        )
                        with self.db_manager.transaction() as conn:
                            conn.execute(
                                """
                                UPDATE campaign_states
                                SET state = ?, failures = ?, retry_at = 0.0
                                WHERE campaign_id = ?
                                """,
                                (CampaignState.QUEUED.value, failures + 1, campaign_id),
                            )
                        self.queue.enqueue(campaign, priority)

            except Exception as e:
                logger.error("Error in monitor retry loop: %s", e)

            time.sleep(1.0)
