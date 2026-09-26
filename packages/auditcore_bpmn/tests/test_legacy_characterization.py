"""Replay: die Übernahmen liefern dieselben Ergebnisse wie die Originale aus audit_designer.

``fixtures/legacy_observed.json`` hält Ein- und Ausgaben der unveränderten
Originale fest (``tools/capture_legacy.py``; pandas 2.1.4, openpyxl 3.1.2,
reportlab 4.0.8). Einzige erwartete Abweichung: Dokumente mit DOCTYPE weist
die BVA-Validierung jetzt ab (``docs/behavior-changes.md``).
"""

from __future__ import annotations

import base64
import hashlib
import io
import json
from typing import Any

import pytest
from helpers import FIXTURES

from auditcore_bpmn.legacy import (
    BpmnAnalyzer,
    analyze_bpmn,
    export_bpmn_to_excel,
    export_bpmn_to_pdf,
    validate_bpmn_bva,
)

OBSERVED = json.loads((FIXTURES / "legacy_observed.json").read_text(encoding="utf-8"))
CASES = OBSERVED["cases"]
RATES: dict[str, float] = OBSERVED["personnel_rates"]
DOCTYPE_DEVIATION = {"doctype-ohne-entitaet"}
UNIQUE = ("unique_owners", "unique_departments", "unique_systems")


def _json(value: Any) -> Any:
    return json.loads(json.dumps(value).replace("NaN", '"NaN"'))


def _order_free(analysis: dict[str, Any]) -> dict[str, Any]:
    """Die Originale geben Mengen in zufälliger Reihenfolge aus; verglichen wird der Inhalt."""
    return {k: (sorted(v) if k in UNIQUE else v) for k, v in analysis.items()}


def _single_valued(case: dict[str, Any]) -> bool:
    return all(len(case["analysis"][key]) <= 1 for key in UNIQUE)


def _ids(cases: list[dict[str, Any]]) -> list[str]:
    return [c["id"] for c in cases]


def test_fixture_is_bound_to_the_pinned_sources() -> None:
    assert OBSERVED["source"]["commit"] == "eff41a4ccedab12b9a73bafff41468712459cb2b"
    assert OBSERVED["environment"]["pandas"] == "2.1.4" and len(CASES) == 95


@pytest.mark.parametrize("case", CASES, ids=_ids(CASES))
def test_bva_validation(case: dict[str, Any]) -> None:
    result = validate_bpmn_bva(case["xml"])
    if case["id"] in DOCTYPE_DEVIATION:
        assert result.valid is False and result.errors[0].startswith("BPMN-XML ist nicht wohlgeformt:")
        return
    assert (result.valid, result.errors, result.warnings) == (
        case["bva"]["valid"],
        case["bva"]["errors"],
        case["bva"]["warnings"],
    )


ANALYSED = [c for c in CASES if "error" not in c]
FAILED = [c for c in CASES if "error" in c]


@pytest.mark.parametrize("case", ANALYSED, ids=_ids(ANALYSED))
def test_analysis_esi_and_personnel(case: dict[str, Any]) -> None:
    xml = case["xml"]
    assert _order_free(_json(analyze_bpmn(xml, "Testprozess"))) == _order_free(case["analysis"])
    with_rates = analyze_bpmn(xml, "Testprozess", personnel_rate=RATES.get)
    assert _order_free(_json(with_rates)) == _order_free(case["analysis_personnel"])
    assert _json(BpmnAnalyzer(xml).extract_esi_requirements()) == case["esi"]


@pytest.mark.parametrize("case", FAILED, ids=_ids(FAILED))
def test_errors_like_the_original(case: dict[str, Any]) -> None:
    with pytest.raises(Exception) as info:
        analyze_bpmn(case["xml"])
    if case["id"] not in DOCTYPE_DEVIATION:
        assert str(info.value) == case["error"]["message"]


EXCEL = [c for c in ANALYSED if _single_valued(c)]


@pytest.mark.parametrize("case", EXCEL, ids=_ids(EXCEL))
def test_excel_workbook_matches(case: dict[str, Any]) -> None:
    pytest.importorskip("openpyxl")
    from capture import workbook_snapshot

    snapshot = workbook_snapshot(export_bpmn_to_excel(case["xml"], "Testprozess").getvalue())
    assert snapshot == case["excel"]


def test_pdf_bytes_or_text_match() -> None:
    reportlab = pytest.importorskip("reportlab")
    from reportlab import rl_config

    rl_config.invariant = 1
    same_version = reportlab.Version == OBSERVED["environment"]["reportlab"]
    checked = 0
    for case in ANALYSED:
        pdf = export_bpmn_to_pdf(case["xml"], "Testprozess").getvalue()
        assert pdf.startswith(b"%PDF-")
        if same_version and _single_valued(case):
            assert hashlib.sha256(pdf).hexdigest() == case["pdf_sha256"], case["id"]
            checked += 1
        if "pdf_base64" in case and _single_valued(case):
            pypdf = pytest.importorskip("pypdf")
            original = base64.b64decode(case["pdf_base64"])
            texts = [
                "".join(page.extract_text() for page in pypdf.PdfReader(io.BytesIO(data)).pages)
                for data in (original, pdf)
            ]
            assert texts[0] == texts[1], case["id"]
            checked += 1
    assert checked >= 2
