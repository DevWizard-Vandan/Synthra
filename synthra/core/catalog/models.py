"""Rich metadata models for the Dataset Catalog subsystem."""

from typing import List
from pydantic import Field

from synthra.core.domain import BaseDomainModel, Region, Universe


class FieldMetadata(BaseDomainModel):
    """Rich metadata profile for a dataset field."""

    name: str
    description: str
    data_type: str
    frequency: str
    delay: int
    nullable: bool = False
    aliases: List[str] = Field(default_factory=list)


class DatasetMetadata(BaseDomainModel):
    """Rich metadata profile for a dataset."""

    name: str
    description: str
    category: str
    regions: List[Region]
    universes: List[Universe]
    aliases: List[str] = Field(default_factory=list)
    fields: List[FieldMetadata]


class OperatorMetadata(BaseDomainModel):
    """Rich metadata profile for an operator."""

    name: str
    description: str
    category: str
    signature: str
    min_args: int
    max_args: int
    argument_types: List[str]
    return_type: str
    aliases: List[str] = Field(default_factory=list)
