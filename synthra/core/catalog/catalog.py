"""Local metadata catalog for datasets, fields, and operators in SYNTHRA."""

import re
from typing import Any, Dict, List, Optional, Set

from synthra.core.domain import Dataset, Operator, Region, Universe
from synthra.core.catalog.exceptions import DatasetNotFoundError, OperatorNotFoundError

# Static definitions representing the WorldQuant BRAIN dataset metadata
DATASETS_METADATA: Dict[str, Any] = {
    "pv": {
        "description": "Standard daily price-volume market data",
        "category": "market_data",
        "regions": {Region.US, Region.EU, Region.AP, Region.GLB},
        "universes": {
            Universe.TOP3000,
            Universe.TOP2000,
            Universe.TOP1000,
            Universe.TOP500,
        },
        "fields": {
            "open": {"min_delay": 1, "description": "Opening price"},
            "close": {"min_delay": 1, "description": "Closing price"},
            "high": {"min_delay": 1, "description": "Highest daily price"},
            "low": {"min_delay": 1, "description": "Lowest daily price"},
            "volume": {"min_delay": 1, "description": "Total traded volume"},
            "vwap": {"min_delay": 1, "description": "Volume-weighted average price"},
            "returns": {"min_delay": 1, "description": "Daily asset returns"},
        },
    },
    "fundamental": {
        "description": "Corporate fundamental accounting metrics",
        "category": "fundamentals",
        "regions": {Region.US, Region.EU},
        "universes": {Universe.TOP2000, Universe.TOP1000, Universe.TOP500},
        "fields": {
            "assets": {"min_delay": 2, "description": "Total corporate assets"},
            "liabilities": {"min_delay": 2, "description": "Total liabilities"},
            "book_value": {"min_delay": 2, "description": "Total book value of equity"},
            "ebitda": {
                "min_delay": 2,
                "description": (
                    "Earnings before interest, taxes, depreciation, and amortization"
                ),
            },
            "net_income": {"min_delay": 2, "description": "Net income"},
        },
    },
    "analyst": {
        "description": "Analyst consensus estimates and recommendations",
        "category": "analyst_estimates",
        "regions": {Region.US},
        "universes": {Universe.TOP2000, Universe.TOP1000, Universe.TOP500},
        "fields": {
            "eps_est": {
                "min_delay": 1,
                "description": "Consensus earnings per share estimate",
            },
            "rev_est": {"min_delay": 1, "description": "Consensus revenue estimate"},
            "recommendation": {
                "min_delay": 1,
                "description": "Average recommendation rating score",
            },
        },
    },
}

# Static definitions representing WorldQuant BRAIN mathematical operators
OPERATORS_METADATA: Dict[str, Any] = {
    "ts_mean": {
        "category": "time_series",
        "signature": "ts_mean(x, d)",
        "description": "Moving average of x for the past d days",
        "arity": 2,
    },
    "ts_sum": {
        "category": "time_series",
        "signature": "ts_sum(x, d)",
        "description": "Moving sum of x for the past d days",
        "arity": 2,
    },
    "rank": {
        "category": "cross_sectional",
        "signature": "rank(x)",
        "description": "Cross-sectional percentile rank of x",
        "arity": 1,
    },
    "delay": {
        "category": "time_series",
        "signature": "delay(x, d)",
        "description": "Value of x delayed by d days",
        "arity": 2,
    },
    "ts_rank": {
        "category": "time_series",
        "signature": "ts_rank(x, d)",
        "description": "Percentile rank of x for the past d days",
        "arity": 2,
    },
    "ts_std_dev": {
        "category": "time_series",
        "signature": "ts_std_dev(x, d)",
        "description": "Moving standard deviation of x for the past d days",
        "arity": 2,
    },
    "ts_max": {
        "category": "time_series",
        "signature": "ts_max(x, d)",
        "description": "Moving maximum of x for the past d days",
        "arity": 2,
    },
    "ts_min": {
        "category": "time_series",
        "signature": "ts_min(x, d)",
        "description": "Moving minimum of x for the past d days",
        "arity": 2,
    },
    "ts_delta": {
        "category": "time_series",
        "signature": "ts_delta(x, d)",
        "description": "Difference between current x and x from d days ago",
        "arity": 2,
    },
}


class DatasetCatalog:
    """Offline Dataset Catalog providing single source of truth for metadata."""

    def __init__(self) -> None:
        self._datasets: Dict[str, Dataset] = {}
        self._operators: Dict[str, Operator] = {}

        # Populate domain objects from static metadata maps
        for name, meta in DATASETS_METADATA.items():
            # For each dataset, instantiate in a specific region.
            # To preserve domain mappings, we can query datasets by region.
            # We will populate the primary dataset maps.
            # Use GLB as default region if GLB in regions, otherwise the first region.
            regions_set: Set[Region] = meta["regions"]
            default_region: Region = (
                Region.GLB
                if Region.GLB in regions_set
                else sorted(list(regions_set))[0]
            )
            self._datasets[name] = Dataset(
                name=name,
                region=default_region,
                category=str(meta["category"]),
                description=str(meta["description"]),
                fields=sorted(list(meta["fields"].keys())),
            )

        for name, meta in OPERATORS_METADATA.items():
            self._operators[name] = Operator(
                name=name,
                category=str(meta["category"]),
                signature=str(meta["signature"]),
                description=str(meta["description"]),
            )

    def get_dataset(self, name: str) -> Optional[Dataset]:
        """Retrieve a dataset by its name from the catalog."""
        return self._datasets.get(name)

    def get_operator(self, name: str) -> Optional[Operator]:
        """Retrieve an operator by its name from the catalog."""
        return self._operators.get(name)

    def search_datasets(self, query: str) -> List[Dataset]:
        """Search datasets matching a query string in name, category, or description."""
        query_lc = query.lower()
        results = []
        for dataset in self._datasets.values():
            if (
                query_lc in dataset.name.lower()
                or query_lc in dataset.category.lower()
                or query_lc in dataset.description.lower()
            ):
                results.append(dataset)
        return results

    def filter_datasets(
        self, region: Optional[Region] = None, universe: Optional[Universe] = None
    ) -> List[Dataset]:
        """Filter datasets by region and universe compatibility.

        Args:
            region: Optional region target.
            universe: Optional universe target.
        """
        results = []
        for name, dataset in self._datasets.items():
            meta = DATASETS_METADATA[name]
            if region and region not in meta["regions"]:
                continue
            if universe and universe not in meta["universes"]:
                continue
            results.append(dataset)
        return results

    def search_operators(self, query: str) -> List[Operator]:
        """Search operators by query in name, category, or description."""
        query_lc = query.lower()
        results = []
        for op in self._operators.values():
            if (
                query_lc in op.name.lower()
                or query_lc in op.category.lower()
                or query_lc in op.description.lower()
            ):
                results.append(op)
        return results

    def filter_operators(self, category: str) -> List[Operator]:
        """Filter operators by category."""
        return [op for op in self._operators.values() if op.category == category]

    def validate_field(self, dataset_name: str, field_name: str) -> bool:
        """Validate if a field exists inside a target dataset."""
        meta = DATASETS_METADATA.get(dataset_name)
        if not meta:
            return False
        return field_name in meta["fields"]

    def validate_delay(self, dataset_name: str, field_name: str, delay: int) -> bool:
        """Verify if delay is compatible with field reporting latency.

        Args:
            dataset_name: Target dataset.
            field_name: Target field.
            delay: Proposed backtest delay.
        """
        meta = DATASETS_METADATA.get(dataset_name)
        if not meta:
            raise DatasetNotFoundError(f"Dataset {dataset_name} not found")
        fields_dict: Dict[str, Any] = meta["fields"]
        field_meta = fields_dict.get(field_name)
        if not field_meta:
            raise ValueError(f"Field {field_name} not found in dataset {dataset_name}")

        return bool(delay >= field_meta["min_delay"])

    def validate_operator(self, operator_name: str, arg_count: int) -> bool:
        """Verify if operator is registered and matches the arity."""
        meta = OPERATORS_METADATA.get(operator_name)
        if not meta:
            return False
        return bool(meta["arity"] == arg_count)

    def validate_expression_variables(
        self, expression: str, dataset_name: str
    ) -> List[str]:
        """Validate expression variables against a target dataset.

        Returns:
            A list of invalid variable names. If empty, the expression is valid.
        """
        meta = DATASETS_METADATA.get(dataset_name)
        if not meta:
            raise DatasetNotFoundError(f"Dataset {dataset_name} not found")

        # Find all word identifiers in the expression
        tokens: Set[str] = set(re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", expression))

        invalid_vars = []
        for token in tokens:
            # If it is a registered operator, it is not a variable
            if token in self._operators:
                continue
            # If it is a field in the dataset, it is a valid variable
            if token in meta["fields"]:
                continue
            # Standalone identifiers not in operators/fields are invalid
            invalid_vars.append(token)

        return sorted(invalid_vars)

    def get_field_description(self, dataset_name: str, field_name: str) -> str:
        """Retrieve description for a specific dataset field."""
        meta = DATASETS_METADATA.get(dataset_name)
        if not meta:
            raise DatasetNotFoundError(f"Dataset {dataset_name} not found")
        fields_dict = meta["fields"]
        field_meta = fields_dict.get(field_name)
        if not field_meta:
            raise ValueError(f"Field {field_name} not found in dataset {dataset_name}")
        return str(field_meta["description"])

    def get_operator_arity(self, operator_name: str) -> int:
        """Retrieve the required argument count (arity) of an operator."""
        meta = OPERATORS_METADATA.get(operator_name)
        if not meta:
            raise OperatorNotFoundError(f"Operator {operator_name} not found")
        return int(meta["arity"])
