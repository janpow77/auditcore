"""Structured harvest errors; the engine decides retries from ``retryable``/``retry_after``."""

from __future__ import annotations

from typing import Any


class HarvestError(Exception):
    """Base error with a stable machine-readable ``code``."""

    code = "harvest_error"
    retryable = False

    def __init__(
        self,
        message: str,
        *,
        retry_after: float | None = None,
        retryable: bool | None = None,
        detail: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.retry_after = retry_after
        if retryable is not None:
            self.retryable = retryable
        self.detail = dict(detail or {})

    def to_dict(self) -> dict[str, Any]:
        """Secret-free representation for results and events."""
        return {
            "code": self.code,
            "message": str(self),
            "retryable": self.retryable,
            "retry_after": self.retry_after,
            "detail": self.detail,
        }


class ConfigError(HarvestError):
    """Invalid or missing adapter configuration (never retried)."""

    code = "config_error"


class AuthError(HarvestError):
    """Credentials missing, rejected or expired (never retried automatically)."""

    code = "auth_error"


class RateLimitError(HarvestError):
    """Source signalled rate limiting; ``retry_after`` in seconds if known."""

    code = "rate_limited"
    retryable = True


class TransportError(HarvestError):
    """Network, timeout or server error; retryable unless stated otherwise."""

    code = "transport_error"
    retryable = True


class ParserError(HarvestError):
    """The response could not be interpreted; never presented as an empty result."""

    code = "parser_error"


class SinkError(HarvestError):
    """The sink did not confirm the batch; the checkpoint is not advanced."""

    code = "sink_error"


class CheckpointConflict(HarvestError):
    """The stored checkpoint changed concurrently (compare-and-set failed)."""

    code = "checkpoint_conflict"


class Cancelled(HarvestError):
    """The run was cancelled cooperatively between pages."""

    code = "cancelled"


class LimitReached(HarvestError):
    """A configured run limit (pages, records, duration) stopped the run."""

    code = "limit_reached"
