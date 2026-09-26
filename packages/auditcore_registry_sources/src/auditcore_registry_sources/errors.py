"""Structured errors of the registry sources; transport errors come from ``auditcore_harvest``."""

from __future__ import annotations


class RegistrySourcesError(Exception):
    """Base error with a stable machine-readable ``code``."""

    code = "registry_sources_error"


class FormatError(RegistrySourcesError, ValueError):
    """A delivery cannot be interpreted; never presented as an empty list."""

    code = "format_error"


class ProfileError(RegistrySourcesError):
    """A profile is missing, incomplete or of the wrong kind."""

    code = "profile_error"


class QueryError(RegistrySourcesError, ValueError):
    """An input violates the rules of the chosen profile (for example a too short name)."""

    code = "query_error"


class DependencyError(RegistrySourcesError, ImportError):
    """An optional extra (``fuzzy``, ``xml``, ``html``) is not installed."""

    code = "dependency_error"
