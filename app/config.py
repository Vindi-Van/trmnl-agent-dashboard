"""
Application configuration via pydantic-settings.

Loads settings from environment variables and .env files. Token
configuration maps bearer tokens to agent identities for auth.
"""

import json
from pathlib import Path
from typing import Any

import structlog
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = structlog.get_logger()


class AgentIdentity:
    """
    Represents the identity mapped from an agent's bearer token.

    Attributes:
        agent_id: Unique identifier for the agent.
        display_name: Human-readable name shown in the dashboard.
    """

    def __init__(self, agent_id: str, display_name: str) -> None:
        self.agent_id = agent_id
        self.display_name = display_name

    def __repr__(self) -> str:
        return f"AgentIdentity(agent_id={self.agent_id!r})"


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Attributes:
        agent_tokens: JSON string mapping bearer tokens to agent
            identity objects (agent_id, display_name).
        trmnl_read_token: Bearer token for the TRMNL read endpoint.
        database_url: Path to the SQLite database file.
        environment: Deployment environment (dev, staging, prod).
        log_level: Logging verbosity level.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Token configuration (JSON string)
    agent_tokens: str = "{}"
    trmnl_read_token: str = ""

    @field_validator("trmnl_read_token", mode="before")
    @classmethod
    def strip_read_token(cls, v: Any) -> str:
        """
        Strip whitespace from the read token.

        Secret Manager values may include trailing newlines
        added by shell piping.

        Args:
            v: Raw value from environment.

        Returns:
            Trimmed token string.
        """
        return v.strip() if isinstance(v, str) else v

    # Database
    database_url: str = "sqlite:///data/status.db"

    # Application
    environment: str = "dev"
    log_level: str = "INFO"

    @field_validator("agent_tokens", mode="before")
    @classmethod
    def validate_agent_tokens(cls, v: Any) -> str:
        """
        Ensure agent_tokens is a valid JSON string.

        Args:
            v: Raw value from environment.

        Returns:
            Validated JSON string.

        Raises:
            ValueError: If the value is not valid JSON.
        """
        if isinstance(v, str):
            v = v.strip()
            try:
                json.loads(v)
            except json.JSONDecodeError as e:
                raise ValueError(
                    f"AGENT_TOKENS must be valid JSON: {e}"
                ) from e
        return v

    def get_token_map(self) -> dict[str, AgentIdentity]:
        """
        Parse the agent_tokens JSON into a token → identity mapping.

        Returns:
            Dictionary mapping bearer token strings to AgentIdentity.
        """
        raw: dict[str, dict[str, str]] = json.loads(self.agent_tokens)
        return {
            token: AgentIdentity(
                agent_id=info["agent_id"],
                display_name=info["display_name"],
            )
            for token, info in raw.items()
        }

    def get_db_path(self) -> Path:
        """
        Extract the filesystem path from the database_url.

        Strips the 'sqlite:///' prefix to get the raw file path.

        Returns:
            Path to the SQLite database file.
        """
        path_str = self.database_url.replace("sqlite:///", "")
        return Path(path_str)
