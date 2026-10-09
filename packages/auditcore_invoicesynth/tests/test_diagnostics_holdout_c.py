"""Diagnosesatz T2c: Trennung, Determinismus, Ziel-JSON = Gedrucktes, Summenlage.

Die Kernlogik läuft mit einer Aufzeichnungs-Zeichenfläche ohne Spezialschrift
(CI hat nur ``fonts-dejavu-core``); Bauläufe mit C059 werden sonst übersprungen.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path

import pytest
from test_diagnostics import ALL_FAMILIES, FULL, RecordingCanvas

from auditcore_invoicesynth.dataset import load_split, verify_dataset
from auditcore_invoicesynth.diagnostics import (
    DIAGNOSTIC_SETS,
    HOLDOUT_B,
    HOLDOUT_C,
    SHUFFLED,
    DiagnosticConfig,
    build_diagnostics,
    plan_diagnostics,
    prepare_diagnostics,
    resolve_sets,
)
from auditcore_invoicesynth.fonts import HOLDOUT_C_FONT_FAMILIES, FontSet
from auditcore_invoicesynth.layout_holdout_c import render_holdout_c
from auditcore_invoicesynth.layout_prose import flow
from auditcore_invoicesynth.layouts import (
    HOLDOUT_C_LAYOUTS,
    LAYOUTS,
    TRAINING_LAYOUTS,
    available_layouts,
    render_layout,
)
from auditcore_invoicesynth.plan import SynthConfig, plan_dataset

REQUIRED = ("invoice_number", "invoice_date", "supply_date", "due_date", "total", "supplier.name")


@pytest.mark.parametrize("variety", ["v1", "v2", "v3"])
def test_holdout_c_never_in_regular_plans(variety: str) -> None:
    specs = plan_dataset(SynthConfig(counts=FULL, variety=variety), ALL_FAMILIES)
    assert specs
    assert not {s.layout for s in specs} & set(HOLDOUT_C_LAYOUTS)
    assert not {s.font_family for s in specs} & set(HOLDOUT_C_FONT_FAMILIES)
    assert not set(HOLDOUT_C_LAYOUTS) & set(TRAINING_LAYOUTS)
    assert not set(HOLDOUT_C_LAYOUTS) & set(available_layouts(variety))


def test_holdout_c_never_in_other_diagnostic_sets() -> None:
    for _, specs in plan_diagnostics(DiagnosticConfig(count=80), ALL_FAMILIES):
        assert not {s.layout for s in specs} & set(HOLDOUT_C_LAYOUTS)
        assert not {s.font_family for s in specs} & set(HOLDOUT_C_FONT_FAMILIES)
    for name, spec in DIAGNOSTIC_SETS.items():
        if name != HOLDOUT_C:
            assert not set(spec.layouts) & set(HOLDOUT_C_LAYOUTS)
            assert not set(spec.fonts) & set(HOLDOUT_C_FONT_FAMILIES)


def test_holdout_c_layouts_differ_from_all_others() -> None:
    for name in HOLDOUT_C_LAYOUTS:
        spec = LAYOUTS[name]
        for other_name, other in LAYOUTS.items():
            if other_name not in HOLDOUT_C_LAYOUTS:
                assert (other.header, other.meta, other.totals, other.bank) != (
                    spec.header,
                    spec.meta,
                    spec.totals,
                    spec.bank,
                )
                assert other.meta != spec.meta and other.totals != spec.totals


def test_holdout_c_plan_uses_both_layouts_and_own_font() -> None:
    config = DiagnosticConfig(count=60, sets=resolve_sets("holdout_c"))
    [(_, specs)] = plan_diagnostics(config, ALL_FAMILIES)
    assert {s.split for s in specs} == {HOLDOUT_C}
    assert {s.layout for s in specs} == set(HOLDOUT_C_LAYOUTS)
    assert {s.font_family for s in specs} == set(HOLDOUT_C_FONT_FAMILIES)
    with pytest.raises(ValueError, match="Schrift"):
        plan_diagnostics(config, tuple(f for f in ALL_FAMILIES if f != "C059"))


def _rendered(count: int = 60) -> list[tuple[str, RecordingCanvas]]:
    config = DiagnosticConfig(count=count, sets=(HOLDOUT_C,))
    result = []
    for sample in prepare_diagnostics(config, ALL_FAMILIES):
        canvas = RecordingCanvas()
        render_layout(canvas, sample.invoice, sample.variant, sample.spec.layout)
        result.append((sample.spec.layout, canvas))
    return result


def test_target_json_holds_only_printed_values() -> None:
    rendered = _rendered()
    for _, canvas in rendered:
        printed = " ".join(canvas.texts)
        for key, value in canvas.fields.items():
            if key not in {"document_type", "currency"}:
                assert value in printed, key
        assert set(REQUIRED) <= set(canvas.fields)
    assert {layout for layout, _ in rendered} == set(HOLDOUT_C_LAYOUTS)


def test_total_precedes_vat_lines_in_letter() -> None:
    """Im Brief steht der Gesamtbetrag mitten in der Summenliste, vor den „davon“-Zeilen."""
    checked = 0
    for layout, canvas in _rendered():
        if layout == "holdout_c_brief" and "vat_lines.0.amount" in canvas.fields:
            order = canvas.field_order
            assert order.index("total") < order.index("vat_lines.0.amount")
            checked += 1
    assert checked


def test_preparation_is_deterministic() -> None:
    first = [c.fields for _, c in _rendered(20)]
    second = [c.fields for _, c in _rendered(20)]
    assert first == second


def test_flow_wraps_and_glues_punctuation() -> None:
    canvas = RecordingCanvas()
    end = flow(canvas, [("eins zwei drei vier", None), ("WERT", "iban"), (").", None)], 0, 0, 30)
    assert canvas.fields == {"iban": "WERT"}
    assert end > canvas.line_height(0.9)
    assert canvas.texts[-1] == ")."


def test_unknown_layout_name_is_rejected() -> None:
    sample = prepare_diagnostics(DiagnosticConfig(count=1, sets=(HOLDOUT_C,)), ALL_FAMILIES)[0]
    with pytest.raises(ValueError):
        render_holdout_c(RecordingCanvas(), sample.invoice, sample.variant, "kopf_links")


#: Plan-Hash der Diagnosesätze T2-gemischt + T2b (Seed 42, 500 je Satz) von origin/main
#: vor T2c; Grundlage des versiegelten Satzes diagnose-997a04c1104f073d.
STABLE_DIAGNOSTIC_PLAN_SHA256 = "ecf8ef577a7c59261f8d55091133b48db419b61ebaebfb66a5b5a586422456f8"


def test_existing_diagnostic_plans_unchanged() -> None:
    config = DiagnosticConfig(sets=(SHUFFLED, HOLDOUT_B))
    specs = [asdict(s) for _, plan in plan_diagnostics(config, ALL_FAMILIES) for s in plan]
    text = json.dumps(specs, sort_keys=True, default=str)
    assert hashlib.sha256(text.encode()).hexdigest() == STABLE_DIAGNOSTIC_PLAN_SHA256
    assert DiagnosticConfig().sets == (SHUFFLED, HOLDOUT_B)


def test_build_holdout_c_with_font(fonts: FontSet, tmp_path: Path) -> None:
    if not set(HOLDOUT_C_FONT_FAMILIES) <= set(fonts.families):
        pytest.skip("C059 (fonts-urw-base35) nicht installiert")
    config = DiagnosticConfig(count=3, sets=(HOLDOUT_C,), dpi_choices=(72,))
    first = build_diagnostics(config, tmp_path / "a", fonts)
    second = build_diagnostics(config, tmp_path / "b", fonts, workers=2)
    assert first["dataset_hash"] == second["dataset_hash"]
    assert verify_dataset(tmp_path / "a").ok
    rows = load_split(tmp_path / "a", HOLDOUT_C)
    assert rows and all(r["meta"]["layout"] in HOLDOUT_C_LAYOUTS for r in rows)
    assert all(r["meta"]["font_family"] == "C059" for r in rows)
