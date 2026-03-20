"""
TRMNL read endpoint.

Handles GET /api/v1/trmnl/openclaw — validates the read token
and returns the pre-shaped JSON display payload.
"""

import structlog
from fastapi import APIRouter, Depends, Request

from app.auth.bearer import extract_bearer_token, validate_read_token
from app.config import Settings
from app.dependencies import get_repo, get_settings
from app.models.agent_status import TrmnlResponse
from app.services.status_service import get_trmnl_payload
from app.storage.base import StatusRepository

logger = structlog.get_logger()

router = APIRouter(prefix="/api/v1", tags=["trmnl"])


@router.get("/trmnl/openclaw", response_model=TrmnlResponse)
async def get_trmnl_openclaw(
    request: Request,
    settings: Settings = Depends(get_settings),
    repo: StatusRepository = Depends(get_repo),
) -> TrmnlResponse:
    """
    Return the TRMNL display payload.

    Authenticates with the read token, then builds and returns
    the complete status board payload with computed staleness,
    freshness, and summary counts.

    Args:
        request: Raw FastAPI request (for header extraction).
        settings: Application settings.
        repo: Storage repository.

    Returns:
        Complete TrmnlResponse with summary and agent list.

    Raises:
        HTTPException: 401 if read token is invalid.
    """
    # Authenticate
    token = extract_bearer_token(request)
    validate_read_token(token, settings.trmnl_read_token)

    # Build payload
    payload = await get_trmnl_payload(repo)

    logger.info(
        "trmnl_payload_served",
        total_agents=payload.summary.total,
    )
    return payload
