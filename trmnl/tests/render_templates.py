"""
TRMNL template renderer for screenshot tests.

Loads the Liquid templates, inlines the card partials, renders
with mock data, and wraps the output in a full HTML page that
references the TRMNL Framework CSS/JS for accurate rendering.
"""

import re
from pathlib import Path
from typing import Any

from liquid import Environment


# ─── Constants ────────────────────────────────────────────────

TRMNL_CSS_URL = "https://trmnl.com/css/latest/plugins.css"
TRMNL_JS_URL = "https://trmnl.com/js/latest/plugins.js"
TRMNL_SCREEN_WIDTH = 800
TRMNL_SCREEN_HEIGHT = 480

# Root of the trmnl/ directory (parent of tests/)
_TRMNL_DIR = Path(__file__).resolve().parent.parent


# ─── Card partial markup ─────────────────────────────────────

BASE_CARD_PARTIAL = """
<div class="flex flex--col" style="gap: 4px;">
  <span class="title title--small" data-clamp="1">{{ agent.display_name }}</span>

  {% if agent.state == "active" %}
    <span class="label label--small label--inverted" style="align-self: flex-start; padding: 1px 6px;">● ACTIVE</span>
  {% elsif agent.state == "blocked" %}
    <span class="label label--small label--outline" style="align-self: flex-start; padding: 1px 6px;">◼ BLOCKED</span>
  {% elsif agent.state == "idle" %}
    <span class="label label--small label--gray" style="align-self: flex-start;">○ IDLE</span>
  {% elsif agent.state == "error" %}
    <span class="label label--small label--inverted" style="align-self: flex-start; padding: 1px 6px;">✕ ERROR</span>
  {% elsif agent.state == "stale" %}
    <span class="label label--small label--gray" style="align-self: flex-start;">◌ STALE</span>
  {% else %}
    <span class="label label--small label--gray" style="align-self: flex-start;">{{ agent.state | upcase }}</span>
  {% endif %}

  <span class="label" data-clamp="2">{{ agent.headline }}</span>

  {% if agent.blocked_on %}
    <span class="label label--small label--gray" data-clamp="1">↳ {{ agent.blocked_on }}</span>
  {% endif %}

  <span class="label label--small label--gray">{{ agent.minutes_ago }}m ago</span>
</div>
""".strip()

UPGRADE_CARD_PARTIAL = """
<div class="flex flex--col" style="gap: 4px;">

  <div class="flex flex--row" style="gap: 8px; align-items: center;">
    <span style="font-size: 24px; line-height: 1;">{{ agent.emoji | default: "🤖" }}</span>
    <span class="title title--small" data-clamp="1">{{ agent.display_name }}</span>
  </div>

  {% if agent.state == "active" %}
    <span class="label label--small label--inverted" style="align-self: flex-start; padding: 1px 6px;">● ACTIVE</span>
  {% elsif agent.state == "blocked" %}
    <span class="label label--small label--outline" style="align-self: flex-start; padding: 1px 6px;">◼ BLOCKED</span>
  {% elsif agent.state == "idle" %}
    <span class="label label--small label--gray" style="align-self: flex-start;">○ IDLE</span>
  {% elsif agent.state == "error" %}
    <span class="label label--small label--inverted" style="align-self: flex-start; padding: 1px 6px;">✕ ERROR</span>
  {% elsif agent.state == "stale" %}
    <span class="label label--small label--gray" style="align-self: flex-start;">◌ STALE</span>
  {% else %}
    <span class="label label--small label--gray" style="align-self: flex-start;">{{ agent.state | upcase }}</span>
  {% endif %}

  <span class="label" data-clamp="2">{{ agent.headline }}</span>

  {% if agent.blocked_on %}
    <span class="label label--small label--gray" data-clamp="1">↳ {{ agent.blocked_on }}</span>
  {% endif %}

  <span class="label label--small label--gray">{{ agent.minutes_ago }}m ago</span>
</div>
""".strip()


# ─── Template helpers ─────────────────────────────────────────


def _load_template_source(template_name: str) -> str:
    """
    Load a .liquid template file from the trmnl/ directory.

    Args:
        template_name: Filename (e.g. 'base_view.liquid').

    Returns:
        Raw template source string.

    Raises:
        FileNotFoundError: If the template file does not exist.
    """
    path = _TRMNL_DIR / template_name
    return path.read_text(encoding="utf-8")


def _inline_partials(source: str, partial_markup: str, partial_name: str) -> str:
    """
    Replace {% include 'partial_name' %} tags with actual card markup.

    This converts the documentation-style includes into renderable
    Liquid by substituting the card partial inline.

    Args:
        source: Raw Liquid template source with {% include %} tags.
        partial_markup: The card HTML/Liquid to substitute.
        partial_name: Name of the partial (e.g. 'agent_card_base').

    Returns:
        Template source with includes replaced by inline markup.
    """
    # Match {% include 'partial_name' %} with flexible whitespace/quotes
    pattern = rf"{{% include ['\"]{ re.escape(partial_name) }['\"] %}}"
    return re.sub(pattern, partial_markup, source)


def _strip_comment_block(source: str) -> str:
    """
    Remove the trailing HTML comment block that contains the
    card partial documentation (everything after </div> closing
    the view).

    Args:
        source: Template source.

    Returns:
        Cleaned template source without trailing comment blocks.
    """
    # Remove all HTML comments (<!-- ... -->)
    return re.sub(r"<!--[\s\S]*?-->", "", source)


def render_template(
    template_name: str,
    view_type: str,
    data: dict[str, Any],
) -> str:
    """
    Render a TRMNL Liquid template with data and return full HTML.

    Loads the template file, inlines the appropriate card partial,
    renders the Liquid with the provided data, and wraps the result
    in a complete HTML page with TRMNL CSS/JS.

    Args:
        template_name: Template file (e.g. 'base_view.liquid').
        view_type: 'base' or 'upgrade' — determines which card partial.
        data: Mock data dictionary with 'summary', 'agents', etc.

    Returns:
        Complete HTML string ready for browser rendering.
    """
    source = _load_template_source(template_name)

    # Choose the right partial and include name
    if view_type == "upgrade":
        partial = UPGRADE_CARD_PARTIAL
        include_name = "agent_card_upgrade"
    else:
        partial = BASE_CARD_PARTIAL
        include_name = "agent_card_base"

    # Inline the partials and strip comment blocks
    source = _inline_partials(source, partial, include_name)
    source = _strip_comment_block(source)

    # Render the Liquid template
    env = Environment()
    template = env.from_string(source)
    rendered_body = template.render(**data)

    # Wrap in a full HTML page with TRMNL framework
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width={TRMNL_SCREEN_WIDTH}">
  <title>TRMNL Preview — {view_type} — {len(data.get('agents', []))} agents</title>
  <link rel="stylesheet" href="{TRMNL_CSS_URL}">
  <script src="{TRMNL_JS_URL}"></script>
  <style>
    /* ── Base viewport ── */
    html, body {{
      margin: 0;
      padding: 0;
      width: {TRMNL_SCREEN_WIDTH}px;
      height: {TRMNL_SCREEN_HEIGHT}px;
      overflow: hidden;
      background: #fff;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI",
                   Roboto, Helvetica, Arial, sans-serif;
      font-size: 14px;
      color: #000;
    }}

    /* ── Screen / View / Layout (TRMNL structure) ── */
    .screen {{
      width: {TRMNL_SCREEN_WIDTH}px;
      height: {TRMNL_SCREEN_HEIGHT}px;
      position: relative;
    }}
    .view {{
      width: 100%;
      height: 100%;
      display: flex;
      flex-direction: column;
    }}
    .layout {{
      flex: 1;
      display: flex;
      flex-direction: column;
      padding: 12px 16px;
      overflow: hidden;
    }}
    .layout--col {{ flex-direction: column; }}
    .layout--row {{ flex-direction: row; }}

    /* ── Grid system ── */
    .grid {{
      display: grid;
      gap: 8px;
    }}
    .grid--cols-1 {{ grid-template-columns: 1fr; }}
    .grid--cols-2 {{ grid-template-columns: 1fr 1fr; }}
    .grid--cols-3 {{ grid-template-columns: 1fr 1fr 1fr; }}
    .grid--cols-4 {{ grid-template-columns: repeat(4, 1fr); }}
    .col {{ display: flex; flex-direction: column; }}

    /* ── Flex system ── */
    .flex {{ display: flex; }}
    .flex--row {{ flex-direction: row; }}
    .flex--col {{ flex-direction: column; }}

    /* ── Title system ── */
    .title {{
      font-weight: 700;
      font-size: 16px;
      line-height: 1.2;
    }}
    .title--small {{ font-size: 14px; }}
    .title--base {{ font-size: 16px; }}
    .title--large {{ font-size: 20px; }}
    .title--xlarge {{ font-size: 24px; }}

    /* ── Label system ── */
    .label {{
      font-size: 13px;
      font-weight: 400;
      line-height: 1.3;
    }}
    .label--small {{ font-size: 11px; }}
    .label--large {{ font-size: 15px; }}
    .label--gray {{ color: #666; }}
    .label--inverted {{
      background: #000;
      color: #fff;
      border-radius: 3px;
      padding: 1px 6px;
      display: inline-block;
    }}
    .label--outline {{
      border: 1px solid #000;
      border-radius: 3px;
      padding: 1px 6px;
      display: inline-block;
    }}

    /* ── Title bar ── */
    .title_bar {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 8px 16px;
      border-top: 1px solid #ccc;
      font-size: 12px;
    }}
    .title_bar .title {{
      font-size: 12px;
      font-weight: 600;
    }}
    .title_bar .instance {{
      font-size: 11px;
      color: #888;
    }}

    /* ── Data-clamp (text overflow) ── */
    [data-clamp="1"] {{
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }}
    [data-clamp="2"] {{
      overflow: hidden;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
    }}
  </style>
</head>
<body>
  <div class="screen">
    {rendered_body}
  </div>
</body>
</html>"""

    return html
