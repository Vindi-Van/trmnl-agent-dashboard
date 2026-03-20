"""
Pytest configuration and fixtures for TRMNL screenshot tests.

Provides shared fixtures for the Playwright browser and
screenshot output directory.
"""

import shutil
from pathlib import Path

import pytest


SCREENSHOTS_DIR = Path(__file__).resolve().parent / "screenshots"


@pytest.fixture(scope="session", autouse=True)
def screenshots_dir() -> Path:
    """
    Create (or clear) the screenshots output directory.

    Returns:
        Path to the screenshots directory.
    """
    if SCREENSHOTS_DIR.exists():
        shutil.rmtree(SCREENSHOTS_DIR)
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    return SCREENSHOTS_DIR
