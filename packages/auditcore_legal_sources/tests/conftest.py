"""Recorded original behavior of auditdatabase@bba911e and audit_designer@030a71e."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

FIXTURE = Path(__file__).parent / "fixtures" / "legacy_harvesters_observed.json"


def revive(value: Any) -> Any:
    """Turn ``{"$datetime": ...}`` markers back into datetimes."""
    if isinstance(value, dict):
        if set(value) == {"$datetime"}:
            return datetime.fromisoformat(value["$datetime"])
        return {k: revive(v) for k, v in value.items()}
    if isinstance(value, list):
        return [revive(v) for v in value]
    return value


@pytest.fixture(scope="session")
def legacy() -> dict[str, Any]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))
