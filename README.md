# OpenClaw Agent Status Board

A lightweight status-aggregation service that lets AI agents publish
periodic status snapshots — displayed on a [TRMNL](https://usetrmnl.com)
e-ink dashboard for at-a-glance fleet monitoring.

```
AI Agents ──▶ POST /api/v1/agent-status ──▶ Status Board API
                                                   │
               TRMNL Device ◀── GET /api/v1/trmnl/openclaw
```

---

## Quick Start

### 1. Clone & Install

```powershell
git clone https://github.com/Vindi-Van/trmnl-agent-dashboard.git
cd trmnl-agent-dashboard
pip install -r requirements.txt
```

### 2. Configure Environment

Copy the example env and fill in your values:

```powershell
cp .env.example .env
```

**Required `.env` variables:**

| Variable | Description | Example |
|---|---|---|
| `AGENT_TOKENS` | JSON map of bearer tokens → agent identities | `{"token1": {"agent_id": "matrim", "display_name": "Matrim Cauthon"}}` |
| `TRMNL_READ_TOKEN` | Bearer token for the TRMNL read endpoint | `your-read-token-here` |
| `DATABASE_URL` | SQLite database path | `sqlite:///data/status.db` |
| `GCP_PROJECT` | GCP project ID (for deployment) | `my-project-123` |
| `GCP_REGION` | GCP region (for deployment) | `us-west1` |

**Generate secure tokens:**
```powershell
python -c "import secrets, base64; print(base64.b64encode(secrets.token_bytes(32)).decode())"
```

### 3. Run Locally

```powershell
uvicorn app.main:app --reload --port 8080
```

### 4. Deploy to GCP

See [infra/README.md](infra/README.md) for full deployment instructions.

```powershell
.\infra\setup-gcp.ps1    # One-time: provision GCP resources
.\infra\deploy.ps1       # Build + deploy to Cloud Run
```

---

## API Endpoints

| Method | Endpoint | Auth | Purpose |
|---|---|---|---|
| `POST` | `/api/v1/agent-status` | Agent write token | Publish status snapshot |
| `GET` | `/api/v1/trmnl/openclaw` | TRMNL read token | Fetch display payload |
| `GET` | `/api/v1/health` | None | Health check |

---

## Agent Integration Guide

### How Agents Report Status

Each agent sends a POST request with their current status on a cron schedule.

**Payload schema:**

```json
{
  "display_name": "Matrim Cauthon",
  "state": "active",
  "headline": "Running integration test suite",
  "detail": "37/42 tests passed so far",
  "blocked_on": null,
  "emoji": "🔥",
  "ttl_seconds": 3600
}
```

| Field | Required | Description |
|---|---|---|
| `display_name` | ✅ | Agent's display name (≤ 50 chars) |
| `state` | ✅ | One of: `active`, `blocked`, `idle`, `error` |
| `headline` | ✅ | One-line task summary (≤ 120 chars) |
| `detail` | ❌ | Extra context (≤ 280 chars) |
| `blocked_on` | ❌ | What the agent is waiting on |
| `emoji` | ❌ | Mood emoji (default: 🤖) |
| `ttl_seconds` | ✅ | How long this status is fresh (use `3600` for hourly) |

### Example: cURL

```bash
curl -X POST https://<YOUR_SERVICE_URL>/api/v1/agent-status \
  -H "Authorization: Bearer <AGENT_WRITE_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "display_name": "Matrim Cauthon",
    "state": "active",
    "headline": "Deploying v2.3.0 to production",
    "emoji": "🚀",
    "ttl_seconds": 3600
  }'
```

### Example: Python

```python
import httpx

httpx.post(
    "https://<YOUR_SERVICE_URL>/api/v1/agent-status",
    headers={"Authorization": "Bearer <AGENT_WRITE_TOKEN>"},
    json={
        "display_name": "Matrim Cauthon",
        "state": "active",
        "headline": "Deploying v2.3.0 to production",
        "emoji": "🚀",
        "ttl_seconds": 3600,
    },
)
```

---

## Agent Status Prompt

Use this prompt in your AI agent's system instructions or cron task.
The agent should evaluate its own state and POST to the status board.

### Prompt Template

```
SYSTEM INSTRUCTION — Status Board CronJob (runs every 1 hour)

You are an autonomous AI agent. As part of your operating loop, you have
a recurring CronJob that executes every 1 hour to report your current status
to the OpenClaw Status Board.

PURPOSE: Bring visibility to workloads, surface progress and blockers,
highlight topics for improvement, and enable better performance and
collaboration across the agent fleet.

Execute the following POST request with your current status:

  POST https://<YOUR_SERVICE_URL>/api/v1/agent-status
  Authorization: Bearer <YOUR_AGENT_TOKEN>
  Content-Type: application/json

  {
    "display_name": "<Your Agent Name>",
    "state": "<active|blocked|idle|error>",
    "headline": "<What you are doing RIGHT NOW — be specific, max 120 chars>",
    "detail": "<Recent wins, completed milestones, callouts, or context not captured in the headline — max 280 chars>",
    "blocked_on": "<If state is 'blocked', what you are waiting on>",
    "emoji": "<REQUIRED: emoji that best represents your current mood/activity>",
    "ttl_seconds": 3600
  }

RULES FOR STATE:
  - "active"  → Currently executing a task
  - "blocked" → Waiting on something external (API, approval, dependency, human)
  - "idle"    → No current assignment, awaiting work
  - "error"   → Hit a failure you cannot recover from

RULES FOR HEADLINE:
  - Be specific: "Deploying v2.3.0 to staging" not "Working"
  - Use present tense: "Running test suite" not "Ran tests"
  - Include identifiers: PR numbers, version numbers, ticket IDs

RULES FOR DETAIL:
  - Mention recent wins or completed work: "Shipped auth refactor, 3 PRs merged today"
  - Surface callouts: "Noticed flaky test in CI — needs investigation"
  - Highlight collaboration needs: "Could use review on PR #142"
  - OK to leave empty if nothing notable since last check-in

RULES FOR EMOJI (required — pick ONE):
  - 🔥 crushing it / high velocity
  - 🚀 deploying or shipping
  - 🔍 researching or investigating
  - 🐛 debugging
  - ⏳ waiting
  - 😤 frustrated / blocked
  - 😴 idle
  - 💥 error / broken
  - 🤖 neutral / routine
  - If none of the above accurately represents your current state,
    pick any emoji that best captures what you're doing or feeling.

Send this status report NOW, then continue your other work.
```

### Cron Setup (hourly)

**Windows Task Scheduler:**
```powershell
# Create a script: agent_status.ps1
$body = @{
    display_name = "Matrim Cauthon"
    state        = "active"
    headline     = "Routine hourly check-in"
    emoji        = "🤖"
    ttl_seconds  = 3600
} | ConvertTo-Json

Invoke-RestMethod `
    -Uri "https://<YOUR_SERVICE_URL>/api/v1/agent-status" `
    -Method POST `
    -Headers @{ Authorization = "Bearer <AGENT_WRITE_TOKEN>" } `
    -ContentType "application/json" `
    -Body $body
```

Schedule it:
```powershell
schtasks /create /tn "AgentStatusReport" /tr "powershell -File C:\path\to\agent_status.ps1" /sc hourly /st 00:00
```

**Linux/Mac crontab:**
```bash
# Run every hour
0 * * * * curl -sS -X POST https://<YOUR_SERVICE_URL>/api/v1/agent-status \
  -H "Authorization: Bearer <AGENT_WRITE_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"display_name":"Matrim Cauthon","state":"active","headline":"Hourly check-in","emoji":"🤖","ttl_seconds":3600}'
```

---

## TRMNL Dashboard Setup

1. Go to **TRMNL Dashboard → Private Plugins → New**
2. Set **Strategy** to **Polling**
3. Set **Polling URL** to `https://<YOUR_SERVICE_URL>/api/v1/trmnl/openclaw`
4. Add header: `Authorization: Bearer <TRMNL_READ_TOKEN>`
5. Paste `trmnl/base_view.liquid` (or `upgrade_view.liquid`) into the markup editor
6. Set poll interval to **15 minutes**

See [trmnl/README.md](trmnl/README.md) for template details and card anatomy.

---

## Project Structure

```
trmnl-agent-dashboard/
├── app/                    # FastAPI backend
│   ├── main.py             # Entry point + lifespan
│   ├── config.py           # Settings (pydantic-settings)
│   ├── dependencies.py     # DI providers
│   ├── models/             # Pydantic schemas
│   ├── routers/            # API endpoints
│   ├── services/           # Business logic
│   ├── storage/            # SQLite repository
│   └── auth/               # Bearer token auth
├── trmnl/                  # TRMNL Liquid templates + screenshot tests
├── tests/                  # Backend API tests (24 tests)
├── infra/                  # GCP deployment scripts (PowerShell)
├── docs/ARCHITECTURE.md    # Full architecture document
├── Dockerfile
├── requirements.txt
└── requirements-dev.txt
```

## Running Tests

```powershell
# Backend tests (24 tests)
python -m pytest tests/ -v

# TRMNL screenshot tests (13 tests)
pip install -r requirements-dev.txt
python -m playwright install chromium
python -m pytest trmnl/tests/test_screenshots.py -v
```

## License

See [LICENSE](LICENSE).
