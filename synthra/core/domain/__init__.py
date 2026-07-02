"""SYNTHRA domain models package.

Exposes all strongly typed, immutable Pydantic models for the quant pipeline.
"""

from synthra.core.domain.models import (
    AlphaCandidate,
    BaseDomainModel,
    Campaign,
    CampaignStatus,
    Dataset,
    Experiment,
    ExperimentStatus,
    Hypothesis,
    HypothesisStatus,
    Operator,
    Region,
    ResearchAsset,
    ResearchAssetType,
    SimulationRequest,
    SimulationResult,
    Universe,
)

__all__ = [
    "BaseDomainModel",
    "Campaign",
    "CampaignStatus",
    "Hypothesis",
    "HypothesisStatus",
    "SimulationRequest",
    "SimulationResult",
    "Experiment",
    "ExperimentStatus",
    "AlphaCandidate",
    "Dataset",
    "Operator",
    "ResearchAsset",
    "ResearchAssetType",
    "Region",
    "Universe",
]
