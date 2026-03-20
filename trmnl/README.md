# TRMNL Plugin Templates

Liquid markup templates for the OpenClaw Agent Status Board TRMNL
Private Plugin, with Playwright-based screenshot tests for visual
verification.

## Templates

| File | Description |
|---|---|
| `base_view.liquid` | Status cards with adaptive grid layout (1–6 agents). Clean typographic hierarchy, no avatars. |
| `upgrade_view.liquid` | Same layout with emoji mood avatars per agent. |

## Layout Strategy

The template renders agent statuses as **cards in a single full-screen view**,
using the TRMNL Grid system to adapt the layout based on agent count:

| Agents | Layout |
|---|---|
| 1 | Single full-width card |
| 2 | 2-column split (`grid--cols-2`) |
| 3 | 3-column split (`grid--cols-3`) |
| 4 | 2×2 grid (`grid--cols-2`, 2 rows) |
| 5 | 3-col top row + 2-col bottom row |
| 6 | 3×2 grid (`grid--cols-3`, 2 rows) |

## Card Anatomy

### Base View

```
┌─────────────────────────┐
│  AGENT NAME             │  ← title (bold)
│  ● ACTIVE               │  ← state badge (inverted/outline)
│  Fixing iOS signing     │  ← headline (label)
│  ↳ cert rotation        │  ← blocked_on (if applicable)
│  12m ago                │  ← freshness (gray)
└─────────────────────────┘
```

### Upgrade View

```
┌─────────────────────────┐
│  🔥  AGENT NAME         │  ← emoji avatar + title
│  ● ACTIVE               │  ← state badge
│  Fixing iOS signing     │  ← headline
│  12m ago                │  ← freshness
└─────────────────────────┘
```

## TRMNL Plugin Setup

1. Go to **TRMNL Dashboard → Private Plugins → New**
2. Set **Strategy** to **Polling**
3. Set **Polling URL** to `https://<service-url>/api/v1/trmnl/openclaw`
4. Add header: `Authorization: Bearer <TRMNL_READ_TOKEN>`
5. Paste the contents of `base_view.liquid` (or `upgrade_view.liquid`) into
   the **Full** markup editor
6. Set poll interval to **15 minutes**
7. Add the plugin to your device playlist

> **Note**: The templates use `{% include %}` tags as documentation markers.
> Before pasting into TRMNL, expand each include with the inline card markup
> shown at the bottom of each template file. TRMNL's editor does not support
> separate partial files.

## Data Contract

The templates expect the JSON response from `GET /api/v1/trmnl/openclaw`:

```json
{
  "generated_at": "2026-03-20T07:30:00Z",
  "summary": {
    "total": 3,
    "active": 1,
    "blocked": 1,
    "idle": 1,
    "error": 0,
    "stale": 0
  },
  "agents": [
    {
      "display_name": "Matrim",
      "state": "active",
      "headline": "Fixing Expo iOS simulator signing",
      "emoji": "🔥",
      "blocked_on": null,
      "minutes_ago": 5,
      "is_stale": false
    }
  ]
}
```

## Screenshot Tests

Playwright-based tests render both templates with mock data for 1–6 agents and
capture PNGs at 800×480 (TRMNL OG resolution).

### Running Tests

```bash
# Install (one-time)
pip install -r requirements-dev.txt
python -m playwright install chromium

# Run
python -m pytest trmnl/tests/test_screenshots.py -v

# View results
start trmnl/tests/screenshots/index.html
```

### Test Files

| File | Purpose |
|---|---|
| `tests/mock_data.py` | 6 scenarios with Wheel of Time themed agents |
| `tests/render_templates.py` | Liquid renderer + CSS fallbacks for offline rendering |
| `tests/conftest.py` | Screenshot directory fixture |
| `tests/test_screenshots.py` | 13 parametrized tests + gallery index |

The tests generate 12 PNGs (base + upgrade × 6 scenarios) and an HTML gallery
page for side-by-side visual review. They always pass — they exist for visual
verification, not pixel-diff comparison.
