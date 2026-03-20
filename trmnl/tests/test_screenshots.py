"""
Screenshot tests for TRMNL Liquid templates.

Renders each template variant (base, upgrade) with mock data
for 1–6 agents, captures screenshots at 800×480 (TRMNL OG
resolution), and saves them for visual review.

These tests always pass — they exist for visual verification,
not pixel-diff comparison. Run them and inspect the output
in trmnl/tests/screenshots/.

Usage:
    pytest trmnl/tests/test_screenshots.py -v
"""

from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

from trmnl.tests.mock_data import ALL_SCENARIOS
from trmnl.tests.render_templates import (
    TRMNL_SCREEN_HEIGHT,
    TRMNL_SCREEN_WIDTH,
    render_template,
)


# ─── Parametrize across all scenarios and views ───────────────

VIEWS = [
    ("base", "base_view.liquid"),
    ("upgrade", "upgrade_view.liquid"),
]

TEST_CASES = [
    (view_type, template_file, scenario_name, scenario_data)
    for view_type, template_file in VIEWS
    for scenario_name, scenario_data in ALL_SCENARIOS.items()
]

TEST_IDS = [
    f"{view_type}_{scenario_name}"
    for view_type, _, scenario_name, _ in TEST_CASES
]


@pytest.mark.parametrize(
    "view_type, template_file, scenario_name, scenario_data",
    TEST_CASES,
    ids=TEST_IDS,
)
def test_screenshot(
    view_type: str,
    template_file: str,
    scenario_name: str,
    scenario_data: dict,
    screenshots_dir: Path,
) -> None:
    """
    Render a TRMNL template and capture a screenshot.

    Generates HTML from the Liquid template with mock data,
    opens it in a headless Chromium browser at the TRMNL
    screen resolution, and saves the screenshot.

    Args:
        view_type: 'base' or 'upgrade'.
        template_file: Liquid template filename.
        scenario_name: Scenario identifier (e.g. '3_agents').
        scenario_data: Mock data dictionary.
        screenshots_dir: Path to output directory (from fixture).
    """
    # Render the template to a full HTML page
    html = render_template(template_file, view_type, scenario_data)

    # Save the rendered HTML for debugging
    html_path = screenshots_dir / f"{view_type}_{scenario_name}.html"
    html_path.write_text(html, encoding="utf-8")

    # Capture screenshot with Playwright
    screenshot_path = screenshots_dir / f"{view_type}_{scenario_name}.png"

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={
                "width": TRMNL_SCREEN_WIDTH,
                "height": TRMNL_SCREEN_HEIGHT,
            },
        )

        # Load the rendered HTML from file
        page.goto(f"file:///{html_path.as_posix()}")

        # Wait for TRMNL CSS/JS to load (network resources)
        # Fall back to a short wait if network is unavailable
        try:
            page.wait_for_load_state("networkidle", timeout=5000)
        except Exception:
            page.wait_for_timeout(1000)

        # Capture the full page screenshot
        page.screenshot(path=str(screenshot_path), full_page=False)

        browser.close()

    # Verify the screenshot was created
    assert screenshot_path.exists(), (
        f"Screenshot not created: {screenshot_path}"
    )
    assert screenshot_path.stat().st_size > 0, (
        f"Screenshot is empty: {screenshot_path}"
    )


def test_generate_index(screenshots_dir: Path) -> None:
    """
    Generate an HTML index page linking all screenshots.

    Creates a simple gallery page for easy side-by-side
    visual review of all rendered template variants.
    """
    screenshots = sorted(screenshots_dir.glob("*.png"))

    if not screenshots:
        pytest.skip("No screenshots to index — run other tests first.")

    rows = []
    for img_path in screenshots:
        name = img_path.stem
        rows.append(
            f'<div style="margin: 16px 0;">'
            f'<h3>{name}</h3>'
            f'<img src="{img_path.name}" '
            f'width="{TRMNL_SCREEN_WIDTH}" '
            f'style="border: 1px solid #ccc; border-radius: 4px;" />'
            f'</div>'
        )

    index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>TRMNL Template Screenshots</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, sans-serif;
      max-width: 900px;
      margin: 0 auto;
      padding: 24px;
      background: #f5f5f5;
    }}
    h1 {{ color: #222; }}
    h3 {{
      font-family: monospace;
      color: #555;
      margin-bottom: 8px;
    }}
    img {{ display: block; }}
  </style>
</head>
<body>
  <h1>🤖 TRMNL Template Screenshots</h1>
  <p>Generated screenshots for visual review of all template
     variants and agent-count layouts.</p>
  {''.join(rows)}
</body>
</html>"""

    index_path = screenshots_dir / "index.html"
    index_path.write_text(index_html, encoding="utf-8")
    assert index_path.exists()
