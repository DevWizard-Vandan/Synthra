"""Background worker thread processing alpha candidate submissions sequentially."""

import json
import logging
import time
from datetime import datetime
from threading import Thread
from typing import Optional

from synthra.governor.events import (
    CandidateSubmitted,
    CandidateSubmissionFailed,
    CandidateRejected,
    CampaignEventBus,
)
from synthra.governor.submission import SubmissionQueue, QueuedCandidate
from synthra.memory import DatabaseManager
from synthra.research.orchestrator import ResearchOrchestrator

logger = logging.getLogger(__name__)


class SubmissionWorker(Thread):
    """Background worker thread executing submissions sequentially from the queue."""

    def __init__(
        self,
        submission_queue: SubmissionQueue,
        orchestrator: ResearchOrchestrator,
        db_manager: DatabaseManager,
        event_bus: CampaignEventBus,
        daily_limit: int = 50,
        submission_delay_seconds: float = 2.0,
    ) -> None:
        """Initialize submission worker thread."""
        super().__init__(name="SubmissionWorker", daemon=True)
        self.submission_queue = submission_queue
        self.orchestrator = orchestrator
        self.db_manager = db_manager
        self.event_bus = event_bus
        self.daily_limit = daily_limit
        self.submission_delay = submission_delay_seconds
        self._running = True

    def stop(self) -> None:
        """Flag this submission worker thread to stop processing."""
        self._running = False

    def run(self) -> None:
        """Process submissions sequentially while running."""
        logger.info("SubmissionWorker starting loop")
        while self._running:
            try:
                candidate = self.submission_queue.dequeue()
                if not candidate:
                    time.sleep(0.5)
                    continue

                self._process_submission(candidate)
            except Exception as e:
                logger.error("SubmissionWorker encountered loop error: %s", e)
                time.sleep(1.0)

    def _process_submission(self, candidate: QueuedCandidate) -> None:
        """Handle validation, duplicate check, limits, and client submission of a candidate."""
        expression = candidate.expression
        campaign_id = candidate.campaign_id

        # 1. Duplicate check (Never submit duplicates)
        with self.db_manager.connection() as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM alpha_candidates WHERE expression = ? AND is_submitted = 1",
                (expression,),
            ).fetchone()
            already_submitted = row[0] > 0 if row else False

        if already_submitted:
            logger.info(
                "Candidate %s with expression '%s' already submitted. Skipping.",
                candidate.candidate_id,
                expression,
            )
            self.event_bus.publish(
                CandidateRejected(
                    campaign_id=campaign_id,
                    expression=expression,
                    reason="duplicate submission check",
                )
            )
            return

        # 2. Extract platform simulation ID from simulation_logs
        simulation_id = self._resolve_simulation_id(expression)
        if not simulation_id:
            logger.warning(
                "Simulation ID not found for expression: %s. Using candidate_id as fallback.",
                expression,
            )
            simulation_id = f"SIM-FALLBACK-{candidate.candidate_id}"

        # 3. Daily limits check
        with self.db_manager.connection() as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM alpha_candidates WHERE is_submitted = 1 AND date(submitted_at) = date('now')"
            ).fetchone()
            submitted_today = row[0] if row else 0

        if submitted_today >= self.daily_limit:
            logger.warning(
                "Daily submission limit (%d) reached. Re-enqueuing candidate %s.",
                self.daily_limit,
                candidate.candidate_id,
            )
            self.submission_queue.enqueue(candidate)
            time.sleep(30.0)  # Wait for limit to reset or cool down
            return

        # 4. Submit using the execution client
        try:
            logger.info(
                "Submitting candidate %s (simulation_id: %s) to WorldQuant BRAIN",
                candidate.candidate_id,
                simulation_id,
            )

            runner = self.orchestrator.simulation_runner
            if hasattr(runner, "_client") and runner._client:
                runner._client.submit_alpha(simulation_id)
            else:
                logger.info(
                    "[Mock Submission] Successfully submitted simulation %s",
                    simulation_id,
                )

            # 5. Persist submission history
            with self.db_manager.transaction() as conn:
                conn.execute(
                    "UPDATE alpha_candidates SET is_submitted = 1, submitted_at = ? WHERE id = ?",
                    (datetime.utcnow().isoformat(), candidate.candidate_id),
                )

            # 6. Publish success event
            self.event_bus.publish(
                CandidateSubmitted(
                    campaign_id=campaign_id,
                    candidate_id=candidate.candidate_id,
                    expression=expression,
                    simulation_id=simulation_id,
                )
            )
            logger.info("Successfully submitted candidate %s", candidate.candidate_id)

            # Throttle submissions to respect platform limits
            time.sleep(self.submission_delay)

        except Exception as e:
            logger.error("Failed to submit candidate %s: %s", candidate.candidate_id, e)
            
            # Record failure in database
            with self.db_manager.transaction() as conn:
                conn.execute(
                    "INSERT INTO campaign_errors (campaign_id, error_type, message, created_at) VALUES (?, ?, ?, ?)",
                    (
                        campaign_id,
                        "submission_failed",
                        str(e),
                        datetime.utcnow().isoformat(),
                    ),
                )

            # Publish failure event
            self.event_bus.publish(
                CandidateSubmissionFailed(
                    campaign_id=campaign_id,
                    candidate_id=candidate.candidate_id,
                    expression=expression,
                    error_message=str(e),
                )
            )

            # Safe retries handling: re-enqueue if the error was transient
            from synthra.execution.exceptions import ExecutionClientError

            is_transient = True
            if isinstance(e, ExecutionClientError) and "client error" in str(e).lower():
                is_transient = False  # Hard error, do not retry

            if is_transient:
                logger.info(
                    "Re-enqueuing candidate %s for retry.", candidate.candidate_id
                )
                self.submission_queue.enqueue(candidate)
                time.sleep(5.0)

    def _resolve_simulation_id(self, expression: str) -> Optional[str]:
        """Look up the platform simulation ID for a given expression in the logs."""
        try:
            with self.db_manager.connection() as conn:
                row = conn.execute(
                    "SELECT raw_response FROM simulation_logs WHERE expression = ? AND status = 'completed' ORDER BY finished_at DESC LIMIT 1",
                    (expression,),
                ).fetchone()
                if row and row[0]:
                    payload = json.loads(row[0])
                    return payload.get("id")
        except Exception as e:
            logger.error("Error resolving simulation ID: %s", e)
        return None
