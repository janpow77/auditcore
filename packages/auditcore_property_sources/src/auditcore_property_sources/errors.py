"""Error contract of the property source library."""

from __future__ import annotations


class PropertySourceError(Exception):
    """Base class; ``code`` is stable and machine readable."""

    code = "property_source_error"


class AccessNotPermitted(PropertySourceError):
    """robots.txt of the portal disallows the requested path (never retried)."""

    code = "access_not_permitted"


class DependencyError(PropertySourceError, ImportError):
    """The optional harvest extra (``auditcore_property_sources[sources]``) is missing."""

    code = "missing_optional_dependency"
