"""Shared type alias of the parsers (no dependency on ``auditcore_harvest``)."""

from __future__ import annotations

from typing import Any

#: JSON-compatible source value (portal JSON, JSON-LD, page state). The one
#: deliberate ``Any`` of the parsers: values are narrowed with ``isinstance``
#: where the code depends on their shape.
JSON = Any
