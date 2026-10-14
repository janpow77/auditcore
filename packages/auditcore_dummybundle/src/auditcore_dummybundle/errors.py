"""Errors of the bundle generator."""

from __future__ import annotations


class BundleError(ValueError):
    """Configuration, recipe or template does not satisfy the generator contract.

    ``code`` is a stable machine-readable reason, ``path`` names the offending
    entry (for example ``fields[3].params.min``); the message is German.
    """

    def __init__(self, message: str, *, code: str = "invalid_input", path: str = "") -> None:
        super().__init__(message)
        self.code = code
        self.path = path


class BudgetExceededError(BundleError):
    """The cooperative time budget of a run is used up."""

    def __init__(self) -> None:
        super().__init__("Die Zeitgrenze der Erzeugung ist überschritten.", code="timeout")
