"""Campaign state machine defining allowed statuses and transitions."""

from enum import Enum
from typing import Set

from synthra.governor.exceptions import InvalidStateTransition


class CampaignState(str, Enum):
    """Lifecycle states of a research campaign managed by the scheduler."""

    DRAFT = "draft"
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# Valid state transition mapping
ALLOWED_TRANSITIONS = {
    CampaignState.DRAFT: {CampaignState.QUEUED, CampaignState.CANCELLED},
    CampaignState.QUEUED: {
        CampaignState.RUNNING,
        CampaignState.PAUSED,
        CampaignState.CANCELLED,
    },
    CampaignState.RUNNING: {
        CampaignState.PAUSED,
        CampaignState.COMPLETED,
        CampaignState.FAILED,
        CampaignState.CANCELLED,
    },
    CampaignState.PAUSED: {
        CampaignState.QUEUED,
        CampaignState.RUNNING,
        CampaignState.CANCELLED,
    },
    CampaignState.COMPLETED: set(),
    CampaignState.FAILED: {CampaignState.QUEUED, CampaignState.CANCELLED},
    CampaignState.CANCELLED: set(),
}


def validate_transition(from_state: CampaignState, to_state: CampaignState) -> None:
    """Validate a transition between two CampaignStates.

    Raises InvalidStateTransition if the transition is prohibited.
    """
    allowed: Set[CampaignState] = ALLOWED_TRANSITIONS.get(from_state, set())
    if to_state not in allowed:
        raise InvalidStateTransition(
            f"Prohibited transition: {from_state.value} -> {to_state.value}"
        )
