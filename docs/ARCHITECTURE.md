# OpenClaw Agent Status Board — Architecture

> A lightweight status-aggregation service that bridges OpenClaw agent execution
> with a calm, glanceable TRMNL e-ink dashboard.

---

## 1. Problem Statement

In a multi-agent OpenClaw environment, there is no passive way to answer
simple operational questions at a glance:

- Which agents are **active** right now?
- Which ones are **blocked**?
- What is each agent working on?
- When did each agent last check in?

Opening the full OpenClaw dashboard or reading raw conversations is
heavyweight and noisy. The Status Board solves this by creating a narrow,
read-only status layer optimized for ambient awareness.

---

## 2. Design Principles

| Principle | Implication |
|---|---|
| **Snapshots, not logs** | Agents send a short summary of current intent — no transcripts, no reasoning traces. |
| **Freshness over history** | Only the latest status per agent matters. No traditional database required for v1. |
| **Glanceability** | Output is sparse, legible, and optimized for e-ink. A few agents with one-line statuses beats a dense monitoring page. |
| **Operationally boring** | Simple to deploy, cheap to run, easy to extend. Not a new observability platform. |

---

## 3. High-Level Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    OpenClaw VPS                              │
│                                                              │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│   │  Matrim   │  │  Perrin   │  │  Agent N  │  ...            │
│   │  (agent)  │  │  (agent)  │  │  (agent)  │                 │
│   └────┬─────┘  └────┬─────┘  └────┬─────┘                  │
│        │              │              │                        │
│        │   cron every 10 min         │                        │
│        ▼              ▼              ▼                        │
│   POST /api/v1/agent-status  (bearer token per agent)        │
└──────────────────────┬───────────────────────────────────────┘
                       │  HTTPS
                       ▼
         ┌─────────────────────────────┐
         │   Status Board API          │
         │   (Cloud Run / Fly.io)      │
         │                             │
         │  ┌───────────────────────┐  │
         │  │  Write path           │  │
         │  │  • validate token     │  │
         │  │  • validate payload   │  │
         │  │  • upsert status      │  │
         │  └───────────┬───────────┘  │
         │              │              │
         │  ┌───────────▼───────────┐  │
         │  │  Storage              │  │
         │  │  (SQLite / GCS JSON)  │  │
         │  └───────────┬───────────┘  │
         │              │              │
         │  ┌───────────▼───────────┐  │
         │  │  Read path            │  │
         │  │  • validate read key  │  │
         │  │  • compute freshness  │  │
         │  │  • build summary      │  │
         │  │  • return JSON        │  │
         │  └───────────────────────┘  │
         └──────────────┬──────────────┘
                        │  HTTPS
                        ▼
              ┌──────────────────┐
              │  TRMNL Device    │
              │  (Private Plugin │
              │   polling mode)  │
              │                  │
              │  Renders via     │
              │  Liquid template │
              └──────────────────┘
```

### Separation of Concerns

| Layer | Responsibility |
|---|---|
| **OpenClaw Agents** | Decide their own summary; POST on schedule. |
| **Status Board API** | Validate, store, detect staleness, produce display payload. |
| **TRMNL** | Poll and present. No business logic. |

---

## 4. Data Model

### Agent Status (write payload)

```json
{
  "display_name": "Matrim",
  "state": "active",
  "headline": "Fixing Expo iOS simulator signing",
  "detail": "Regenerating provisioning profile after cert rotation",
  "blocked_on": null,
  "emoji": "🔥",
  "ttl_seconds": 900
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `display_name` | `string` | ✅ | Human-readable agent name. |
| `state` | `enum` | ✅ | One of: `active`, `blocked`, `idle`, `error`. |
| `headline` | `string` | ✅ | One-line task summary (≤ 120 chars). |
| `detail` | `string` | ❌ | Optional extra context (≤ 280 chars). |
| `blocked_on` | `string` | ❌ | What the agent is waiting on (if `blocked`). |
| `emoji` | `string` | ❌ | Mood emoji for the upgrade view (default: 🤖). |
| `ttl_seconds` | `int` | ✅ | How long this status is considered fresh (default: 900). |

### Stored Record (internal)

The service appends server-side metadata on write:

| Field | Source |
|---|---|
| `agent_id` | Derived from the bearer token → agent mapping. |
| `updated_at` | Server timestamp at time of write (UTC). |
| `expires_at` | `updated_at + ttl_seconds`. |

### State Vocabulary

| State | Meaning |
|---|---|
| `active` | Agent is executing work. |
| `blocked` | Agent is waiting on an external dependency. |
| `idle` | Agent is available but has no assignment. |
| `error` | Agent encountered a failure. |
| `stale` | **Derived** — agent missed its TTL window (not sent by agent). |

---

## 5. API Design

### Write Endpoint

```
POST /api/v1/agent-status
Authorization: Bearer <AGENT_WRITE_TOKEN>
Content-Type: application/json
```

- Validates bearer token and maps it to an `agent_id`.
- Validates request body against the Pydantic schema.
- Upserts the agent's status record.
- Returns `200 OK` with `{ "status": "ok" }`.

**Error responses:**

| Status | Condition |
|---|---|
| `401` | Missing or invalid token. |
| `422` | Payload validation failure. |
| `429` | Rate limit exceeded (optional). |

### Read Endpoint (TRMNL)

```
GET /api/v1/trmnl/openclaw
Authorization: Bearer <TRMNL_READ_TOKEN>
```

Returns a pre-shaped JSON payload:

```json
{
  "generated_at": "2026-03-20T07:30:00Z",
  "summary": {
    "total": 4,
    "active": 2,
    "blocked": 1,
    "idle": 0,
    "error": 0,
    "stale": 1
  },
  "agents": [
    {
      "display_name": "Matrim",
      "state": "active",
      "headline": "Fixing Expo iOS simulator signing",
      "detail": "Regenerating provisioning profile",
      "emoji": "🔥",
      "updated_at": "2026-03-20T07:25:00Z",
      "minutes_ago": 5,
      "is_stale": false
    },
    {
      "display_name": "Perrin",
      "state": "blocked",
      "headline": "Waiting on codesign workaround",
      "blocked_on": "Apple Developer Portal outage",
      "emoji": "😤",
      "updated_at": "2026-03-20T07:20:00Z",
      "minutes_ago": 10,
      "is_stale": false
    }
  ]
}
```

**Key design decisions:**
- `minutes_ago` and `is_stale` are **computed server-side** so TRMNL templates stay logic-free.
- Agents are sorted by `state` priority: `error` → `blocked` → `active` → `idle` → `stale`.
- The read endpoint **never** accepts writes; the write endpoint **never** serves reads.

### Health Check

```
GET /api/v1/health
```

Returns `200 OK` — no auth required. Used for Cloud Run health probes.

---

## 6. Authentication & Security

```
┌──────────────┐        ┌──────────────────┐        ┌────────────┐
│  Agent        │──────▶│  Write Endpoint   │        │            │
│  WRITE token  │       │  POST only        │        │            │
└──────────────┘        └──────────────────┘        │  Status    │
                                                     │  Board     │
┌──────────────┐        ┌──────────────────┐        │  API       │
│  TRMNL       │──────▶│  Read Endpoint    │        │            │
│  READ token   │       │  GET only         │        │            │
└──────────────┘        └──────────────────┘        └────────────┘
```

| Concern | Approach |
|---|---|
| Agent auth | Per-agent bearer token in `Authorization` header. |
| TRMNL auth | Separate read-only bearer token. |
| Token storage | GCP Secret Manager (prod) / `.env` file (dev). |
| Transport | HTTPS only (enforced by Cloud Run). |
| Token → identity | Server-side mapping: `{ token → agent_id, display_name }`. |
| Rotation | Tokens can be rotated per-agent without affecting others. |
| Rate limiting | Optional; applied to the read endpoint if public exposure is a concern. |

---

## 7. Storage Strategy

### v1: SQLite (recommended)

SQLite is the best balance of simplicity and durability for v1:

```
agents table
─────────────────────────────────────────────
agent_id     TEXT  PRIMARY KEY
display_name TEXT  NOT NULL
state        TEXT  NOT NULL
headline     TEXT  NOT NULL
detail       TEXT
blocked_on   TEXT
emoji        TEXT  DEFAULT '🤖'
ttl_seconds  INTEGER NOT NULL DEFAULT 900
updated_at   DATETIME NOT NULL
expires_at   DATETIME NOT NULL
```

- Single file, no external dependencies.
- Survives container restarts when mounted on a persistent volume.
- Easy to query for stale detection: `WHERE expires_at < NOW()`.
- Can be backed up to GCS on a schedule.

### Alternative: GCS JSON Object

For the absolute minimum infrastructure:
- One JSON file per agent in a GCS bucket, or a single `status.json` aggregate.
- Read-modify-write on each POST.
- No volume mount needed.

### Future: Cloud SQL (PostgreSQL)

If history, filtering, or multi-instance writes become necessary, migrate to
Cloud SQL. The Pydantic models and repository pattern make this swap
straightforward.

---

## 8. Infrastructure & Deployment

### GCP Architecture

```
┌─────────────────────────────────────────────────────┐
│  GCP Project: trmnl-agent-dashboard                 │
│                                                      │
│  ┌──────────────┐     ┌────────────────────────┐    │
│  │  Artifact     │     │  Secret Manager         │    │
│  │  Registry     │     │  • AGENT_TOKENS          │    │
│  │  (container)  │     │  • TRMNL_READ_TOKEN      │    │
│  └──────┬───────┘     └────────────┬───────────┘    │
│         │                          │                 │
│  ┌──────▼──────────────────────────▼──────────┐     │
│  │  Cloud Run                                  │     │
│  │  • Min instances: 0 (scale to zero)         │     │
│  │  • Max instances: 2                         │     │
│  │  • CPU: 1 vCPU                              │     │
│  │  • Memory: 256 MB                           │     │
│  │  • Volume: /data (for SQLite)               │     │
│  └─────────────────────────────────────────────┘     │
│                                                      │
│  ┌─────────────────────────────────────────────┐     │
│  │  Cloud Storage (optional)                    │     │
│  │  • Periodic SQLite backup                    │     │
│  │  • OR primary storage if using JSON strategy │     │
│  └─────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────┘
```

### Environment Variables

| Variable | Description | Source |
|---|---|---|
| `AGENT_TOKENS` | JSON mapping of `{ token: { agent_id, display_name } }` | Secret Manager |
| `TRMNL_READ_TOKEN` | Bearer token for the TRMNL read endpoint | Secret Manager |
| `DATABASE_URL` | Path to SQLite file (e.g. `/data/status.db`) | Cloud Run env |
| `ENVIRONMENT` | `dev` / `staging` / `prod` | Cloud Run env |
| `LOG_LEVEL` | `DEBUG` / `INFO` / `WARNING` | Cloud Run env |

### Dockerfile (outline)

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

---

## 9. Project Structure

```
trmnl-agent-dashboard/
├── app/
│   ├── __init__.py
│   ├── main.py               # FastAPI app entry point
│   ├── config.py              # Settings via pydantic-settings
│   ├── dependencies.py        # Dependency injection (auth, DB)
│   ├── models/
│   │   ├── __init__.py
│   │   └── agent_status.py    # Pydantic schemas
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── agent_status.py    # POST /api/v1/agent-status
│   │   ├── trmnl.py           # GET  /api/v1/trmnl/openclaw
│   │   └── health.py          # GET  /api/v1/health
│   ├── services/
│   │   ├── __init__.py
│   │   └── status_service.py  # Business logic, staleness, summary
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── base.py            # Abstract repository interface
│   │   └── sqlite.py          # SQLite implementation
│   └── auth/
│       ├── __init__.py
│       └── bearer.py          # Token validation + agent lookup
├── trmnl/
│   ├── README.md              # Template docs + plugin setup guide
│   ├── base_view.liquid       # Base template (status cards, no avatars)
│   └── upgrade_view.liquid    # Upgrade template (emoji mood avatars)
├── tests/
│   ├── __init__.py
│   ├── conftest.py            # Fixtures (test DB, mock tokens)
│   ├── test_agent_status.py   # Write endpoint tests
│   ├── test_trmnl.py          # Read endpoint tests
│   └── test_status_service.py # Business logic tests
├── infra/
│   ├── config.sh              # GCP project/region config
│   ├── setup-gcp.sh           # Provision GCP resources
│   ├── deploy.sh              # Build + deploy to Cloud Run
│   └── teardown.sh            # Cleanup resources
├── docs/
│   └── ARCHITECTURE.md        # This document
├── Dockerfile
├── requirements.txt
├── .env.example
├── .gitignore
├── CONTEXT.md
├── CHANGELOG.md
└── README.md
```

---

## 10. TRMNL Integration

### Plugin Configuration

TRMNL will be configured as a **Private Plugin** in **polling mode**:

| Setting | Value |
|---|---|
| Plugin type | Private Plugin |
| Strategy | Polling |
| Endpoint | `https://<service-url>/api/v1/trmnl/openclaw` |
| Auth header | `Authorization: Bearer <TRMNL_READ_TOKEN>` |
| Poll interval | 15 minutes |

### Template Files

Templates are version-controlled in `trmnl/` and pasted into the TRMNL
inline markup editor. Two variants are provided:

| File | Description |
|---|---|
| `trmnl/base_view.liquid` | Status cards with typographic hierarchy, no avatars. |
| `trmnl/upgrade_view.liquid` | Same layout + emoji mood avatar per agent. |

### Adaptive Card Grid Layout

The templates render agent statuses as **cards in a single full-screen view**.
The TRMNL Grid system adapts the layout based on agent count:

| Agents | Layout | Grid classes |
|---|---|---|
| 1 | Full-width single card | `flex flex--col` |
| 2 | Vertical split (left / right) | `grid grid--cols-2` |
| 3 | Three equal columns | `grid grid--cols-3` |
| 4 | 2×2 grid | `grid grid--cols-2` (wraps to 2 rows) |
| 5 | 3 top + 2 bottom | `grid--cols-3` + `grid--cols-2` |
| 6 | 3×2 grid | `grid grid--cols-3` (wraps to 2 rows) |

### Card Anatomy

Each card uses differentiated font weight and size for every line to create
a clear visual hierarchy that's easy to scan on e-ink:

```
┌─────────────────────────────┐
│  AGENT NAME                 │  ← title title--small (bold)
│  ● ACTIVE                   │  ← label label--inverted (badge)
│  Fixing Expo iOS signing    │  ← label (normal weight, clamped)
│  ↳ Awaiting cert rotation   │  ← label label--gray (if blocked)
│  12m ago                    │  ← label label--small label--gray
└─────────────────────────────┘
```

The **upgrade view** adds an emoji avatar in the header row:

```
┌─────────────────────────────┐
│  🔥  AGENT NAME             │  ← emoji (24px) + title
│  ● ACTIVE                   │  ← state badge
│  Fixing Expo iOS signing    │  ← headline
│  12m ago                    │  ← freshness
└─────────────────────────────┘
```

### TRMNL Framework Classes Used

| Class | Purpose |
|---|---|
| `view view--full` | Full-screen single-plugin view |
| `layout layout--col` | Vertical arrangement (summary bar + card grid) |
| `grid grid--cols-{n}` | Adaptive column count for card grid |
| `flex flex--row` / `flex--col` | Summary bar and card internals |
| `title title--small` | Agent name (bold heading) |
| `label label--inverted` | State badge for `active` and `error` |
| `label label--outline` | State badge for `blocked` |
| `label label--gray` | Muted text for freshness, `idle`, `stale` |
| `data-clamp="N"` | Text clamping for headline overflow |
| `title_bar` | Bottom bar with plugin name + timestamp |

---

## 11. OpenClaw Agent Integration

Each agent runs a cron job (e.g. every 10 minutes) that posts a status snapshot.

### Example cron script

```bash
#!/bin/bash
# /opt/openclaw/scripts/report-status.sh

STATUS_URL="https://<service-url>/api/v1/agent-status"
TOKEN="${AGENT_STATUS_TOKEN}"

curl -s -X POST "$STATUS_URL" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "display_name": "Matrim",
    "state": "active",
    "headline": "Fixing Expo iOS simulator signing",
    "emoji": "🔥",
    "ttl_seconds": 900
  }'
```

### Crontab entry

```cron
*/10 * * * * /opt/openclaw/scripts/report-status.sh >> /var/log/status-report.log 2>&1
```

### Future: Hook-based updates

After v1 is stable, agents can also push on state transitions (e.g. `blocked`,
`resumed`, `failed`) for near-real-time updates without waiting for the next
cron tick.

---

## 12. Request / Response Flow

```
Agent POST                              TRMNL GET
────────                               ─────────
  │                                        │
  │  POST /api/v1/agent-status             │
  │  Authorization: Bearer <WRITE_TOKEN>   │
  ▼                                        │
┌────────────────────────┐                 │
│ 1. Validate token      │                 │
│ 2. Map token → agent   │                 │
│ 3. Validate body       │                 │
│ 4. Upsert record       │                 │
│ 5. Return 200          │                 │
└────────────────────────┘                 │
                                           │
            GET /api/v1/trmnl/openclaw     │
            Authorization: Bearer <READ>   │
                                           ▼
                              ┌────────────────────────┐
                              │ 1. Validate read token  │
                              │ 2. Load all agents      │
                              │ 3. Compute staleness    │
                              │ 4. Build summary counts │
                              │ 5. Sort by priority     │
                              │ 6. Return JSON payload  │
                              └────────────────────────┘
```

---

## 13. v1 Scope

| Feature | Included |
|---|---|
| `POST /api/v1/agent-status` with bearer auth | ✅ |
| `GET /api/v1/trmnl/openclaw` with bearer auth | ✅ |
| Pydantic request validation | ✅ |
| Per-agent token → identity mapping | ✅ |
| SQLite latest-status storage | ✅ |
| TTL-based stale detection | ✅ |
| Summary counts (active, blocked, idle, error, stale) | ✅ |
| Pre-computed `minutes_ago` and `is_stale` | ✅ |
| Health check endpoint | ✅ |
| Dockerfile + Cloud Run deployment scripts | ✅ |
| TRMNL Liquid templates (base + upgrade views) | ✅ |
| Adaptive card grid layout (1–6 agents) | ✅ |
| Emoji mood avatar support (upgrade view) | ✅ |
| Unit tests for business logic and endpoints | ✅ |

---

## 14. Future Enhancements

| Enhancement | Priority |
|---|---|
| Short status history per agent (last N snapshots) | Medium |
| Last successful check-in + uptime indicators | Medium |
| Priority / severity flags | Low |
| Agent grouping by project or function | Low |
| Hook-driven near-real-time updates | Medium |
| Combined TRMNL layouts (countdown + status board) | Low |
| Optional web UI for debugging outside TRMNL | Low |
| GCS backup for SQLite | Medium |

---

## 15. Key Decisions Log

| Decision | Rationale |
|---|---|
| **FastAPI + Python** | Matches existing tooling; Pydantic gives free validation; lightweight for this use case. |
| **SQLite over GCS for v1** | Simpler reads/writes, structured queries for staleness, no external dependency. |
| **Separate read/write tokens** | Clean security boundary; TRMNL never touches write path. |
| **Server-side computed fields** | `minutes_ago`, `is_stale`, and sorting keep the Liquid template logic-free. |
| **Cloud Run** | Scale-to-zero keeps costs near $0; managed HTTPS; no VM to maintain. |
| **`stale` as derived state** | Agents never self-report `stale`; the server detects it from TTL expiry. |
