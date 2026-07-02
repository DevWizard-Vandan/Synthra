"""Database manager and migrations for the SYNTHRA persistence layer."""

from contextlib import contextmanager
from datetime import datetime
import os
import sqlite3
from typing import Generator

# Schema migration scripts. Index 0 is version 1.
MIGRATIONS = [
    # Version 1 DDL schema creation
    [
        """
        CREATE TABLE campaigns (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            region TEXT NOT NULL,
            universe TEXT NOT NULL,
            budget_limit REAL NOT NULL,
            budget_spent REAL NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            concluded_at TEXT
        );
        """,
        """
        CREATE TABLE hypotheses (
            id TEXT PRIMARY KEY,
            campaign_id TEXT NOT NULL,
            rationale TEXT NOT NULL,
            target_variable TEXT NOT NULL,
            datasets TEXT NOT NULL,
            operators TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (campaign_id) REFERENCES campaigns (id) ON DELETE CASCADE
        );
        """,
        """
        CREATE TABLE experiments (
            id TEXT PRIMARY KEY,
            campaign_id TEXT NOT NULL,
            hypothesis_id TEXT NOT NULL,
            expression TEXT NOT NULL,
            status TEXT NOT NULL,
            request TEXT NOT NULL,
            result TEXT,
            error_message TEXT,
            created_at TEXT NOT NULL,
            finished_at TEXT,
            FOREIGN KEY (campaign_id) REFERENCES campaigns (id) ON DELETE CASCADE,
            FOREIGN KEY (hypothesis_id) REFERENCES hypotheses (id) ON DELETE CASCADE
        );
        """,
        """
        CREATE TABLE alpha_candidates (
            id TEXT PRIMARY KEY,
            experiment_id TEXT NOT NULL,
            hypothesis_id TEXT NOT NULL,
            campaign_id TEXT NOT NULL,
            expression TEXT NOT NULL,
            result TEXT NOT NULL,
            is_submitted INTEGER NOT NULL,
            submitted_at TEXT,
            FOREIGN KEY (experiment_id) REFERENCES experiments (id) ON DELETE CASCADE,
            FOREIGN KEY (hypothesis_id) REFERENCES hypotheses (id) ON DELETE CASCADE,
            FOREIGN KEY (campaign_id) REFERENCES campaigns (id) ON DELETE CASCADE
        );
        """,
        """
        CREATE TABLE research_assets (
            id TEXT PRIMARY KEY,
            campaign_id TEXT NOT NULL,
            type TEXT NOT NULL,
            file_path TEXT NOT NULL,
            description TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (campaign_id) REFERENCES campaigns (id) ON DELETE CASCADE
        );
        """,
    ]
]


class DatabaseManager:
    """Manages SQLite database connections, initialization, and migrations."""

    def __init__(self, db_path: str) -> None:
        """Initialize database manager and run migrations.

        Args:
            db_path: Path to SQLite DB file, or ':memory:' for transient DB.
        """
        self.db_path = db_path

        # If file-based database, ensure parent directories exist
        if db_path != ":memory:":
            os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)

        self._run_migrations()

    def _run_migrations(self) -> None:
        """Executes any pending migrations on initialization."""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version INTEGER PRIMARY KEY,
                    applied_at TEXT NOT NULL
                );
                """)
            conn.commit()

            cursor = conn.execute("SELECT MAX(version) FROM schema_migrations")
            row = cursor.fetchone()
            current_version = row[0] if row and row[0] is not None else 0

            for i, migration_steps in enumerate(MIGRATIONS, start=1):
                if i > current_version:
                    for step in migration_steps:
                        conn.execute(step)
                    conn.execute(
                        "INSERT INTO schema_migrations (version, applied_at) "
                        "VALUES (?, ?)",
                        (i, datetime.utcnow().isoformat()),
                    )
                    conn.commit()
        finally:
            conn.close()

    @contextmanager
    def connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Provides a thread-safe connection context manager.

        Yields:
            A sqlite3.Connection with Row factory and foreign keys enabled.
        """
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        try:
            yield conn
        finally:
            conn.close()

    @contextmanager
    def transaction(self) -> Generator[sqlite3.Connection, None, None]:
        """Provides a connection context manager wrapped in a transaction.

        Commit is called automatically on exit unless an error is raised,
        in which case rollback is called.

        Yields:
            A sqlite3.Connection inside an active transaction.
        """
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
