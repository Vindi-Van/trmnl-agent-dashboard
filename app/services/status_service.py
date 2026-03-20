"""
Business logic for agent status operations.

Handles the write path (building records from requests) and
the read path (computing staleness, minutes_ago, summary
counts, and priority-based sorting).
"""

from datetime import datetime, timedelta

import structlog

from app.config import AgentIdentity
from app.models.agent_status import (
    STATE_PRIORITY,
    AgentStatusRecord,
    AgentStatusRequest,
    AgentStatusResponse,
    SummaryResponse,
    TrmnlResponse,
)
from app.storage.base import StatusRepository

logger = structlog.get_logger()


async def upsert_agent_status(
    repo: StatusRepository,
    request: AgentStatusRequest,
    identity: AgentIdentity,
) -> None:
    """
    Process an agent status write request.

    Builds an internal record from the request payload and
    agent identity, then persists it via upsert.

    Args:
        repo: Storage repository instance.
        request: Validated agent status payload.
        identity: Agent identity from token validation.
    """
    now = datetime.utcnow()
    record = AgentStatusRecord(
        agent_id=identity.agent_id,
        display_name=request.display_name,
        state=request.state.value,
        headline=request.headline,
        detail=request.detail,
        blocked_on=request.blocked_on,
        emoji=request.emoji,
        ttl_seconds=request.ttl_seconds,
        updated_at=now,
        expires_at=now + timedelta(seconds=request.ttl_seconds),
    )
    await repo.upsert(record)
    logger.info(
        "status_updated",
        agent_id=identity.agent_id,
        state=request.state.value,
        headline=request.headline,
    )


async def get_trmnl_payload(repo: StatusRepository) -> TrmnlResponse:
    """
    Build the full TRMNL display payload.

    Loads all agents, computes staleness and freshness for each,
    builds aggregate summary counts, and sorts agents by state
    priority (error → blocked → active → idle → stale).

    Args:
        repo: Storage repository instance.

    Returns:
        Complete TrmnlResponse ready for JSON serialization.
    """
    now = datetime.utcnow()
    records = await repo.get_all()

    agents: list[AgentStatusResponse] = []
    state_counts: dict[str, int] = {
        "active": 0,
        "blocked": 0,
        "idle": 0,
        "error": 0,
        "stale": 0,
    }

    for record in records:
        # Compute staleness
        is_stale = now > record.expires_at
        effective_state = "stale" if is_stale else record.state

        # Compute minutes since last check-in
        delta = now - record.updated_at
        minutes_ago = int(delta.total_seconds() / 60)

        # Increment state count
        state_counts[effective_state] = (
            state_counts.get(effective_state, 0) + 1
        )

        agents.append(
            AgentStatusResponse(
                display_name=record.display_name,
                state=effective_state,
                headline=record.headline,
                detail=record.detail,
                emoji=record.emoji or "🤖",
                blocked_on=record.blocked_on,
                updated_at=record.updated_at,
                minutes_ago=minutes_ago,
                is_stale=is_stale,
            )
        )

    # Sort by state priority: error → blocked → active → idle → stale
    agents.sort(key=lambda a: STATE_PRIORITY.get(a.state, 99))

    summary = SummaryResponse(
        total=len(agents),
        **state_counts,
    )

    return TrmnlResponse(
        generated_at=now,
        summary=summary,
        agents=agents,
    )
