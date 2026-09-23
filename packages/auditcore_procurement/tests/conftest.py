"""The recorded original behavior of audit-portal, flowinvoice and audit_designer."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import Any

FIXTURE = Path(__file__).parent / "fixtures" / "procurement_legacy_observed.json"
LEGACY: dict[str, Any] = json.loads(FIXTURE.read_text(encoding="utf-8"))


def revive(value: Any) -> Any:
    """Turn ``{"$decimal": ...}`` markers back into Decimals."""
    if isinstance(value, dict):
        if set(value) == {"$decimal"}:
            return Decimal(value["$decimal"])
        return {k: revive(v) for k, v in value.items()}
    if isinstance(value, list):
        return [revive(v) for v in value]
    return value


def normalise(value: Any) -> Any:
    """JSON round trip so tuples/lists compare like the fixture."""
    return json.loads(json.dumps(value, ensure_ascii=False))
