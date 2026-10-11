"""Structured harvest errors; the engine decides retries from ``retryable``/``retry_after``.

Every error carries an :class:`ErrorKind` and, where a response was received,
the ``http_status``; consumers no longer reconstruct both from exception types
or message texts.
"""

from __future__ import annotations

from .kinds import ErrorKind as ErrorKind
from .model import JSON


class HarvestError(Exception):
    """Base error with a stable machine-readable ``code`` and an error ``kind``."""

    code = "harvest_error"
    retryable = False
    kind = ErrorKind.UNKNOWN

    def __init__(
        self,
        message: str,
        *,
        retry_after: float | None = None,
        retryable: bool | None = None,
        detail: dict[str, JSON] | None = None,
        http_status: int | None = None,
        kind: ErrorKind | None = None,
    ) -> None:
        super().__init__(message)
        self.retry_after = retry_after
        if retryable is not None:
            self.retryable = retryable
        if kind is not None:
            self.kind = kind
        self.http_status = http_status
        self.detail = dict(detail or {})

    def to_dict(self) -> dict[str, JSON]:
        """Secret-free representation for results and events."""
        return {
            "code": self.code,
            "message": str(self),
            "retryable": self.retryable,
            "retry_after": self.retry_after,
            "detail": self.detail,
            "http_status": self.http_status,
            "error_kind": self.kind.value,
        }


class ConfigError(HarvestError):
    """Invalid or missing adapter configuration (never retried)."""

    code = "config_error"
    kind = ErrorKind.CONFIG


class AuthError(HarvestError):
    """Credentials missing, rejected or expired (never retried automatically)."""

    code = "auth_error"
    kind = ErrorKind.AUTH


class RateLimitError(HarvestError):
    """Source signalled rate limiting; ``retry_after`` in seconds if known."""

    code = "rate_limited"
    retryable = True
    kind = ErrorKind.RATE_LIMITED


class TransportError(HarvestError):
    """Network, timeout or server error; retryable unless stated otherwise."""

    code = "transport_error"
    retryable = True
    kind = ErrorKind.NETWORK


class ParserError(HarvestError):
    """The response could not be interpreted; never presented as an empty result."""

    code = "parser_error"
    kind = ErrorKind.PARSE


class SinkError(HarvestError):
    """The sink did not confirm the batch; the checkpoint is not advanced."""

    code = "sink_error"
    kind = ErrorKind.SINK


class CheckpointConflict(HarvestError):
    """The stored checkpoint changed concurrently (compare-and-set failed)."""

    code = "checkpoint_conflict"
    kind = ErrorKind.CHECKPOINT


class Cancelled(HarvestError):
    """The run was cancelled cooperatively between pages."""

    code = "cancelled"
    kind = ErrorKind.CANCELLED


class LimitReached(HarvestError):
    """A configured run limit (pages, records, duration) stopped the run."""

    code = "limit_reached"
    kind = ErrorKind.LIMIT
