"""Machine-readable error kinds shared by the error and result contracts."""

from __future__ import annotations

from enum import StrEnum


class ErrorKind(StrEnum):
    """What went wrong, independent of the error class and its message.

    ``code`` of a :class:`~auditcore_harvest.errors.HarvestError` stays the
    stable class identifier; ``ErrorKind`` refines it (for example a
    ``transport_error`` caused by a timeout or by an HTTP status).
    """

    NETWORK = "network"
    TIMEOUT = "timeout"
    HTTP_STATUS = "http_status"
    RATE_LIMITED = "rate_limited"
    AUTH = "auth"
    PARSE = "parse"
    CONFIG = "config"
    SINK = "sink"
    CHECKPOINT = "checkpoint"
    CANCELLED = "cancelled"
    LIMIT = "limit"
    UNKNOWN = "unknown"
