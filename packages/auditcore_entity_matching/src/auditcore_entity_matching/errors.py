"""Error contract of the entity matching library."""

from __future__ import annotations


class EntityMatchingError(Exception):
    """Base class; ``code`` is stable and machine readable."""

    code = "entity_matching_error"


class ProfileError(EntityMatchingError):
    """A profile is missing, malformed or of the wrong kind."""

    code = "profile_error"


class DependencyError(EntityMatchingError, ImportError):
    """The optional fuzzy extra (``auditcore_entity_matching[fuzzy]``) is not installed."""

    code = "missing_optional_dependency"
