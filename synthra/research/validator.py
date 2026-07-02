"""Validator subsystem checking Fast Expressions against catalog rules."""

from synthra.core.catalog import DatasetCatalog, tokenize_expression, TokenType
from synthra.core.domain import SimulationRequest


class Validator:
    """Validator subsystem enforcing schema and syntax rules on expressions."""

    def __init__(self, catalog: DatasetCatalog) -> None:
        """Initialize with the shared DatasetCatalog dependency."""
        self.catalog = catalog

    def validate_request(self, request: SimulationRequest, dataset_name: str) -> bool:
        """Validate a SimulationRequest against the target dataset schema.

        Checks for unknown variables, invalid delays, unknown operators,
        and syntax arity mismatches.
        """
        # Validate dataset exists
        ds = self.catalog.get_dataset(dataset_name)
        if not ds:
            return False

        # Validate variables/fields
        try:
            invalid_vars = self.catalog.validate_expression_variables(
                request.expression, dataset_name
            )
            if invalid_vars:
                return False
        except Exception:
            return False

        # Validate delay compatibility for used fields
        try:
            tokens = tokenize_expression(request.expression)
        except ValueError:
            return False

        for token in tokens:
            if token.type == TokenType.IDENTIFIER:
                val = token.value
                if self.catalog.validate_field(dataset_name, val):
                    # Check reporting delay compatibility
                    if not self.catalog.validate_delay(
                        dataset_name, val, request.delay
                    ):
                        return False

        # Validate operator arities
        return self._validate_operator_arities(request.expression)

    def _validate_operator_arities(self, expression: str) -> bool:
        """Scan expression and verify that all operator calls have correct arity."""
        try:
            tokens = tokenize_expression(expression)
        except ValueError:
            return False

        for i, token in enumerate(tokens):
            if token.type == TokenType.IDENTIFIER:
                op_name = token.value
                op = self.catalog.get_operator(op_name)
                if op:
                    # Check if next token is '('
                    if i + 1 < len(tokens) and tokens[i + 1].value == "(":
                        depth = 0
                        arg_count = 1
                        has_args = False

                        for j in range(i + 2, len(tokens)):
                            t = tokens[j]
                            if t.value == "(":
                                depth += 1
                            elif t.value == ")":
                                if depth == 0:
                                    break
                                depth -= 1
                            elif t.value == "," and depth == 0:
                                arg_count += 1

                            if depth == 0 and t.type in (
                                TokenType.IDENTIFIER,
                                TokenType.NUMBER,
                            ):
                                has_args = True
                        else:
                            # Unmatched parenthesis
                            return False

                        if not has_args and arg_count == 1:
                            arg_count = 0

                        if not self.catalog.validate_operator(op_name, arg_count):
                            return False
        return True
