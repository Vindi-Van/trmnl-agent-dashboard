"""
FastAPI dependency injection providers.

Exposes singleton instances of Settings and the StatusRepository
for use as FastAPI dependencies in route handlers.
"""

from app.config import Settings
from app.storage.base import StatusRepository

# ─── Singletons (set during app lifespan) ─────────────────────

_settings: Settings | None = None
_repo: StatusRepository | None = None


def set_settings(settings: Settings) -> None:
    """
    Set the global settings instance.

    Called during app lifespan startup.

    Args:
        settings: Configured Settings instance.
    """
    global _settings
    _settings = settings


def set_repo(repo: StatusRepository) -> None:
    """
    Set the global repository instance.

    Called during app lifespan startup.

    Args:
        repo: Initialized StatusRepository instance.
    """
    global _repo
    _repo = repo


def get_settings() -> Settings:
    """
    Provide the Settings instance as a FastAPI dependency.

    Returns:
        The configured Settings singleton.

    Raises:
        RuntimeError: If settings have not been initialized.
    """
    if _settings is None:
        raise RuntimeError("Settings not initialized")
    return _settings


def get_repo() -> StatusRepository:
    """
    Provide the StatusRepository instance as a FastAPI dependency.

    Returns:
        The initialized StatusRepository singleton.

    Raises:
        RuntimeError: If the repository has not been initialized.
    """
    if _repo is None:
        raise RuntimeError("Repository not initialized")
    return _repo
