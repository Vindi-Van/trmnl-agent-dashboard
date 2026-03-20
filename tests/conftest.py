"""
Shared pytest fixtures for backend tests.

Provides an isolated test database, mock token configuration,
a configured Settings instance, and an async FastAPI test client.
"""

import json
import os
import tempfile
from pathlib import Path
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.config import Settings
from app.dependencies import set_repo, set_settings
from app.main import create_app
from app.storage.sqlite import SqliteStatusRepository


# ─── Test tokens ──────────────────────────────────────────────

TEST_AGENT_TOKENS = {
    "test-token-matrim": {
        "agent_id": "matrim",
        "display_name": "Matrim Cauthon",
    },
    "test-token-perrin": {
        "agent_id": "perrin",
        "display_name": "Perrin Aybara",
    },
}

TEST_READ_TOKEN = "test-read-token"


# ─── Fixtures ─────────────────────────────────────────────────


@pytest.fixture
def test_settings(tmp_path: Path) -> Settings:
    """
    Create a Settings instance with test configuration.

    Uses a temporary directory for the SQLite database.

    Args:
        tmp_path: Pytest-provided temporary directory.

    Returns:
        Configured Settings for testing.
    """
    db_path = tmp_path / "test.db"
    return Settings(
        agent_tokens=json.dumps(TEST_AGENT_TOKENS),
        trmnl_read_token=TEST_READ_TOKEN,
        database_url=f"sqlite:///{db_path}",
        environment="test",
        log_level="DEBUG",
    )


@pytest_asyncio.fixture
async def test_repo(test_settings: Settings) -> AsyncGenerator[
    SqliteStatusRepository, None
]:
    """
    Create and initialize an isolated SQLite repository.

    Yields the repository for use in tests, then closes it.

    Args:
        test_settings: Test Settings instance with temp DB path.

    Yields:
        Initialized SqliteStatusRepository.
    """
    repo = SqliteStatusRepository(test_settings.get_db_path())
    await repo.initialize()
    yield repo
    await repo.close()


@pytest_asyncio.fixture
async def client(
    test_settings: Settings,
    test_repo: SqliteStatusRepository,
) -> AsyncGenerator[AsyncClient, None]:
    """
    Create an async HTTP test client for the FastAPI app.

    Registers test settings and repository as singletons,
    then yields an httpx AsyncClient bound to the app.

    Args:
        test_settings: Test Settings instance.
        test_repo: Initialized test repository.

    Yields:
        AsyncClient for making test requests.
    """
    # Register singletons
    set_settings(test_settings)
    set_repo(test_repo)

    app = create_app()

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as ac:
        yield ac
