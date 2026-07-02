"""Repository interfaces for the SYNTHRA persistence layer."""

from abc import ABC, abstractmethod
from typing import List, Optional
from synthra.core.domain import (
    AlphaCandidate,
    Campaign,
    Experiment,
    Hypothesis,
    ResearchAsset,
)


class ICampaignRepository(ABC):
    """Interface for Campaign persistence."""

    @abstractmethod
    def save(self, campaign: Campaign) -> None:
        """Create or update a campaign."""
        pass

    @abstractmethod
    def get_by_id(self, campaign_id: str) -> Optional[Campaign]:
        """Retrieve a campaign by its ID."""
        pass

    @abstractmethod
    def list(self) -> List[Campaign]:
        """Retrieve all campaigns."""
        pass


class IHypothesisRepository(ABC):
    """Interface for Hypothesis persistence."""

    @abstractmethod
    def save(self, hypothesis: Hypothesis) -> None:
        """Create or update a hypothesis."""
        pass

    @abstractmethod
    def get_by_id(self, hypothesis_id: str) -> Optional[Hypothesis]:
        """Retrieve a hypothesis by its ID."""
        pass

    @abstractmethod
    def list_by_campaign(self, campaign_id: str) -> List[Hypothesis]:
        """Retrieve all hypotheses associated with a campaign."""
        pass

    @abstractmethod
    def list(self) -> List[Hypothesis]:
        """Retrieve all hypotheses."""
        pass


class IExperimentRepository(ABC):
    """Interface for Experiment persistence."""

    @abstractmethod
    def save(self, experiment: Experiment) -> None:
        """Create or update an experiment."""
        pass

    @abstractmethod
    def get_by_id(self, experiment_id: str) -> Optional[Experiment]:
        """Retrieve an experiment by its ID."""
        pass

    @abstractmethod
    def list_by_campaign(self, campaign_id: str) -> List[Experiment]:
        """Retrieve all experiments associated with a campaign."""
        pass

    @abstractmethod
    def list_by_hypothesis(self, hypothesis_id: str) -> List[Experiment]:
        """Retrieve all experiments associated with a hypothesis."""
        pass

    @abstractmethod
    def list(self) -> List[Experiment]:
        """Retrieve all experiments."""
        pass


class IAlphaCandidateRepository(ABC):
    """Interface for AlphaCandidate persistence."""

    @abstractmethod
    def save(self, candidate: AlphaCandidate) -> None:
        """Create or update an alpha candidate."""
        pass

    @abstractmethod
    def get_by_id(self, candidate_id: str) -> Optional[AlphaCandidate]:
        """Retrieve an alpha candidate by its ID."""
        pass

    @abstractmethod
    def list_by_campaign(self, campaign_id: str) -> List[AlphaCandidate]:
        """Retrieve all alpha candidates associated with a campaign."""
        pass

    @abstractmethod
    def list(self) -> List[AlphaCandidate]:
        """Retrieve all alpha candidates."""
        pass


class IResearchAssetRepository(ABC):
    """Interface for ResearchAsset persistence."""

    @abstractmethod
    def save(self, asset: ResearchAsset) -> None:
        """Create or update a research asset."""
        pass

    @abstractmethod
    def get_by_id(self, asset_id: str) -> Optional[ResearchAsset]:
        """Retrieve a research asset by its ID."""
        pass

    @abstractmethod
    def list_by_campaign(self, campaign_id: str) -> List[ResearchAsset]:
        """Retrieve all research assets associated with a campaign."""
        pass

    @abstractmethod
    def list(self) -> List[ResearchAsset]:
        """Retrieve all research assets."""
        pass
