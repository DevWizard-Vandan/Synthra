"""Novelty detection subsystem evaluating AST and structural similarities."""

import hashlib
from typing import Set

from synthra.core.catalog import TokenType, tokenize_expression


class NoveltyDetector:
    """Detects duplicates and structural equivalent strategy expressions."""

    def __init__(self) -> None:
        """Initialize empty hash sets for expressions, ASTs, and fingerprints."""
        self.expression_hashes: Set[str] = set()
        self.ast_hashes: Set[str] = set()
        self.fingerprint_hashes: Set[str] = set()

    def get_fingerprint(self, expression: str) -> str:
        """Build structural fingerprint from operator keywords."""
        operators = {"+", "-", "*", "/"}
        try:
            tokens = tokenize_expression(expression)
            found = sorted(
                list(
                    {
                        t.value.lower()
                        for t in tokens
                        if t.type == TokenType.IDENTIFIER or t.value in operators
                    }
                )
            )
            return "".join(found)
        except Exception:
            return ""

    def get_normalized_ast(self, expression: str) -> str:
        """Return a normalized string representing syntax layout."""
        standard_fields = {
            "open",
            "close",
            "high",
            "low",
            "volume",
            "open_interest",
            "returns",
        }
        try:
            tokens = tokenize_expression(expression)
            parts = []
            for t in tokens:
                if t.type == TokenType.NUMBER:
                    parts.append("#")
                elif t.type == TokenType.IDENTIFIER:
                    val = t.value.lower()
                    if val in standard_fields:
                        parts.append("X")
                    else:
                        parts.append(val)
                else:
                    parts.append(t.value)
            return "".join(parts).replace(" ", "")
        except Exception:
            return expression.strip().lower().replace(" ", "")

    def is_novel(self, expression: str) -> bool:
        """Evaluate if an expression is structurally novel."""
        expr_hash = hashlib.sha256(expression.strip().encode()).hexdigest()
        if expr_hash in self.expression_hashes:
            return False

        ast = self.get_normalized_ast(expression)
        ast_hash = hashlib.sha256(ast.encode()).hexdigest()
        if ast_hash in self.ast_hashes:
            return False

        fingerprint = self.get_fingerprint(expression)
        fp_hash = hashlib.sha256(fingerprint.encode()).hexdigest()
        if fp_hash in self.fingerprint_hashes:
            return False

        return True

    def add_expression(self, expression: str) -> None:
        """Record expression metrics to the novelty tracker database."""
        expr_hash = hashlib.sha256(expression.strip().encode()).hexdigest()
        self.expression_hashes.add(expr_hash)

        ast = self.get_normalized_ast(expression)
        ast_hash = hashlib.sha256(ast.encode()).hexdigest()
        self.ast_hashes.add(ast_hash)

        fingerprint = self.get_fingerprint(expression)
        fp_hash = hashlib.sha256(fingerprint.encode()).hexdigest()
        self.fingerprint_hashes.add(fp_hash)
