"""
Tests for the status service business logic.

Covers status upsert, staleness detection, minutes_ago computation,
summary count aggregation, and state-priority sorting.
"""

from datetime import datetime, timedelta

import pytest
import pytest_asyncio

from app.config import AgentIdentity
from app.models.agent_status import AgentStatusRecord, AgentStatusRequest
from app.services.status_service import get_trmnl_payload, upsert_agent_status
from app.storage.sqlite import SqliteStatusRepository


# ─── Helper ───────────────────────────────────────────────────


def _make_record(
    agent_id: str,
    state: str = "active",
    headline: str = "Testing",
    ttl_seconds: int = 900,
    minutes_old: int = 5,
) -> AgentStatusRecord:
    """
    Build an AgentStatusRecord with a controlled timestamp.

    Args:
        agent_id: Unique agent identifier.
        state: Agent state string.
        headline: One-line task summary.
        ttl_seconds: TTL in seconds.
        minutes_old: How many minutes ago the record was written.

    Returns:
        AgentStatusRecord with computed timestamps.
    """
    now = datetime.utcnow()
    updated_at = now - timedelta(minutes=minutes_old)
    return AgentStatusRecord(
        agent_id=agent_id,
        display_name=agent_id.capitalize(),
        state=state,
        headline=headline,
        ttl_seconds=ttl_seconds,
        updated_at=updated_at,
        expires_at=updated_at + timedelta(seconds=ttl_seconds),
    )


# ─── Upsert tests ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_upsert_agent_status_creates_record(
    test_repo: SqliteStatusRepository,
) -> None:
    """
    Verify that upsert creates a new record for a new agent.
    """
    request = AgentStatusRequest(
        display_name="Matrim Cauthon",
        state="active",
        headline="Fixing tests",
        ttl_seconds=900,
    )
    identity = AgentIdentity(agent_id="matrim", display_name="Matrim Cauthon")

    await upsert_agent_status(test_repo, request, identity)

    records = await test_repo.get_all()
    assert len(records) == 1
    assert records[0].agent_id == "matrim"
    assert records[0].state == "active"
    assert records[0].headline == "Fixing tests"


@pytest.mark.asyncio
async def test_upsert_agent_status_replaces_existing(
    test_repo: SqliteStatusRepository,
) -> None:
    """
    Verify that upsert replaces an existing record for the same agent.
    """
    identity = AgentIdentity(agent_id="matrim", display_name="Matrim Cauthon")

    # First upsert
    request1 = AgentStatusRequest(
        display_name="Matrim Cauthon",
        state="active",
        headline="First task",
        ttl_seconds=900,
    )
    await upsert_agent_status(test_repo, request1, identity)

    # Second upsert (same agent, different status)
    request2 = AgentStatusRequest(
        display_name="Matrim Cauthon",
        state="blocked",
        headline="Second task",
        blocked_on="CI pipeline",
        ttl_seconds=900,
    )
    await upsert_agent_status(test_repo, request2, identity)

    records = await test_repo.get_all()
    assert len(records) == 1
    assert records[0].state == "blocked"
    assert records[0].headline == "Second task"
    assert records[0].blocked_on == "CI pipeline"


@pytest.mark.asyncio
async def test_upsert_agent_status_preserves_emoji(
    test_repo: SqliteStatusRepository,
) -> None:
    """
    Verify that emoji is stored and retrievable.
    """
    request = AgentStatusRequest(
        display_name="Matrim Cauthon",
        state="active",
        headline="On fire",
        emoji="🔥",
        ttl_seconds=900,
    )
    identity = AgentIdentity(agent_id="matrim", display_name="Matrim Cauthon")

    await upsert_agent_status(test_repo, request, identity)

    records = await test_repo.get_all()
    assert records[0].emoji == "🔥"


# ─── TRMNL payload tests ─────────────────────────────────────


@pytest.mark.asyncio
async def test_get_trmnl_payload_empty_returns_zeros(
    test_repo: SqliteStatusRepository,
) -> None:
    """
    Verify empty DB returns a valid payload with zero counts.
    """
    payload = await get_trmnl_payload(test_repo)

    assert payload.summary.total == 0
    assert payload.summary.active == 0
    assert payload.agents == []
    assert payload.generated_at is not None


@pytest.mark.asyncio
async def test_get_trmnl_payload_computes_minutes_ago(
    test_repo: SqliteStatusRepository,
) -> None:
    """
    Verify minutes_ago is computed correctly from updated_at.
    """
    record = _make_record("matrim", minutes_old=12)
    await test_repo.upsert(record)

    payload = await get_trmnl_payload(test_repo)

    # Should be approximately 12 minutes (allow ±1 for test timing)
    assert 11 <= payload.agents[0].minutes_ago <= 13


@pytest.mark.asyncio
async def test_get_trmnl_payload_detects_stale(
    test_repo: SqliteStatusRepository,
) -> None:
    """
    Verify that agents past their TTL are marked stale.
    """
    # TTL of 300s (5 min), but last updated 10 min ago → stale
    record = _make_record(
        "matrim", state="active", ttl_seconds=300, minutes_old=10,
    )
    await test_repo.upsert(record)

    payload = await get_trmnl_payload(test_repo)

    assert payload.agents[0].state == "stale"
    assert payload.agents[0].is_stale is True
    assert payload.summary.stale == 1
    assert payload.summary.active == 0


@pytest.mark.asyncio
async def test_get_trmnl_payload_fresh_not_stale(
    test_repo: SqliteStatusRepository,
) -> None:
    """
    Verify that agents within their TTL are NOT marked stale.
    """
    # TTL of 900s (15 min), last updated 5 min ago → fresh
    record = _make_record(
        "matrim", state="active", ttl_seconds=900, minutes_old=5,
    )
    await test_repo.upsert(record)

    payload = await get_trmnl_payload(test_repo)

    assert payload.agents[0].state == "active"
    assert payload.agents[0].is_stale is False


@pytest.mark.asyncio
async def test_get_trmnl_payload_summary_counts(
    test_repo: SqliteStatusRepository,
) -> None:
    """
    Verify summary counts aggregate correctly across states.
    """
    await test_repo.upsert(_make_record("a1", state="active"))
    await test_repo.upsert(_make_record("a2", state="active"))
    await test_repo.upsert(_make_record("b1", state="blocked"))
    await test_repo.upsert(_make_record("i1", state="idle"))
    await test_repo.upsert(_make_record("e1", state="error"))

    payload = await get_trmnl_payload(test_repo)

    assert payload.summary.total == 5
    assert payload.summary.active == 2
    assert payload.summary.blocked == 1
    assert payload.summary.idle == 1
    assert payload.summary.error == 1
    assert payload.summary.stale == 0


@pytest.mark.asyncio
async def test_get_trmnl_payload_sorts_by_priority(
    test_repo: SqliteStatusRepository,
) -> None:
    """
    Verify agents are sorted: error → blocked → active → idle → stale.
    """
    await test_repo.upsert(_make_record("idle_agent", state="idle"))
    await test_repo.upsert(_make_record("active_agent", state="active"))
    await test_repo.upsert(_make_record("error_agent", state="error"))
    await test_repo.upsert(_make_record("blocked_agent", state="blocked"))

    payload = await get_trmnl_payload(test_repo)

    states = [a.state for a in payload.agents]
    assert states == ["error", "blocked", "active", "idle"]


@pytest.mark.asyncio
async def test_get_trmnl_payload_default_emoji(
    test_repo: SqliteStatusRepository,
) -> None:
    """
    Verify agents without emoji get the default robot emoji.
    """
    record = _make_record("matrim")
    record.emoji = None
    await test_repo.upsert(record)

    payload = await get_trmnl_payload(test_repo)

    assert payload.agents[0].emoji == "🤖"
