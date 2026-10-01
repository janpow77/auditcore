"""Kollisionsfreie Pseudonymisierungs-Engine mit fester Scope-Bindung."""

from __future__ import annotations

import hashlib
import secrets
from collections.abc import Iterable
from datetime import UTC, datetime

from .errors import CollisionError
from .generators import (
    generate_company_pseudonym,
    generate_email_pseudonym,
    generate_iban_pseudonym,
    generate_person_pseudonym,
    generate_phone_pseudonym,
    generate_placeholder,
)
from .models import (
    DEFAULT_REPLACEMENT_KINDS,
    PLACEHOLDER_LABELS,
    EntityType,
    PseudonymMapping,
    ReplacementKind,
)


def generate_salt() -> str:
    """Erzeugt einen kryptografisch sicheren Zufalls-Salt für einen Scope."""
    return secrets.token_hex(16)


def compute_original_hash(salt: str, entity_type: str, original: str) -> str:
    """Berechnet den Einweg-Hash für die Zuordnungstabelle ohne Klartextablage."""
    raw = f"{salt}|{entity_type}|{original.strip()}".encode()
    return hashlib.blake2b(raw, digest_size=24).hexdigest()


class PseudonymEngine:
    """Verwaltet deterministische und kollisionsfreie Pseudonyme für einen Scope."""

    def __init__(
        self,
        scope_key: str,
        salt: str,
        existing_mappings: Iterable[PseudonymMapping] = (),
    ) -> None:
        self.scope_key = scope_key
        self.salt = salt
        self._mappings: dict[tuple[str, str], PseudonymMapping] = {}
        self._allocated: dict[str, set[str]] = {}
        self._counters: dict[str, int] = {}
        self._new_mappings: list[PseudonymMapping] = []

        for m in existing_mappings:
            key = (m.entity_type, m.original_hash)
            self._mappings[key] = m
            self._allocated.setdefault(m.entity_type, set()).add(m.pseudonym)
            if self._is_placeholder(m.entity_type):
                self._counters[m.entity_type] = self._counters.get(m.entity_type, 0) + 1

    @property
    def new_mappings(self) -> tuple[PseudonymMapping, ...]:
        """In dieser Sitzung neu erzeugte Zuordnungseinträge."""
        return tuple(self._new_mappings)

    @property
    def all_mappings(self) -> tuple[PseudonymMapping, ...]:
        """Alle vorhandenen Zuordnungseinträge des Scopes."""
        return tuple(self._mappings.values())

    def get_or_create(self, entity_type: EntityType | str, original: str) -> str:
        """Gibt ein eindeutiges Pseudonym zurück — beim zweiten Aufruf stets dasselbe."""
        etype_str = str(entity_type)
        cleaned = original.strip()
        h = compute_original_hash(self.salt, etype_str, cleaned)
        key = (etype_str, h)

        existing = self._mappings.get(key)
        if existing is not None:
            return existing.pseudonym

        pseudonym = self._generate_unique(etype_str, cleaned)
        mapping = PseudonymMapping(
            scope_key=self.scope_key,
            entity_type=etype_str,
            original_hash=h,
            pseudonym=pseudonym,
            created_at=datetime.now(UTC).isoformat(),
        )
        self._mappings[key] = mapping
        self._allocated.setdefault(etype_str, set()).add(pseudonym)
        self._new_mappings.append(mapping)
        return pseudonym

    def _is_placeholder(self, entity_type: str) -> bool:
        try:
            etype_enum = EntityType(entity_type)
            return DEFAULT_REPLACEMENT_KINDS.get(etype_enum) == ReplacementKind.PLACEHOLDER
        except ValueError:
            return True

    def _generate_unique(self, entity_type: str, original: str) -> str:
        if self._is_placeholder(entity_type):
            return self._create_placeholder(entity_type)
        return self._create_named_replacement(entity_type, original)

    def _create_placeholder(self, entity_type: str) -> str:
        self._counters[entity_type] = self._counters.get(entity_type, 0) + 1
        label = "Angabe"
        try:
            etype_enum = EntityType(entity_type)
            label = PLACEHOLDER_LABELS.get(etype_enum, "Angabe")
        except ValueError:
            pass
        return generate_placeholder(label, self._counters[entity_type])

    def _create_named_replacement(self, entity_type: str, original: str) -> str:
        allocated = self._allocated.setdefault(entity_type, set())
        for attempt in range(64):
            candidate = self._call_generator(entity_type, original, attempt)
            if candidate not in allocated:
                return candidate
        return self._create_numbered_fallback(entity_type, original, allocated)

    def _call_generator(self, entity_type: str, original: str, attempt: int) -> str:
        if entity_type == EntityType.PERSON.value:
            return generate_person_pseudonym(self.salt, original, attempt)
        if entity_type == EntityType.COMPANY.value:
            return generate_company_pseudonym(self.salt, original, attempt)
        if entity_type == EntityType.IBAN.value:
            return generate_iban_pseudonym(self.salt, original, attempt)
        if entity_type == EntityType.EMAIL.value:
            return generate_email_pseudonym(self.salt, original, attempt)
        if entity_type == EntityType.PHONE.value:
            return generate_phone_pseudonym(self.salt, original, attempt)
        raise CollisionError(f"Kein Generator für Entity-Typ '{entity_type}' definiert.")

    def _create_numbered_fallback(
        self, entity_type: str, original: str, allocated: set[str]
    ) -> str:
        base = self._call_generator(entity_type, original, 0)
        number = 2
        while f"{base} ({number})" in allocated:
            number += 1
        return f"{base} ({number})"
