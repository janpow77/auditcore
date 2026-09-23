"""Error contract of the risk library; ``code`` is stable and machine readable."""

from __future__ import annotations


class RiskError(Exception):
    """Base class of all library errors."""

    code = "risk_error"


class ProfileError(RiskError):
    """A rule profile is missing, malformed or not explicitly selected."""

    code = "profile_error"


class InputError(RiskError, ValueError):
    """Records violate the column/value contract of the selected profile."""

    code = "input_error"


class DependencyError(RiskError, ImportError):
    """An optional extra needed by the selected profile is not installed."""

    code = "missing_optional_dependency"
