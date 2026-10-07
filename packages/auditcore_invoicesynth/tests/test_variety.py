"""Generatorvariante v2 (Stufe 5): Kopfdatenvielfalt, Holdout-Trennung, Determinismus."""

from __future__ import annotations

from pathlib import Path

import pytest

from auditcore_invoicesynth.dataset import build_dataset, load_split, prepare_samples
from auditcore_invoicesynth.fonts import FontSet
from auditcore_invoicesynth.layouts import HOLDOUT_LAYOUTS, V2_LAYOUTS, render_layout
from auditcore_invoicesynth.plan import SynthConfig, plan_dataset

FAMILIES = ("DejaVu Sans", "DejaVu Serif", "Liberation Sans", "Lato")
COUNTS = {"train": 300, "validation": 20, "test_synthetic": 20, "test_layout_holdout": 40}


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


def _config(variety: str) -> SynthConfig:
    return SynthConfig(counts=COUNTS, variety=variety)


def _render(variety: str) -> list[tuple[str, RecordingCanvas]]:
    config = _config(variety)
    samples = prepare_samples(config, plan_dataset(config, FAMILIES))
    result = []
    for sample in samples:
        canvas = RecordingCanvas()
        render_layout(canvas, sample.invoice, sample.variant, sample.spec.layout)
        result.append((sample.spec.layout, canvas))
    return result


def test_v1_plan_unchanged_by_v2_fonts_and_layouts() -> None:
    v1 = plan_dataset(_config("v1"), FAMILIES)
    assert all(s.font_family != "Lato" and s.layout not in V2_LAYOUTS for s in v1)
    assert all("variety" not in s.to_dict() for s in v1)
    assert v1 == plan_dataset(_config("v1"), FAMILIES[:3])


def test_v2_keeps_layout_holdout_identical_and_separate() -> None:
    v1 = plan_dataset(_config("v1"), FAMILIES)
    v2 = plan_dataset(_config("v2"), FAMILIES)
    assert [s for s in v1 if s.split == "test_layout_holdout"] == [
        s for s in v2 if s.split == "test_layout_holdout"
    ]
    for spec in v2:
        holdout = spec.split == "test_layout_holdout"
        assert (spec.layout in HOLDOUT_LAYOUTS) == holdout
        assert (spec.font_family == "DejaVu Serif") == holdout
    used = {s.layout for s in v2}
    assert set(V2_LAYOUTS) <= used
    assert "Lato" in {s.font_family for s in v2}
    assert any(s.degrade is not None for s in v2)


def test_v2_varies_meta_order_and_omits_supply_date() -> None:
    orders = set()
    without_supply = 0
    due_texts = set()
    for _, canvas in _render("v2"):
        orders.add(
            tuple(k for k in canvas.field_order if k.endswith("_date") or k == "invoice_number")
        )
        without_supply += "supply_date" not in canvas.fields
        due_texts.update(t.split(" ")[0] for t in canvas.texts if "Zahl" in t or "Bitte" in t)
    assert len(orders) >= 6
    assert without_supply > 20
    assert len(due_texts) >= 2


def test_v2_fields_equal_printed_values() -> None:
    for layout, canvas in _render("v2"):
        printed = " ".join(canvas.texts)
        for key, value in canvas.fields.items():
            if key in {"document_type", "currency"}:
                continue
            assert value in printed, (layout, key, value)
        assert "supplier.name" in canvas.fields


def test_new_arrangements_capture_all_header_fields() -> None:
    seen = set()
    for layout, canvas in _render("v2"):
        if layout in V2_LAYOUTS:
            seen.add(layout)
            assert {"invoice_number", "invoice_date", "due_date"} <= set(canvas.fields)
    assert seen == set(V2_LAYOUTS)


def test_unknown_variety_rejected() -> None:
    with pytest.raises(ValueError, match="Generatorvariante"):
        plan_dataset(SynthConfig(variety="v9"), FAMILIES)


@pytest.mark.slow
def test_v2_build_is_deterministic(tmp_path: Path, fonts: FontSet) -> None:
    config = SynthConfig(
        counts={"train": 8, "validation": 1, "test_synthetic": 1, "test_layout_holdout": 2},
        variety="v2",
        degrade_share=0.5,
        dpi_choices=(100,),
    )
    first = build_dataset(config, tmp_path / "a", fonts)
    second = build_dataset(config, tmp_path / "b", fonts)
    assert first["dataset_hash"] == second["dataset_hash"]
    rows = load_split(tmp_path / "a", "train")
    assert all(row["meta"]["variety"] == "v2" for row in rows)
    holdout = load_split(tmp_path / "a", "test_layout_holdout")
    assert all("variety" not in row["meta"] for row in holdout)
