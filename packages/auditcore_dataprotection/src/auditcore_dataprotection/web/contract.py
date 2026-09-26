"""REST contract ``dataprotection_ui/1``: principal, error answer and body checks.

Every error answer has the form ``{"error": {"code": …, "message": …}}`` with a
stable code and a German message; library errors keep their own ``code``.
Contract: ``docs/ui/dataprotection-rest.md`` in the auditcore repository.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from ..errors import (
    AuthorizationError,
    ConflictError,
    DataProtectionError,
    FourEyesViolation,
    NotFoundError,
    ProfileError,
    TenantMismatchError,
    ValidationError,
)
from ..model import Actor

CONTRACT = "dataprotection_ui/1"

#: JSON object of a request or answer.
JsonObject = dict[str, object]

_STATUS: tuple[tuple[type[DataProtectionError], int], ...] = (
    (FourEyesViolation, 403),
    (AuthorizationError, 403),
    (TenantMismatchError, 404),
    (NotFoundError, 404),
    (ConflictError, 409),
    (ValidationError, 422),
    (ProfileError, 422),
)


class ApiError(Exception):
    """Error answer: HTTP ``status``, machine-readable ``code``, German ``message``."""

    def __init__(self, status: int, code: str, message: str) -> None:
        self.status, self.code, self.message = status, code, message
        super().__init__(message)

    def to_dict(self) -> JsonObject:
        """Response body ``{"error": {"code": …, "message": …}}``."""
        return {"error": {"code": self.code, "message": self.message}}


def library_error(exc: DataProtectionError) -> ApiError:
    """HTTP answer of a library error (403, 404, 409, 422; otherwise 400)."""
    for kind, status in _STATUS:
        if isinstance(exc, kind):
            return ApiError(status, exc.code, str(exc))
    return ApiError(400, exc.code, str(exc))


@dataclass(frozen=True)
class Principal:
    """Tenant and person of a request, established by the consumer (``identify``)."""

    tenant_id: str
    actor: Actor


def invalid(message: str) -> ApiError:
    """400 answer for a malformed request."""
    return ApiError(400, "invalid_request", message)


def body_object(body: object, allowed: frozenset[str]) -> Mapping[str, object]:
    """The request body as an object without unknown fields."""
    if body is None:
        return {}
    if not isinstance(body, Mapping) or not all(isinstance(k, str) for k in body):
        raise invalid("Der Anfragekörper muss ein JSON-Objekt sein.")
    unknown = sorted(set(body) - allowed)
    if unknown:
        raise invalid(f"Unbekannte Felder: {', '.join(unknown)}.")
    return body


def revision(body: Mapping[str, object], *, required: bool = True) -> int | None:
    """``expected_revision`` as a positive integer (optional for a first draft)."""
    value = body.get("expected_revision")
    if value is None and not required:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise invalid("'expected_revision' muss die gelesene Revision (ganze Zahl ≥ 1) sein.")
    return value


def text(body: Mapping[str, object], key: str, *, required: bool = True) -> str:
    """A text field; required fields must not be blank."""
    value = body.get(key, "")
    if value is None:
        value = ""
    if not isinstance(value, str):
        raise invalid(f"'{key}' muss Text sein.")
    if required and not value.strip():
        raise invalid(f"'{key}' fehlt.")
    return value


def text_list(body: Mapping[str, object], key: str) -> tuple[str, ...]:
    """A list of texts (for example the conditions of a decision)."""
    value = body.get(key, [])
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        raise invalid(f"'{key}' muss eine Liste von Texten sein.")
    return tuple(value)
