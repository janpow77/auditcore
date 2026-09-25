"""Structured errors. Every message is redacted; no exception carries a secret.

Errors raised from transport failures are *not* chained to the underlying
httpx exception (``raise ... from None``): httpx messages may contain the
request URL, and tracebacks of chained exceptions end up in logs. The original
exception type is kept as ``cause_type``.
"""

from __future__ import annotations

from collections.abc import Iterable
from enum import StrEnum

from auditcore_llm_client.redaction import ERROR_MESSAGE_LENGTH, redact


class ErrorKind(StrEnum):
    """Why a call failed."""

    CONFIGURATION = "configuration"
    UNREACHABLE = "unreachable"
    TIMEOUT = "timeout"
    HTTP_STATUS = "http_status"
    INVALID_RESPONSE = "invalid_response"
    CIRCUIT_OPEN = "circuit_open"
    NOT_ASSIGNED = "not_assigned"
    UNSUPPORTED = "unsupported"
    SENSITIVITY_REJECTED = "sensitivity_rejected"
    EGRESS_DENIED = "egress_denied"


#: Kinds that indicate the router/gateway itself is unavailable.
AVAILABILITY_KINDS = frozenset({ErrorKind.UNREACHABLE, ErrorKind.TIMEOUT})
#: Policy decisions of the Flow-Agent: never retried, not counted by breaker or health.
POLICY_KINDS = frozenset({ErrorKind.SENSITIVITY_REJECTED, ErrorKind.EGRESS_DENIED})


class LlmClientError(RuntimeError):
    """Base error of all client calls (legacy name: ``AiRouterError``)."""

    kind: ErrorKind = ErrorKind.INVALID_RESPONSE

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        endpoint: str | None = None,
        retry_after: float | None = None,
        cause_type: str | None = None,
        secrets: Iterable[str] = (),
    ) -> None:
        super().__init__(redact(message, secrets=secrets, max_len=ERROR_MESSAGE_LENGTH))
        self.status_code = status_code
        self.endpoint = endpoint
        self.retry_after = retry_after
        self.cause_type = cause_type

    @property
    def message(self) -> str:
        """The redacted message."""
        return str(self)

    def to_dict(self) -> dict[str, str | int | float | None]:
        """Serialisable form for APIs and health endpoints (already redacted)."""
        return {
            "kind": self.kind.value,
            "message": self.message,
            "status_code": self.status_code,
            "endpoint": self.endpoint,
            "retry_after": self.retry_after,
        }


class ConfigurationError(LlmClientError):
    """Missing or unsafe configuration (no URL, missing key, direct GPU host)."""

    kind = ErrorKind.CONFIGURATION


class RouterUnavailableError(LlmClientError):
    """Router/gateway not reachable (connection error)."""

    kind = ErrorKind.UNREACHABLE


class RouterTimeoutError(RouterUnavailableError):
    """The call exceeded its timeout."""

    kind = ErrorKind.TIMEOUT


class RouterHttpError(LlmClientError):
    """The router answered with an HTTP error status."""

    kind = ErrorKind.HTTP_STATUS


class InvalidResponseError(LlmClientError):
    """The response did not match the expected schema."""

    kind = ErrorKind.INVALID_RESPONSE


class CircuitOpenError(LlmClientError):
    """The circuit breaker is open; the call was not sent."""

    kind = ErrorKind.CIRCUIT_OPEN


class NotAssignedError(LlmClientError):
    """Flow-Agent readiness: the capability is not assigned to a healthy worker."""

    kind = ErrorKind.NOT_ASSIGNED


class SensitivityRejectedError(LlmClientError):
    """Flow-Agent HTTP 400: invalid ``X-Flow-Sensitivity`` value (policy, not an outage)."""

    kind = ErrorKind.SENSITIVITY_REJECTED


class EgressDeniedError(LlmClientError):
    """Flow-Agent HTTP 403: the effective sensitivity allows no available model.

    No upstream call was made; the gateway audits ``ai.egress-denied``. Not retried.
    """

    kind = ErrorKind.EGRESS_DENIED


class UnsupportedOperationError(LlmClientError):
    """The operation is not offered in the configured mode."""

    kind = ErrorKind.UNSUPPORTED


#: Migration alias for the name used in audit_designer, flowinvoice and audit-portal.
AiRouterError = LlmClientError
