"""Error contract of the package."""

from __future__ import annotations


class FundingSourceError(Exception):
    """Base class; ``code`` is stable and machine readable."""

    code = "funding_source_error"


class ProfileError(FundingSourceError):
    """A packaged profile is missing or malformed."""

    code = "profile_error"


class SourceFormatError(FundingSourceError, ValueError):
    """The source file cannot be read as a table of the declared format."""

    code = "source_format_error"


class SnapshotRejected(FundingSourceError, ValueError):
    """Validation found hard errors; the previous inventory must stay untouched."""

    code = "snapshot_rejected"

    def __init__(self, errors: list[str]) -> None:
        self.errors = list(errors)
        preview = " ".join(self.errors[:8])
        suffix = " …" if len(self.errors) > 8 else ""
        super().__init__(f"Snapshot abgewiesen: {preview}{suffix}")


class OptionalDependencyError(FundingSourceError, ImportError):
    """An optional extra such as ``[xlsx]`` is required for this operation."""

    code = "optional_dependency_missing"
