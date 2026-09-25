"""Random identifiers."""

from __future__ import annotations

import uuid


def new_uuid() -> str:
    """Random UUID 4 in its canonical text form."""
    return str(uuid.uuid4())
