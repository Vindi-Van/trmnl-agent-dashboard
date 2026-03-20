"""
Mock data fixtures for TRMNL template screenshot tests.

Provides realistic agent status scenarios for 1–6 agents,
each with precomputed summary counts matching the agent states.
"""

from typing import Any


def _build_scenario(agents: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Build a complete TRMNL response payload from a list of agents.

    Computes summary counts automatically from agent states.

    Args:
        agents: List of agent status dictionaries.

    Returns:
        Complete payload with generated_at, summary, and agents.
    """
    states = [a["state"] for a in agents]
    return {
        "generated_at": "2026-03-20T07:30:00Z",
        "summary": {
            "total": len(agents),
            "active": states.count("active"),
            "blocked": states.count("blocked"),
            "idle": states.count("idle"),
            "error": states.count("error"),
            "stale": states.count("stale"),
        },
        "agents": agents,
    }


# ─── Agent pool ───────────────────────────────────────────────

MATRIM = {
    "display_name": "Matrim",
    "state": "active",
    "headline": "Fixing Expo iOS simulator signing",
    "detail": "Regenerating provisioning profile",
    "emoji": "🔥",
    "blocked_on": None,
    "updated_at": "2026-03-20T07:25:00Z",
    "minutes_ago": 5,
    "is_stale": False,
}

PERRIN = {
    "display_name": "Perrin",
    "state": "blocked",
    "headline": "Waiting on codesign workaround",
    "detail": "Apple Developer Portal outage",
    "emoji": "😤",
    "blocked_on": "Apple Developer Portal outage",
    "updated_at": "2026-03-20T07:20:00Z",
    "minutes_ago": 10,
    "is_stale": False,
}

RAND = {
    "display_name": "Rand",
    "state": "idle",
    "headline": "Awaiting next assignment",
    "detail": None,
    "emoji": "😴",
    "blocked_on": None,
    "updated_at": "2026-03-20T07:28:00Z",
    "minutes_ago": 2,
    "is_stale": False,
}

EGWENE = {
    "display_name": "Egwene",
    "state": "error",
    "headline": "Build failed — missing dependency",
    "detail": "ModuleNotFoundError: pydantic_settings",
    "emoji": "💥",
    "blocked_on": None,
    "updated_at": "2026-03-20T07:15:00Z",
    "minutes_ago": 15,
    "is_stale": False,
}

NYNAEVE = {
    "display_name": "Nynaeve",
    "state": "active",
    "headline": "Deploying v2.1.0 to staging",
    "detail": "Running database migrations",
    "emoji": "🚀",
    "blocked_on": None,
    "updated_at": "2026-03-20T07:29:00Z",
    "minutes_ago": 1,
    "is_stale": False,
}

MOIRAINE = {
    "display_name": "Moiraine",
    "state": "stale",
    "headline": "Last seen running integration tests",
    "detail": None,
    "emoji": "👻",
    "blocked_on": None,
    "updated_at": "2026-03-20T06:45:00Z",
    "minutes_ago": 45,
    "is_stale": True,
}


# ─── Scenarios ────────────────────────────────────────────────

SCENARIO_1_AGENT = _build_scenario([MATRIM])

SCENARIO_2_AGENTS = _build_scenario([MATRIM, PERRIN])

SCENARIO_3_AGENTS = _build_scenario([MATRIM, PERRIN, RAND])

SCENARIO_4_AGENTS = _build_scenario([MATRIM, PERRIN, RAND, EGWENE])

SCENARIO_5_AGENTS = _build_scenario([MATRIM, PERRIN, RAND, EGWENE, NYNAEVE])

SCENARIO_6_AGENTS = _build_scenario(
    [MATRIM, PERRIN, RAND, EGWENE, NYNAEVE, MOIRAINE]
)


# ─── Lookup for parametrized tests ───────────────────────────

ALL_SCENARIOS: dict[str, dict[str, Any]] = {
    "1_agent": SCENARIO_1_AGENT,
    "2_agents": SCENARIO_2_AGENTS,
    "3_agents": SCENARIO_3_AGENTS,
    "4_agents": SCENARIO_4_AGENTS,
    "5_agents": SCENARIO_5_AGENTS,
    "6_agents": SCENARIO_6_AGENTS,
}
