"""Reusable expression tokenizer for SYNTHRA fast expressions."""

from enum import Enum
import re
from typing import List


class TokenType(str, Enum):
    """Types of tokens in the expression tokenizer."""

    IDENTIFIER = "IDENTIFIER"
    NUMBER = "NUMBER"
    SYMBOL = "SYMBOL"


class Token:
    """A single token produced by the tokenizer."""

    def __init__(self, type: TokenType, value: str, position: int) -> None:
        self.type = type
        self.value = value
        self.position = position

    def __repr__(self) -> str:
        return f"Token({self.type.name}, {repr(self.value)}, pos={self.position})"


def tokenize_expression(expression: str) -> List[Token]:
    """Tokenize a fast expression string without parsing it.

    Args:
        expression: The mathematical/expression string to tokenize.

    Returns:
        A list of Token instances.

    Raises:
        ValueError: If an unexpected character is encountered.
    """
    token_specification = [
        ("IDENTIFIER", r"[a-zA-Z_][a-zA-Z0-9_]*"),
        ("NUMBER", r"\d+(?:\.\d+)?"),
        ("SYMBOL", r"[()+\-*/,]"),
        ("SKIP", r"[ \t\n\r]+"),
        ("MISMATCH", r"."),
    ]
    tok_regex = "|".join(
        f"(?P<{name}>{pattern})" for name, pattern in token_specification
    )

    tokens = []
    for mo in re.finditer(tok_regex, expression):
        kind = mo.lastgroup
        if not kind:
            continue
        value = mo.group()
        column = mo.start()
        if kind == "SKIP":
            continue
        elif kind == "MISMATCH":
            raise ValueError(f"Unexpected character {value!r} at position {column}")
        else:
            tokens.append(Token(TokenType(kind), value, column))
    return tokens
