"""Shared helpers: fixture decoding and loaded profiles."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

FIXTURES = Path(__file__).parent / "fixtures"
sys.path.insert(0, str(Path(__file__).parent))


def decode(value: Any) -> Any:
    """Inverse of the capture tools' ``encode`` (NaN/inf/timestamps)."""
    if isinstance(value, dict):
        if "$float" in value:
            return float(value["$float"])
        if "$nat" in value:
            return None
        if "$datetime" in value:
            return datetime.fromisoformat(value["$datetime"])
        return {k: decode(v) for k, v in value.items()}
    if isinstance(value, list):
        return [decode(v) for v in value]
    return value


def fixture(name: str) -> dict[str, Any]:
    data: dict[str, Any] = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    return data
