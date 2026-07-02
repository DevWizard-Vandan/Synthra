"""Unit tests for the SYNTHRA SQLite persistence layer."""

from datetime import datetime
from pathlib import Path
import pytest


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
from synthra.memory import (
    AlphaCandidateRepository,
    CampaignRepository,
    DatabaseManager,
    ExperimentRepository,
    HypothesisRepository,
    IntegrityError,
    ResearchAssetRepository,
)


@pytest.fixture
def db_manager(tmp_path: Path) -> DatabaseManager:
    """Fixture providing a temporary file-backed DatabaseManager."""
    db_file = tmp_path / "test_synthra.db"
    return DatabaseManager(str(db_file))


def test_database_initialization_and_migrations(db_manager: DatabaseManager) -> None:
    """Tests that DB manager successfully initializes and runs migrations."""
    with db_manager.connection() as conn:
        # Check that all tables exist
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [row["name"] for row in cursor.fetchall()]
        assert "campaigns" in tables
        assert "hypotheses" in tables
        assert "experiments" in tables
        assert "alpha_candidates" in tables
        assert "research_assets" in tables
        assert "schema_migrations" in tables

        # Verify migration record is present
        cursor = conn.execute("SELECT version FROM schema_migrations")
        row = cursor.fetchone()
        assert row is not None
        assert row["version"] == 1


def test_campaign_repository_crud(db_manager: DatabaseManager) -> None:
    """Tests CampaignRepository basic save, retrieve, list, and update actions."""
    campaign = Campaign(
        id="CMP-0001",
        name="Trend Following Research",
        region=Region.US,
        universe=Universe.TOP3000,
        budget_limit=1000.0,
        budget_spent=0.0,
        status=CampaignStatus.DRAFT,
    )

    with db_manager.transaction() as conn:
        repo = CampaignRepository(conn)
        # Test save (insert)
        repo.save(campaign)

    with db_manager.connection() as conn:
        repo = CampaignRepository(conn)
        # Test get_by_id
        retrieved = repo.get_by_id("CMP-0001")
        assert retrieved is not None
        assert retrieved.id == "CMP-0001"
        assert retrieved.name == "Trend Following Research"
        assert retrieved.region == Region.US
        assert retrieved.status == CampaignStatus.DRAFT

        # Test list
        campaigns = repo.list()
        assert len(campaigns) == 1
        assert campaigns[0].id == "CMP-0001"

    # Test update
    updated_campaign = Campaign(
        id="CMP-0001",
        name="Trend Following Research Updated",
        region=Region.US,
        universe=Universe.TOP3000,
        budget_limit=1000.0,
        budget_spent=250.0,
        status=CampaignStatus.ACTIVE,
        created_at=campaign.created_at,
        concluded_at=datetime.utcnow(),
    )

    with db_manager.transaction() as conn:
        repo = CampaignRepository(conn)
        repo.save(updated_campaign)

    with db_manager.connection() as conn:
        repo = CampaignRepository(conn)
        retrieved = repo.get_by_id("CMP-0001")
        assert retrieved is not None
        assert retrieved.name == "Trend Following Research Updated"
        assert retrieved.budget_spent == 250.0
        assert retrieved.status == CampaignStatus.ACTIVE
        assert retrieved.concluded_at is not None


def test_hypothesis_repository_crud(db_manager: DatabaseManager) -> None:
    """Tests HypothesisRepository save, list, and foreign key enforcement."""
    campaign = Campaign(
        id="CMP-0001",
        name="Trend Following Research",
        region=Region.US,
        universe=Universe.TOP3000,
        budget_limit=1000.0,
        budget_spent=0.0,
    )

    hypothesis = Hypothesis(
        id="HYP-0001",
        campaign_id="CMP-0001",
        rationale="If 20-day returns are positive, trend continues.",
        target_variable="returns",
        datasets=["pv_history"],
        operators=["ts_rank"],
        status=HypothesisStatus.DRAFT,
    )

    # Save hypothesis without saving campaign first -> should raise IntegrityError
    with pytest.raises(IntegrityError):
        with db_manager.transaction() as conn:
            repo = HypothesisRepository(conn)
            repo.save(hypothesis)

    # Save campaign, then hypothesis
    with db_manager.transaction() as conn:
        CampaignRepository(conn).save(campaign)
        HypothesisRepository(conn).save(hypothesis)

    # Retrieve and list checks
    with db_manager.connection() as conn:
        repo = HypothesisRepository(conn)
        retrieved = repo.get_by_id("HYP-0001")
        assert retrieved is not None
        assert retrieved.id == "HYP-0001"
        assert retrieved.datasets == ["pv_history"]
        assert retrieved.operators == ["ts_rank"]

        by_camp = repo.list_by_campaign("CMP-0001")
        assert len(by_camp) == 1
        assert by_camp[0].id == "HYP-0001"

        all_hyps = repo.list()
        assert len(all_hyps) == 1


def test_experiment_repository_crud(db_manager: DatabaseManager) -> None:
    """Tests ExperimentRepository handling of nested Pydantic models."""
    campaign = Campaign(
        id="CMP-0001",
        name="Trend Following",
        region=Region.US,
        universe=Universe.TOP3000,
        budget_limit=1000.0,
    )
    hypothesis = Hypothesis(
        id="HYP-0001",
        campaign_id="CMP-0001",
        rationale="Some generic rationale here.",
        target_variable="ret",
        datasets=["prices"],
        operators=["ts_sum"],
    )

    req = SimulationRequest(
        expression="ts_sum(close, 10)", region=Region.US, universe=Universe.TOP3000
    )
    res = SimulationResult(
        sharpe=1.2, fitness=1.0, margin=0.05, turnover=0.3, coverage=0.9
    )

    experiment = Experiment(
        id="EXP-0001",
        campaign_id="CMP-0001",
        hypothesis_id="HYP-0001",
        expression="ts_sum(close, 10)",
        status=ExperimentStatus.COMPLETED,
        request=req,
        result=res,
    )

    with db_manager.transaction() as conn:
        CampaignRepository(conn).save(campaign)
        HypothesisRepository(conn).save(hypothesis)
        ExperimentRepository(conn).save(experiment)

    with db_manager.connection() as conn:
        repo = ExperimentRepository(conn)
        retrieved = repo.get_by_id("EXP-0001")
        assert retrieved is not None
        assert retrieved.id == "EXP-0001"
        assert retrieved.status == ExperimentStatus.COMPLETED
        assert retrieved.request.expression == "ts_sum(close, 10)"
        assert retrieved.result is not None
        assert retrieved.result.sharpe == 1.2
        assert retrieved.result.coverage == 0.9

        by_camp = repo.list_by_campaign("CMP-0001")
        assert len(by_camp) == 1

        by_hyp = repo.list_by_hypothesis("HYP-0001")
        assert len(by_hyp) == 1


def test_alpha_candidate_repository_crud(db_manager: DatabaseManager) -> None:
    """Tests AlphaCandidateRepository with embedded SimulationResult."""
    campaign = Campaign(
        id="CMP-0001",
        name="Trend Following",
        region=Region.US,
        universe=Universe.TOP3000,
        budget_limit=1000.0,
    )
    hypothesis = Hypothesis(
        id="HYP-0001",
        campaign_id="CMP-0001",
        rationale="Some generic rationale here.",
        target_variable="ret",
        datasets=["prices"],
        operators=["ts_sum"],
    )
    req = SimulationRequest(
        expression="ts_sum(close, 10)", region=Region.US, universe=Universe.TOP3000
    )
    res = SimulationResult(
        sharpe=1.2, fitness=1.0, margin=0.05, turnover=0.3, coverage=0.9
    )
    experiment = Experiment(
        id="EXP-0001",
        campaign_id="CMP-0001",
        hypothesis_id="HYP-0001",
        expression="ts_sum(close, 10)",
        request=req,
        result=res,
    )

    candidate = AlphaCandidate(
        id="AST-0001",
        experiment_id="EXP-0001",
        hypothesis_id="HYP-0001",
        campaign_id="CMP-0001",
        expression="ts_sum(close, 10)",
        result=res,
        is_submitted=False,
    )

    with db_manager.transaction() as conn:
        CampaignRepository(conn).save(campaign)
        HypothesisRepository(conn).save(hypothesis)
        ExperimentRepository(conn).save(experiment)
        AlphaCandidateRepository(conn).save(candidate)

    with db_manager.connection() as conn:
        repo = AlphaCandidateRepository(conn)
        retrieved = repo.get_by_id("AST-0001")
        assert retrieved is not None
        assert retrieved.id == "AST-0001"
        assert retrieved.result.sharpe == 1.2
        assert not retrieved.is_submitted
        assert retrieved.submitted_at is None

    # Test update submission status
    updated = AlphaCandidate(
        id="AST-0001",
        experiment_id="EXP-0001",
        hypothesis_id="HYP-0001",
        campaign_id="CMP-0001",
        expression="ts_sum(close, 10)",
        result=res,
        is_submitted=True,
        submitted_at=datetime.utcnow(),
    )

    with db_manager.transaction() as conn:
        AlphaCandidateRepository(conn).save(updated)

    with db_manager.connection() as conn:
        repo = AlphaCandidateRepository(conn)
        retrieved = repo.get_by_id("AST-0001")
        assert retrieved is not None
        assert retrieved.is_submitted
        assert retrieved.submitted_at is not None


def test_research_asset_repository_crud(db_manager: DatabaseManager) -> None:
    """Tests ResearchAssetRepository Path serialization and type Enums."""
    campaign = Campaign(
        id="CMP-0001",
        name="Trend Following",
        region=Region.US,
        universe=Universe.TOP3000,
        budget_limit=1000.0,
    )

    asset = ResearchAsset(
        id="AST-0002",
        campaign_id="CMP-0001",
        type=ResearchAssetType.REPORT,
        file_path=Path("outputs/reports/summary.pdf"),
        description="Execution final PDF report",
    )

    with db_manager.transaction() as conn:
        CampaignRepository(conn).save(campaign)
        ResearchAssetRepository(conn).save(asset)

    with db_manager.connection() as conn:
        repo = ResearchAssetRepository(conn)
        retrieved = repo.get_by_id("AST-0002")
        assert retrieved is not None
        assert retrieved.id == "AST-0002"
        assert retrieved.type == ResearchAssetType.REPORT
        assert retrieved.file_path == Path("outputs/reports/summary.pdf")


def test_transaction_rollback_on_failure(db_manager: DatabaseManager) -> None:
    """Tests that db_manager transaction rollback works on exceptions."""
    campaign = Campaign(
        id="CMP-0001",
        name="Trend Following Research",
        region=Region.US,
        universe=Universe.TOP3000,
        budget_limit=1000.0,
    )

    # Let's save a campaign inside a transaction block that subsequently fails
    try:
        with db_manager.transaction() as conn:
            CampaignRepository(conn).save(campaign)
            # Raise an arbitrary exception to force rollback
            raise ValueError("Forced error to verify rollback")
    except ValueError:
        pass

    # Confirm that the campaign was NOT saved (it was rolled back)
    with db_manager.connection() as conn:
        repo = CampaignRepository(conn)
        assert repo.get_by_id("CMP-0001") is None
