"""Error contract; ``code`` is stable and distinguishes the error classes of the adapter guide."""

from __future__ import annotations


class LegalSourceError(Exception):
    """Base class of all errors raised by this package."""

    code = "legal_source_error"


class ProfileError(LegalSourceError):
    """A source profile is missing, malformed or does not match its fingerprint."""

    code = "profile_error"


class ConfigurationError(LegalSourceError):
    """Configuration or credentials are missing or invalid (maps to NOT_CONFIGURED)."""

    code = "configuration_error"


class ParseError(LegalSourceError):
    """A source response does not have the documented structure; never an empty success."""

    code = "parse_error"

    def __init__(self, message: str, *, source_id: str = "", location: str = "") -> None:
        super().__init__(message)
        self.source_id = source_id
        self.location = location
