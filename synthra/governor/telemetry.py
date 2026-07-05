"""Telemetry and system metrics tracker for SYNTHRA."""

import time
from collections import deque
from threading import Lock
from typing import Any, Dict, List

from synthra.governor.events import (
    CampaignStarted,
    CampaignFinished,
    SimulationStarted,
    SimulationCompleted,
    SimulationFailed,
    MutationCreated,
    CandidateAccepted,
    CandidateRejected,
    CandidateSubmitted,
    CandidateSubmissionFailed,
    Event,
)


class TelemetryManager:
    """Manages system telemetry by listening to the event bus."""

    def __init__(self, governor: Any = None) -> None:
        """Initialize telemetry state with zero values."""
        self.governor = governor
        self._lock = Lock()
        self._start_time: float = time.time()
        self._event_history: deque[Event] = deque(maxlen=200)

        # Counters
        self.completed_jobs: int = 0
        self.failed_jobs: int = 0
        self.campaigns_running: int = 0
        self.campaigns_completed: int = 0
        self.simulations_running: int = 0
        self.simulations_completed: int = 0
        self.accepted_candidates: int = 0
        self.rejected_candidates: int = 0
        self.mutations_generated: int = 0
        self.submitted_candidates: int = 0
        self.failed_submissions: int = 0

        # Simulation duration tracking
        self._active_simulations: Dict[str, float] = {}  # key -> start_time
        self._total_simulation_time: float = 0.0
        self._simulation_count_for_avg: int = 0

    def start(self) -> None:
        """Reset start time on system startup."""
        with self._lock:
            self._start_time = time.time()

    def handle_event(self, event: Event) -> None:
        """Update metrics based on received event type."""
        with self._lock:
            self._event_history.append(event)
            if isinstance(event, CampaignStarted):
                self.campaigns_running += 1
            elif isinstance(event, CampaignFinished):
                if self.campaigns_running > 0:
                    self.campaigns_running -= 1
                if event.status == "completed":
                    self.campaigns_completed += 1
                    self.completed_jobs += 1
                elif event.status == "failed":
                    self.failed_jobs += 1
            elif isinstance(event, SimulationStarted):
                self.simulations_running += 1
                key = f"{event.campaign_id}:{event.expression}"
                self._active_simulations[key] = time.time()
            elif isinstance(event, SimulationCompleted):
                if self.simulations_running > 0:
                    self.simulations_running -= 1
                self.simulations_completed += 1

                key = f"{event.campaign_id}:{event.expression}"
                start_time = self._active_simulations.pop(key, None)
                if start_time is not None:
                    duration = time.time() - start_time
                    self._total_simulation_time += duration
                    self._simulation_count_for_avg += 1
            elif isinstance(event, SimulationFailed):
                if self.simulations_running > 0:
                    self.simulations_running -= 1
                key = f"{event.campaign_id}:{event.expression}"
                self._active_simulations.pop(key, None)
            elif isinstance(event, MutationCreated):
                self.mutations_generated += 1
            elif isinstance(event, CandidateAccepted):
                self.accepted_candidates += 1
            elif isinstance(event, CandidateRejected):
                self.rejected_candidates += 1
            elif isinstance(event, CandidateSubmitted):
                self.submitted_candidates += 1
            elif isinstance(event, CandidateSubmissionFailed):
                self.failed_submissions += 1

    @property
    def average_simulation_time(self) -> float:
        """Calculate the average simulation time in seconds."""
        with self._lock:
            if self._simulation_count_for_avg == 0:
                return 0.0
            return round(
                self._total_simulation_time / self._simulation_count_for_avg, 3
            )

    @property
    def uptime(self) -> float:
        """Calculate system uptime in seconds."""
        with self._lock:
            return round(time.time() - self._start_time, 2)

    def get_metrics(self) -> Dict[str, Any]:
        """Compile and return current snapshot of all system metrics."""
        running_workers = 0
        queued_jobs = 0
        if self.governor and self.governor.scheduler:
            running_workers = len(
                [w for w in self.governor.scheduler._workers if w.is_alive()]
            )
            queued_jobs = self.governor.queue.size()

        with self._lock:
            return {
                "running_workers": running_workers,
                "queued_jobs": queued_jobs,
                "completed_jobs": self.completed_jobs,
                "failed_jobs": self.failed_jobs,
                "campaigns_running": self.campaigns_running,
                "campaigns_completed": self.campaigns_completed,
                "simulations_running": self.simulations_running,
                "simulations_completed": self.simulations_completed,
                "accepted_candidates": self.accepted_candidates,
                "rejected_candidates": self.rejected_candidates,
                "mutations_generated": self.mutations_generated,
                "submitted_candidates": self.submitted_candidates,
                "failed_submissions": self.failed_submissions,
                "average_simulation_time": self.average_simulation_time,
                "uptime": self.uptime,
            }

    def get_events(self) -> List[Event]:
        """Return the recent event history."""
        with self._lock:
            return list(self._event_history)
