"""Unit tests for the SYNTHRA Dataset Catalog subsystem."""

import pytest

from synthra.core.catalog import (
    DatasetCatalog,
    DatasetNotFoundError,
    OperatorNotFoundError,
    tokenize_expression,
    TokenType,
)
from synthra.core.domain import Region, Universe


@pytest.fixture
def catalog() -> DatasetCatalog:
    """Fixture providing a DatasetCatalog instance."""
    return DatasetCatalog()


def test_catalog_initialization(catalog: DatasetCatalog) -> None:
    """Tests that the catalog correctly populates standard datasets and operators."""
    # Datasets
    pv = catalog.get_dataset("pv")
    assert pv is not None
    assert pv.name == "pv"
    assert "close" in pv.fields
    assert "open" in pv.fields

    fund = catalog.get_dataset("fundamental")
    assert fund is not None
    assert fund.name == "fundamental"
    assert "assets" in fund.fields

    # Operators
    ts_mean = catalog.get_operator("ts_mean")
    assert ts_mean is not None
    assert ts_mean.name == "ts_mean"
    assert ts_mean.category == "time_series"

    assert catalog.get_dataset("invalid") is None
    assert catalog.get_operator("invalid") is None


def test_search_datasets(catalog: DatasetCatalog) -> None:
    """Tests searching datasets by query string in name/description/category."""
    # Match by name
    pv_results = catalog.search_datasets("pv")
    assert len(pv_results) == 1
    assert pv_results[0].name == "pv"

    # Match by category
    fund_results = catalog.search_datasets("fundamentals")
    assert len(fund_results) == 1
    assert fund_results[0].name == "fundamental"

    # Match by description
    consensus_results = catalog.search_datasets("consensus")
    assert len(consensus_results) == 1
    assert consensus_results[0].name == "analyst"

    # Match multiple or none
    no_results = catalog.search_datasets("unknown_query_pattern")
    assert len(no_results) == 0


def test_filter_datasets(catalog: DatasetCatalog) -> None:
    """Tests filtering datasets by region and universe compatibility."""
    # Region filtering
    us_datasets = catalog.filter_datasets(region=Region.US)
    assert len(us_datasets) == 3  # pv, fundamental, analyst all support US

    ap_datasets = catalog.filter_datasets(region=Region.AP)
    assert len(ap_datasets) == 1  # Only pv supports AP
    assert ap_datasets[0].name == "pv"

    # Universe filtering
    top3000_datasets = catalog.filter_datasets(universe=Universe.TOP3000)
    assert len(top3000_datasets) == 1  # Only pv supports TOP3000
    assert top3000_datasets[0].name == "pv"

    top1000_datasets = catalog.filter_datasets(universe=Universe.TOP1000)
    assert len(top1000_datasets) == 3  # All support TOP1000/TOP500

    # Combined filtering
    filtered = catalog.filter_datasets(region=Region.EU, universe=Universe.TOP2000)
    assert len(filtered) == 2  # pv and fundamental support EU and TOP2000
    names = [d.name for d in filtered]
    assert "pv" in names
    assert "fundamental" in names


def test_search_and_filter_operators(catalog: DatasetCatalog) -> None:
    """Tests searching and filtering operators by query and category."""
    # Search
    mean_results = catalog.search_operators("mean")
    assert len(mean_results) == 1
    assert mean_results[0].name == "ts_mean"

    # Filter
    ts_ops = catalog.filter_operators("time_series")
    assert len(ts_ops) > 0
    assert all(op.category == "time_series" for op in ts_ops)


def test_validate_field(catalog: DatasetCatalog) -> None:
    """Tests field presence validation inside a dataset."""
    assert catalog.validate_field("pv", "close") is True
    assert catalog.validate_field("pv", "volume") is True
    assert catalog.validate_field("pv", "invalid_field") is False
    assert catalog.validate_field("invalid_dataset", "close") is False


def test_validate_delay(catalog: DatasetCatalog) -> None:
    """Tests delay compatibility based on reporting latency."""
    # Daily price volume data has minimum delay of 1 day
    assert catalog.validate_delay("pv", "close", 1) is True
    assert catalog.validate_delay("pv", "close", 2) is True
    assert catalog.validate_delay("pv", "close", 0) is False

    # Fundamentals reports have minimum delay of 2 days
    assert catalog.validate_delay("fundamental", "assets", 2) is True
    assert catalog.validate_delay("fundamental", "assets", 3) is True
    assert catalog.validate_delay("fundamental", "assets", 1) is False

    with pytest.raises(DatasetNotFoundError):
        catalog.validate_delay("invalid_dataset", "assets", 2)

    with pytest.raises(ValueError) as excinfo:
        catalog.validate_delay("fundamental", "invalid_field", 2)
    assert "Field invalid_field not found" in str(excinfo.value)


def test_validate_operator(catalog: DatasetCatalog) -> None:
    """Tests operator arity validation."""
    assert catalog.validate_operator("ts_mean", 2) is True
    assert catalog.validate_operator("ts_mean", 1) is False
    assert catalog.validate_operator("ts_mean", 3) is False

    assert catalog.validate_operator("rank", 1) is True
    assert catalog.validate_operator("rank", 2) is False

    assert catalog.validate_operator("invalid_operator", 1) is False


def test_validate_expression_variables(catalog: DatasetCatalog) -> None:
    """Tests parsing and validation of expression variables."""
    # Valid expression using pv fields and registered operators
    invalid = catalog.validate_expression_variables(
        "ts_mean(close, 20) / open + ts_rank(volume, 5)", "pv"
    )
    assert len(invalid) == 0

    # Expression with invalid variables (not in pv fields)
    invalid_vars = catalog.validate_expression_variables(
        "ts_mean(invalid_var_1, 20) / invalid_var_2", "pv"
    )
    assert sorted(invalid_vars) == ["invalid_var_1", "invalid_var_2"]

    # Expression with invalid operators
    invalid_ops = catalog.validate_expression_variables(
        "ts_moving_average(close, 20)", "pv"
    )
    assert invalid_ops == ["ts_moving_average"]

    # Test error if dataset does not exist
    with pytest.raises(DatasetNotFoundError):
        catalog.validate_expression_variables("close", "invalid_dataset")


def test_metadata_helpers(catalog: DatasetCatalog) -> None:
    """Tests additional metadata helper methods."""
    assert catalog.get_field_description("pv", "close") == "Closing price"
    assert catalog.get_operator_arity("ts_mean") == 2

    with pytest.raises(DatasetNotFoundError):
        catalog.get_field_description("invalid_dataset", "close")

    with pytest.raises(ValueError):
        catalog.get_field_description("pv", "invalid_field")

    with pytest.raises(OperatorNotFoundError):
        catalog.get_operator_arity("invalid_operator")


def test_rich_metadata_models(catalog: DatasetCatalog) -> None:
    """Tests retrieving and verifying rich metadata models from the catalog."""
    # Dataset Metadata
    ds_meta = catalog.get_dataset_metadata("pv")
    assert ds_meta is not None
    assert ds_meta.name == "pv"
    assert ds_meta.category == "market_data"
    assert Region.US in ds_meta.regions
    assert Universe.TOP3000 in ds_meta.universes
    assert "market" in ds_meta.aliases

    # Field Metadata
    f_meta = catalog.get_field_metadata("pv", "close")
    assert f_meta is not None
    assert f_meta.name == "close"
    assert f_meta.data_type == "float"
    assert f_meta.frequency == "daily"
    assert f_meta.delay == 1
    assert f_meta.nullable is False
    assert "close_price" in f_meta.aliases

    # Operator Metadata
    op_meta = catalog.get_operator_metadata("ts_mean")
    assert op_meta is not None
    assert op_meta.name == "ts_mean"
    assert op_meta.min_args == 2
    assert op_meta.max_args == 2
    assert op_meta.argument_types == ["float", "int"]
    assert op_meta.return_type == "float"
    assert "avg" in op_meta.aliases


def test_alias_lookups(catalog: DatasetCatalog) -> None:
    """Tests that lookups correctly resolve dataset, field, and operator aliases."""
    # Dataset alias lookup
    ds = catalog.get_dataset("market")
    assert ds is not None
    assert ds.name == "pv"

    # Operator alias lookup
    op = catalog.get_operator("avg")
    assert op is not None
    assert op.name == "ts_mean"

    # Field alias validation
    assert catalog.validate_field("market", "c") is True
    assert catalog.validate_field("pv", "close_price") is True
    assert catalog.validate_field("pv", "c") is True

    # Delay validation with field aliases
    assert catalog.validate_delay("market", "c", 1) is True
    assert catalog.validate_delay("pv", "close_price", 1) is True

    # Operator validation with operator aliases
    assert catalog.validate_operator("avg", 2) is True
    assert catalog.validate_operator("lag", 2) is True


def test_tokenizer() -> None:
    """Tests the reusable expression tokenizer."""
    expr = "ts_mean(close, 20) / open + 1.5"
    tokens = tokenize_expression(expr)

    # Validate types and values
    expected = [
        (TokenType.IDENTIFIER, "ts_mean"),
        (TokenType.SYMBOL, "("),
        (TokenType.IDENTIFIER, "close"),
        (TokenType.SYMBOL, ","),
        (TokenType.NUMBER, "20"),
        (TokenType.SYMBOL, ")"),
        (TokenType.SYMBOL, "/"),
        (TokenType.IDENTIFIER, "open"),
        (TokenType.SYMBOL, "+"),
        (TokenType.NUMBER, "1.5"),
    ]

    assert len(tokens) == len(expected)
    for token, (exp_type, exp_val) in zip(tokens, expected):
        assert token.type == exp_type
        assert token.value == exp_val

    # Test mismatch error
    with pytest.raises(ValueError) as excinfo:
        tokenize_expression("close @ vwap")
    assert "Unexpected character '@'" in str(excinfo.value)
