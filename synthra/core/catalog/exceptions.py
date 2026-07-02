"""Exceptions for the Dataset Catalog subsystem."""


class CatalogError(Exception):
    """Base exception for all Dataset Catalog errors."""

    pass


class DatasetNotFoundError(CatalogError):
    """Raised when a requested dataset is not found in the catalog."""

    pass


class OperatorNotFoundError(CatalogError):
    """Raised when a requested operator is not found in the catalog."""

    pass
