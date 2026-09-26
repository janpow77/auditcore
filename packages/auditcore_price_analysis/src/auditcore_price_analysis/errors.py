"""Structured errors of the price analysis contract."""

from __future__ import annotations

from typing import Any


class PriceAnalysisError(ValueError):
    """Invalid input, profile or tariff; ``code`` is stable and machine-readable.

    Subclasses ``ValueError`` so that callers which already guard the legacy
    calculator with ``except ValueError`` keep working.
    """

    def __init__(self, code: str, message: str, *, field: str | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.field = field

    def to_dict(self) -> dict[str, Any]:
        """JSON view."""
        return {"code": self.code, "field": self.field, "message": str(self)}


class ProfileError(PriceAnalysisError):
    """A profile is unknown, malformed or does not fit the tariff."""

    def __init__(self, message: str, *, field: str | None = None) -> None:
        super().__init__("profile_error", message, field=field)
