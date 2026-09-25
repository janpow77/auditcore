"""Router reachability tracking and graceful-degradation wrappers.

``RouterHealth`` merges the audit_designer and flowinvoice variants: thread-safe
counters, injectable clock (flowinvoice), "never succeeded = not reachable"
(audit_designer) and redacted error messages of at most 160 characters.
"""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Awaitable, Callable, Iterable
from typing import ParamSpec, TypeVar

from auditcore_llm_client.errors import LlmClientError
from auditcore_llm_client.redaction import HEALTH_MESSAGE_LENGTH, redact

log = logging.getLogger("auditcore_llm_client")

P = ParamSpec("P")
T = TypeVar("T")

#: Legacy thresholds of both apps.
HEALTHY_WINDOW_S = 60.0
MAX_CONSECUTIVE_FAILURES = 3


class RouterHealth:
    """Last success, last error and consecutive failures of the gateway."""

    _shared: RouterHealth | None = None
    _shared_lock = threading.Lock()

    def __init__(
        self,
        *,
        clock: Callable[[], float] = time.time,
        secrets: Iterable[str] = (),
    ) -> None:
        self._now = clock
        self._secrets = tuple(secrets)
        self._lock = threading.Lock()
        self.last_success_at = 0.0
        self.last_error_at = 0.0
        self.last_error_message = ""
        self.consecutive_failures = 0

    @classmethod
    def shared(cls) -> RouterHealth:
        """Process-wide instance (legacy ``router_health()`` singleton)."""
        if cls._shared is None:
            with cls._shared_lock:
                if cls._shared is None:
                    cls._shared = cls()
        return cls._shared

    def add_secrets(self, secrets: Iterable[str]) -> None:
        """Register further values that must never be stored in clear text."""
        with self._lock:
            self._secrets = tuple({*self._secrets, *secrets})

    def record_success(self) -> None:
        """A call succeeded."""
        with self._lock:
            self.last_success_at = self._now()
            self.consecutive_failures = 0
            self.last_error_message = ""

    def record_failure(self, message: str) -> None:
        """A call failed; the message is stored redacted and truncated."""
        with self._lock:
            self.last_error_at = self._now()
            self.last_error_message = redact(
                message, secrets=self._secrets, max_len=HEALTH_MESSAGE_LENGTH
            )
            self.consecutive_failures += 1

    def _reachable(self, now: float) -> bool:
        if not self.last_success_at:
            return False
        return (
            now - self.last_success_at < HEALTHY_WINDOW_S
            and self.consecutive_failures < MAX_CONSECUTIVE_FAILURES
        )

    def is_healthy(self) -> bool:
        """Last success younger than 60 s and fewer than 3 failures in a row."""
        with self._lock:
            return self._reachable(self._now())

    def to_dict(self) -> dict[str, bool | int | str | None]:
        """Legacy ``/api/health`` shape."""
        with self._lock:
            now = self._now()
            return {
                "reachable": self._reachable(now),
                "last_success_age_s": (
                    int(now - self.last_success_at) if self.last_success_at else None
                ),
                "last_error_age_s": int(now - self.last_error_at) if self.last_error_at else None,
                "last_error_message": self.last_error_message or None,
                "consecutive_failures": self.consecutive_failures,
            }


def _unexpected(exc: Exception, secrets: Iterable[str]) -> str:
    log.warning("LLM-Aufruf: unerwarteter Fehler (%s)", type(exc).__name__)
    return redact(str(exc), secrets=secrets, max_len=HEALTH_MESSAGE_LENGTH)


def safe_call(
    func: Callable[P, T],
    *args: P.args,
    **kwargs: P.kwargs,
) -> tuple[T | None, str | None]:
    """Run ``func``; return ``(result, None)`` or ``(None, redacted message)``."""
    try:
        return func(*args, **kwargs), None
    except LlmClientError as error:
        return None, error.message
    except Exception as exc:  # noqa: BLE001 - graceful degradation is the purpose
        return None, _unexpected(exc, ())


async def async_safe_call(
    func: Callable[P, Awaitable[T]],
    *args: P.args,
    **kwargs: P.kwargs,
) -> tuple[T | None, str | None]:
    """Async variant of :func:`safe_call`."""
    try:
        return await func(*args, **kwargs), None
    except LlmClientError as error:
        return None, error.message
    except Exception as exc:  # noqa: BLE001 - graceful degradation is the purpose
        return None, _unexpected(exc, ())
