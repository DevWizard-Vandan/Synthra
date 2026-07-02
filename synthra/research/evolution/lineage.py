"""Lineage subsystem tracking parent/child alpha expression trees."""

import hashlib
from typing import Optional
from pydantic import BaseModel, ConfigDict

from synthra.memory import DatabaseManager


class LineageNode(BaseModel):
    """Represents a node in the expression lineage evolution tree."""

    model_config = ConfigDict(
        frozen=True,
        strict=True,
    )

    expression: str
    parent_id: Optional[str] = None
    generation: int = 0
    mutation_type: Optional[str] = None
    campaign_id: str = "default"
    hypothesis_id: str = "default"
    origin: str = "generated"


class LineageTracker:
    """Handles persistence of expression lineage to SQLite."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        """Initialize tracker and table structure."""
        self.db_manager = db_manager
        self._init_table()

    def _init_table(self) -> None:
        """Ensure the lineage table exists in SQLite database."""
        with self.db_manager.transaction() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS expression_lineages (
                    expression_hash TEXT PRIMARY KEY,
                    expression TEXT NOT NULL,
                    parent_id TEXT,
                    generation INTEGER NOT NULL,
                    mutation_type TEXT,
                    campaign_id TEXT NOT NULL,
                    hypothesis_id TEXT NOT NULL,
                    origin TEXT NOT NULL
                );
            """)

    def record_node(self, node: LineageNode) -> None:
        """Persist a lineage node record into the SQLite database."""
        expr_hash = hashlib.sha256(node.expression.strip().encode()).hexdigest()
        with self.db_manager.transaction() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO expression_lineages (
                    expression_hash, expression, parent_id, generation,
                    mutation_type, campaign_id, hypothesis_id, origin
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """,
                (
                    expr_hash,
                    node.expression,
                    node.parent_id,
                    node.generation,
                    node.mutation_type,
                    node.campaign_id,
                    node.hypothesis_id,
                    node.origin,
                ),
            )

    def get_node(self, expression: str) -> Optional[LineageNode]:
        """Fetch lineage node for a specific expression string."""
        expr_hash = hashlib.sha256(expression.strip().encode()).hexdigest()
        with self.db_manager.connection() as conn:
            row = conn.execute(
                "SELECT * FROM expression_lineages WHERE expression_hash = ?",
                (expr_hash,),
            ).fetchone()
            if not row:
                return None
            return LineageNode(
                expression=row["expression"],
                parent_id=row["parent_id"],
                generation=row["generation"],
                mutation_type=row["mutation_type"],
                campaign_id=row["campaign_id"],
                hypothesis_id=row["hypothesis_id"],
                origin=row["origin"],
            )
