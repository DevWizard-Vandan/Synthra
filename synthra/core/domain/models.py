"""Domain models for the SYNTHRA quantitative research loop.

This module defines all core business entities as strongly typed, immutable
Pydantic schemas. It serves as the primary system-wide interface vocabulary.
"""

import re
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class CampaignStatus(str, Enum):
    """Execution status of a research campaign."""
    DRAFT = "draft"
    ACTIVE = "active"
    CONCLUDED = "concluded"


class HypothesisStatus(str, Enum):
    """Validation status of a research hypothesis."""
    DRAFT = "draft"
    TESTED = "tested"
    ARCHIVED = "archived"


class ExperimentStatus(str, Enum):
    """Orchestration status of an experiment simulation."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Region(str, Enum):
    """Trading regions supported by the backtesting platform."""
    US = "US"
    EU = "EU"
    AP = "AP"
    GLB = "GLB"


class Universe(str, Enum):
    """Trading universes supported by the backtesting platform."""
    TOP3000 = "TOP3000"
    TOP2000 = "TOP2000"
    TOP1000 = "TOP1000"
    TOP500 = "TOP500"


class ResearchAssetType(str, Enum):
    """Categories of assets generated during research execution."""
    NOTEBOOK = "notebook"
    REPORT = "report"
    PLOT = "plot"
    FAST_EXPRESSION = "fast_expression"
    PYTHON_ALPHA = "python_alpha"
    DATASET_EXPORT = "dataset_export"
    LOG = "log"


class BaseDomainModel(BaseModel):
    """Base class for all SYNTHRA domain models, enforcing strict immutability."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        arbitrary_types_allowed=True,
        use_enum_values=True,  # Serialize enums directly to their values
    )


class Campaign(BaseDomainModel):
    """Bounding context for a quantitative research program."""

    id: str = Field(..., description="Unique ID matching 'CMP-XXXX'")
    name: str = Field(..., min_length=1)
    region: Region = Field(..., description="Target trading region")
    universe: Universe = Field(..., description="Target trading universe")
    budget_limit: float = Field(..., gt=0.0)
    budget_spent: float = Field(default=0.0, ge=0.0)
    status: CampaignStatus = Field(default=CampaignStatus.DRAFT)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    concluded_at: Optional[datetime] = Field(default=None)

    @field_validator("id")
    @classmethod
    def validate_campaign_id(cls, v: str) -> str:
        """Enforces that the campaign ID follows the strict 'CMP-XXXX' pattern."""
        if not re.match(r"^CMP-\d{4}$", v):
            raise ValueError("Campaign ID must match the format 'CMP-XXXX'")
        return v


class Hypothesis(BaseDomainModel):
    """An economic rationale outlining predictive variables and datasets."""

    id: str = Field(..., description="Unique ID matching 'HYP-XXXX'")
    campaign_id: str = Field(..., description="Parent campaign ID")
    rationale: str = Field(..., min_length=10)
    target_variable: str = Field(..., min_length=1)
    datasets: List[str] = Field(..., min_length=1)
    operators: List[str] = Field(..., min_length=1)
    status: HypothesisStatus = Field(default=HypothesisStatus.DRAFT)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("id")
    @classmethod
    def validate_hypothesis_id(cls, v: str) -> str:
        """Enforces that the hypothesis ID follows the strict 'HYP-XXXX' pattern."""
        if not re.match(r"^HYP-\d{4}$", v):
            raise ValueError("Hypothesis ID must match the format 'HYP-XXXX'")
        return v

    @field_validator("campaign_id")
    @classmethod
    def validate_campaign_id(cls, v: str) -> str:
        """Enforces that campaign ID follows the strict 'CMP-XXXX' pattern."""
        if not re.match(r"^CMP-\d{4}$", v):
            raise ValueError("Campaign ID must match the format 'CMP-XXXX'")
        return v


class SimulationRequest(BaseDomainModel):
    """System-agnostic simulation request parameters."""

    expression: str = Field(..., min_length=1)
    region: Region
    universe: Universe
    delay: int = Field(default=1, ge=0)
    decay: int = Field(default=0, ge=0)
    neutralization: str = Field(default="SUBINDUSTRY", min_length=1)


class SimulationResult(BaseDomainModel):
    """Unified result metrics returned from backtesting."""

    sharpe: float
    fitness: float
    margin: float
    turnover: float
    coverage: float
    simulated_at: datetime = Field(default_factory=datetime.utcnow)


class Experiment(BaseDomainModel):
    """An orchestrated test execution linking a hypothesis variant to results."""

    id: str = Field(..., description="Unique ID matching 'EXP-XXXX'")
    campaign_id: str = Field(..., description="Parent campaign ID")
    hypothesis_id: str = Field(..., description="Parent hypothesis ID")
    expression: str = Field(..., min_length=1)
    status: ExperimentStatus = Field(default=ExperimentStatus.PENDING)
    request: SimulationRequest
    result: Optional[SimulationResult] = Field(default=None)
    error_message: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: Optional[datetime] = Field(default=None)

    @field_validator("id")
    @classmethod
    def validate_experiment_id(cls, v: str) -> str:
        """Enforces that the experiment ID follows the strict 'EXP-XXXX' pattern."""
        if not re.match(r"^EXP-\d{4}$", v):
            raise ValueError("Experiment ID must match the format 'EXP-XXXX'")
        return v

    @field_validator("campaign_id")
    @classmethod
    def validate_campaign_id(cls, v: str) -> str:
        """Enforces that the parent campaign ID follows the 'CMP-XXXX' pattern."""
        if not re.match(r"^CMP-\d{4}$", v):
            raise ValueError("Campaign ID must match the format 'CMP-XXXX'")
        return v

    @field_validator("hypothesis_id")
    @classmethod
    def validate_hypothesis_id(cls, v: str) -> str:
        """Enforces that the parent hypothesis ID follows the 'HYP-XXXX' pattern."""
        if not re.match(r"^HYP-\d{4}$", v):
            raise ValueError("Hypothesis ID must match the format 'HYP-XXXX'")
        return v


class AlphaCandidate(BaseDomainModel):
    """A high-performing strategy flagged for submission review."""

    id: str = Field(..., description="Unique ID matching 'AST-XXXX'")
    experiment_id: str = Field(..., description="Source experiment ID")
    hypothesis_id: str = Field(..., description="Source hypothesis ID")
    campaign_id: str = Field(..., description="Source campaign ID")
    expression: str = Field(..., min_length=1)
    result: SimulationResult = Field(..., description="Embedded backtest results")
    is_submitted: bool = Field(default=False)
    submitted_at: Optional[datetime] = Field(default=None)

    @field_validator("id")
    @classmethod
    def validate_asset_id(cls, v: str) -> str:
        """Enforces that the alpha candidate ID follows the 'AST-XXXX' pattern."""
        if not re.match(r"^AST-\d{4}$", v):
            raise ValueError("Asset ID must match the format 'AST-XXXX'")
        return v

    @field_validator("experiment_id")
    @classmethod
    def validate_experiment_id(cls, v: str) -> str:
        """Enforces that the experiment ID follows the 'EXP-XXXX' pattern."""
        if not re.match(r"^EXP-\d{4}$", v):
            raise ValueError("Experiment ID must match the format 'EXP-XXXX'")
        return v

    @field_validator("hypothesis_id")
    @classmethod
    def validate_hypothesis_id(cls, v: str) -> str:
        """Enforces that the hypothesis ID follows the 'HYP-XXXX' pattern."""
        if not re.match(r"^HYP-\d{4}$", v):
            raise ValueError("Hypothesis ID must match the format 'HYP-XXXX'")
        return v

    @field_validator("campaign_id")
    @classmethod
    def validate_campaign_id(cls, v: str) -> str:
        """Enforces that the campaign ID follows the 'CMP-XXXX' pattern."""
        if not re.match(r"^CMP-\d{4}$", v):
            raise ValueError("Campaign ID must match the format 'CMP-XXXX'")
        return v


class Dataset(BaseDomainModel):
    """Platform dataset metadata profile."""

    name: str = Field(..., min_length=1)
    region: Region = Field(..., description="Region mapping for dataset")
    category: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    fields: List[str] = Field(..., min_length=1)


class Operator(BaseDomainModel):
    """Platform operator metadata signature."""

    name: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1)
    signature: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)


class ResearchAsset(BaseDomainModel):
    """Arbitrary file output produced during the research lifecycle."""

    id: str = Field(..., description="Unique ID matching 'AST-XXXX'")
    campaign_id: str = Field(..., description="Associated campaign ID")
    type: ResearchAssetType = Field(..., description="Asset type classification")
    file_path: Path
    description: str = Field(..., min_length=1)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("id")
    @classmethod
    def validate_asset_id(cls, v: str) -> str:
        """Enforces that the research asset ID follows the 'AST-XXXX' pattern."""
        if not re.match(r"^AST-\d{4}$", v):
            raise ValueError("Asset ID must match the format 'AST-XXXX'")
        return v

    @field_validator("campaign_id")
    @classmethod
    def validate_campaign_id(cls, v: str) -> str:
        """Enforces that the campaign ID follows the 'CMP-XXXX' pattern."""
        if not re.match(r"^CMP-\d{4}$", v):
            raise ValueError("Campaign ID must match the format 'CMP-XXXX'")
        return v
