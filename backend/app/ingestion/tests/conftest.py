"""Shared test configuration and fixtures."""

import json
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(name: str):
    """Load a JSON fixture file from tests/fixtures/.

    Supports paths like "kalshi/KXELONMARS-99.json" for per-event fixtures.
    """
    path = FIXTURES_DIR / name
    return json.loads(path.read_text())


def list_fixtures(subdir: str) -> list[str]:
    """List all JSON fixture filenames in a subdirectory."""
    path = FIXTURES_DIR / subdir
    if not path.is_dir():
        return []
    return sorted(f.name for f in path.glob("*.json"))
