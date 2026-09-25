"""The fraud-check profile type shared by the three fraud mechanics."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .base import JsonObject
from .errors import InputError, ProfileError

SCHEMA = "auditcore_risk.fraud-profile/1"
FRAUD_KINDS = ("signal_score", "ted_contractor", "duplicates")


@dataclass(frozen=True)
class FraudProfile:
    """Immutable fraud-check profile (one mechanic, one source variant)."""

    id: str
    version: str
    kind: str
    status: str
    legal_status: str
    source: JsonObject
    parameters: JsonObject
    open_decisions: tuple[str, ...]
    fingerprint: str

    @property
    def reference(self) -> dict[str, str]:
        """Identity recorded with every result."""
        return {
            "id": self.id,
            "version": self.version,
            "fingerprint": self.fingerprint,
            "status": self.status,
        }


def require_parameters(profile: FraudProfile, kind: str) -> JsonObject:
    """Parameters of an explicitly loaded profile of ``kind`` (anything else is an error)."""
    if not isinstance(profile, FraudProfile) or profile.kind != kind:
        raise ProfileError(f"Ein ausdrücklich geladenes {kind}-Profil ist erforderlich.")
    return profile.parameters


def as_number(value: object, where: str) -> float:
    """Number of a sub-check result (``int``/``float``/``Decimal``, booleans excluded)."""
    if isinstance(value, bool) or not isinstance(value, int | float | Decimal):
        raise InputError(f"{where}: Zahl erwartet, erhalten {type(value).__name__}.")
    return float(value)
