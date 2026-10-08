"""Generatorvariante v3: Summenorte, waagerechte Kopfdaten, Ziel-JSON, Geometrie, Trennung."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from pathlib import Path

import pytest

from auditcore_invoicesynth import layouts
from auditcore_invoicesynth.dataset import (
    PreparedSample,
    build_dataset,
    load_split,
    prepare_samples,
)
from auditcore_invoicesynth.fonts import DIAGNOSTIC_FONT_FAMILIES, FontSet
from auditcore_invoicesynth.layout_body import table
from auditcore_invoicesynth.layout_extra import meta_header_row
from auditcore_invoicesynth.layouts import (
    DIAGNOSTIC_LAYOUTS,
    HOLDOUT_LAYOUTS,
    LAYOUTS,
    effective_spec,
    render_layout,
)
from auditcore_invoicesynth.plan import SynthConfig, plan_dataset
from auditcore_invoicesynth.variety import V3_TOTALS_PLACES

FAMILIES = ("DejaVu Sans", "DejaVu Serif", "Liberation Sans", "Lato", "URW Gothic")
COUNTS = {"train": 400, "validation": 30, "test_synthetic": 30, "test_layout_holdout": 40}
Box = tuple[float, float, float, float]


class BoxCanvas:
    """Zeichenfläche ohne Pillow: merkt Texte, Felder und Textrahmen je Abschnitt."""

    page_number = 1

    def __init__(self) -> None:
        self.texts: list[str] = []
        self.fields: dict[str, str] = {}
        self.phase = "head"
        self.boxes: dict[str, list[Box]] = {}

    def text(self, x: float, y: float, value: str, **options: object) -> None:
        size = float(options.get("size", 1.0))  # type: ignore[arg-type]
        width = self.text_width(value, size=size)
        left = {"right": x - width, "center": x - width / 2}.get(str(options.get("align")), x)
        self.texts.append(value)
        if self.page_number == 1 and value.strip():
            box = (left, y, left + width, y + self.line_height(size))
            self.boxes.setdefault(self.phase, []).append(box)

    def text_width(self, value: str, *, size: float = 1.0, bold: bool = False) -> float:
        return len(value) * 1.9 * size

    def line_height(self, size: float = 1.0) -> float:
        return 4.5 * size

    def line(self, *args: float, width: float = 0.25) -> None:
        return None

    def rect(self, *args: float, **_: object) -> None:
        return None

    def field(self, key: str, value: str) -> str:
        self.fields.setdefault(key, value)
        return value

    def new_page(self) -> None:
        self.page_number += 1


def _samples(variety: str = "v3") -> list[PreparedSample]:
    config = SynthConfig(counts=COUNTS, variety=variety)
    return prepare_samples(config, plan_dataset(config, FAMILIES))


def _phased(phase: str, function: Callable[..., float]) -> Callable[..., float]:
    def wrapped(canvas: BoxCanvas, *args: object) -> float:
        canvas.phase = phase
        result = function(canvas, *args)
        canvas.phase = "rest"
        return result

    return wrapped


@pytest.fixture(scope="module")
def rendered() -> list[tuple[PreparedSample, BoxCanvas]]:
    patch = pytest.MonkeyPatch()
    patch.setattr(layouts, "_head_data", _phased("head", layouts._head_data))
    patch.setattr(layouts, "_totals", _phased("totals", layouts._totals))
    patch.setattr(layouts, "table", _phased("table", table))
    result = []
    try:
        for sample in _samples():
            canvas = BoxCanvas()
            render_layout(canvas, sample.invoice, sample.variant, sample.spec.layout)
            result.append((sample, canvas))
    finally:
        patch.undo()
    return result


def _overlap(a: Box, b: Box) -> bool:
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def test_v3_shares_cover_every_new_arrangement() -> None:
    train = [s for s in _samples() if s.spec.split == "train"]
    places = Counter(s.variant.variety.totals_place for s in train if s.variant.variety)
    rows = sum(1 for s in train if s.variant.variety and s.variant.variety.header_row)
    for place in V3_TOTALS_PLACES:
        assert places[place] >= 0.08 * len(train), places
    assert rows >= 0.08 * len(train)
    assert places[None] >= 0.5 * len(train)
    assert all(s.variant["line_amount"] != "Gesamt" for s in train)


def test_v3_is_deterministic_and_keeps_layout_holdout() -> None:
    first, second = _samples(), _samples()
    assert [s.variant for s in first] == [s.variant for s in second]
    v1 = [s.spec for s in _samples("v1") if s.spec.split == "test_layout_holdout"]
    assert v1 == [s.spec for s in first if s.spec.split == "test_layout_holdout"]


def test_holdout_layouts_and_fonts_never_in_training_splits() -> None:
    forbidden_fonts = {"DejaVu Serif", *DIAGNOSTIC_FONT_FAMILIES}
    for sample in _samples():
        spec = sample.spec
        if spec.split == "test_layout_holdout":
            assert spec.layout in HOLDOUT_LAYOUTS and sample.variant.variety is None
            continue
        assert spec.layout not in (*HOLDOUT_LAYOUTS, *DIAGNOSTIC_LAYOUTS)
        assert spec.font_family not in forbidden_fonts
        assert effective_spec(spec.layout, sample.variant).totals != "above_table"


def test_v3_fields_equal_printed_values(rendered: list[tuple[PreparedSample, BoxCanvas]]) -> None:
    seen: set[str] = set()
    for sample, canvas in rendered:
        spec = effective_spec(sample.spec.layout, sample.variant)
        seen.update((spec.totals, spec.meta))
        printed = " ".join(canvas.texts)
        for key, value in canvas.fields.items():
            if key not in {"document_type", "currency"}:
                assert value in printed, (sample.spec.sample_id, key, value)
        assert {"total", "invoice_number", "invoice_date"} <= set(canvas.fields)
    assert {*V3_TOTALS_PLACES, "header_row"} <= seen


def test_totals_block_does_not_overlap_head_or_table(
    rendered: list[tuple[PreparedSample, BoxCanvas]],
) -> None:
    checked = 0
    for sample, canvas in rendered:
        if sample.variant.variety is None or sample.variant.variety.totals_place is None:
            continue
        totals = canvas.boxes.get("totals", [])
        others = canvas.boxes.get("head", []) + canvas.boxes.get("table", [])
        for box in totals:
            assert box[0] >= 15 and box[2] <= 195, (sample.spec.sample_id, box)
            assert not any(_overlap(box, other) for other in others), sample.spec.sample_id
        checked += bool(totals)
    assert checked > 50


def test_header_row_has_three_to_five_cells(
    rendered: list[tuple[PreparedSample, BoxCanvas]],
) -> None:
    from auditcore_invoicesynth.layout_extra import header_cells

    for sample, _ in rendered:
        row = sample.variant.variety.header_row if sample.variant.variety else None
        if row is not None:
            spec = effective_spec(sample.spec.layout, sample.variant)
            assert 3 <= len(header_cells(sample.invoice, sample.variant, spec, row)) <= 5


def test_header_row_requires_v3() -> None:
    sample = _samples("v1")[0]
    with pytest.raises(ValueError, match="v3"):
        meta_header_row(BoxCanvas(), sample.invoice, sample.variant, LAYOUTS["kopf_links"], 80)


@pytest.mark.slow
def test_v3_build_is_deterministic(tmp_path: Path, fonts: FontSet) -> None:
    config = SynthConfig(
        counts={"train": 10, "validation": 1, "test_synthetic": 1, "test_layout_holdout": 2},
        variety="v3",
        dpi_choices=(72,),
    )
    first = build_dataset(config, tmp_path / "a", fonts)
    second = build_dataset(config, tmp_path / "b", fonts)
    assert first["dataset_hash"] == second["dataset_hash"]
    rows = load_split(tmp_path / "a", "train")
    assert all(row["meta"]["variety"] == "v3" and "totals_place" in row["meta"] for row in rows)
    holdout = load_split(tmp_path / "a", "test_layout_holdout")
    assert all("variety" not in row["meta"] for row in holdout)
