"""Eigenschaftstests der Vorlagen-Invarianten I14–I18 aus ``docs/spezifikation.md`` (Hypothesis).

Synthetische Daten; jede Testfunktion nennt ihre Invariante.
"""

from __future__ import annotations

import io
from html import escape
from typing import Any

import pytest
from docx import Document
from hypothesis import given, settings
from hypothesis import strategies as st

from auditcore_reporting.templates import (
    TemplateDataError,
    TemplateError,
    TemplateRegistry,
    define_template,
    render,
)

EINSTELLUNG = settings(max_examples=60, deadline=None)
# XML-1.0-taugliche Texte, einschließlich Markup- und Platzhalterzeichen.
TEXT = st.text(
    alphabet=st.characters(blacklist_categories=("Cs", "Cc"), blacklist_characters="\ufffe\uffff"),
    max_size=40,
) | st.sampled_from(["{{ name }}", "{%p if x %}", "<b>&amp;</b>", "=1+1", "„Zitat“ ß"])
DEFINITION: dict[str, Any] = {
    "id": "eigenschaft",
    "version": "1.0.0",
    "title": "Eigenschaft",
    "schema": {
        "type": "object",
        "required": ["name"],
        "properties": {
            "name": {"type": "string", "maxLength": 40},
            "betrag": {"type": "number", "minimum": 0},
            "punkte": {"type": "array", "items": {"type": "string"}},
        },
    },
    "text_blocks": [
        {"id": "hoch", "if": {"greater": ["betrag", 100]}, "text": "BAUSTEIN-HOCH"},
        {"id": "niedrig", "if": {"not": {"greater": ["betrag", 100]}}, "text": "BAUSTEIN-NIEDRIG"},
    ],
    "blocks": [
        {"type": "paragraph", "text": "{{ name }}"},
        {"type": "textblock", "id": "hoch"},
        {"type": "textblock", "id": "niedrig"},
        {"type": "list", "source": "punkte", "as": "p", "item": "{{ p }}"},
    ],
    "sample": {"name": "x"},
}
TEMPLATE = define_template(DEFINITION)
DATEN = st.fixed_dictionaries(
    {"name": TEXT},
    optional={
        "betrag": st.floats(min_value=0, max_value=1e9, allow_nan=False),
        "punkte": st.lists(TEXT, max_size=5),
    },
)


def docx_texts(content: bytes) -> list[str]:
    return [p.text for p in Document(io.BytesIO(content)).paragraphs]


@EINSTELLUNG
@given(DATEN, st.sampled_from(["docx", "html", "pdf"]))
def test_i14_ausgabe_deterministisch(daten: dict[str, Any], ausgabe: str) -> None:
    """I14: Gleiche Vorlage, Daten und Gestaltung ergeben bytegleiche Dateien."""
    erste = render(TEMPLATE, daten, ausgabe)
    zweite = render(TEMPLATE, dict(daten), ausgabe)
    assert erste.content == zweite.content
    assert erste.data_sha256 == zweite.data_sha256
    assert erste.template_fingerprint == TEMPLATE.fingerprint


@EINSTELLUNG
@given(DATEN)
def test_i15_daten_bleiben_text(daten: dict[str, Any]) -> None:
    """I15: Datenwerte erscheinen wörtlich und werden nie als Platzhalter oder Markup ausgewertet."""
    texte = docx_texts(render(TEMPLATE, daten, "docx").content)
    html = render(TEMPLATE, daten, "html").content.decode()
    name = daten["name"]
    if name.strip():
        assert name in texte
        assert f"<p>{escape(name)}</p>" in html
    for punkt in daten.get("punkte", []):
        assert punkt in texte
        assert f"<li>{escape(punkt)}</li>" in html


@EINSTELLUNG
@given(
    st.dictionaries(st.sampled_from(["name", "betrag", "punkte", "fremd"]), TEXT | st.integers())
)
def test_i16_datenvertrag_vor_ausgabe(daten: dict[str, Any]) -> None:
    """I16: Verletzen die Daten den Datenvertrag, entsteht keine Datei, sondern TemplateDataError."""
    gueltig = (
        isinstance(daten.get("name"), str)
        and len(daten["name"]) <= 40
        and "fremd" not in daten
        and ("betrag" not in daten or (isinstance(daten["betrag"], int) and daten["betrag"] >= 0))
        and "punkte" not in daten
    )
    if gueltig:
        assert render(TEMPLATE, daten, "docx").content[:2] == b"PK"
    else:
        with pytest.raises(TemplateDataError):
            render(TEMPLATE, daten, "docx")


@EINSTELLUNG
@given(st.floats(min_value=0, max_value=1e6, allow_nan=False))
def test_i17_textbaustein_genau_bei_bedingung(betrag: float) -> None:
    """I17: Ein Textbaustein erscheint genau dann, wenn seine Bedingung gilt."""
    ergebnis = render(TEMPLATE, {"name": "n", "betrag": betrag}, "html")
    html = ergebnis.content.decode()
    hoch = betrag > 100
    assert ("BAUSTEIN-HOCH" in html) is hoch
    assert ("BAUSTEIN-NIEDRIG" in html) is not hoch
    assert ergebnis.text_blocks == (("hoch",) if hoch else ("niedrig",))


@EINSTELLUNG
@given(
    st.text(min_size=1, max_size=30).filter(
        lambda t: "{" not in t and "}" not in t and "%" not in t
    )
)
def test_i18_version_unveraenderlich(beschreibung: str) -> None:
    """I18: Jede Änderung der Definition ändert den Fingerabdruck; eine Version bleibt unveränderlich."""
    try:
        geaendert = define_template({**DEFINITION, "description": beschreibung})
    except TemplateError:
        return  # Steuerzeichen werden schon bei der Definition abgewiesen
    assert geaendert.fingerprint != TEMPLATE.fingerprint
    registry = TemplateRegistry([TEMPLATE])
    with pytest.raises(TemplateError, match="neue Version"):
        registry.register(geaendert)
    registry.register(
        define_template({**DEFINITION, "description": beschreibung, "version": "1.0.1"})
    )
    assert registry.versions("eigenschaft") == ("1.0.0", "1.0.1")
