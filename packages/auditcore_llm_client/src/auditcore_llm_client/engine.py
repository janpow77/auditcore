"""Transport-independent call bookkeeping shared by the sync and async clients."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, replace
from typing import Generic, TypeVar

from auditcore_llm_client.config import ClientConfig, Mode
from auditcore_llm_client.errors import POLICY_KINDS, ErrorKind, LlmClientError
from auditcore_llm_client.health import RouterHealth
from auditcore_llm_client.received import ReceivedResponse, error_for_status
from auditcore_llm_client.resilience import CircuitBreaker
from auditcore_llm_client.results import LlmResult, UsageRecord
from auditcore_llm_client.wire import PreparedRequest

T = TypeVar("T")
log = logging.getLogger("auditcore_llm_client")

#: Placeholder passed to ``Operation.parse`` when no request is necessary.
NO_RESPONSE = ReceivedResponse(status=0, content=b"", path="")


@dataclass(frozen=True)
class Operation(Generic[T]):
    """One public call: the request (``None`` = answer without network) and its parser."""

    request: PreparedRequest | None
    parse: Callable[[ReceivedResponse], T]


def with_timeout(request: PreparedRequest, timeout: float | None) -> PreparedRequest:
    """Apply a per-call timeout to the request and its 404 fallback."""
    if timeout is None:
        return request
    fallback = request.fallback_on_404
    return replace(
        request,
        timeout=timeout,
        fallback_on_404=with_timeout(fallback, timeout) if fallback else None,
    )


class Resilience:
    """Circuit breaker, retry decisions and health tracking of one client."""

    def __init__(self, config: ClientConfig, health: RouterHealth | None) -> None:
        self.config = config
        self.health = health
        self.breaker = CircuitBreaker(config.breaker) if config.breaker else None
        if health is not None:
            health.add_secrets(config.secrets)

    def before(self, request: PreparedRequest) -> None:
        """Raise ``CircuitOpenError`` while the breaker is open."""
        if self.breaker is not None:
            self.breaker.before_call(request.path)

    def retry_delay(self, error: LlmClientError, attempt: int) -> float | None:
        """Seconds to wait before the next attempt, or ``None`` to give up."""
        policy = self.config.retry
        if not policy.should_retry(error, attempt):
            return None
        delay = policy.delay(attempt, error.retry_after)
        log.info("LLM-Aufruf %s: Versuch %d fehlgeschlagen (%s), neuer Versuch in %.2fs",
                 error.endpoint, attempt, error.kind.value, delay)
        return delay

    def succeeded(self) -> None:
        """Record a successful call."""
        if self.breaker is not None:
            self.breaker.record_success()
        if self.health is not None:
            self.health.record_success()

    def failed(self, error: LlmClientError) -> None:
        """Record a failed call (an open breaker is not counted as another outage).

        Flow-Agent policy rejections are no outage: neither breaker nor health count them.
        """
        if error.kind in POLICY_KINDS:
            log.warning("LLM-Aufruf %s abgelehnt: %s", error.endpoint, error.kind.value)
            return
        if self.breaker is not None and error.kind is not ErrorKind.CIRCUIT_OPEN:
            self.breaker.record_failure(error)
        if self.health is not None:
            self.health.record_failure(error.message)
        log.warning("LLM-Aufruf %s fehlgeschlagen: %s", error.endpoint, error.kind.value)


def status_error(config: ClientConfig, received: ReceivedResponse) -> LlmClientError:
    """Error for an HTTP status >= 400 in the dialect of the configured mode."""
    return error_for_status(
        received, config.secrets, flow_agent=config.mode is Mode.FLOW_AGENT
    )


def notify_usage(config: ClientConfig, operation: str, result: object) -> None:
    """Pass token usage of LLM answers to ``config.usage_hook`` (audit-portal metering)."""
    if config.usage_hook is None or not isinstance(result, LlmResult):
        return
    config.usage_hook(
        UsageRecord(
            operation=operation,
            model=result.model,
            prompt_tokens=result.input_tokens,
            completion_tokens=result.output_tokens,
            latency_ms=result.latency_ms,
        )
    )
