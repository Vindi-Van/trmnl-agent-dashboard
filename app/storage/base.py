"""
Abstract base class for the status storage repository.

Defines the interface that all storage implementations must
conform to, enabling swappable backends (SQLite, GCS, PostgreSQL).
"""

from abc import ABC, abstractmethod

from app.models.agent_status import AgentStatusRecord


class StatusRepository(ABC):
    """
    Abstract interface for agent status persistence.

    All storage backends must implement these methods.
    """

    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize the storage backend (create tables, etc.).

        Raises:
            RuntimeError: If initialization fails.
        """

    @abstractmethod
    async def upsert(self, record: AgentStatusRecord) -> None:
        """
        Insert or update an agent's status record.

        If a record with the same agent_id exists, it is replaced.

        Args:
            record: The agent status record to persist.
        """

    @abstractmethod
    async def get_all(self) -> list[AgentStatusRecord]:
        """
        Retrieve all stored agent status records.

        Returns:
            List of all agent status records, unordered.
        """

    @abstractmethod
    async def close(self) -> None:
        """Close the storage connection and release resources."""
