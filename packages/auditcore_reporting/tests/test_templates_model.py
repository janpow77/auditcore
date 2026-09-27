"""Template definition: data contract, conditions, placeholders, text blocks, registry."""

from __future__ import annotations

import copy
from typing import Any

import pytest

from auditcore_reporting.templates import (
    DesignProfile,
    TemplateDataError,
    TemplateError,
    TemplateNotFoundError,
    TemplateRegistry,
    builtin_registry,
    define_template,
    design_from_dict,
    resolve,
)
from auditcore_reporting.templates.conditions import evaluate
from auditcore_reporting.templates.resolve import RParagraph, RTable
from auditcore_reporting.templates.schema import validate
from auditcore_reporting.templates.values import format_value

SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["name"],
    "properties": {
        "name": {"type": "string", "minLength": 1},
        "betrag": {"type": "number", "minimum": 0},
        "datum": {"type": "string", "format": "date"},
        "art": {"type": "string", "enum": ["formell", "finanziell"]},
        "posten": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"text": {"type": "string"}, "wert": {"type": "number"}},
            },
        },
    },
}


def definition(**change: object) -> dict[str, Any]:
    base: dict[str, Any] = {
        "id": "test",
        "version": "1.0.0",
        "title": "Test {{ name }}",
        "schema": copy.deepcopy(SCHEMA),
        "conditions": {"mit_posten": {"filled": "posten"}},
        "text_blocks": [
            {"id": "hinweis", "text": "Betrag {{ betrag | eur }}", "if": {"greater": ["betrag", 0]}},
            {"id": "pflicht", "text": "Pflichttext.", "required": True, "legal_basis": "Art. 1"},
        ],
        "blocks": [
            {"type": "paragraph", "text": "Hallo {{ name }}"},
            {"type": "textblock", "id": "hinweis"},
            {"type": "textblock", "id": "pflicht"},
            {"type": "table", "source": "posten", "as": "p", "empty": "Keine Posten.",
             "columns": [{"header": "Text", "cell": "{{ p.text }}"},
                         {"header": "Wert", "cell": "{{ p.wert | zahl }}", "align": "right"}]},
            {"type": "section", "for": "posten", "as": "p", "if": {"greater": ["p.wert", 1]},
             "title": "Posten {{ p.text }}", "blocks": [{"type": "paragraph", "text": "groß"}]},
        ],
        "sample": {"name": "Muster"},
    }  # fmt: skip
    base.update(change)
    return base


def test_valid_definition_is_fingerprinted_and_frozen() -> None:
    template = define_template(definition())
    assert template.formats == ("docx", "pdf", "html")
    assert template.name == "Test" and template.title == "Test {{ name }}"
    assert define_template(definition(name="Prüfung")).name == "Prüfung"
    assert len(template.fingerprint) == 64
    assert define_template(definition()).fingerprint == template.fingerprint
    assert define_template(definition(description="x")).fingerprint != template.fingerprint
    with pytest.raises(TypeError):
        template.schema["type"] = "array"  # type: ignore[index]


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"id": "Test"}, "id"),
        ({"version": "1.0"}, "MAJOR.MINOR.PATCH"),
        ({"status": "aktiv"}, "status"),
        ({"extra": 1}, "unbekannte Felder"),
        ({"schema": {"type": "object", "pattern": "x"}}, "nicht unterstützte"),
        ({"schema": {"type": "text"}}, "unbekannter Typ"),
        ({"blocks": [{"type": "paragraph", "text": "{{ unbekannt }}"}]}, "nicht deklariert"),
        ({"blocks": [{"type": "paragraph", "text": "{{ name | geheim }}"}]}, "unbekannter Filter"),
        ({"blocks": [{"type": "paragraph", "text": "{{ name "}]}, "nicht geschlossen"),
        ({"blocks": [{"type": "paragraph", "text": "{% if name %}"}]}, "DOCX-Vorlagen"),
        ({"blocks": [{"type": "paragraph", "text": "{{ name.__class__ }}"}]}, "nicht deklariert"),
        ({"blocks": [{"type": "paragraph", "text": "{{ open('x') }}"}]}, "Datenpfad"),
        ({"blocks": [{"type": "list", "source": "name", "item": "x"}]}, "keine Liste"),
        ({"blocks": [{"type": "textblock", "id": "fehlt"}]}, "unbekannter Textbaustein"),
        ({"blocks": [{"type": "paragraph", "text": "x"}]}, "Pflichtbaustein"),
        ({"blocks": [{"type": "bild"}]}, "erlaubt sind"),
        ({"conditions": {"a": "b", "b": "a"}}, "zyklisch"),
        ({"conditions": {"a": {"between": ["betrag", 1]}}}, "unbekannter Operator"),
        ({"conditions": {"a": {"greater": ["betrag", "1"]}}}, "nur mit Zahlen"),
        ({"text_blocks": [{"id": "x", "text": "{{ textbaustein.x }}"}]}, "keine Textbausteine"),
        ({"sample": {"name": ""}}, "sample"),
        ({"formats": ["odt"]}, "formats"),
        ({"title": "Test {{ fehlt }}"}, "nicht deklariert"),
        ({"name": "Test {{ name }}"}, "ohne Platzhalter"),
    ],
)
def test_invalid_definitions_are_rejected(change: dict[str, object], message: str) -> None:
    with pytest.raises(TemplateError, match=message):
        define_template(definition(**change))


def test_data_contract_reports_every_issue_with_path() -> None:
    template = define_template(definition())
    data = {"betrag": -1, "datum": "31.01.2026", "art": "x", "posten": [{"wert": "1"}], "zu": 1}
    with pytest.raises(TemplateDataError) as caught:
        resolve(template, data)
    paths = {issue.path: issue.message for issue in caught.value.issues}
    assert paths == {
        "$.name": "Pflichtangabe fehlt",
        "$.betrag": "muss mindestens 0 sein",
        "$.datum": "muss ein ISO-Datum (JJJJ-MM-TT) sein",
        "$.art": "muss einer der Werte ['formell', 'finanziell'] sein",
        "$.posten[0].wert": "Typ number erwartet",
        "$.zu": "ist im Datenvertrag nicht vorgesehen",
    }
    assert validate([], SCHEMA)[0].message == "Typ object erwartet"


def test_resolution_applies_conditions_loops_and_text_blocks() -> None:
    template = define_template(definition())
    empty = resolve(template, {"name": "Ä"})
    assert empty.title == "Test Ä"
    assert [n.text for n in empty.nodes if isinstance(n, RParagraph)] == [
        "Hallo Ä",
        "Pflichttext.",
        "Keine Posten.",
    ]
    assert empty.text_blocks == ("pflicht",)
    full = resolve(
        template,
        {
            "name": "B",
            "betrag": 1234.5,
            "posten": [{"text": "a", "wert": 1}, {"text": "b", "wert": 2.5}],
        },
    )
    assert full.text_blocks == ("hinweis", "pflicht")
    table = next(n for n in full.nodes if isinstance(n, RTable))
    assert table.rows == (("a", "1"), ("b", "2,50")) and table.aligns == ("left", "right")
    assert "Betrag 1.234,50 €" in [getattr(n, "text", "") for n in full.nodes]
    assert [getattr(n, "text", "") for n in full.nodes][-2:] == ["Posten b", "groß"]


@pytest.mark.parametrize(
    ("value", "filter_name", "expected"),
    [
        (1234567.891, "eur", "1.234.567,89 €"),
        (0.125, "prozent", "12,50 %"),
        (1234, None, "1.234"),
        (2.5, "zahl", "2,50"),
        (2.4999, "ganzzahl", "2"),
        (True, None, "ja"),
        (False, "ja_nein", "nein"),
        ("2026-01-31", "datum", "31.01.2026"),
        ("2026-01-31T10:00:00", "datum", "31.01.2026"),
        (None, "eur", ""),
        ("<b>&", None, "<b>&"),
    ],
)
def test_german_formatting(value: object, filter_name: str | None, expected: str) -> None:
    assert format_value(value, filter_name, "t") == expected


@pytest.mark.parametrize(
    ("value", "filter_name"), [("x", "eur"), ([1], None), ("31.01.", "datum"), ("a\x00", None)]
)
def test_formatting_rejects_wrong_types(value: object, filter_name: str | None) -> None:
    with pytest.raises(TemplateError):
        format_value(value, filter_name, "t")


def test_conditions_are_data_not_code() -> None:
    named = {"hoch": {"greater": ["betrag", 100]}}
    values = {"betrag": 150, "fonds": "ESF+", "liste": [], "text": " "}
    assert evaluate("hoch", values, named)
    assert evaluate({"in": ["fonds", ["EFRE", "ESF+"]]}, values, named)
    assert evaluate({"all": ["hoch", {"empty": "liste"}, {"empty": "text"}]}, values, named)
    assert not evaluate({"any": [{"filled": "liste"}, {"not": "hoch"}]}, values, named)
    assert not evaluate({"greater": ["fonds", 1]}, values, named)


def test_registry_keeps_versions_immutable() -> None:
    first = define_template(definition())
    second = define_template(definition(version="1.1.0", status="Entwurf"))
    archived = define_template(definition(version="2.0.0", status="Archiviert"))
    registry = TemplateRegistry([first, second, archived])
    assert registry.versions("test") == ("1.0.0", "1.1.0", "2.0.0")
    assert registry.get("test").version == "1.1.0"
    assert registry.get("test", "2.0.0").status == "Archiviert"
    registry.register(define_template(definition()))
    with pytest.raises(TemplateError, match="neue Version"):
        registry.register(define_template(definition(description="geändert")))
    with pytest.raises(TemplateNotFoundError):
        registry.get("fehlt")


def test_builtin_templates_are_neutral_and_valid() -> None:
    registry = builtin_registry()
    assert [t.id for t in registry.latest()] == ["pruefbericht", "vermerk"]
    report = registry.get("pruefbericht")
    assert report.text_block("rechtsgrundlage").required  # type: ignore[union-attr]
    text = str(report.definition).lower()
    for word in ("hessen", "hmwvw", "gellix", "wibank"):
        assert word not in text
    assert "verwaltungsüberprüfung" in text and "feststellungen" in text
    visible = " ".join(b.title for b in report.text_blocks)
    visible += " ".join(getattr(n, "text", "") for n in resolve(report, report.sample).nodes)
    for ascii_umlaut in ("pruefung", "foerder", "ueberpruefung", "gemaess", "begruend"):
        assert ascii_umlaut not in visible.lower()


def test_design_profiles_are_validated() -> None:
    custom = design_from_dict({"id": "amt-v1", "accent_color": "003366", "header_text": "Amt"})
    assert custom.accent_color == "003366" and custom.font_family == "Arial"
    assert custom.to_dict()["heading_sizes_pt"] == [16.0, 13.0, 11.5]
    for bad in (
        {"accent_color": "red"},
        {"pdf_font": "Comic"},
        {"logo": "x"},
        {"font_size_pt": 99},
    ):
        with pytest.raises(TemplateError):
            design_from_dict({"id": "x-v1", **bad})
    with pytest.raises(TemplateError):
        DesignProfile(id="X")
