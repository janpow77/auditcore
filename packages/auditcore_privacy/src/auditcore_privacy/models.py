"""Datenmodelle und Aufzählungen für Pseudonymisierung und Maskierung."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum

from .errors import JsonObject


class ReplacementKind(StrEnum):
    """Art der Ersetzung für sensible Angaben."""

    PSEUDONYM = "pseudonym"
    FORMAT_PRESERVING = "formattreu"
    PLACEHOLDER = "platzhalter"


class EntityType(StrEnum):
    """Kategorie sensibler personenbezogener oder geschäftlicher Daten."""

    PERSON = "person_name"
    COMPANY = "company_name"
    ADDRESS = "address"
    IBAN = "iban"
    ACCOUNT = "account"
    EMAIL = "email"
    PHONE = "phone"
    FILE_NUMBER = "file_number"
    TAX_NUMBER = "tax_number"
    VAT_NUMBER = "vat_number"


DEFAULT_REPLACEMENT_KINDS: Mapping[EntityType, ReplacementKind] = {
    EntityType.PERSON: ReplacementKind.PSEUDONYM,
    EntityType.COMPANY: ReplacementKind.PSEUDONYM,
    EntityType.IBAN: ReplacementKind.FORMAT_PRESERVING,
    EntityType.EMAIL: ReplacementKind.FORMAT_PRESERVING,
    EntityType.PHONE: ReplacementKind.FORMAT_PRESERVING,
    EntityType.ADDRESS: ReplacementKind.PLACEHOLDER,
    EntityType.ACCOUNT: ReplacementKind.PLACEHOLDER,
    EntityType.FILE_NUMBER: ReplacementKind.PLACEHOLDER,
    EntityType.TAX_NUMBER: ReplacementKind.PLACEHOLDER,
    EntityType.VAT_NUMBER: ReplacementKind.PLACEHOLDER,
}

PLACEHOLDER_LABELS: Mapping[EntityType, str] = {
    EntityType.ADDRESS: "Anschrift",
    EntityType.ACCOUNT: "Konto",
    EntityType.FILE_NUMBER: "Aktenzeichen",
    EntityType.TAX_NUMBER: "Steuernummer",
    EntityType.VAT_NUMBER: "USt-IdNr",
}


@dataclass(frozen=True)
class PseudonymMapping:
    """Eintrag in der geschützten Zuordnungstabelle eines Scopes."""

    scope_key: str
    entity_type: str
    original_hash: str
    pseudonym: str
    created_at: str

    def to_dict(self) -> JsonObject:
        """Serialisiert den Zuordnungseintrag."""
        return {
            "scope_key": self.scope_key,
            "entity_type": self.entity_type,
            "original_hash": self.original_hash,
            "pseudonym": self.pseudonym,
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class MappingExport:
    """Exportfähiges Bündel aller Pseudonymzuordnungen eines Scopes."""

    scope_key: str
    salt: str
    mappings: tuple[PseudonymMapping, ...]

    def to_dict(self) -> JsonObject:
        """Serialisiert das Exportbündel."""
        return {
            "scope_key": self.scope_key,
            "salt": self.salt,
            "mappings": [m.to_dict() for m in self.mappings],
        }
