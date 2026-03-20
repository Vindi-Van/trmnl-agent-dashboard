"""
Tests for the TRMNL read endpoint.

Covers authentication, empty-state response, and full payload
structure via GET /api/v1/trmnl/openclaw.
"""

import pytest
from httpx import AsyncClient

from tests.conftest import TEST_READ_TOKEN


# ─── Auth ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_trmnl_missing_auth(client: AsyncClient) -> None:
    """
    Verify 401 when Authorization header is missing.
    """
    response = await client.get("/api/v1/trmnl/openclaw")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_trmnl_invalid_token(client: AsyncClient) -> None:
    """
    Verify 401 when an invalid read token is provided.
    """
    response = await client.get(
        "/api/v1/trmnl/openclaw",
        headers={"Authorization": "Bearer wrong-read-token"},
    )
    assert response.status_code == 401


# ─── Empty state ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_trmnl_empty_returns_valid_payload(
    client: AsyncClient,
) -> None:
    """
    Verify an empty DB returns a valid payload with zero counts.
    """
    response = await client.get(
        "/api/v1/trmnl/openclaw",
        headers={"Authorization": f"Bearer {TEST_READ_TOKEN}"},
    )
    assert response.status_code == 200

    data = response.json()
    assert data["summary"]["total"] == 0
    assert data["agents"] == []
    assert "generated_at" in data


# ─── Full flow ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_trmnl_after_posts_returns_agents(
    client: AsyncClient,
) -> None:
    """
    Verify the read endpoint returns agents after they POST status.
    """
    # Post two agent statuses
    await client.post(
        "/api/v1/agent-status",
        headers={"Authorization": "Bearer test-token-matrim"},
        json={
            "display_name": "Matrim Cauthon",
            "state": "active",
            "headline": "Running tests",
            "emoji": "🔥",
            "ttl_seconds": 900,
        },
    )
    await client.post(
        "/api/v1/agent-status",
        headers={"Authorization": "Bearer test-token-perrin"},
        json={
            "display_name": "Perrin Aybara",
            "state": "blocked",
            "headline": "Waiting on review",
            "blocked_on": "PR #42",
            "ttl_seconds": 900,
        },
    )

    # Read the TRMNL payload
    response = await client.get(
        "/api/v1/trmnl/openclaw",
        headers={"Authorization": f"Bearer {TEST_READ_TOKEN}"},
    )
    assert response.status_code == 200

    data = response.json()
    assert data["summary"]["total"] == 2
    assert data["summary"]["active"] == 1
    assert data["summary"]["blocked"] == 1

    # Verify sort order: blocked before active
    agents = data["agents"]
    assert len(agents) == 2
    assert agents[0]["state"] == "blocked"
    assert agents[1]["state"] == "active"

    # Verify agent fields
    assert agents[0]["display_name"] == "Perrin Aybara"
    assert agents[0]["blocked_on"] == "PR #42"
    assert agents[1]["emoji"] == "🔥"
    assert "minutes_ago" in agents[1]
    assert "is_stale" in agents[1]


# ─── Health check ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient) -> None:
    """
    Verify the health endpoint returns 200 with no auth.
    """
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
