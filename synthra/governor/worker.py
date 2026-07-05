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
    CandidateRejected,
    ExpressionGenerated,
    CandidateQueued,
    MutationCreated,
    LearningUpdated,
    CampaignCheckpointed,
    CampaignRecovered,
    WorkerIdle,
    WorkerBusy,
    CandidateAccepted,
    CampaignFinished,
)
from synthra.governor.exceptions import InvalidStateTransition
from synthra.governor.queue import CampaignQueue
from synthra.governor.state import CampaignState, validate_transition
from synthra.governor.tracker import CampaignProgressTracker
from synthra.governor.submission import SubmissionQueue, QueuedCandidate
from synthra.research.orchestrator import ResearchOrchestrator
from synthra.research.evolution import NoveltyDetector, EvolutionStrategies

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
        submission_queue: SubmissionQueue,
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
        self.submission_queue = submission_queue
        self.max_failures = max_failures
        self.timeout_seconds = timeout_seconds
        self.alpha_target_sharpe = alpha_target_sharpe
        self._running = True

    def stop(self) -> None:
        """Flag this worker thread to stop processing."""
        self._running = False

    def run(self) -> None:
        """Process campaign tasks sequentially while flagged as running."""
        logger.info("CampaignWorker-%d thread starting loop", self.worker_id)
        self.event_bus.publish(WorkerIdle(worker_name=f"Worker-{self.worker_id}"))

        while self._running:
            try:
                # Dequeue next campaign
                entry = self.queue.dequeue()
                if not entry:
                    time.sleep(0.1)
                    continue

                campaign, priority = entry

                self.event_bus.publish(
                    WorkerBusy(
                        worker_name=f"Worker-{self.worker_id}",
                        campaign_id=campaign.id,
                    )
                )

                logger.info(
                    "Worker %d dequeued Campaign %s with priority %d",
                    self.worker_id,
                    campaign.id,
                    priority,
                )

                # Process the campaign
                try:
                    self._process_campaign(campaign)
                except Exception as e:
                    logger.error(
                        "Worker %d failed to process campaign %s: %s",
                        self.worker_id,
                        campaign.id,
                        e,
                    )
                    if self.orchestrator.history_tracker:
                        self.orchestrator.history_tracker.record_error(
                            campaign_id=campaign.id,
                            error_type="campaign_execution_failed",
                            message=str(e),
                        )
                    self._conclude_campaign(campaign.id, CampaignState.FAILED)

                self.event_bus.publish(
                    WorkerIdle(worker_name=f"Worker-{self.worker_id}")
                )

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

        # Check for checkpoint recovery
        start_task_idx = 0
        restored_generation = 0
        if self.orchestrator.db_manager:
            with self.orchestrator.db_manager.connection() as conn:
                row = conn.execute(
                    "SELECT task_index, generation FROM campaign_checkpoints "
                    "WHERE campaign_id = ?",
                    (campaign_id,),
                ).fetchone()
                if row:
                    start_task_idx = row[0]
                    restored_generation = row[1]
                    logger.info(
                        "Recovered campaign %s from task index %d, generation %d",
                        campaign_id,
                        start_task_idx,
                        restored_generation,
                    )
                    self.event_bus.publish(
                        CampaignRecovered(
                            campaign_id=campaign_id,
                            task_index=start_task_idx,
                            generation=restored_generation,
                        )
                    )

        # Initialize Novelty Detector
        self.novelty_detector = NoveltyDetector()

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

        for task_idx, task in enumerate(tasks):
            if task_idx < start_task_idx:
                continue

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
                    "Failed to generate hypothesis for campaign %s: %s",
                    campaign_id,
                    e,
                )
                if self.orchestrator.history_tracker:
                    self.orchestrator.history_tracker.record_error(
                        campaign_id=campaign_id,
                        error_type="hypothesis_generation_failed",
                        message=str(e),
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
                    if self.orchestrator.history_tracker:
                        self.orchestrator.history_tracker.record_error(
                            campaign_id=campaign_id,
                            error_type="expression_generation_failed",
                            message=str(e),
                        )
                    continue

                # Run generation loop
                generation = restored_generation
                current_requests = requests

                while current_requests and not aborted:
                    sim_results = []
                    for req in current_requests:
                        if aborted or not self._running:
                            break

                        # Check for external pause/cancel signals
                        state = self.get_state(campaign_id)
                        if state == CampaignState.PAUSED:
                            logger.info(
                                "Campaign %s paused during simulation.",
                                campaign_id,
                            )
                            self.event_bus.publish(
                                CampaignPaused(campaign_id=campaign_id)
                            )
                            self.queue.enqueue(campaign, priority=0)
                            aborted = True
                            break
                        elif state == CampaignState.CANCELLED:
                            logger.info(
                                "Campaign %s cancelled during simulation.",
                                campaign_id,
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
                            # Reached max simulations limit
                            if (
                                progress.completed_simulations
                                >= campaign.max_simulations
                            ):
                                logger.info(
                                    "Campaign %s reached maximum simulations limit.",
                                    campaign_id,
                                )
                                self._conclude_campaign(
                                    campaign_id, CampaignState.COMPLETED
                                )
                                aborted = True
                                break
                            # Reached timeout
                            if progress.uptime >= campaign.max_runtime_seconds:
                                logger.info(
                                    "Campaign %s reached runtime timeout.",
                                    campaign_id,
                                )
                                self._conclude_campaign(
                                    campaign_id, CampaignState.COMPLETED
                                )
                                aborted = True
                                break
                            # Reached target alpha count
                            if (
                                progress.approved_candidates
                                >= campaign.target_alpha_count
                            ):
                                logger.info(
                                    "Campaign %s reached target Alpha count limit.",
                                    campaign_id,
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
                                self._conclude_campaign(
                                    campaign_id, CampaignState.FAILED
                                )
                                aborted = True
                                break

                        # 5. Novelty Check
                        if not self.novelty_detector.is_novel(req.expression):
                            self.event_bus.publish(
                                CandidateRejected(
                                    campaign_id=campaign_id,
                                    expression=req.expression,
                                    reason="failed novelty check",
                                )
                            )
                            if self.orchestrator.history_tracker:
                                rej_id = f"REJ-{cand_counter:04d}"
                                cand_counter += 1
                                tracker = self.orchestrator.history_tracker
                                tracker.record_rejected_candidate(
                                    candidate_id=rej_id,
                                    campaign_id=campaign_id,
                                    hypothesis_id=hyp.id,
                                    expression=req.expression,
                                    reason="failed novelty check",
                                )
                            continue

                        self.novelty_detector.add_expression(req.expression)
                        self.event_bus.publish(
                            ExpressionGenerated(
                                campaign_id=campaign_id,
                                expression=req.expression,
                            )
                        )

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
                            self.orchestrator.history_tracker.record_experiment(
                                experiment
                            )

                        try:
                            # Mock backtest run cost
                            budget_spent += 10.0
                            self.progress_tracker.update_metrics(
                                campaign_id, queue_size=self.queue.size()
                            )

                            result = self.orchestrator.simulation_runner.run(req)
                            sim_results.append((req, result))

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
                                fb_generator = self.orchestrator.feedback_generator
                                rec = fb_generator.generate_record(
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
                                self.event_bus.publish(
                                    LearningUpdated(
                                        campaign_id=campaign_id,
                                        expression=req.expression,
                                        metrics=result.model_dump(mode="json"),
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
                                self.event_bus.publish(
                                    CandidateAccepted(
                                        campaign_id=campaign_id,
                                        candidate_id=cand_id,
                                        expression=req.expression,
                                        sharpe=result.sharpe,
                                    )
                                )
                                progress = self.progress_tracker.get_progress(
                                    campaign_id
                                )
                                app_cands = (
                                    progress.approved_candidates if progress else 0
                                ) + 1
                                self.progress_tracker.update_metrics(
                                    campaign_id, approved_candidates=app_cands
                                )

                                # Record approved candidate to database
                                if self.orchestrator.history_tracker:
                                    from synthra.core.domain import AlphaCandidate

                                    cand = AlphaCandidate(
                                        id=cand_id,
                                        experiment_id=exp_id,
                                        hypothesis_id=hyp.id,
                                        campaign_id=campaign_id,
                                        expression=req.expression,
                                        result=result,
                                        is_submitted=False,
                                    )
                                    self.orchestrator.history_tracker.record_candidate(
                                        cand
                                    )

                                # Candidate Queue Integration
                                lineage_dict = None
                                generation_num = 0
                                if self.orchestrator.mutation_engine:
                                    engine = self.orchestrator.mutation_engine
                                    lin_tracker = engine.lineage_tracker
                                    if lin_tracker:
                                        node = lin_tracker.get_node(req.expression)
                                        if node:
                                            lineage_dict = node.model_dump()
                                            generation_num = node.generation

                                queued_cand = QueuedCandidate(
                                    candidate_id=cand_id,
                                    campaign_id=campaign_id,
                                    hypothesis_id=hyp.id,
                                    expression=req.expression,
                                    metrics=result.model_dump(mode="json"),
                                    lineage=lineage_dict,
                                    generation=generation_num,
                                    reason_selected=(
                                        "passed selection criteria " "(Sharpe >= 1.0)"
                                    ),
                                )
                                self.submission_queue.enqueue(queued_cand)

                                self.event_bus.publish(
                                    CandidateQueued(
                                        campaign_id=campaign_id,
                                        candidate_id=cand_id,
                                        expression=req.expression,
                                    )
                                )
                            else:
                                # Sharpe < 1.0 candidate rejection
                                self.event_bus.publish(
                                    CandidateRejected(
                                        campaign_id=campaign_id,
                                        expression=req.expression,
                                        reason="failed Sharpe threshold (Sharpe < 1.0)",
                                    )
                                )
                                if self.orchestrator.history_tracker:
                                    tracker = self.orchestrator.history_tracker
                                    tracker.record_rejected_candidate(
                                        candidate_id=cand_id,
                                        campaign_id=campaign_id,
                                        hypothesis_id=hyp.id,
                                        expression=req.expression,
                                        reason=(
                                            f"failed Sharpe threshold "
                                            f"(Sharpe={result.sharpe:.4f} < 1.0)"
                                        ),
                                        metrics=result.model_dump(mode="json"),
                                    )

                        except Exception as e:
                            # Update experiment to failed
                            if self.orchestrator.history_tracker:
                                failed_exp = experiment.model_copy(
                                    update={
                                        "status": ExperimentStatus.FAILED,
                                        "finished_at": datetime.utcnow(),
                                        "error_message": str(e),
                                    }
                                )
                                self.orchestrator.history_tracker.record_experiment(
                                    failed_exp
                                )
                                self.orchestrator.history_tracker.record_error(
                                    campaign_id=campaign_id,
                                    error_type="simulation_failed",
                                    message=str(e),
                                )

                            logger.error(
                                "Simulation failed for expression %s: %s",
                                req.expression,
                                e,
                            )
                            progress = self.progress_tracker.get_progress(campaign_id)
                            fail_sims = (
                                progress.failed_simulations if progress else 0
                            ) + 1
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

                    # 6. Selection & Mutation
                    if aborted or not self._running:
                        break

                    scored_candidates = []
                    for req, res in sim_results:
                        score = self.orchestrator.selection_engine.calculate_score(
                            req.expression, res
                        )
                        scored_candidates.append((req, score))

                    next_requests = []
                    if scored_candidates:
                        parents = EvolutionStrategies.select_elitism(
                            scored_candidates, k=min(2, len(scored_candidates))
                        )
                        for parent_req in parents:
                            # Find the result corresponding to parent_req
                            parent_res = next(
                                res
                                for r, res in sim_results
                                if r.expression == parent_req.expression
                            )
                            mutations = (
                                self.orchestrator.mutation_engine.mutate_request(
                                    parent_req,
                                    parent_res,
                                    dataset_name,
                                    campaign_id=campaign_id,
                                    hypothesis_id=hyp.id,
                                )
                            )
                            for mut_req in mutations:
                                validator = self.orchestrator.validator
                                if validator.validate_request(mut_req, dataset_name):
                                    mut_type = "parameter_tuning"
                                    engine = self.orchestrator.mutation_engine
                                    lin_tracker = (
                                        engine.lineage_tracker if engine else None
                                    )
                                    if lin_tracker:
                                        node = lin_tracker.get_node(mut_req.expression)
                                        if node:
                                            mut_type = (
                                                node.mutation_type or "parameter_tuning"
                                            )

                                    self.event_bus.publish(
                                        MutationCreated(
                                            campaign_id=campaign_id,
                                            expression=mut_req.expression,
                                            mutation_type=mut_type,
                                        )
                                    )
                                    next_requests.append(mut_req)

                    generation += 1
                    if self.orchestrator.scorer and next_requests:
                        next_requests = self.orchestrator.scorer.rank_mutations(
                            next_requests, dataset_name, hyp.operators
                        )
                    current_requests = next_requests[
                        :5
                    ]  # Limit loop breadth per generation

            # 7. Checkpoint Campaign progress after each task
            if not aborted:
                if self.orchestrator.db_manager:
                    with self.orchestrator.db_manager.transaction() as conn:
                        conn.execute(
                            """
                            INSERT OR REPLACE INTO campaign_checkpoints (
                                campaign_id, task_index, generation, checkpoint_data
                            ) VALUES (?, ?, ?, ?)
                            """,
                            (
                                campaign_id,
                                task_idx + 1,
                                restored_generation,
                                "{}",
                            ),
                        )
                self.event_bus.publish(
                    CampaignCheckpointed(
                        campaign_id=campaign_id,
                        task_index=task_idx + 1,
                        generation=restored_generation,
                    )
                )

        # 8. Conclude execution if it completed all tasks successfully
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
            # Delete checkpoint
            if self.orchestrator.db_manager:
                with self.orchestrator.db_manager.transaction() as conn:
                    conn.execute(
                        "DELETE FROM campaign_checkpoints WHERE campaign_id = ?",
                        (campaign_id,),
                    )
            if terminal_state == CampaignState.COMPLETED:
                self.event_bus.publish(CampaignCompleted(campaign_id=campaign_id))
            elif terminal_state == CampaignState.CANCELLED:
                self.event_bus.publish(CampaignCancelled(campaign_id=campaign_id))
            self.event_bus.publish(
                CampaignFinished(
                    campaign_id=campaign_id,
                    status=terminal_state.value,
                )
            )
        except Exception as e:
            logger.error("Failed to conclude campaign %s: %s", campaign_id, e)
