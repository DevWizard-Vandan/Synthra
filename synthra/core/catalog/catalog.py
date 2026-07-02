"""Local metadata catalog loading from versioned TOML configurations."""

from pathlib import Path
import tomllib
from typing import Dict, List, Optional

from synthra.core.domain import Dataset, Operator, Region, Universe
from synthra.core.catalog.exceptions import DatasetNotFoundError, OperatorNotFoundError
from synthra.core.catalog.models import DatasetMetadata, FieldMetadata, OperatorMetadata
from synthra.core.catalog.tokenizer import tokenize_expression, TokenType


class DatasetCatalog:
    """Offline Dataset Catalog providing single source of truth for metadata."""

    def __init__(self, toml_path: Optional[Path] = None) -> None:
        """Initialize the catalog by loading TOML resource and indexing metadata.

        Args:
            toml_path: Optional path to the catalog TOML file. Resolves to the
                       default configuration location if omitted.
        """
        if toml_path is None:
            # Default to the versioned catalog configuration location
            toml_path = Path(__file__).parents[3] / "config" / "catalog.toml"
            if not toml_path.exists():
                toml_path = Path("config/catalog.toml")

        # Load raw TOML structure
        try:
            with open(toml_path, "rb") as f:
                config_data = tomllib.load(f)
        except (OSError, tomllib.TOMLDecodeError) as err:
            raise RuntimeError(
                f"Failed to load catalog TOML file at {toml_path}: {err}"
            ) from err

        # Primary maps
        self._datasets: Dict[str, Dataset] = {}
        self._operators: Dict[str, Operator] = {}

        # Rich Metadata maps (by primary name)
        self._dataset_metadata: Dict[str, DatasetMetadata] = {}
        self._operator_metadata: Dict[str, OperatorMetadata] = {}

        # O(1) Lookup indexes (mapping both primary names and aliases)
        self._dataset_by_alias: Dict[str, DatasetMetadata] = {}
        self._operator_by_alias: Dict[str, OperatorMetadata] = {}
        self._field_by_alias: Dict[str, Dict[str, FieldMetadata]] = {}

        # Parse datasets from TOML configuration
        for ds_data in config_data.get("datasets", []):
            # Parse list of fields
            fields_list = []
            for f_data in ds_data.get("fields", []):
                field_meta = FieldMetadata(
                    name=f_data["name"],
                    description=f_data["description"],
                    data_type=f_data["data_type"],
                    frequency=f_data["frequency"],
                    delay=f_data["delay"],
                    nullable=f_data.get("nullable", False),
                    aliases=f_data.get("aliases", []),
                )
                fields_list.append(field_meta)

            ds_meta = DatasetMetadata(
                name=ds_data["name"],
                description=ds_data["description"],
                category=ds_data["category"],
                regions=[Region(r) for r in ds_data.get("regions", [])],
                universes=[Universe(u) for u in ds_data.get("universes", [])],
                aliases=ds_data.get("aliases", []),
                fields=fields_list,
            )

            # Store in primary metadata map
            self._dataset_metadata[ds_meta.name] = ds_meta

            # Populate alias and name index
            self._dataset_by_alias[ds_meta.name] = ds_meta
            for alias in ds_meta.aliases:
                self._dataset_by_alias[alias] = ds_meta

            # Build field alias/name index for this dataset
            field_index: Dict[str, FieldMetadata] = {}
            for f_meta in ds_meta.fields:
                field_index[f_meta.name] = f_meta
                for f_alias in f_meta.aliases:
                    field_index[f_alias] = f_meta
            self._field_by_alias[ds_meta.name] = field_index

            # Create default domain model wrapper (GLB or first region)
            if "GLB" in ds_meta.regions:
                default_region = Region.GLB
            else:
                default_region = Region(ds_meta.regions[0])
            self._datasets[ds_meta.name] = Dataset(
                name=ds_meta.name,
                region=default_region,
                category=ds_meta.category,
                description=ds_meta.description,
                fields=sorted([f.name for f in ds_meta.fields]),
            )

        # Parse operators from TOML configuration
        for op_data in config_data.get("operators", []):
            op_meta = OperatorMetadata(
                name=op_data["name"],
                description=op_data["description"],
                category=op_data["category"],
                signature=op_data["signature"],
                min_args=op_data["min_args"],
                max_args=op_data["max_args"],
                argument_types=op_data.get("argument_types", []),
                return_type=op_data["return_type"],
                aliases=op_data.get("aliases", []),
            )

            # Store in primary metadata map
            self._operator_metadata[op_meta.name] = op_meta

            # Populate alias and name index
            self._operator_by_alias[op_meta.name] = op_meta
            for alias in op_meta.aliases:
                self._operator_by_alias[alias] = op_meta

            # Create domain model wrapper
            self._operators[op_meta.name] = Operator(
                name=op_meta.name,
                category=op_meta.category,
                signature=op_meta.signature,
                description=op_meta.description,
            )

    def get_dataset(self, name: str) -> Optional[Dataset]:
        """Retrieve a dataset by its name or alias from the catalog."""
        ds_meta = self._dataset_by_alias.get(name)
        if not ds_meta:
            return None
        return self._datasets[ds_meta.name]

    def get_operator(self, name: str) -> Optional[Operator]:
        """Retrieve an operator by its name or alias from the catalog."""
        op_meta = self._operator_by_alias.get(name)
        if not op_meta:
            return None
        return self._operators[op_meta.name]

    def get_dataset_metadata(self, name: str) -> Optional[DatasetMetadata]:
        """Retrieve rich metadata for a dataset by name or alias."""
        return self._dataset_by_alias.get(name)

    def get_operator_metadata(self, name: str) -> Optional[OperatorMetadata]:
        """Retrieve rich metadata for an operator by name or alias."""
        return self._operator_by_alias.get(name)

    def get_field_metadata(
        self, dataset_name: str, field_name: str
    ) -> Optional[FieldMetadata]:
        """Retrieve rich metadata for a field by dataset and field name/alias."""
        ds_meta = self._dataset_by_alias.get(dataset_name)
        if not ds_meta:
            return None
        return self._field_by_alias[ds_meta.name].get(field_name)

    def search_datasets(self, query: str) -> List[Dataset]:
        """Search datasets by query in name, category, description, or aliases."""
        query_lc = query.lower()
        results = []
        seen = set()
        for meta in self._dataset_metadata.values():
            if meta.name in seen:
                continue
            if (
                query_lc in meta.name.lower()
                or query_lc in meta.category.lower()
                or query_lc in meta.description.lower()
                or any(query_lc in alias.lower() for alias in meta.aliases)
            ):
                results.append(self._datasets[meta.name])
                seen.add(meta.name)
        return results

    def filter_datasets(
        self, region: Optional[Region] = None, universe: Optional[Universe] = None
    ) -> List[Dataset]:
        """Filter datasets by region and universe compatibility."""
        results = []
        for meta in self._dataset_metadata.values():
            if region and region.value not in meta.regions:
                continue
            if universe and universe.value not in meta.universes:
                continue
            results.append(self._datasets[meta.name])
        return results

    def search_operators(self, query: str) -> List[Operator]:
        """Search operators by query in name, category, description, or aliases."""
        query_lc = query.lower()
        results = []
        seen = set()
        for meta in self._operator_metadata.values():
            if meta.name in seen:
                continue
            if (
                query_lc in meta.name.lower()
                or query_lc in meta.category.lower()
                or query_lc in meta.description.lower()
                or any(query_lc in alias.lower() for alias in meta.aliases)
            ):
                results.append(self._operators[meta.name])
                seen.add(meta.name)
        return results

    def filter_operators(self, category: str) -> List[Operator]:
        """Filter operators by category."""
        return [
            self._operators[meta.name]
            for meta in self._operator_metadata.values()
            if meta.category == category
        ]

    def validate_field(self, dataset_name: str, field_name: str) -> bool:
        """Validate if a field exists inside a target dataset (supports aliases)."""
        ds_meta = self._dataset_by_alias.get(dataset_name)
        if not ds_meta:
            return False
        fields_index = self._field_by_alias[ds_meta.name]
        return field_name in fields_index

    def validate_delay(self, dataset_name: str, field_name: str, delay: int) -> bool:
        """Verify if delay is compatible with field reporting latency.

        Args:
            dataset_name: Target dataset (name or alias).
            field_name: Target field (name or alias).
            delay: Proposed backtest delay.
        """
        ds_meta = self._dataset_by_alias.get(dataset_name)
        if not ds_meta:
            raise DatasetNotFoundError(f"Dataset {dataset_name} not found")
        fields_index = self._field_by_alias[ds_meta.name]
        field_meta = fields_index.get(field_name)
        if not field_meta:
            raise ValueError(f"Field {field_name} not found in dataset {dataset_name}")

        return bool(delay >= field_meta.delay)

    def validate_operator(self, operator_name: str, arg_count: int) -> bool:
        """Verify if operator is registered and matches the arity constraint."""
        op_meta = self._operator_by_alias.get(operator_name)
        if not op_meta:
            return False
        return bool(op_meta.min_args <= arg_count <= op_meta.max_args)

    def validate_expression_variables(
        self, expression: str, dataset_name: str
    ) -> List[str]:
        """Validate expression variables against a target dataset.

        Returns:
            A list of invalid variable names. If empty, the expression is valid.
        """
        ds_meta = self._dataset_by_alias.get(dataset_name)
        if not ds_meta:
            raise DatasetNotFoundError(f"Dataset {dataset_name} not found")

        # Use the expression tokenizer
        tokens = tokenize_expression(expression)
        invalid_vars = set()
        fields_index = self._field_by_alias[ds_meta.name]

        for token in tokens:
            if token.type == TokenType.IDENTIFIER:
                val = token.value
                # If it is a registered operator, it is not a variable
                if val in self._operator_by_alias:
                    continue
                # If it is a field in the dataset, it is a valid variable
                if val in fields_index:
                    continue
                invalid_vars.add(val)

        return sorted(list(invalid_vars))

    def get_field_description(self, dataset_name: str, field_name: str) -> str:
        """Retrieve description for a specific dataset field."""
        ds_meta = self._dataset_by_alias.get(dataset_name)
        if not ds_meta:
            raise DatasetNotFoundError(f"Dataset {dataset_name} not found")
        field_meta = self._field_by_alias[ds_meta.name].get(field_name)
        if not field_meta:
            raise ValueError(f"Field {field_name} not found in dataset {dataset_name}")
        return field_meta.description

    def get_operator_arity(self, operator_name: str) -> int:
        """Retrieve the required argument count (arity) of an operator."""
        op_meta = self._operator_by_alias.get(operator_name)
        if not op_meta:
            raise OperatorNotFoundError(f"Operator {operator_name} not found")
        return op_meta.min_args
