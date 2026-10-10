"""Diagnosesatz T2d: Trennung, Determinismus, Ziel-JSON = Gedrucktes, Hash-Stabilität.

Die Kernlogik läuft mit einer Aufzeichnungs-Zeichenfläche ohne Spezialschrift
(CI hat nur ``fonts-dejavu-core``); Bauläufe mit IBM Plex Serif werden sonst
übersprungen.
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
    HOLDOUT_C,
    HOLDOUT_D,
    DiagnosticConfig,
    build_diagnostics,
    plan_diagnostics,
    prepare_diagnostics,
    resolve_sets,
)
from auditcore_invoicesynth.fonts import (
    FONT_CATALOG,
    HOLDOUT_D_FONT_FAMILIES,
    V4_FONT_FAMILIES,
    FontSet,
)
from auditcore_invoicesynth.layout_holdout_d import render_holdout_d
from auditcore_invoicesynth.layouts import (
    HOLDOUT_D_LAYOUTS,
    LAYOUTS,
    TRAINING_LAYOUTS,
    available_layouts,
    render_layout,
)
from auditcore_invoicesynth.plan import SynthConfig, plan_dataset

REQUIRED = ("invoice_number", "invoice_date", "supply_date", "due_date", "total", "supplier.name")
#: Trainings-, T2-, T2b- und T2c-Schriften; die T2d-Schrift ist keine davon und kein Klon.
KNOWN_FONTS = {
    "URW Gothic",
    "C059",
    "DejaVu Serif",
    "Lato",
    "Nimbus Sans",
    "URW Bookman",
    "P052",
    "Liberation Serif",
    "Noto Serif",
}


@pytest.mark.parametrize("variety", ["v1", "v2", "v3", "v4"])
def test_holdout_d_never_in_regular_plans(variety: str) -> None:
    specs = plan_dataset(SynthConfig(counts=FULL, variety=variety), ALL_FAMILIES)
    assert specs
    assert not {s.layout for s in specs} & set(HOLDOUT_D_LAYOUTS)
    assert not {s.font_family for s in specs} & set(HOLDOUT_D_FONT_FAMILIES)
    assert not set(HOLDOUT_D_LAYOUTS) & set(TRAINING_LAYOUTS)
    assert not set(HOLDOUT_D_LAYOUTS) & set(available_layouts(variety))


def test_holdout_d_font_is_new() -> None:
    assert not set(HOLDOUT_D_FONT_FAMILIES) & (KNOWN_FONTS | set(V4_FONT_FAMILIES))
    for family in HOLDOUT_D_FONT_FAMILIES:
        files = (*FONT_CATALOG[family].regular, *FONT_CATALOG[family].bold)
        others = {
            name
            for other, spec in FONT_CATALOG.items()
            if other != family
            for name in (*spec.regular, *spec.bold)
        }
        assert not set(files) & others


def test_holdout_d_never_in_other_diagnostic_sets() -> None:
    config = DiagnosticConfig(count=80, sets=tuple(n for n in DIAGNOSTIC_SETS if n != HOLDOUT_D))
    for _, specs in plan_diagnostics(config, ALL_FAMILIES):
        assert not {s.layout for s in specs} & set(HOLDOUT_D_LAYOUTS)
        assert not {s.font_family for s in specs} & set(HOLDOUT_D_FONT_FAMILIES)
    for name, spec in DIAGNOSTIC_SETS.items():
        if name != HOLDOUT_D:
            assert not set(spec.layouts) & set(HOLDOUT_D_LAYOUTS)
            assert not set(spec.fonts) & set(HOLDOUT_D_FONT_FAMILIES)


def test_holdout_d_layouts_differ_from_all_others() -> None:
    for name in HOLDOUT_D_LAYOUTS:
        spec = LAYOUTS[name]
        for other_name, other in LAYOUTS.items():
            if other_name not in HOLDOUT_D_LAYOUTS:
                assert other.meta != spec.meta
                assert other.totals != spec.totals
                assert other.bank != spec.bank


def test_holdout_d_plan_uses_both_layouts_and_own_font() -> None:
    config = DiagnosticConfig(count=60, sets=resolve_sets("holdout_d"))
    [(_, specs)] = plan_diagnostics(config, ALL_FAMILIES)
    assert {s.split for s in specs} == {HOLDOUT_D}
    assert {s.layout for s in specs} == set(HOLDOUT_D_LAYOUTS)
    assert {s.font_family for s in specs} == set(HOLDOUT_D_FONT_FAMILIES)
    with pytest.raises(ValueError, match="Schrift"):
        plan_diagnostics(config, tuple(f for f in ALL_FAMILIES if f != "IBM Plex Serif"))


def _rendered(count: int = 80) -> list[tuple[str, RecordingCanvas]]:
    config = DiagnosticConfig(count=count, sets=(HOLDOUT_D,))
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
    assert {layout for layout, _ in rendered} == set(HOLDOUT_D_LAYOUTS)
    assert any("iban" in c.fields and "bic" in c.fields for _, c in rendered)
    assert any("supplier.vat_id" in c.fields for _, c in rendered)


def test_identifiers_before_head_data_in_info_table() -> None:
    """In ``holdout_d_zahlinfo`` stehen IBAN und USt-IdNr. vor der Belegnummer."""
    checked = 0
    for layout, canvas in _rendered():
        if layout == "holdout_d_zahlinfo" and "iban" in canvas.fields:
            order = canvas.field_order
            assert order.index("iban") < order.index("invoice_number")
            assert order.index("supplier.name") > order.index("total")
            checked += 1
    assert checked


def test_total_and_ids_in_transfer_slip() -> None:
    """Im Überweisungsträger folgt der Gesamtbetrag auf Empfänger und IBAN."""
    checked = 0
    for layout, canvas in _rendered():
        if layout == "holdout_d_ueberweisung" and "iban" in canvas.fields:
            order = canvas.field_order
            assert order.index("net_amount") < order.index("supplier.name")
            assert order.index("supplier.name") < order.index("iban") < order.index("total")
            checked += 1
    assert checked


def test_preparation_is_deterministic() -> None:
    first = [c.fields for _, c in _rendered(20)]
    second = [c.fields for _, c in _rendered(20)]
    assert first == second


def test_unknown_layout_name_is_rejected() -> None:
    sample = prepare_diagnostics(DiagnosticConfig(count=1, sets=(HOLDOUT_D,)), ALL_FAMILIES)[0]
    with pytest.raises(ValueError):
        render_holdout_d(RecordingCanvas(), sample.invoice, sample.variant, "kopf_links")


#: Plan-Hash des versiegelten T2c (Seed 42, 500) von origin/main vor T2d; Grundlage
#: des Satzes holdout-c-a0ff61e91cefd77a.
STABLE_HOLDOUT_C_PLAN_SHA256 = "42acfce461e491ff5a20d244df86feb63aced3a2721428b31374e9652a8df788"


def test_holdout_c_plan_unchanged() -> None:
    config = DiagnosticConfig(sets=(HOLDOUT_C,))
    specs = [asdict(s) for _, plan in plan_diagnostics(config, ALL_FAMILIES) for s in plan]
    text = json.dumps(specs, sort_keys=True, default=str)
    assert hashlib.sha256(text.encode()).hexdigest() == STABLE_HOLDOUT_C_PLAN_SHA256


def test_build_holdout_d_with_font(fonts: FontSet, tmp_path: Path) -> None:
    if not set(HOLDOUT_D_FONT_FAMILIES) <= set(fonts.families):
        pytest.skip("IBM Plex Serif nicht installiert")
    config = DiagnosticConfig(count=3, sets=(HOLDOUT_D,), dpi_choices=(72,))
    first = build_diagnostics(config, tmp_path / "a", fonts)
    second = build_diagnostics(config, tmp_path / "b", fonts, workers=2)
    assert first["dataset_hash"] == second["dataset_hash"]
    assert verify_dataset(tmp_path / "a").ok
    rows = load_split(tmp_path / "a", HOLDOUT_D)
    assert rows and all(r["meta"]["layout"] in HOLDOUT_D_LAYOUTS for r in rows)
    assert all(r["meta"]["font_family"] == "IBM Plex Serif" for r in rows)
