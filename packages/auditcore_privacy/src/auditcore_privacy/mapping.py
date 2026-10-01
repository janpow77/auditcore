"""Verwaltung und Austausch von Scope-Zuordnungstabellen."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from .engine import PseudonymEngine, generate_salt
from .errors import ScopeError
from .models import MappingExport, PseudonymMapping


class MappingStore:
    """Verwaltet Zuordnungstabellen getrennt nach Scopes."""

    def __init__(self) -> None:
        self._engines: dict[str, PseudonymEngine] = {}

    def get_or_create_scope(self, scope_key: str, salt: str | None = None) -> PseudonymEngine:
        """Liefert oder erstellt die Pseudonymisierungs-Engine für einen Scope."""
        if not scope_key.strip():
            raise ScopeError("Scope-Schlüssel darf nicht leer sein.")
        if scope_key in self._engines:
            return self._engines[scope_key]
        effective_salt = salt or generate_salt()
        engine = PseudonymEngine(scope_key=scope_key, salt=effective_salt)
        self._engines[scope_key] = engine
        return engine

    def get_scope(self, scope_key: str) -> PseudonymEngine:
        """Gibt die Engine zu einem bekannten Scope zurück oder wirft ScopeError."""
        engine = self._engines.get(scope_key)
        if engine is None:
            raise ScopeError(f"Scope '{scope_key}' ist nicht registriert.", code="SCOPE_NOT_FOUND")
        return engine

    def export_scope(self, scope_key: str) -> MappingExport:
        """Exportiert alle Zuordnungen eines Scopes als übertragbares Bündel."""
        engine = self.get_scope(scope_key)
        return MappingExport(
            scope_key=engine.scope_key,
            salt=engine.salt,
            mappings=engine.all_mappings,
        )

    def import_scope(self, data: MappingExport | Mapping[str, object]) -> PseudonymEngine:
        """Importiert ein Zuordnungsbündel in den Speicher."""
        if isinstance(data, MappingExport):
            scope_key = data.scope_key
            salt = data.salt
            mappings = data.mappings
        else:
            scope_key = str(data.get("scope_key", ""))
            salt = str(data.get("salt", ""))
            raw_mappings = data.get("mappings")
            parsed_mappings: list[PseudonymMapping] = []
            if isinstance(raw_mappings, Sequence):
                for m in raw_mappings:
                    if isinstance(m, Mapping):
                        parsed_mappings.append(
                            PseudonymMapping(
                                scope_key=str(m.get("scope_key", scope_key)),
                                entity_type=str(m.get("entity_type", "")),
                                original_hash=str(m.get("original_hash", "")),
                                pseudonym=str(m.get("pseudonym", "")),
                                created_at=str(m.get("created_at", "")),
                            )
                        )
            mappings = tuple(parsed_mappings)

        if not scope_key or not salt:
            raise ScopeError("Importdaten unvollständig: scope_key und salt erforderlich.")

        engine = PseudonymEngine(
            scope_key=scope_key,
            salt=salt,
            existing_mappings=mappings,
        )
        self._engines[scope_key] = engine
        return engine
