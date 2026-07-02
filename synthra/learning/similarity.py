"""Similarity subsystem to detect duplicate and highly correlated expressions."""

import re

from synthra.core.catalog import tokenize_expression, TokenType


def normalize_expression(expression: str) -> str:
    """Normalize a Fast Expression to eliminate syntactic variation.

    Strip whitespace, convert to lower case, and replace integer/float
    numeric literals with a standard placeholder.
    """
    # Standardize casing and strip whitespaces
    expr = re.sub(r"\s+", "", expression).lower()

    # Match numeric float/integer sequences
    expr = re.sub(r"\b\d+(\.\d+)?\b", "#", expr)
    return expr


def jaccard_similarity(expr1: str, expr2: str) -> float:
    """Compute Jaccard token similarity over normalized token sets."""
    # Standard structural separators to discard
    separators = {",", "(", ")"}

    try:
        # Tokenize using catalog tokenizer
        tokens1 = {
            t.value.lower()
            for t in tokenize_expression(expr1)
            if t.value not in separators and t.type != TokenType.NUMBER
        }
        tokens2 = {
            t.value.lower()
            for t in tokenize_expression(expr2)
            if t.value not in separators and t.type != TokenType.NUMBER
        }

        if not tokens1 or not tokens2:
            return 0.0

        return len(tokens1.intersection(tokens2)) / len(tokens1.union(tokens2))

    except Exception:
        # Simple word token regex fallback
        w1 = {w for w in re.findall(r"\b\w+\b", expr1.lower())}
        w2 = {w for w in re.findall(r"\b\w+\b", expr2.lower())}

        if not w1 or not w2:
            return 0.0

        return len(w1.intersection(w2)) / len(w1.union(w2))
