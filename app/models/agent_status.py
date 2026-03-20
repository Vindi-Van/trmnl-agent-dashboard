"""
Pydantic models for agent status data.

Defines the request/response schemas, internal record model,
state enumeration, and the TRMNL display payload structure.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class AgentState(str, Enum):
    """
    Valid states an agent can report.

    The 'stale' state is derived server-side and never sent
    by agents directly.
    """

    ACTIVE = "active"
    BLOCKED = "blocked"
    IDLE = "idle"
    ERROR = "error"


class DerivedState(str, Enum):
    """
    Extended state enum that includes server-derived states.

    Used in read responses where staleness is computed.
    """

    ACTIVE = "active"
    BLOCKED = "blocked"
    IDLE = "idle"
    ERROR = "error"
    STALE = "stale"


# ─── State priority for display sorting ───────────────────────

STATE_PRIORITY: dict[str, int] = {
    "error": 0,
    "blocked": 1,
    "active": 2,
    "idle": 3,
    "stale": 4,
}


# ─── Write payload ────────────────────────────────────────────


class AgentStatusRequest(BaseModel):
    """
    Schema for the agent status write payload.

    Attributes:
        display_name: Human-readable agent name.
        state: Current agent state.
        headline: One-line task summary.
        detail: Optional extra context.
        blocked_on: What the agent is waiting on (if blocked).
        emoji: Mood emoji for the upgrade view.
        ttl_seconds: How long this status is fresh.
    """

    display_name: str = Field(
        ..., min_length=1, max_length=50,
        description="Human-readable agent name",
    )
    state: AgentState = Field(
        ..., description="Current agent state",
    )
    headline: str = Field(
        ..., min_length=1, max_length=120,
        description="One-line task summary",
    )
    detail: Optional[str] = Field(
        None, max_length=280,
        description="Optional extra context",
    )
    blocked_on: Optional[str] = Field(
        None, max_length=200,
        description="What the agent is waiting on",
    )
    emoji: Optional[str] = Field(
        None, max_length=10,
        description="Mood emoji for the upgrade view",
    )
    ttl_seconds: int = Field(
        900, ge=60, le=86400,
        description="TTL in seconds (min 60, max 86400)",
    )


# ─── Internal record ──────────────────────────────────────────


class AgentStatusRecord(BaseModel):
    """
    Internal representation of a stored agent status.

    Includes server-side metadata appended on write.

    Attributes:
        agent_id: Unique agent identifier (from token mapping).
        display_name: Human-readable agent name.
        state: Current agent state.
        headline: One-line task summary.
        detail: Optional extra context.
        blocked_on: What the agent is waiting on.
        emoji: Mood emoji.
        ttl_seconds: TTL in seconds.
        updated_at: Server timestamp at write time.
        expires_at: When this status becomes stale.
    """

    agent_id: str
    display_name: str
    state: str
    headline: str
    detail: Optional[str] = None
    blocked_on: Optional[str] = None
    emoji: Optional[str] = None
    ttl_seconds: int = 900
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(default_factory=datetime.utcnow)


# ─── Read response models ─────────────────────────────────────


class AgentStatusResponse(BaseModel):
    """
    Single agent entry in the TRMNL read response.

    Attributes:
        display_name: Agent name for display.
        state: Current or derived state (may be 'stale').
        headline: One-line task summary.
        detail: Optional extra context.
        emoji: Mood emoji (defaults to robot).
        blocked_on: Blocking dependency (if applicable).
        updated_at: When the agent last checked in.
        minutes_ago: Minutes since last check-in.
        is_stale: Whether the agent has exceeded its TTL.
    """

    display_name: str
    state: str
    headline: str
    detail: Optional[str] = None
    emoji: str = "🤖"
    blocked_on: Optional[str] = None
    updated_at: datetime
    minutes_ago: int
    is_stale: bool


class SummaryResponse(BaseModel):
    """
    Aggregate state counts across all agents.

    Attributes:
        total: Total number of agents.
        active: Count of active agents.
        blocked: Count of blocked agents.
        idle: Count of idle agents.
        error: Count of agents in error state.
        stale: Count of stale agents.
    """

    total: int = 0
    active: int = 0
    blocked: int = 0
    idle: int = 0
    error: int = 0
    stale: int = 0


class TrmnlResponse(BaseModel):
    """
    Complete TRMNL read endpoint response.

    Attributes:
        generated_at: Timestamp when this payload was generated.
        summary: Aggregate state counts.
        agents: List of agent status entries.
    """

    generated_at: datetime
    summary: SummaryResponse
    agents: list[AgentStatusResponse]
