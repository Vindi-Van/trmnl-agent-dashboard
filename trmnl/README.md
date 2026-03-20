# TRMNL Plugin Templates

This directory contains the Liquid markup templates for the OpenClaw Agent
Status Board TRMNL Private Plugin.

## Templates

| File | Description |
|---|---|
| `base_view.liquid` | Status cards with adaptive grid layout (1–6 agents). Clean typographic hierarchy, no avatars. |
| `upgrade_view.liquid` | Same layout with emoji mood avatars per agent. |

## Layout Strategy

The template renders agent status as **cards in a single full-screen view**,
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
┌─────────────────────┐
│  AGENT NAME         │  ← title (bold)
│  ● ACTIVE           │  ← state badge (label--inverted)
│  Fixing iOS signing │  ← headline (label)
│  12m ago            │  ← freshness (label--gray)
└─────────────────────┘
```

### Upgrade View
```
┌─────────────────────┐
│  🔥  AGENT NAME     │  ← emoji avatar + title
│  ● ACTIVE           │  ← state badge
│  Fixing iOS signing │  ← headline
│  12m ago            │  ← freshness
└─────────────────────┘
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

## Data Contract

The templates expect the JSON response shape documented in
[ARCHITECTURE.md](../docs/ARCHITECTURE.md#5-api-design) — specifically the
`summary` object and `agents` array from `GET /api/v1/trmnl/openclaw`.

### Required Fields per Agent

- `display_name` — agent name
- `state` — one of: `active`, `blocked`, `idle`, `error`, `stale`
- `headline` — one-line task summary
- `minutes_ago` — computed freshness
- `is_stale` — boolean
- `emoji` — mood emoji (upgrade view only)
