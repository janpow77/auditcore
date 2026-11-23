"""Result objects: every check returns a :class:`CheckResult`, never raises for bad input."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from types import MappingProxyType

#: Scalar values allowed in :attr:`CheckResult.details` (JSON-compatible).
DetailValue = str | int | bool | None


class IdentifierKind(StrEnum):
    """Kinds of identifiers the library checks."""

    IBAN = "iban"
    BIC = "bic"
    VAT_ID = "vat_id"
    TAX_ID = "tax_id"
    TAX_NUMBER = "tax_number"
    LEI = "lei"
    REGISTER_NUMBER = "register_number"


class Status(StrEnum):
    """Outcome of a check (same three values as the flowinvoice ``ValidationStatus``)."""

    VALID = "VALID"
    INVALID = "INVALID"
    MISSING = "MISSING"


class Reason(StrEnum):
    """Why a value is not valid; ``None`` on :attr:`Status.VALID`."""

    MISSING = "missing"
    INVALID_TYPE = "invalid_type"
    INVALID_CHARACTERS = "invalid_characters"
    INVALID_LENGTH = "invalid_length"
    INVALID_FORMAT = "invalid_format"
    UNKNOWN_COUNTRY = "unknown_country"
    COUNTRY_MISMATCH = "country_mismatch"
    INVALID_CHECKSUM = "invalid_checksum"


class CheckDigit(StrEnum):
    """What the check of the check digit established (:attr:`CheckResult.check_digit`)."""

    #: The check digit was computed and matches.
    VERIFIED = "verified"
    #: The check digit was computed and does not match (result INVALID).
    FAILED = "failed"
    #: The identifier (variant) carries a check digit, but the library cannot verify it.
    NOT_CHECKED = "not_checked"
    #: The identifier (variant) has no check digit (e.g. BIC, Handelsregisternummer).
    NONE = "none"


class Verdict(StrEnum):
    """Overall verdict: ``valid`` only if the format holds *and* the check digit is verified."""

    VALID = "valid"
    #: Format valid, but no check digit exists or it could not be verified.
    FORMAT_VALID = "format_valid"
    INVALID = "invalid"
    MISSING = "missing"


_EMPTY: Mapping[str, DetailValue] = MappingProxyType({})


@dataclass(frozen=True)
class CheckResult:
    """Outcome of one identifier check.

    ``normalized`` is the canonical electronic form (for legacy profiles: the value
    the original function returned on success). ``message`` is German for the
    ``strict`` profile and the original wording for legacy profiles.
    """

    kind: IdentifierKind
    status: Status
    raw: object
    normalized: str | None = None
    reason: Reason | None = None
    message: str = ""
    country: str | None = None
    profile: str = "strict"
    details: Mapping[str, DetailValue] = field(default_factory=lambda: _EMPTY)
    #: Check digit status; ``None`` if the check did not get that far (or a legacy
    #: profile does not report it).
    check_digit: CheckDigit | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "details", MappingProxyType(dict(self.details)))

    @property
    def valid(self) -> bool:
        """True only for :attr:`Status.VALID`."""
        return self.status is Status.VALID

    def __bool__(self) -> bool:
        return self.valid

    @property
    def verdict(self) -> Verdict:
        """``valid`` only with a verified check digit; otherwise ``format_valid``."""
        if self.status is Status.MISSING:
            return Verdict.MISSING
        if self.status is Status.INVALID:
            return Verdict.INVALID
        if self.check_digit is CheckDigit.VERIFIED:
            return Verdict.VALID
        return Verdict.FORMAT_VALID

    def to_dict(self) -> dict[str, DetailValue | dict[str, DetailValue]]:
        """JSON-compatible representation (``raw`` as ``str`` or ``None``)."""
        return {
            "kind": self.kind.value,
            "status": self.status.value,
            "raw": None if self.raw is None else str(self.raw),
            "normalized": self.normalized,
            "reason": None if self.reason is None else self.reason.value,
            "message": self.message,
            "country": self.country,
            "profile": self.profile,
            "details": dict(self.details),
            "check_digit": None if self.check_digit is None else self.check_digit.value,
            "verdict": self.verdict.value,
        }


def valid(
    kind: IdentifierKind,
    raw: object,
    normalized: str,
    *,
    country: str | None = None,
    profile: str = "strict",
    message: str = "",
    details: Mapping[str, DetailValue] | None = None,
    check_digit: CheckDigit | None = None,
) -> CheckResult:
    """Build a VALID result."""
    return CheckResult(
        kind,
        Status.VALID,
        raw,
        normalized,
        None,
        message,
        country,
        profile,
        details or _EMPTY,
        check_digit,
    )


def invalid(
    kind: IdentifierKind,
    raw: object,
    reason: Reason,
    message: str,
    *,
    country: str | None = None,
    profile: str = "strict",
    details: Mapping[str, DetailValue] | None = None,
) -> CheckResult:
    """Build an INVALID (or MISSING, if ``reason`` is MISSING) result.

    A wrong check digit (``INVALID_CHECKSUM``) sets :attr:`CheckResult.check_digit`
    to ``failed``; other reasons leave it ``None`` (check not reached).
    """
    status = Status.MISSING if reason is Reason.MISSING else Status.INVALID
    check_digit = CheckDigit.FAILED if reason is Reason.INVALID_CHECKSUM else None
    return CheckResult(
        kind, status, raw, None, reason, message, country, profile, details or _EMPTY, check_digit
    )
