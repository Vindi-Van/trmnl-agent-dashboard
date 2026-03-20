"""
Health check endpoint.

Provides a simple liveness probe for Cloud Run and
load balancers — no authentication required.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1", tags=["health"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    """
    Return a simple health status.

    Returns:
        Dictionary with status 'ok'.
    """
    return {"status": "ok"}
