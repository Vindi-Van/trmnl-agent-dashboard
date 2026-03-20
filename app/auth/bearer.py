"""
Bearer token authentication for agent write and TRMNL read endpoints.

Maps bearer tokens to agent identities for the write path,
and validates a single read token for the TRMNL endpoint.
"""

import structlog
from fastapi import HTTPException, Request, status

from app.config import AgentIdentity

logger = structlog.get_logger()


def extract_bearer_token(request: Request) -> str:
    """
    Extract the bearer token from the Authorization header.

    Args:
        request: The incoming FastAPI request.

    Returns:
        The raw token string (without 'Bearer ' prefix).

    Raises:
        HTTPException: 401 if the header is missing or malformed.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        logger.warning("auth_missing_header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
        )

    parts = auth_header.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        logger.warning("auth_malformed_header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format",
        )

    return parts[1]


def validate_agent_token(
    token: str,
    token_map: dict[str, AgentIdentity],
) -> AgentIdentity:
    """
    Validate an agent's write token and return its identity.

    Args:
        token: The bearer token from the request.
        token_map: Mapping of valid tokens to agent identities.

    Returns:
        The AgentIdentity associated with the token.

    Raises:
        HTTPException: 401 if the token is not recognized.
    """
    identity = token_map.get(token)
    if identity is None:
        logger.warning("auth_invalid_agent_token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid agent token",
        )

    logger.debug(
        "auth_agent_validated",
        agent_id=identity.agent_id,
    )
    return identity


def validate_read_token(token: str, expected_token: str) -> None:
    """
    Validate the TRMNL read endpoint bearer token.

    Args:
        token: The bearer token from the request.
        expected_token: The expected read token from config.

    Raises:
        HTTPException: 401 if the token does not match.
    """
    if token != expected_token:
        logger.warning("auth_invalid_read_token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid read token",
        )
    logger.debug("auth_read_token_validated")
