"""Exceptions for the Governor and Campaign Scheduler."""


class GovernorError(Exception):
    """Base exception for all governor and scheduler errors."""

    pass


class InvalidStateTransition(GovernorError):
    """Raised when an invalid campaign state transition is attempted."""

    pass


class CampaignNotFoundError(GovernorError):
    """Raised when a campaign is not found in the queue or scheduler."""

    pass
