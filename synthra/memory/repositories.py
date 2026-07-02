"""SQLite implementations of repositories for the SYNTHRA persistence layer."""

from datetime import datetime
import json
import logging
from pathlib import Path
import sqlite3
from typing import List, Optional

from synthra.core.domain import (
    AlphaCandidate,
    Campaign,
    CampaignStatus,
    Experiment,
    ExperimentStatus,
    Hypothesis,
    HypothesisStatus,
    Region,
    ResearchAsset,
    ResearchAssetType,
    SimulationRequest,
    SimulationResult,
    Universe,
)
from synthra.memory.exceptions import DatabaseError, IntegrityError
from synthra.memory.interfaces import (
    IAlphaCandidateRepository,
    ICampaignRepository,
    IExperimentRepository,
    IHypothesisRepository,
    IResearchAssetRepository,
)

logger = logging.getLogger(__name__)


def serialize_dt(dt: Optional[datetime]) -> Optional[str]:
    """Convert datetime object to ISO string format."""
    return dt.isoformat() if dt else None


def deserialize_dt(val: Optional[str]) -> Optional[datetime]:
    """Convert ISO string format to datetime object."""
    return datetime.fromisoformat(val) if val else None


def deserialize_dt_required(val: Optional[str]) -> datetime:
    """Convert ISO string format to a non-optional datetime object."""
    if not val:
        raise DatabaseError("Missing required datetime value")
    return datetime.fromisoformat(val)


class CampaignRepository(ICampaignRepository):
    """SQLite repository for Campaign entities."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def save(self, campaign: Campaign) -> None:
        try:
            cursor = self.conn.execute(
                "SELECT 1 FROM campaigns WHERE id = ?", (campaign.id,)
            )
            exists = cursor.fetchone() is not None

            if exists:
                self.conn.execute(
                    """
                    UPDATE campaigns
                    SET name = ?, region = ?, universe = ?, budget_limit = ?,
                        budget_spent = ?, status = ?, created_at = ?, concluded_at = ?
                    WHERE id = ?
                    """,
                    (
                        campaign.name,
                        campaign.region,
                        campaign.universe,
                        campaign.budget_limit,
                        campaign.budget_spent,
                        campaign.status,
                        serialize_dt(campaign.created_at),
                        serialize_dt(campaign.concluded_at),
                        campaign.id,
                    ),
                )
            else:
                self.conn.execute(
                    """
                    INSERT INTO campaigns (
                        id, name, region, universe, budget_limit,
                        budget_spent, status, created_at, concluded_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        campaign.id,
                        campaign.name,
                        campaign.region,
                        campaign.universe,
                        campaign.budget_limit,
                        campaign.budget_spent,
                        campaign.status,
                        serialize_dt(campaign.created_at),
                        serialize_dt(campaign.concluded_at),
                    ),
                )
        except sqlite3.IntegrityError as err:
            logger.error("Integrity error saving campaign %s: %s", campaign.id, err)
            raise IntegrityError(f"Integrity constraint violation: {err}") from err
        except sqlite3.Error as err:
            logger.error("Error saving campaign %s: %s", campaign.id, err)
            raise DatabaseError(f"Database operation failed: {err}") from err

    def get_by_id(self, campaign_id: str) -> Optional[Campaign]:
        try:
            cursor = self.conn.execute(
                "SELECT * FROM campaigns WHERE id = ?", (campaign_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None
            return Campaign(
                id=row["id"],
                name=row["name"],
                region=Region(row["region"]),
                universe=Universe(row["universe"]),
                budget_limit=row["budget_limit"],
                budget_spent=row["budget_spent"],
                status=CampaignStatus(row["status"]),
                created_at=deserialize_dt_required(row["created_at"]),
                concluded_at=deserialize_dt(row["concluded_at"]),
            )
        except sqlite3.Error as err:
            logger.error("Error getting campaign %s: %s", campaign_id, err)
            raise DatabaseError(f"Database operation failed: {err}") from err

    def list(self) -> List[Campaign]:
        try:
            cursor = self.conn.execute("SELECT * FROM campaigns")
            rows = cursor.fetchall()
            return [
                Campaign(
                    id=row["id"],
                    name=row["name"],
                    region=Region(row["region"]),
                    universe=Universe(row["universe"]),
                    budget_limit=row["budget_limit"],
                    budget_spent=row["budget_spent"],
                    status=CampaignStatus(row["status"]),
                    created_at=deserialize_dt_required(row["created_at"]),
                    concluded_at=deserialize_dt(row["concluded_at"]),
                )
                for row in rows
            ]
        except sqlite3.Error as err:
            logger.error("Error listing campaigns: %s", err)
            raise DatabaseError(f"Database operation failed: {err}") from err


class HypothesisRepository(IHypothesisRepository):
    """SQLite repository for Hypothesis entities."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def save(self, hypothesis: Hypothesis) -> None:
        try:
            cursor = self.conn.execute(
                "SELECT 1 FROM hypotheses WHERE id = ?", (hypothesis.id,)
            )
            exists = cursor.fetchone() is not None

            datasets_str = json.dumps(hypothesis.datasets)
            operators_str = json.dumps(hypothesis.operators)

            if exists:
                self.conn.execute(
                    """
                    UPDATE hypotheses
                    SET campaign_id = ?, rationale = ?, target_variable = ?,
                        datasets = ?, operators = ?, status = ?, created_at = ?
                    WHERE id = ?
                    """,
                    (
                        hypothesis.campaign_id,
                        hypothesis.rationale,
                        hypothesis.target_variable,
                        datasets_str,
                        operators_str,
                        hypothesis.status,
                        serialize_dt(hypothesis.created_at),
                        hypothesis.id,
                    ),
                )
            else:
                self.conn.execute(
                    """
                    INSERT INTO hypotheses (id, campaign_id, rationale, target_variable,
                                            datasets, operators, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        hypothesis.id,
                        hypothesis.campaign_id,
                        hypothesis.rationale,
                        hypothesis.target_variable,
                        datasets_str,
                        operators_str,
                        hypothesis.status,
                        serialize_dt(hypothesis.created_at),
                    ),
                )
        except sqlite3.IntegrityError as err:
            logger.error("Integrity error saving hypothesis %s: %s", hypothesis.id, err)
            raise IntegrityError(f"Integrity constraint violation: {err}") from err
        except sqlite3.Error as err:
            logger.error("Error saving hypothesis %s: %s", hypothesis.id, err)
            raise DatabaseError(f"Database operation failed: {err}") from err

    def get_by_id(self, hypothesis_id: str) -> Optional[Hypothesis]:
        try:
            cursor = self.conn.execute(
                "SELECT * FROM hypotheses WHERE id = ?", (hypothesis_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None
            return Hypothesis(
                id=row["id"],
                campaign_id=row["campaign_id"],
                rationale=row["rationale"],
                target_variable=row["target_variable"],
                datasets=json.loads(row["datasets"]),
                operators=json.loads(row["operators"]),
                status=HypothesisStatus(row["status"]),
                created_at=deserialize_dt_required(row["created_at"]),
            )
        except sqlite3.Error as err:
            logger.error("Error getting hypothesis %s: %s", hypothesis_id, err)
            raise DatabaseError(f"Database operation failed: {err}") from err

    def list_by_campaign(self, campaign_id: str) -> List[Hypothesis]:
        try:
            cursor = self.conn.execute(
                "SELECT * FROM hypotheses WHERE campaign_id = ?", (campaign_id,)
            )
            rows = cursor.fetchall()
            return [
                Hypothesis(
                    id=row["id"],
                    campaign_id=row["campaign_id"],
                    rationale=row["rationale"],
                    target_variable=row["target_variable"],
                    datasets=json.loads(row["datasets"]),
                    operators=json.loads(row["operators"]),
                    status=HypothesisStatus(row["status"]),
                    created_at=deserialize_dt_required(row["created_at"]),
                )
                for row in rows
            ]
        except sqlite3.Error as err:
            logger.error(
                "Error listing hypotheses by campaign %s: %s", campaign_id, err
            )
            raise DatabaseError(f"Database operation failed: {err}") from err

    def list(self) -> List[Hypothesis]:
        try:
            cursor = self.conn.execute("SELECT * FROM hypotheses")
            rows = cursor.fetchall()
            return [
                Hypothesis(
                    id=row["id"],
                    campaign_id=row["campaign_id"],
                    rationale=row["rationale"],
                    target_variable=row["target_variable"],
                    datasets=json.loads(row["datasets"]),
                    operators=json.loads(row["operators"]),
                    status=HypothesisStatus(row["status"]),
                    created_at=deserialize_dt_required(row["created_at"]),
                )
                for row in rows
            ]
        except sqlite3.Error as err:
            logger.error("Error listing hypotheses: %s", err)
            raise DatabaseError(f"Database operation failed: {err}") from err


class ExperimentRepository(IExperimentRepository):
    """SQLite repository for Experiment entities."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def save(self, experiment: Experiment) -> None:
        try:
            cursor = self.conn.execute(
                "SELECT 1 FROM experiments WHERE id = ?", (experiment.id,)
            )
            exists = cursor.fetchone() is not None

            req_str = experiment.request.model_dump_json()
            res_str = experiment.result.model_dump_json() if experiment.result else None

            if exists:
                self.conn.execute(
                    """
                    UPDATE experiments
                    SET campaign_id = ?, hypothesis_id = ?, expression = ?,
                        status = ?, request = ?, result = ?, error_message = ?,
                        created_at = ?, finished_at = ?
                    WHERE id = ?
                    """,
                    (
                        experiment.campaign_id,
                        experiment.hypothesis_id,
                        experiment.expression,
                        experiment.status,
                        req_str,
                        res_str,
                        experiment.error_message,
                        serialize_dt(experiment.created_at),
                        serialize_dt(experiment.finished_at),
                        experiment.id,
                    ),
                )
            else:
                self.conn.execute(
                    """
                    INSERT INTO experiments (id, campaign_id, hypothesis_id, expression,
                                             status, request, result, error_message,
                                             created_at, finished_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        experiment.id,
                        experiment.campaign_id,
                        experiment.hypothesis_id,
                        experiment.expression,
                        experiment.status,
                        req_str,
                        res_str,
                        experiment.error_message,
                        serialize_dt(experiment.created_at),
                        serialize_dt(experiment.finished_at),
                    ),
                )
        except sqlite3.IntegrityError as err:
            logger.error("Integrity error saving experiment %s: %s", experiment.id, err)
            raise IntegrityError(f"Integrity constraint violation: {err}") from err
        except sqlite3.Error as err:
            logger.error("Error saving experiment %s: %s", experiment.id, err)
            raise DatabaseError(f"Database operation failed: {err}") from err

    def _parse_row(self, row: sqlite3.Row) -> Experiment:
        res_val = row["result"]
        res_obj = SimulationResult.model_validate_json(res_val) if res_val else None
        return Experiment(
            id=row["id"],
            campaign_id=row["campaign_id"],
            hypothesis_id=row["hypothesis_id"],
            expression=row["expression"],
            status=ExperimentStatus(row["status"]),
            request=SimulationRequest.model_validate_json(row["request"]),
            result=res_obj,
            error_message=row["error_message"],
            created_at=deserialize_dt_required(row["created_at"]),
            finished_at=deserialize_dt(row["finished_at"]),
        )

    def get_by_id(self, experiment_id: str) -> Optional[Experiment]:
        try:
            cursor = self.conn.execute(
                "SELECT * FROM experiments WHERE id = ?", (experiment_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None
            return self._parse_row(row)
        except sqlite3.Error as err:
            logger.error("Error getting experiment %s: %s", experiment_id, err)
            raise DatabaseError(f"Database operation failed: {err}") from err

    def list_by_campaign(self, campaign_id: str) -> List[Experiment]:
        try:
            cursor = self.conn.execute(
                "SELECT * FROM experiments WHERE campaign_id = ?", (campaign_id,)
            )
            rows = cursor.fetchall()
            return [self._parse_row(row) for row in rows]
        except sqlite3.Error as err:
            logger.error(
                "Error listing experiments by campaign %s: %s", campaign_id, err
            )
            raise DatabaseError(f"Database operation failed: {err}") from err

    def list_by_hypothesis(self, hypothesis_id: str) -> List[Experiment]:
        try:
            cursor = self.conn.execute(
                "SELECT * FROM experiments WHERE hypothesis_id = ?", (hypothesis_id,)
            )
            rows = cursor.fetchall()
            return [self._parse_row(row) for row in rows]
        except sqlite3.Error as err:
            logger.error(
                "Error listing experiments by hypothesis %s: %s", hypothesis_id, err
            )
            raise DatabaseError(f"Database operation failed: {err}") from err

    def list(self) -> List[Experiment]:
        try:
            cursor = self.conn.execute("SELECT * FROM experiments")
            rows = cursor.fetchall()
            return [self._parse_row(row) for row in rows]
        except sqlite3.Error as err:
            logger.error("Error listing experiments: %s", err)
            raise DatabaseError(f"Database operation failed: {err}") from err


class AlphaCandidateRepository(IAlphaCandidateRepository):
    """SQLite repository for AlphaCandidate entities."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def save(self, candidate: AlphaCandidate) -> None:
        try:
            cursor = self.conn.execute(
                "SELECT 1 FROM alpha_candidates WHERE id = ?", (candidate.id,)
            )
            exists = cursor.fetchone() is not None

            res_str = candidate.result.model_dump_json()
            is_sub_val = 1 if candidate.is_submitted else 0

            if exists:
                self.conn.execute(
                    """
                    UPDATE alpha_candidates
                    SET experiment_id = ?, hypothesis_id = ?, campaign_id = ?,
                        expression = ?, result = ?, is_submitted = ?, submitted_at = ?
                    WHERE id = ?
                    """,
                    (
                        candidate.experiment_id,
                        candidate.hypothesis_id,
                        candidate.campaign_id,
                        candidate.expression,
                        res_str,
                        is_sub_val,
                        serialize_dt(candidate.submitted_at),
                        candidate.id,
                    ),
                )
            else:
                self.conn.execute(
                    """
                    INSERT INTO alpha_candidates (id, experiment_id, hypothesis_id,
                                                  campaign_id, expression, result,
                                                  is_submitted, submitted_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        candidate.id,
                        candidate.experiment_id,
                        candidate.hypothesis_id,
                        candidate.campaign_id,
                        candidate.expression,
                        res_str,
                        is_sub_val,
                        serialize_dt(candidate.submitted_at),
                    ),
                )
        except sqlite3.IntegrityError as err:
            logger.error(
                "Integrity error saving alpha candidate %s: %s", candidate.id, err
            )
            raise IntegrityError(f"Integrity constraint violation: {err}") from err
        except sqlite3.Error as err:
            logger.error("Error saving alpha candidate %s: %s", candidate.id, err)
            raise DatabaseError(f"Database operation failed: {err}") from err

    def _parse_row(self, row: sqlite3.Row) -> AlphaCandidate:
        return AlphaCandidate(
            id=row["id"],
            experiment_id=row["experiment_id"],
            hypothesis_id=row["hypothesis_id"],
            campaign_id=row["campaign_id"],
            expression=row["expression"],
            result=SimulationResult.model_validate_json(row["result"]),
            is_submitted=bool(row["is_submitted"]),
            submitted_at=deserialize_dt(row["submitted_at"]),
        )

    def get_by_id(self, candidate_id: str) -> Optional[AlphaCandidate]:
        try:
            cursor = self.conn.execute(
                "SELECT * FROM alpha_candidates WHERE id = ?", (candidate_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None
            return self._parse_row(row)
        except sqlite3.Error as err:
            logger.error("Error getting alpha candidate %s: %s", candidate_id, err)
            raise DatabaseError(f"Database operation failed: {err}") from err

    def list_by_campaign(self, campaign_id: str) -> List[AlphaCandidate]:
        try:
            cursor = self.conn.execute(
                "SELECT * FROM alpha_candidates WHERE campaign_id = ?", (campaign_id,)
            )
            rows = cursor.fetchall()
            return [self._parse_row(row) for row in rows]
        except sqlite3.Error as err:
            logger.error(
                "Error listing alpha candidates by campaign %s: %s", campaign_id, err
            )
            raise DatabaseError(f"Database operation failed: {err}") from err

    def list(self) -> List[AlphaCandidate]:
        try:
            cursor = self.conn.execute("SELECT * FROM alpha_candidates")
            rows = cursor.fetchall()
            return [self._parse_row(row) for row in rows]
        except sqlite3.Error as err:
            logger.error("Error listing alpha candidates: %s", err)
            raise DatabaseError(f"Database operation failed: {err}") from err


class ResearchAssetRepository(IResearchAssetRepository):
    """SQLite repository for ResearchAsset entities."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def save(self, asset: ResearchAsset) -> None:
        try:
            cursor = self.conn.execute(
                "SELECT 1 FROM research_assets WHERE id = ?", (asset.id,)
            )
            exists = cursor.fetchone() is not None

            if exists:
                self.conn.execute(
                    """
                    UPDATE research_assets
                    SET campaign_id = ?, type = ?, file_path = ?,
                        description = ?, created_at = ?
                    WHERE id = ?
                    """,
                    (
                        asset.campaign_id,
                        asset.type,
                        str(asset.file_path),
                        asset.description,
                        serialize_dt(asset.created_at),
                        asset.id,
                    ),
                )
            else:
                self.conn.execute(
                    """
                    INSERT INTO research_assets (id, campaign_id, type, file_path,
                                                 description, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        asset.id,
                        asset.campaign_id,
                        asset.type,
                        str(asset.file_path),
                        asset.description,
                        serialize_dt(asset.created_at),
                    ),
                )
        except sqlite3.IntegrityError as err:
            logger.error("Integrity error saving research asset %s: %s", asset.id, err)
            raise IntegrityError(f"Integrity constraint violation: {err}") from err
        except sqlite3.Error as err:
            logger.error("Error saving research asset %s: %s", asset.id, err)
            raise DatabaseError(f"Database operation failed: {err}") from err

    def _parse_row(self, row: sqlite3.Row) -> ResearchAsset:
        return ResearchAsset(
            id=row["id"],
            campaign_id=row["campaign_id"],
            type=ResearchAssetType(row["type"]),
            file_path=Path(row["file_path"]),
            description=row["description"],
            created_at=deserialize_dt_required(row["created_at"]),
        )

    def get_by_id(self, asset_id: str) -> Optional[ResearchAsset]:
        try:
            cursor = self.conn.execute(
                "SELECT * FROM research_assets WHERE id = ?", (asset_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None
            return self._parse_row(row)
        except sqlite3.Error as err:
            logger.error("Error getting research asset %s: %s", asset_id, err)
            raise DatabaseError(f"Database operation failed: {err}") from err

    def list_by_campaign(self, campaign_id: str) -> List[ResearchAsset]:
        try:
            cursor = self.conn.execute(
                "SELECT * FROM research_assets WHERE campaign_id = ?", (campaign_id,)
            )
            rows = cursor.fetchall()
            return [self._parse_row(row) for row in rows]
        except sqlite3.Error as err:
            logger.error(
                "Error listing research assets by campaign %s: %s", campaign_id, err
            )
            raise DatabaseError(f"Database operation failed: {err}") from err

    def list(self) -> List[ResearchAsset]:
        try:
            cursor = self.conn.execute("SELECT * FROM research_assets")
            rows = cursor.fetchall()
            return [self._parse_row(row) for row in rows]
        except sqlite3.Error as err:
            logger.error("Error listing research assets: %s", err)
            raise DatabaseError(f"Database operation failed: {err}") from err
