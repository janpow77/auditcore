"""Diagnosesätze T2-gemischt und T2b: Trennung, Determinismus, Ziel-JSON, Reihenfolge."""

from __future__ import annotations

from pathlib import Path

import pytest

from auditcore_invoicesynth.cli import main
from auditcore_invoicesynth.dataset import DatasetError, load_split, plan_summary, verify_dataset
from auditcore_invoicesynth.diagnostics import (
    DIAGNOSTIC_SETS,
    HOLDOUT_B,
    SHUFFLED,
    DiagnosticConfig,
    build_diagnostics,
    plan_diagnostics,
    prepare_diagnostics,
    resolve_sets,
)
from auditcore_invoicesynth.fonts import DIAGNOSTIC_FONT_FAMILIES, FONT_CATALOG, FontSet
from auditcore_invoicesynth.layout_head import meta_rows
from auditcore_invoicesynth.layouts import (
    DIAGNOSTIC_LAYOUTS,
    HOLDOUT_LAYOUTS,
    LAYOUTS,
    TRAINING_LAYOUTS,
    available_layouts,
    render_layout,
)
from auditcore_invoicesynth.plan import SynthConfig, plan_dataset

ALL_FAMILIES = tuple(FONT_CATALOG)


class RecordingCanvas:
    """Zeichenfläche ohne Pillow: merkt Texte und Felder in Zeichenreihenfolge."""

    page_number = 1

    def __init__(self) -> None:
        self.texts: list[str] = []
        self.fields: dict[str, str] = {}
        self.field_order: list[str] = []

    def text(self, x: float, y: float, value: str, **_: object) -> None:
        self.texts.append(value)

    def text_width(self, value: str, *, size: float = 1.0, bold: bool = False) -> float:
        return len(value) * 2.0 * size

    def line_height(self, size: float = 1.0) -> float:
        return 5.0 * size

    def line(self, *args: float, width: float = 0.25) -> None:
        return None

    def rect(self, *args: float, **_: object) -> None:
        return None

    def field(self, key: str, value: str) -> str:
        if key not in self.fields:
            self.field_order.append(key)
        self.fields.setdefault(key, value)
        return value

    def new_page(self) -> None:
        self.page_number += 1


FULL = {"train": 400, "validation": 40, "test_synthetic": 40, "test_layout_holdout": 40}
META = ("invoice_number", "invoice_date", "supply_date", "due_date")


@pytest.mark.parametrize("variety", ["v1", "v2"])
def test_diagnostic_layout_and_font_never_in_regular_splits(variety: str) -> None:
    specs = plan_dataset(SynthConfig(counts=FULL, variety=variety), ALL_FAMILIES)
    assert specs
    for spec in specs:
        assert spec.layout not in DIAGNOSTIC_LAYOUTS
        assert spec.font_family not in DIAGNOSTIC_FONT_FAMILIES
        if spec.split != "test_layout_holdout":
            assert spec.layout not in HOLDOUT_LAYOUTS
            assert spec.font_family != "DejaVu Serif"
    assert not set(DIAGNOSTIC_LAYOUTS) & set(TRAINING_LAYOUTS)
    assert not set(DIAGNOSTIC_LAYOUTS) & set(available_layouts(variety))


def test_diagnostic_layout_differs_from_all_others() -> None:
    spec = LAYOUTS[DIAGNOSTIC_LAYOUTS[0]]
    for name, other in LAYOUTS.items():
        if name not in DIAGNOSTIC_LAYOUTS:
            assert other.meta != spec.meta and other.totals != spec.totals
            assert other.header != spec.header


def test_plans_use_only_their_layouts_and_fonts() -> None:
    config = DiagnosticConfig(count=60)
    for _, specs in plan_diagnostics(config, ALL_FAMILIES):
        assert len(specs) == 60
        name = specs[0].split
        assert {s.split for s in specs} == {name}
        assert {s.layout for s in specs} <= set(DIAGNOSTIC_SETS[name].layouts)
        assert {s.font_family for s in specs} == set(DIAGNOSTIC_SETS[name].fonts)
        assert specs[0].sample_id == f"{name}-000001"


def test_missing_set_font_is_an_error() -> None:
    families = tuple(f for f in ALL_FAMILIES if f not in DIAGNOSTIC_FONT_FAMILIES)
    with pytest.raises(ValueError, match="Schrift"):
        plan_diagnostics(DiagnosticConfig(sets=(HOLDOUT_B,)), families)


def test_resolve_sets_and_validation() -> None:
    assert resolve_sets("shuffled, holdout_b") == (SHUFFLED, HOLDOUT_B)
    with pytest.raises(ValueError):
        DiagnosticConfig(sets=("train",)).validate()
    with pytest.raises(ValueError):
        DiagnosticConfig(count=0).validate()


def _rendered(sets: tuple[str, ...], count: int = 80) -> list[tuple[str, RecordingCanvas]]:
    samples = prepare_diagnostics(DiagnosticConfig(count=count, sets=sets), ALL_FAMILIES)
    result = []
    for sample in samples:
        canvas = RecordingCanvas()
        render_layout(canvas, sample.invoice, sample.variant, sample.spec.layout)
        result.append((sample.spec.split, canvas))
    return result


@pytest.mark.parametrize("name", [SHUFFLED, HOLDOUT_B])
def test_target_json_holds_only_printed_values(name: str) -> None:
    for _, canvas in _rendered((name,), 40):
        printed = " ".join(canvas.texts)
        for key, value in canvas.fields.items():
            if key not in {"document_type", "currency"}:
                assert value in printed, key


def test_shuffled_order_varies_and_supply_date_sometimes_missing() -> None:
    orders = set()
    without_supply = 0
    for _, canvas in _rendered((SHUFFLED,)):
        order = tuple(key for key in canvas.field_order if key in META)
        orders.add(order)
        without_supply += "supply_date" not in canvas.fields
    assert len(orders) >= 6
    assert 0 < without_supply < 80


def test_shuffled_keeps_t2_labels_and_holdout_b_fixed_order() -> None:
    samples = prepare_diagnostics(DiagnosticConfig(count=40), ALL_FAMILIES)
    shuffled = [s for s in samples if s.spec.split == SHUFFLED]
    assert all(s.variant.variety is not None for s in shuffled)
    assert all(not s.variant.variety.due_in_text for s in shuffled if s.variant.variety)
    holdout_b = [s for s in samples if s.spec.split == HOLDOUT_B]
    assert all(s.variant.variety is None for s in holdout_b)
    keys = [
        row[1]
        for row in meta_rows(
            holdout_b[0].invoice, holdout_b[0].variant, LAYOUTS[DIAGNOSTIC_LAYOUTS[0]]
        )
    ]
    assert set(keys) <= set(META)


def _fonts_or_skip(fonts: FontSet) -> FontSet:
    if not set(DIAGNOSTIC_FONT_FAMILIES) <= set(fonts.families):
        pytest.skip("fonts-urw-base35 nicht installiert")
    return fonts


def test_build_is_deterministic_and_verifiable(fonts: FontSet, tmp_path: Path) -> None:
    fonts = _fonts_or_skip(fonts)
    config = DiagnosticConfig(count=3, dpi_choices=(72,))
    first = build_diagnostics(config, tmp_path / "a", fonts)
    second = build_diagnostics(config, tmp_path / "b", fonts, workers=2)
    assert first["dataset_hash"] == second["dataset_hash"]
    assert verify_dataset(tmp_path / "a").ok
    for name in (SHUFFLED, HOLDOUT_B):
        rows = load_split(tmp_path / "a", name)
        assert rows and all(r["meta"]["layout"] in DIAGNOSTIC_SETS[name].layouts for r in rows)
    shuffled = load_split(tmp_path / "a", SHUFFLED)
    assert all("meta_order" in r["meta"] for r in shuffled)
    other = build_diagnostics(
        DiagnosticConfig(count=3, seed=1, dpi_choices=(72,)), tmp_path / "c", fonts
    )
    assert other["dataset_hash"] != first["dataset_hash"]


def test_build_shuffled_only_without_diagnostic_font(fonts: FontSet, tmp_path: Path) -> None:
    """T2-gemischt braucht nur die T2-Schrift; läuft daher auch ohne URW Gothic (CI)."""
    config = DiagnosticConfig(count=2, sets=(SHUFFLED,), dpi_choices=(72,))
    manifest = build_diagnostics(config, tmp_path / "s", fonts)
    assert manifest["kind"] == "diagnostics" and manifest["evaluation_only"] is True
    assert verify_dataset(tmp_path / "s").ok
    assert len(load_split(tmp_path / "s", SHUFFLED)) >= 2
    assert not (tmp_path / "s" / HOLDOUT_B).exists()
    with pytest.raises(DatasetError):
        build_diagnostics(config, tmp_path / "s", fonts)


def test_cli_build_diagnostics(
    fonts: FontSet, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _fonts_or_skip(fonts)
    out = tmp_path / "d"
    argv = ["build-diagnostics", "--out", str(out), "--count", "2", "--dpi", "72"]
    assert main([*argv, "--sets", "holdout_b", "--workers", "1"]) == 0
    assert '"dataset_hash"' in capsys.readouterr().out
    assert (out / HOLDOUT_B / "metadata.jsonl").is_file()
    assert not (out / SHUFFLED).exists()
    assert main([*argv, "--workers", "-1"]) == 2


# Plan-Hashes von origin/main (vor den Diagnosesätzen) mit allen Katalogschriften,
# Seed 42, 20000/1000/1000/500; die Diagnoseschrift darf daran nichts ändern.
STABLE_PLAN_SHA256 = {
    "v1": "3da7d6e15f5f3327e827b6fdcd8911e6f0ddaf049f4684789a6f618b300e8503",
    "v2": "c50af53aa36d592d85db17ba56bae757de849010640cb729c76515c50357d852",
    # v3 (eingeführt mit den Summenorten): Wert dieser Einführung, ab dann stabil.
    "v3": "1250705c48e1ead786d0658bc2e3329064fc8679bf84e7967bd83fdb2466852f",
    # v4 (Stufe 7): Wert der Einführung; v1–v3 blieben dabei unverändert, obwohl der
    # Katalog drei weitere Familien kennt (nur v4 zieht sie, mit eigener Zufallsfolge).
    "v4": "42a03538548312e15817acde85c24a35d18c74947be4e43a0a01278d458c520d",
}


@pytest.mark.parametrize("variety", ["v1", "v2", "v3", "v4"])
def test_regular_plan_hashes_unchanged(variety: str) -> None:
    counts = {
        "train": 20000,
        "validation": 1000,
        "test_synthetic": 1000,
        "test_layout_holdout": 500,
    }
    config = SynthConfig(counts=counts, variety=variety)
    summary = plan_summary(config, ALL_FAMILIES)
    assert summary["plan_sha256"] == STABLE_PLAN_SHA256[variety]
