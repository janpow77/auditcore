"""Tests für die PseudonymEngine und Scope-Bindung."""

from __future__ import annotations

from auditcore_privacy import EntityType, PseudonymEngine


def test_deterministic_repetition(engine: PseudonymEngine) -> None:
    """Wiederholte Aufrufe für denselben Klartext liefern stets dasselbe Pseudonym."""
    name = "Dr. Susanne Fischer"
    first = engine.get_or_create(EntityType.PERSON, name)
    second = engine.get_or_create(EntityType.PERSON, name)
    third = engine.get_or_create("person_name", name)

    assert first == second
    assert first == third
    assert len(engine.all_mappings) == 1
    assert len(engine.new_mappings) == 1


def test_scope_separation(sample_salt: str, alternate_salt: str) -> None:
    """Unterschiedliche Scopes liefern für denselben Klartext unterschiedliche Pseudonyme."""
    engine_a = PseudonymEngine(scope_key="scope-alpha", salt=sample_salt)
    engine_b = PseudonymEngine(scope_key="scope-beta", salt=alternate_salt)

    name = "Klaus Peter Hoffmann"
    pseudo_a = engine_a.get_or_create(EntityType.PERSON, name)
    pseudo_b = engine_b.get_or_create(EntityType.PERSON, name)

    assert pseudo_a != pseudo_b


def test_collision_free_generation(engine: PseudonymEngine) -> None:
    """100 unterschiedliche Personen erhalten 100 paarweise verschiedene Pseudonyme."""
    generated: set[str] = set()
    for i in range(100):
        name = f"Mitarbeiter {i} Testperson"
        pseudo = engine.get_or_create(EntityType.PERSON, name)
        assert pseudo not in generated
        generated.add(pseudo)

    assert len(generated) == 100
    assert len(engine.all_mappings) == 100


def test_collision_fallback_numbering(sample_salt: str) -> None:
    """Nach Ausschöpfen von Kandidaten greift die nummerierte Kollisionsauflösung."""
    engine = PseudonymEngine(scope_key="test-numbered", salt=sample_salt)
    # Erzeuge viele Personen, so dass die Kandidaten erschöpft werden
    # Da FirstNames (30) * LastNames (40) = 1200 Kombinationen existieren,
    # prüfen wir direkt die Fallback-Methode oder provozieren Kollisionen.
    allocated: set[str] = set()
    base_candidate = engine._call_generator(EntityType.PERSON.value, "Testperson", 0)
    allocated.add(base_candidate)
    fallback = engine._create_numbered_fallback(EntityType.PERSON.value, "Testperson", allocated)
    assert fallback == f"{base_candidate} (2)"

    allocated.add(f"{base_candidate} (2)")
    fallback_3 = engine._create_numbered_fallback(EntityType.PERSON.value, "Testperson", allocated)
    assert fallback_3 == f"{base_candidate} (3)"


def test_placeholder_generation_and_repetition(engine: PseudonymEngine) -> None:
    """Platzhalter werden nummeriert und wiederholen sich für identische Klartexte."""
    addr1 = "Musterstraße 12, 10115 Berlin"
    addr2 = "Hauptstraße 45, 80331 München"

    p1_first = engine.get_or_create(EntityType.ADDRESS, addr1)
    p2 = engine.get_or_create(EntityType.ADDRESS, addr2)
    p1_second = engine.get_or_create(EntityType.ADDRESS, addr1)

    assert p1_first == "[Anschrift 1]"
    assert p2 == "[Anschrift 2]"
    assert p1_first == p1_second

    tax1 = engine.get_or_create(EntityType.TAX_NUMBER, "12/345/67890")
    assert tax1 == "[Steuernummer 1]"


def test_mappings_tracking(sample_salt: str) -> None:
    """Verfolgung von Bestands- und Neuzuordnungen."""
    first_engine = PseudonymEngine(scope_key="tracking-test", salt=sample_salt)
    first_engine.get_or_create(EntityType.PERSON, "Hans Schmidt")

    stored_mappings = first_engine.all_mappings
    assert len(stored_mappings) == 1

    second_engine = PseudonymEngine(
        scope_key="tracking-test",
        salt=sample_salt,
        existing_mappings=stored_mappings,
    )
    assert len(second_engine.all_mappings) == 1
    assert len(second_engine.new_mappings) == 0

    # Neuer Eintrag
    second_engine.get_or_create(EntityType.PERSON, "Anna Meier")
    assert len(second_engine.all_mappings) == 2
    assert len(second_engine.new_mappings) == 1
