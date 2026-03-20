"""
SQLite storage implementation for agent status records.

Uses aiosqlite for async database access. The table is
auto-created on initialization with UPSERT semantics
(INSERT OR REPLACE) keyed on agent_id.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

import aiosqlite
import structlog

from app.models.agent_status import AgentStatusRecord
from app.storage.base import StatusRepository

logger = structlog.get_logger()


class SqliteStatusRepository(StatusRepository):
    """
    SQLite-backed agent status storage.

    Attributes:
        db_path: Filesystem path to the SQLite database file.
    """

    def __init__(self, db_path: Path) -> None:
        """
        Initialize the repository with a database path.

        Args:
            db_path: Path to the SQLite database file.
        """
        self.db_path = db_path
        self._db: Optional[aiosqlite.Connection] = None

    async def initialize(self) -> None:
        """
        Create the database file and agents table if not present.

        Ensures the parent directory exists and creates the table
        with the full schema including the emoji column.

        Raises:
            RuntimeError: If database connection fails.
        """
        # Ensure the data directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._db = await aiosqlite.connect(str(self.db_path))
        self._db.row_factory = aiosqlite.Row

        await self._db.execute("""
            CREATE TABLE IF NOT EXISTS agents (
                agent_id     TEXT PRIMARY KEY,
                display_name TEXT NOT NULL,
                state        TEXT NOT NULL,
                headline     TEXT NOT NULL,
                detail       TEXT,
                blocked_on   TEXT,
                emoji        TEXT DEFAULT '🤖',
                ttl_seconds  INTEGER NOT NULL DEFAULT 900,
                updated_at   TEXT NOT NULL,
                expires_at   TEXT NOT NULL
            )
        """)
        await self._db.commit()
        logger.info("sqlite_initialized", db_path=str(self.db_path))

    async def upsert(self, record: AgentStatusRecord) -> None:
        """
        Insert or replace an agent's status record.

        Uses INSERT OR REPLACE with agent_id as the primary key,
        so each agent only ever has one row.

        Args:
            record: The agent status record to persist.
        """
        if self._db is None:
            raise RuntimeError("Database not initialized")

        await self._db.execute(
            """
            INSERT OR REPLACE INTO agents (
                agent_id, display_name, state, headline,
                detail, blocked_on, emoji, ttl_seconds,
                updated_at, expires_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.agent_id,
                record.display_name,
                record.state,
                record.headline,
                record.detail,
                record.blocked_on,
                record.emoji,
                record.ttl_seconds,
                record.updated_at.isoformat(),
                record.expires_at.isoformat(),
            ),
        )
        await self._db.commit()
        logger.info(
            "agent_status_upserted",
            agent_id=record.agent_id,
            state=record.state,
        )

    async def get_all(self) -> list[AgentStatusRecord]:
        """
        Retrieve all agent status records from the database.

        Returns:
            List of AgentStatusRecord objects, one per agent.
        """
        if self._db is None:
            raise RuntimeError("Database not initialized")

        cursor = await self._db.execute("SELECT * FROM agents")
        rows = await cursor.fetchall()

        records = []
        for row in rows:
            records.append(
                AgentStatusRecord(
                    agent_id=row["agent_id"],
                    display_name=row["display_name"],
                    state=row["state"],
                    headline=row["headline"],
                    detail=row["detail"],
                    blocked_on=row["blocked_on"],
                    emoji=row["emoji"],
                    ttl_seconds=row["ttl_seconds"],
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                    expires_at=datetime.fromisoformat(row["expires_at"]),
                )
            )
        return records

    async def close(self) -> None:
        """Close the database connection."""
        if self._db is not None:
            await self._db.close()
            self._db = None
            logger.info("sqlite_closed")
