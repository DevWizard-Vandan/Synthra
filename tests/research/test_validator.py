"""Unit tests for the Validator subsystem."""

from synthra.core.domain import Region, SimulationRequest, Universe
from synthra.research.validator import Validator


def test_validator_accepts_valid_request(validator: Validator) -> None:
    """Verify that a valid simulation request passes all validator checks."""
    req = SimulationRequest(
        expression="ts_mean(close, 20) / open",
        region=Region.US,
        universe=Universe.TOP2000,
        delay=1,
    )
    assert validator.validate_request(req, "pv") is True


def test_validator_rejects_unknown_fields(validator: Validator) -> None:
    """Verify that expressions containing unregistered fields are rejected."""
    req = SimulationRequest(
        expression="ts_mean(unknown_field, 20)",
        region=Region.US,
        universe=Universe.TOP2000,
        delay=1,
    )
    assert validator.validate_request(req, "pv") is False


def test_validator_rejects_unknown_operators(validator: Validator) -> None:
    """Verify that expressions containing unregistered operators are rejected."""
    req = SimulationRequest(
        expression="invalid_operator(close, 20)",
        region=Region.US,
        universe=Universe.TOP2000,
        delay=1,
    )
    assert validator.validate_request(req, "pv") is False


def test_validator_rejects_invalid_arity(validator: Validator) -> None:
    """Verify that operator calls with incorrect argument count are rejected."""
    # ts_mean expects 2 arguments: ts_mean(x, d)
    req1 = SimulationRequest(
        expression="ts_mean(close)",
        region=Region.US,
        universe=Universe.TOP2000,
        delay=1,
    )
    assert validator.validate_request(req1, "pv") is False

    req2 = SimulationRequest(
        expression="ts_mean(close, 20, 30)",
        region=Region.US,
        universe=Universe.TOP2000,
        delay=1,
    )
    assert validator.validate_request(req2, "pv") is False


def test_validator_rejects_invalid_delays(validator: Validator) -> None:
    """Verify that fields are validated against minimum reporting delay constraints."""
    # fundamental dataset fields (like assets) have a minimum delay of 2 days
    req1 = SimulationRequest(
        expression="assets / liabilities",
        region=Region.US,
        universe=Universe.TOP2000,
        delay=1,  # Incompatible delay (requires >= 2)
    )
    assert validator.validate_request(req1, "fundamental") is False

    req2 = SimulationRequest(
        expression="assets / liabilities",
        region=Region.US,
        universe=Universe.TOP2000,
        delay=2,  # Compatible delay
    )
    assert validator.validate_request(req2, "fundamental") is True
