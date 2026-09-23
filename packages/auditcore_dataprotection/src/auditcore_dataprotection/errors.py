"""Error contract. Consumers map ``code`` to their own HTTP or UI responses."""

from __future__ import annotations


class DataProtectionError(Exception):
    """Base class; ``code`` is stable and machine readable."""

    code = "dataprotection_error"


class ProfileError(DataProtectionError):
    """A rule profile is missing, malformed or does not contain a key."""

    code = "profile_error"


class ValidationError(DataProtectionError):
    """Input does not satisfy the contract (maps to 400/422)."""

    code = "validation_error"


class NotFoundError(DataProtectionError):
    """The entity does not exist within the given tenant (maps to 404)."""

    code = "not_found"


class ConflictError(DataProtectionError):
    """The requested transition is not allowed in the current state (409)."""

    code = "conflict"


class LockedVersionError(ConflictError):
    """A released version is immutable; a new version must be created."""

    code = "version_locked"


class StaleRevisionError(ConflictError):
    """Optimistic concurrency check failed; reload and retry."""

    code = "stale_revision"


class FourEyesViolation(DataProtectionError):
    """The releasing person also edited the version or gave the DPO statement (403)."""

    code = "vier_augen_verletzt"


class AuthorizationError(DataProtectionError):
    """The authorizer port denied the operation (403)."""

    code = "forbidden"


class TenantMismatchError(DataProtectionError):
    """An object of another tenant was presented; treated like not found by consumers."""

    code = "tenant_mismatch"
