# OpenClaw Agent Status Board

A lightweight status-aggregation service that lets OpenClaw agents publish
periodic, authenticated progress snapshots to a secure endpoint — and exposes
a clean, read-only JSON feed for [TRMNL](https://usetrmnl.com) e-ink display.

## What It Does

```
OpenClaw Agents ──▶ POST /api/v1/agent-status ──▶ Status Board API
                                                        │
                    TRMNL Device ◀── GET /api/v1/trmnl/openclaw
```

- **Agents** send short status snapshots on a cron schedule (every ~10 min)
- **Status Board API** validates, stores, computes staleness, and builds a
  compact display payload
- **TRMNL** polls the read endpoint and renders an e-ink dashboard

The board answers simple operational questions at a glance: *Which agents are
active? Which are blocked? What are they working on? When did they last
check in?*

## Status Model

| State | Meaning |
|---|---|
| `active` | Agent is executing work |
| `blocked` | Agent is waiting on an external dependency |
| `idle` | Agent is available but has no assignment |
| `error` | Agent encountered a failure |
| `stale` | Derived — agent missed its TTL window |

## Project Structure

```
trmnl-agent-dashboard/
├── app/                    # FastAPI backend service
│   ├── main.py             # App entry point
│   ├── config.py           # Settings (pydantic-settings)
│   ├── models/             # Pydantic schemas
│   ├── routers/            # API endpoints
│   ├── services/           # Business logic
│   ├── storage/            # SQLite repository
│   └── auth/               # Bearer token auth
├── trmnl/                  # TRMNL plugin templates + tests
│   ├── base_view.liquid    # Status cards (no avatars)
│   ├── upgrade_view.liquid # Status cards + emoji mood avatars
│   └── tests/              # Playwright screenshot tests
├── tests/                  # Backend API tests
├── infra/                  # GCP deployment scripts
├── docs/
│   └── ARCHITECTURE.md     # Full architecture document
├── Dockerfile
├── requirements.txt
└── requirements-dev.txt
```

## Tech Stack

| Layer | Technology |
|---|---|
| API | Python 3.12 + FastAPI |
| Validation | Pydantic |
| Storage | SQLite (v1) |
| Auth | Bearer tokens (per-agent write, separate read) |
| Display | TRMNL Private Plugin (Liquid templates) |
| Hosting | GCP Cloud Run + Secret Manager |

## Quick Start

### Prerequisites

- Python 3.12+
- A TRMNL device (for display) — optional for API development

### Development

```bash
# Clone and install
git clone https://github.com/your-org/trmnl-agent-dashboard.git
cd trmnl-agent-dashboard
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your tokens

# Run locally
uvicorn app.main:app --reload --port 8080
```

### Run Screenshot Tests

```bash
pip install -r requirements-dev.txt
python -m playwright install chromium
python -m pytest trmnl/tests/test_screenshots.py -v

# Open the visual gallery
start trmnl/tests/screenshots/index.html
```

## API Endpoints

| Method | Endpoint | Auth | Purpose |
|---|---|---|---|
| `POST` | `/api/v1/agent-status` | Agent write token | Publish status snapshot |
| `GET` | `/api/v1/trmnl/openclaw` | TRMNL read token | Fetch display payload |
| `GET` | `/api/v1/health` | None | Health check |

## TRMNL Dashboard Preview

The templates adapt to 1–6 agents with cards arranged in responsive grids:

| Agents | Layout |
|---|---|
| 1 | Full-width card |
| 2 | Side-by-side split |
| 3 | 3-column row |
| 4 | 2×2 grid |
| 5 | 3 top + 2 bottom |
| 6 | 3×2 grid |

See [trmnl/README.md](trmnl/README.md) for template details and plugin setup.

## Documentation

- [Architecture](docs/ARCHITECTURE.md) — system design, data model, API,
  auth, storage, infrastructure, and deployment
- [TRMNL Templates](trmnl/README.md) — template docs, card anatomy,
  plugin setup guide

## License

See [LICENSE](LICENSE).
