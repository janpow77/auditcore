"""The only module of the package that imports ``auditcore_harvest`` (extra ``sources``)."""

from __future__ import annotations

try:
    from auditcore_harvest import (
        AuthKind,
        Capabilities,
        FetchContext,
        HarvestError,
        HarvestRecord,
        PageResult,
        PageStatus,
        ParserError,
        RecordIssue,
        SnapshotSemantics,
        Source,
        raise_for_status,
    )
    from auditcore_harvest.adapter import require
    from auditcore_harvest.errors import ConfigError
except ImportError as exc:  # pragma: no cover - exercised without the extra
    from ..errors import DependencyError

    raise DependencyError(
        "auditcore_harvest fehlt: auditcore_property_sources[sources] installieren."
    ) from exc

__all__ = [
    "AuthKind",
    "Capabilities",
    "ConfigError",
    "FetchContext",
    "HarvestError",
    "HarvestRecord",
    "PageResult",
    "PageStatus",
    "ParserError",
    "RecordIssue",
    "SnapshotSemantics",
    "Source",
    "raise_for_status",
    "require",
]
