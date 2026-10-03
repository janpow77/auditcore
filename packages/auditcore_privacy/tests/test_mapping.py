"""Tests für MappingStore, Hash-Speicherung und Export/Import."""

from __future__ import annotations

import pytest

from auditcore_privacy import (
    EntityType,
    MappingExport,
    MappingStore,
    ScopeError,
    compute_original_hash,
)


def test_cleartext_never_stored(store: MappingStore, sample_salt: str) -> None:
    """Klartext wird niemals im Zuordnungsobjekt abgelegt, nur der Einweg-Hash."""
    engine = store.get_or_create_scope("audit-project-100", salt=sample_salt)
    secret_name = "Vertraulicher Name GmbH"
    engine.get_or_create(EntityType.COMPANY, secret_name)

    mapping = engine.all_mappings[0]
    assert mapping.original_hash == compute_original_hash(
        sample_salt, EntityType.COMPANY.value, secret_name
    )
    assert secret_name not in mapping.original_hash
    # Mapping-Objekt besitzt kein 'original'-Attribut
    assert not hasattr(mapping, "original")


def test_store_scope_lifecycle(store: MappingStore, sample_salt: str) -> None:
    """Erstellung, Abruf und Fehlerbehandlung für Scopes."""
    # Scope anlegen
    engine = store.get_or_create_scope("scope-1", salt=sample_salt)
    assert engine.scope_key == "scope-1"

    # Selben Scope erneut abrufen
    same_engine = store.get_scope("scope-1")
    assert same_engine is engine

    # Unbekannter Scope wirft ScopeError
    with pytest.raises(ScopeError) as exc_info:
        store.get_scope("unbekannter-scope")
    assert exc_info.value.code == "SCOPE_NOT_FOUND"

    # Leerer Scope-Schlüssel wirft ScopeError
    with pytest.raises(ScopeError):
        store.get_or_create_scope("   ")


def test_export_and_import_roundtrip(store: MappingStore, sample_salt: str) -> None:
    """Export und Import stellen denselben Zustand und Zuordnungen wieder her."""
    engine = store.get_or_create_scope("roundtrip-scope", salt=sample_salt)
    p1 = engine.get_or_create(EntityType.PERSON, "Dr. Hans Meyer")
    c1 = engine.get_or_create(EntityType.COMPANY, "Alpha Bau GmbH")

    # Exportieren
    exported = store.export_scope("roundtrip-scope")
    assert isinstance(exported, MappingExport)
    assert exported.scope_key == "roundtrip-scope"
    assert exported.salt == sample_salt
    assert len(exported.mappings) == 2

    export_dict = exported.to_dict()
    assert export_dict["scope_key"] == "roundtrip-scope"
    assert len(export_dict["mappings"]) == 2

    # In neuen Store importieren
    new_store = MappingStore()
    imported_engine = new_store.import_scope(export_dict)

    # Identische Pseudonyme werden zurückgegeben ohne Neuzuordnungen
    assert imported_engine.get_or_create(EntityType.PERSON, "Dr. Hans Meyer") == p1
    assert imported_engine.get_or_create(EntityType.COMPANY, "Alpha Bau GmbH") == c1
    assert len(imported_engine.new_mappings) == 0
    assert len(imported_engine.all_mappings) == 2


def test_import_validation(store: MappingStore) -> None:
    """Fehlerhafte Importdaten werden abgelehnt."""
    with pytest.raises(ScopeError):
        store.import_scope({"scope_key": "", "salt": ""})


def test_get_or_create_scope_reuses_engine_and_salt(store: MappingStore, sample_salt: str) -> None:
    """Ein bestehender Scope wird wiederverwendet, ein später abweichender Salt ändert nichts."""
    engine = store.get_or_create_scope("scope-reuse", salt=sample_salt)
    pseudo = engine.get_or_create(EntityType.PERSON, "Petra Wagner")

    again = store.get_or_create_scope("scope-reuse", salt="anderer-salt")

    assert again is engine
    assert again.salt == sample_salt
    assert again.get_or_create(EntityType.PERSON, "Petra Wagner") == pseudo


def test_scope_without_salt_gets_random_salt(store: MappingStore) -> None:
    """Ohne vorgegebenen Salt erhalten getrennte Scopes je einen eigenen Zufalls-Salt."""
    engine_a = store.get_or_create_scope("scope-ohne-salt-a")
    engine_b = store.get_or_create_scope("scope-ohne-salt-b")

    assert len(engine_a.salt) == 32
    assert engine_a.salt != engine_b.salt


def test_import_from_mapping_export_object(store: MappingStore, sample_salt: str) -> None:
    """Ein MappingExport-Objekt lässt sich direkt und ohne Neuzuordnung importieren."""
    engine = store.get_or_create_scope("export-objekt", salt=sample_salt)
    person = engine.get_or_create(EntityType.PERSON, "Jürgen Becker")
    address = engine.get_or_create(EntityType.ADDRESS, "Lindenallee 7, Gießen")

    exported = store.export_scope("export-objekt")
    target = MappingStore()
    imported = target.import_scope(exported)

    assert target.get_scope("export-objekt") is imported
    assert imported.salt == sample_salt
    assert imported.get_or_create(EntityType.PERSON, "Jürgen Becker") == person
    assert imported.get_or_create(EntityType.ADDRESS, "Lindenallee 7, Gießen") == address
    assert imported.get_or_create(EntityType.ADDRESS, "Bahnhofstraße 2, Wetzlar") == (
        "[Anschrift 2]"
    )
    assert len(imported.new_mappings) == 1
