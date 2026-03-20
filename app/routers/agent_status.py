"""
Agent status write endpoint.

Handles POST /api/v1/agent-status — validates the bearer token,
maps it to an agent identity, validates the request body, and
upserts the status record.
"""

import structlog
from fastapi import APIRouter, Depends, Request

from app.auth.bearer import extract_bearer_token, validate_agent_token
from app.config import AgentIdentity, Settings
from app.dependencies import get_repo, get_settings
from app.models.agent_status import AgentStatusRequest
from app.services.status_service import upsert_agent_status
from app.storage.base import StatusRepository

logger = structlog.get_logger()

router = APIRouter(prefix="/api/v1", tags=["agent-status"])


@router.post("/agent-status")
async def post_agent_status(
    body: AgentStatusRequest,
    request: Request,
    settings: Settings = Depends(get_settings),
    repo: StatusRepository = Depends(get_repo),
) -> dict[str, str]:
    """
    Receive an agent status update.

    Authenticates the agent via bearer token, validates the
    request body, and upserts the status record.

    Args:
        body: Validated agent status payload.
        request: Raw FastAPI request (for header extraction).
        settings: Application settings.
        repo: Storage repository.

    Returns:
        Confirmation dict with status 'ok'.

    Raises:
        HTTPException: 401 if token is invalid, 422 if body fails validation.
    """
    # Authenticate
    token = extract_bearer_token(request)
    token_map = settings.get_token_map()
    identity: AgentIdentity = validate_agent_token(token, token_map)

    # Process
    await upsert_agent_status(repo, body, identity)

    logger.info(
        "agent_status_received",
        agent_id=identity.agent_id,
        display_name=body.display_name,
        state=body.state.value,
    )
    return {"status": "ok"}
