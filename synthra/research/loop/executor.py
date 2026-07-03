"""Executor modules for the autonomous research loop."""

import logging
import time
from typing import Optional, Tuple

from synthra.core.domain import (
    Experiment,
    ExperimentStatus,
    SimulationRequest,
    SimulationResult,
)
from synthra.execution.exceptions import (
    ExecutionRateLimitError,
    ExecutionServerError,
    ExecutionTransportError,
    SimulationTimeoutError,
)
from synthra.execution.runner import SimulationRunner
from synthra.learning.history import HistoryTracker

logger = logging.getLogger(__name__)


class LoopExecutor:
    """Submits simulation requests and stores results via HistoryTracker."""

    def __init__(
        self,
        runner: SimulationRunner,
        history_tracker: HistoryTracker,
        max_retries: int = 3,
        initial_backoff: float = 0.5,
    ) -> None:
        """Initialize loop executor with simulation runner and history tracker."""
        self.runner = runner
        self.history_tracker = history_tracker
        self.max_retries = max_retries
        self.initial_backoff = initial_backoff

    def execute_simulation(
        self,
        request: SimulationRequest,
        campaign_id: str,
        hypothesis_id: str,
        experiment_id: str,
    ) -> Tuple[Optional[SimulationResult], Optional[str]]:
        """Submit a simulation request with retries for transient exceptions."""
        last_error: Optional[str] = None

        # Initialize the experiment as PENDING in history
        experiment = Experiment(
            id=experiment_id,
            campaign_id=campaign_id,
            hypothesis_id=hypothesis_id,
            expression=request.expression,
            status=ExperimentStatus.PENDING,
            request=request,
            result=None,
        )
        self.history_tracker.record_experiment(experiment)

        for attempt in range(self.max_retries):
            try:
                result = self.runner.run(request)
                # Success! Record and return
                experiment = experiment.model_copy(
                    update={
                        "status": ExperimentStatus.COMPLETED,
                        "result": result,
                        "finished_at": result.simulated_at,
                    }
                )
                self.history_tracker.record_experiment(experiment)
                return result, None
            except (
                SimulationTimeoutError,
                ExecutionTransportError,
                ExecutionRateLimitError,
                ExecutionServerError,
            ) as err:
                last_error = str(err)
                logger.warning(
                    "Simulation %s failed with transient error: %s. Retrying...",
                    experiment_id,
                    err,
                )
                if attempt < self.max_retries - 1:
                    time.sleep(self.initial_backoff * (2**attempt))
            except Exception as err:
                # Terminal error
                last_error = str(err)
                experiment = experiment.model_copy(
                    update={
                        "status": ExperimentStatus.FAILED,
                        "error_message": last_error,
                    }
                )
                self.history_tracker.record_experiment(experiment)
                return None, last_error

        # If we exhausted retries
        experiment = experiment.model_copy(
            update={
                "status": ExperimentStatus.FAILED,
                "error_message": f"Exhausted retries. Last error: {last_error}",
            }
        )
        self.history_tracker.record_experiment(experiment)
        return None, last_error
