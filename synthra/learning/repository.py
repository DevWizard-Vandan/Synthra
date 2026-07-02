"""Repository persisting learning records to local SQLite state."""

import json
from typing import List

from synthra.learning.feedback import LearningRecord
from synthra.memory import DatabaseManager


class LearningRepository:
    """Handles CRUD database persistence for historical LearningRecords."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        """Initialize database tables for learning records."""
        self.db_manager = db_manager
        self._init_table()

    def _init_table(self) -> None:
        """Ensure local learning records persistence table exists."""
        with self.db_manager.transaction() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS learning_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    expression TEXT NOT NULL,
                    datasets TEXT NOT NULL,
                    operators TEXT NOT NULL,
                    delay INTEGER NOT NULL,
                    neutralization TEXT NOT NULL,
                    universe TEXT NOT NULL,
                    region TEXT NOT NULL,
                    sharpe REAL NOT NULL,
                    fitness REAL NOT NULL,
                    margin REAL NOT NULL,
                    turnover REAL NOT NULL,
                    coverage REAL NOT NULL,
                    success INTEGER NOT NULL,
                    failure_reasons TEXT NOT NULL,
                    success_reasons TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
            """)

    def add_record(self, record: LearningRecord) -> None:
        """Insert a new LearningRecord into the SQLite database."""
        with self.db_manager.transaction() as conn:
            conn.execute(
                """
                INSERT INTO learning_records (
                    expression, datasets, operators, delay, neutralization,
                    universe, region, sharpe, fitness, margin, turnover,
                    coverage, success, failure_reasons, success_reasons
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
                (
                    record.expression,
                    json.dumps(record.datasets),
                    json.dumps(record.operators),
                    record.delay,
                    record.neutralization,
                    record.universe,
                    record.region,
                    record.sharpe,
                    record.fitness,
                    record.margin,
                    record.turnover,
                    record.coverage,
                    1 if record.success else 0,
                    json.dumps(record.failure_reasons),
                    json.dumps(record.success_reasons),
                ),
            )

    def get_all_records(self) -> List[LearningRecord]:
        """Query and return all persisted LearningRecords."""
        with self.db_manager.connection() as conn:
            rows = conn.execute(
                "SELECT * FROM learning_records ORDER BY id ASC;"
            ).fetchall()
            records = []
            for row in rows:
                records.append(
                    LearningRecord(
                        expression=row["expression"],
                        datasets=json.loads(row["datasets"]),
                        operators=json.loads(row["operators"]),
                        delay=row["delay"],
                        neutralization=row["neutralization"],
                        universe=row["universe"],
                        region=row["region"],
                        sharpe=row["sharpe"],
                        fitness=row["fitness"],
                        margin=row["margin"],
                        turnover=row["turnover"],
                        coverage=row["coverage"],
                        success=bool(row["success"]),
                        failure_reasons=json.loads(row["failure_reasons"]),
                        success_reasons=json.loads(row["success_reasons"]),
                    )
                )
            return records
