"""Exceptions for the SYNTHRA persistence layer."""


class DatabaseError(Exception):
    """Base exception for all persistence layer errors."""

    pass


class EntityNotFoundError(DatabaseError):
    """Raised when an operation references a non-existent entity."""

    pass


class IntegrityError(DatabaseError):
    """Raised when a database constraint (like foreign keys) is violated."""

    pass
