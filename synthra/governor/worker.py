"""Worker subclass executing individual campaign optimization runs."""

import logging
import time
from datetime import datetime
from threading import Thread
from typing import Callable

from synthra.core.domain import Campaign, Experiment, ExperimentStatus
from synthra.governor.events import (
    CampaignCancelled,
    CampaignCompleted,
    CampaignEventBus,
    CampaignPaused,
    CampaignStarted,
    CandidateApproved,
    HypothesisGenerated,
    LearningRecorded,
    SimulationCompleted,
    SimulationFailed,
    SimulationStarted,
)
from synthra.governor.exceptions import InvalidStateTransition
from synthra.governor.queue import CampaignQueue
from synthra.governor.state import CampaignState, validate_transition
from synthra.governor.tracker import CampaignProgressTracker
from synthra.research.orchestrator import ResearchOrchestrator

logger = logging.getLogger(__name__)


class CampaignWorker(Thread):
    """Background worker thread executing campaigns sequentially from the queue."""

    def __init__(
        self,
        worker_id: int,
        queue: CampaignQueue,
        orchestrator: ResearchOrchestrator,
        progress_tracker: CampaignProgressTracker,
        event_bus: CampaignEventBus,
        update_state_cb: Callable[[str, CampaignState], None],
        get_state_cb: Callable[[str], CampaignState],
        max_failures: int = 5,
        timeout_seconds: int = 3600,
        alpha_target_sharpe: float = 2.0,
    ) -> None:
        """Initialize worker with necessary handlers and stop thresholds."""
        super().__init__(name=f"CampaignWorker-{worker_id}", daemon=True)
        self.worker_id = worker_id
        self.queue = queue
        self.orchestrator = orchestrator
        self.progress_tracker = progress_tracker
        self.event_bus = event_bus
        self.update_state = update_state_cb
        self.get_state = get_state_cb
        self.max_failures = max_failures
        self.timeout_seconds = timeout_seconds
        self.alpha_target_sharpe = alpha_target_sharpe
        self._running = True

    def stop(self) -> None:
        """Flag this worker thread to stop processing."""
        self._running = False

    def run(self) -> None:
        """Repeatedly pull campaigns and execute them until stopped."""
        logger.info("Worker %d starting run loop", self.worker_id)
        while self._running:
            try:
                # Dequeue next campaign
                queued_item = self.queue.dequeue()
                if not queued_item:
                    time.sleep(0.1)
                    continue

                campaign, priority = queued_item
                logger.info(
                    "Worker %d dequeued campaign %s", self.worker_id, campaign.id
                )

                # Process the campaign
                self._process_campaign(campaign)

            except Exception as e:
                logger.error("Worker %d encountered loop error: %s", self.worker_id, e)
                time.sleep(0.5)

    def _process_campaign(self, campaign: Campaign) -> None:
        """Execute the full optimization loop for a given campaign."""
        campaign_id = campaign.id

        # 1. Verify and transition to RUNNING state
        current_state = self.get_state(campaign_id)
        try:
            validate_transition(current_state, CampaignState.RUNNING)
            self.update_state(campaign_id, CampaignState.RUNNING)
        except InvalidStateTransition:
            logger.warning(
                "Campaign %s not in valid state to run. State: %s",
                campaign_id,
                current_state,
            )
            return

        # Initialize progress tracking
        self.progress_tracker.update_metrics(
            campaign_id,
            started_at=datetime.utcnow(),
            current_stage="running",
        )
        self.event_bus.publish(CampaignStarted(campaign_id=campaign_id))

        # 2. Decompose campaign into tasks
        tasks = self.orchestrator.planner.plan_campaign(campaign)
        self.progress_tracker.update_metrics(campaign_id, queue_size=self.queue.size())

        hyp_counter = 1
        exp_counter = 1
        cand_counter = 1

        budget_spent = campaign.budget_spent
        best_sharpe = 0.0
        best_fitness = 0.0
        best_score = 0.0

        aborted = False

        for task in tasks:
            if aborted or not self._running:
                break

            # 3. Generate structured hypotheses
            hyp_id = f"HYP-{hyp_counter:04d}"
            try:
                structured_hyp = (
                    self.orchestrator.hypothesis_generator.generate_hypothesis(task)
                )
                hyp = self.orchestrator.hypothesis_generator.to_domain(
                    structured_hyp, campaign_id, hyp_id
                )
                hyp_counter += 1

                # Record in history tracker
                if self.orchestrator.history_tracker:
                    self.orchestrator.history_tracker.record_hypothesis(hyp)

                # Update progress & emit event
                progress = self.progress_tracker.get_progress(campaign_id)
                num_hyps = (progress.generated_hypotheses if progress else 0) + 1
                self.progress_tracker.update_metrics(
                    campaign_id, generated_hypotheses=num_hyps
                )
                self.event_bus.publish(
                    HypothesisGenerated(
                        campaign_id=campaign_id,
                        hypothesis_id=hyp.id,
                        rationale=hyp.rationale,
                    )
                )
            except Exception as e:
                logger.error(
                    "Failed to generate hypothesis for campaign %s: %s", campaign_id, e
                )
                continue

            # 4. Generate candidate expressions for each dataset
            hypothesis_records = []
            for dataset_name in hyp.datasets:
                if aborted or not self._running:
                    break

                try:
                    generator = self.orchestrator.expression_generator
                    requests = generator.generate_expressions_for_dataset(
                        hyp,
                        dataset_name,
                        region=campaign.region,
                        universe=campaign.universe,
                    )
                except Exception as e:
                    logger.error("Failed to generate expressions: %s", e)
                    continue

                # 5. Simulate each generated expression
                for req in requests:
                    if aborted or not self._running:
                        break

                    # Check for external pause/cancel signals
                    state = self.get_state(campaign_id)
                    if state == CampaignState.PAUSED:
                        logger.info(
                            "Campaign %s paused during simulation.", campaign_id
                        )
                        self.event_bus.publish(CampaignPaused(campaign_id=campaign_id))
                        # Put back to queue to allow execution pause
                        self.queue.enqueue(campaign, priority=0)
                        aborted = True
                        break
                    elif state == CampaignState.CANCELLED:
                        logger.info(
                            "Campaign %s cancelled during simulation.", campaign_id
                        )
                        self.event_bus.publish(
                            CampaignCancelled(campaign_id=campaign_id)
                        )
                        aborted = True
                        break

                    # Check stop conditions
                    progress = self.progress_tracker.get_progress(campaign_id)
                    if progress:
                        # Reached simulation budget limit
                        if budget_spent >= campaign.budget_limit:
                            logger.info(
                                "Campaign %s reached simulation budget limit.",
                                campaign_id,
                            )
                            self._conclude_campaign(
                                campaign_id, CampaignState.COMPLETED
                            )
                            aborted = True
                            break
                        # Reached timeout
                        if progress.uptime >= self.timeout_seconds:
                            logger.info(
                                "Campaign %s reached runtime timeout.", campaign_id
                            )
                            self._conclude_campaign(
                                campaign_id, CampaignState.COMPLETED
                            )
                            aborted = True
                            break
                        # Reached max failures limit
                        if progress.failed_simulations >= self.max_failures:
                            logger.info(
                                "Campaign %s reached maximum failures limit.",
                                campaign_id,
                            )
                            self._conclude_campaign(campaign_id, CampaignState.FAILED)
                            aborted = True
                            break
                        # Reached alpha target sharpe
                        if best_sharpe >= self.alpha_target_sharpe:
                            logger.info(
                                "Campaign %s reached target Alpha Sharpe threshold.",
                                campaign_id,
                            )
                            self._conclude_campaign(
                                campaign_id, CampaignState.COMPLETED
                            )
                            aborted = True
                            break

                    # Execute simulation
                    self.event_bus.publish(
                        SimulationStarted(
                            campaign_id=campaign_id,
                            expression=req.expression,
                            dataset=dataset_name,
                        )
                    )

                    # Record pending experiment
                    exp_id = f"EXP-{exp_counter:04d}"
                    exp_counter += 1

                    if self.orchestrator.history_tracker:
                        experiment = Experiment(
                            id=exp_id,
                            campaign_id=campaign_id,
                            hypothesis_id=hyp.id,
                            expression=req.expression,
                            request=req,
                            status=ExperimentStatus.PENDING,
                            created_at=datetime.utcnow(),
                        )
                        self.orchestrator.history_tracker.record_experiment(experiment)

                    try:
                        # Mock backtest run cost
                        budget_spent += 10.0
                        self.progress_tracker.update_metrics(
                            campaign_id, queue_size=self.queue.size()
                        )

                        result = self.orchestrator.simulation_runner.run(req)

                        # Update experiment to completed
                        if self.orchestrator.history_tracker:
                            completed_exp = experiment.model_copy(
                                update={
                                    "status": ExperimentStatus.COMPLETED,
                                    "result": result,
                                    "finished_at": datetime.utcnow(),
                                }
                            )
                            self.orchestrator.history_tracker.record_experiment(
                                completed_exp
                            )

                        # Update tracker counters
                        progress = self.progress_tracker.get_progress(campaign_id)
                        comp_sims = (
                            progress.completed_simulations if progress else 0
                        ) + 1
                        succ_sims = (
                            progress.successful_simulations if progress else 0
                        ) + 1

                        # Update best metrics
                        best_sharpe = max(best_sharpe, result.sharpe)
                        best_fitness = max(best_fitness, result.fitness)

                        # Calculate EFV Score if scorer is present
                        cand_score = 0.0
                        if self.orchestrator.scorer:
                            cand_score = self.orchestrator.scorer.score_expression(
                                req.expression, result
                            )
                            best_score = max(best_score, cand_score)

                        self.progress_tracker.update_metrics(
                            campaign_id,
                            completed_simulations=comp_sims,
                            successful_simulations=succ_sims,
                            current_best_sharpe=best_sharpe,
                            current_best_fitness=best_fitness,
                            current_best_score=best_score,
                        )

                        self.event_bus.publish(
                            SimulationCompleted(
                                campaign_id=campaign_id,
                                expression=req.expression,
                                sharpe=result.sharpe,
                                fitness=result.fitness,
                            )
                        )

                        # Save learning record feedback
                        if (
                            self.orchestrator.feedback_generator
                            and self.orchestrator.learning_repository
                        ):
                            rec = self.orchestrator.feedback_generator.generate_record(
                                req,
                                result,
                                datasets=[dataset_name],
                                operators=hyp.operators,
                            )
                            self.orchestrator.learning_repository.add_record(rec)
                            hypothesis_records.append(rec)
                            self.event_bus.publish(
                                LearningRecorded(
                                    campaign_id=campaign_id,
                                    expression=req.expression,
                                    success=rec.success,
                                    sharpe=result.sharpe,
                                )
                            )

                        # Validate and handle candidate
                        cand_id = f"AST-{cand_counter:04d}"
                        cand_counter += 1
                        if result.sharpe >= 1.0:
                            self.event_bus.publish(
                                CandidateApproved(
                                    campaign_id=campaign_id,
                                    candidate_id=cand_id,
                                    expression=req.expression,
                                    sharpe=result.sharpe,
                                )
                            )
                            progress = self.progress_tracker.get_progress(campaign_id)
                            app_cands = (
                                progress.approved_candidates if progress else 0
                            ) + 1
                            self.progress_tracker.update_metrics(
                                campaign_id, approved_candidates=app_cands
                            )

                    except Exception as e:
                        # Update experiment to failed
                        if self.orchestrator.history_tracker:
                            failed_exp = experiment.model_copy(
                                update={
                                    "status": ExperimentStatus.FAILED,
                                    "finished_at": datetime.utcnow(),
                                }
                            )
                            self.orchestrator.history_tracker.record_experiment(
                                failed_exp
                            )

                        logger.error(
                            "Simulation failed for expression %s: %s",
                            req.expression,
                            e,
                        )
                        progress = self.progress_tracker.get_progress(campaign_id)
                        fail_sims = (progress.failed_simulations if progress else 0) + 1
                        comp_sims = (
                            progress.completed_simulations if progress else 0
                        ) + 1
                        self.progress_tracker.update_metrics(
                            campaign_id,
                            failed_simulations=fail_sims,
                            completed_simulations=comp_sims,
                        )
                        self.event_bus.publish(
                            SimulationFailed(
                                campaign_id=campaign_id,
                                expression=req.expression,
                                error_message=str(e),
                            )
                        )

        # 6. Conclude execution if it completed all tasks successfully
        if not aborted:
            self._conclude_campaign(campaign_id, CampaignState.COMPLETED)

    def _conclude_campaign(
        self, campaign_id: str, terminal_state: CampaignState
    ) -> None:
        """Transition campaign to completed, failed, or cancelled and log it."""
        try:
            self.update_state(campaign_id, terminal_state)
            self.progress_tracker.update_metrics(
                campaign_id,
                concluded_at=datetime.utcnow(),
                current_stage=terminal_state.value,
            )
            if terminal_state == CampaignState.COMPLETED:
                self.event_bus.publish(CampaignCompleted(campaign_id=campaign_id))
            elif terminal_state == CampaignState.CANCELLED:
                self.event_bus.publish(CampaignCancelled(campaign_id=campaign_id))
        except Exception as e:
            logger.error("Failed to conclude campaign %s: %s", campaign_id, e)
