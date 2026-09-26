"""``docs/eingabefelder.md`` bleibt mit den Profilen synchron.

Das Werkzeug ``tools/document_fields.py`` erzeugt die Übersicht Feld ↔ Regel ↔
Bedeutung ↔ Pflicht/optional ↔ Verhalten bei fehlenden Daten aus allen Profilen.
Ändert sich ein Profil oder eine Regelart, schlägt dieser Test fehl, bis die Datei
neu erzeugt ist (``python tools/document_fields.py``).
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

import pytest

from auditcore_risk.rules import KINDS

ROOT = Path(__file__).resolve().parents[1]


def _tool() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "document_fields", ROOT / "tools" / "document_fields.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_generated_file_is_current() -> None:
    tool = _tool()
    expected = tool.render()
    actual = (ROOT / "docs" / "eingabefelder.md").read_text(encoding="utf-8")
    assert actual == expected, "docs/eingabefelder.md veraltet: python tools/document_fields.py"
    assert tool.main(["--check"]) == 0


def test_every_rule_kind_is_documented() -> None:
    assert set(KINDS) <= set(_tool().EXTRACTORS)


def test_every_profile_has_a_table() -> None:
    text = (ROOT / "docs" / "eingabefelder.md").read_text(encoding="utf-8")
    for path in sorted((ROOT / "src" / "auditcore_risk" / "profile_data").glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        assert f"\n## {data['id']} {data['version']}\n" in text


def test_recommended_riskanalysis_profile_documents_every_field() -> None:
    tool = _tool()
    data = json.loads(
        (
            ROOT
            / "src"
            / "auditcore_risk"
            / "profile_data"
            / "riskanalysis.year_bound-2026.09.5.json"
        ).read_text(encoding="utf-8")
    )
    fields = tool.profile_entries(data)
    assert set(fields) == {
        "Anzahl_Versionen",
        "Anzahl_ungueltige_Versionen",
        "Gruppennummer",
        "Name",
        "_pseudonym_rf09",
        "abweichungen_betrag",
        "antrag",
        "auszahlungsdauer_tage",
        "bruttobetrag",
        "indikator_erreichungsquote",
        "kostenart_auswertung_bezeichnung",
        "nettobetrag",
        "payee_canonical",
        "rechnungsdatum_dt",
        "sanktionslisten_status",
        "vergabenummer",
        "zahlungsempfaenger",
    }
    known = tool.meanings(data["id"], data["version"])
    assert set(fields) <= set(known)
    # K2a: ohne Nettobetrag unbestimmt, keine Pflichtspalte
    netto = fields["nettobetrag"]
    assert {e.code for e in netto} == {"RF02", "RF08"}
    assert not any(e.required for e in netto)
    assert all("Nettobetrag fehlt in der Quelle" in e.empty for e in netto)
    # Abbruch ohne Bruttobetrag bzw. Namen
    assert any(e.required for e in fields["bruttobetrag"])
    assert all(e.required for e in fields["Name"])


def test_unknown_field_parameter_is_rejected() -> None:
    tool = _tool()
    rule = {
        "code": "X",
        "label": "x",
        "kind": "text_equals",
        "params": {
            "field": "a",
            "column_missing_value": "",
            "value": "b",
            "other_field": "c",
        },
    }
    with pytest.raises(SystemExit, match="other_field|\\['c'\\]"):
        tool.rule_entries(rule)
