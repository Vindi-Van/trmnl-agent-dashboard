"""
Tests for the agent status write endpoint.

Covers authentication, payload validation, and successful upsert
via POST /api/v1/agent-status.
"""

import pytest
from httpx import AsyncClient

from tests.conftest import TEST_AGENT_TOKENS


# ─── Valid auth + payload ─────────────────────────────────────


@pytest.mark.asyncio
async def test_post_agent_status_success(client: AsyncClient) -> None:
    """
    Verify a valid POST creates the agent status and returns 200.
    """
    response = await client.post(
        "/api/v1/agent-status",
        headers={"Authorization": "Bearer test-token-matrim"},
        json={
            "display_name": "Matrim Cauthon",
            "state": "active",
            "headline": "Running integration tests",
            "ttl_seconds": 900,
        },
    )
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_post_agent_status_with_all_fields(
    client: AsyncClient,
) -> None:
    """
    Verify a POST with all optional fields succeeds.
    """
    response = await client.post(
        "/api/v1/agent-status",
        headers={"Authorization": "Bearer test-token-perrin"},
        json={
            "display_name": "Perrin Aybara",
            "state": "blocked",
            "headline": "Waiting on PR review",
            "detail": "PR #142 needs approval from two reviewers",
            "blocked_on": "Code review",
            "emoji": "😤",
            "ttl_seconds": 1800,
        },
    )
    assert response.status_code == 200


# ─── Auth failures ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_post_agent_status_missing_auth_header(
    client: AsyncClient,
) -> None:
    """
    Verify 401 when Authorization header is missing.
    """
    response = await client.post(
        "/api/v1/agent-status",
        json={
            "display_name": "Test",
            "state": "active",
            "headline": "Test",
            "ttl_seconds": 900,
        },
    )
    assert response.status_code == 401
    assert "Missing Authorization" in response.json()["detail"]


@pytest.mark.asyncio
async def test_post_agent_status_invalid_token(
    client: AsyncClient,
) -> None:
    """
    Verify 401 when an unrecognized token is provided.
    """
    response = await client.post(
        "/api/v1/agent-status",
        headers={"Authorization": "Bearer wrong-token"},
        json={
            "display_name": "Test",
            "state": "active",
            "headline": "Test",
            "ttl_seconds": 900,
        },
    )
    assert response.status_code == 401
    assert "Invalid agent token" in response.json()["detail"]


@pytest.mark.asyncio
async def test_post_agent_status_malformed_auth(
    client: AsyncClient,
) -> None:
    """
    Verify 401 when Authorization header is malformed (no 'Bearer').
    """
    response = await client.post(
        "/api/v1/agent-status",
        headers={"Authorization": "Basic abc123"},
        json={
            "display_name": "Test",
            "state": "active",
            "headline": "Test",
            "ttl_seconds": 900,
        },
    )
    assert response.status_code == 401


# ─── Payload validation ──────────────────────────────────────


@pytest.mark.asyncio
async def test_post_agent_status_invalid_state(
    client: AsyncClient,
) -> None:
    """
    Verify 422 when an invalid state is provided.
    """
    response = await client.post(
        "/api/v1/agent-status",
        headers={"Authorization": "Bearer test-token-matrim"},
        json={
            "display_name": "Matrim",
            "state": "sleeping",
            "headline": "Test",
            "ttl_seconds": 900,
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_post_agent_status_missing_required_field(
    client: AsyncClient,
) -> None:
    """
    Verify 422 when a required field (headline) is missing.
    """
    response = await client.post(
        "/api/v1/agent-status",
        headers={"Authorization": "Bearer test-token-matrim"},
        json={
            "display_name": "Matrim",
            "state": "active",
            "ttl_seconds": 900,
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_post_agent_status_headline_too_long(
    client: AsyncClient,
) -> None:
    """
    Verify 422 when headline exceeds 120 characters.
    """
    response = await client.post(
        "/api/v1/agent-status",
        headers={"Authorization": "Bearer test-token-matrim"},
        json={
            "display_name": "Matrim",
            "state": "active",
            "headline": "x" * 121,
            "ttl_seconds": 900,
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_post_agent_status_ttl_too_low(
    client: AsyncClient,
) -> None:
    """
    Verify 422 when TTL is below minimum (60 seconds).
    """
    response = await client.post(
        "/api/v1/agent-status",
        headers={"Authorization": "Bearer test-token-matrim"},
        json={
            "display_name": "Matrim",
            "state": "active",
            "headline": "Test",
            "ttl_seconds": 10,
        },
    )
    assert response.status_code == 422
