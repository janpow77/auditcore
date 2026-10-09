"""Generatorvariante v4: hervorgehobener Betrag, Summenfolge, Fußzeilenkennungen, Schriften."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

import pytest
from test_variety_v3 import Box, BoxCanvas, _overlap

from auditcore_invoicesynth import layout_v4, layouts
from auditcore_invoicesynth.dataset import (
    PreparedSample,
    build_dataset,
    load_split,
    prepare_samples,
)
from auditcore_invoicesynth.diagnostics import (
    DIAGNOSTIC_SETS,
    DiagnosticConfig,
    prepare_diagnostics,
)
from auditcore_invoicesynth.fonts import (
    DIAGNOSTIC_FONT_FAMILIES,
    FONT_CATALOG,
    V4_FONT_FAMILIES,
    FontSet,
)
from auditcore_invoicesynth.layout_body import table
from auditcore_invoicesynth.layouts import effective_spec, render_layout
from auditcore_invoicesynth.plan import SynthConfig, plan_dataset
from auditcore_invoicesynth.variety_v4 import HIGHLIGHT_PLACES, TOTALS_ORDERS

FAMILIES = ("DejaVu Sans", "DejaVu Serif", "Liberation Sans", "Lato", *V4_FONT_FAMILIES)
COUNTS = {"train": 500, "validation": 30, "test_synthetic": 30, "test_layout_holdout": 40}
#: Holdout-Schriften (T2, T2b, T2c) und bekannte Klone davon; nie in v4.
FORBIDDEN_FONTS = {"URW Gothic", "TeX Gyre Adventor", "C059", "DejaVu Serif"}


def _config(variety: str = "v4") -> SynthConfig:
    return SynthConfig(counts=COUNTS, variety=variety)


def _samples(variety: str = "v4", families: tuple[str, ...] = FAMILIES) -> list[PreparedSample]:
    config = _config(variety)
    return prepare_samples(config, plan_dataset(config, families))


def _train(samples: list[PreparedSample]) -> list[PreparedSample]:
    return [s for s in samples if s.spec.split == "train"]


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
    patch.setattr(layouts, "draw_highlight", _phased("highlight", layout_v4.draw_highlight))
    patch.setattr(layouts, "_footer", _phased("footer", layouts._footer))
    result = []
    try:
        for sample in _samples():
            canvas = BoxCanvas()
            render_layout(canvas, sample.invoice, sample.variant, sample.spec.layout)
            result.append((sample, canvas))
    finally:
        patch.undo()
    return result


def test_v4_shares_cover_every_new_concept() -> None:
    train = _train(_samples())
    varieties = [s.variant.variety for s in train if s.variant.variety is not None]
    assert len(varieties) == len(train)
    minimum = 0.08 * len(train)
    assert sum(v.highlight is not None for v in varieties) >= minimum
    assert sum(v.totals_order is not None for v in varieties) >= minimum
    assert sum(v.footer_ids is not None for v in varieties) >= minimum
    assert sum(s.spec.font_family in V4_FONT_FAMILIES for s in train) >= minimum
    places = Counter(v.highlight.place for v in varieties if v.highlight is not None)
    assert set(places) == set(HIGHLIGHT_PLACES)
    orders = {v.totals_order.order for v in varieties if v.totals_order is not None}
    assert orders == set(TOTALS_ORDERS)
    plain = [v for v in varieties if not (v.highlight or v.totals_order or v.footer_ids)]
    assert len(plain) >= 0.35 * len(train)


def test_v4_is_deterministic_and_keeps_v3_draws() -> None:
    first, second = _samples(), _samples()
    assert [s.variant for s in first] == [s.variant for s in second]
    v3 = _samples("v3")
    for new, old in zip(first, v3, strict=True):
        if new.spec.split == "test_layout_holdout":
            assert new.spec == old.spec and new.variant == old.variant
            continue
        assert replace(new.spec, variety="v3", font_family=old.spec.font_family) == old.spec
        assert new.variant.variety is not None and old.variant.variety is not None
        plain = replace(new.variant.variety, highlight=None, totals_order=None, footer_ids=None)
        assert plain == old.variant.variety
        assert new.variant.labels == old.variant.labels


def test_v4_fonts_exclude_holdout_fonts_and_clones() -> None:
    assert not set(V4_FONT_FAMILIES) & (FORBIDDEN_FONTS | set(DIAGNOSTIC_FONT_FAMILIES))
    for family in V4_FONT_FAMILIES:
        spec = FONT_CATALOG[family]
        for name in (*spec.regular, *spec.bold):
            assert not any(part in name for part in ("Gothic", "Adventor", "C059", "DejaVu"))
    for variety in ("v1", "v2", "v3"):
        specs = plan_dataset(_config(variety), tuple(FONT_CATALOG))
        assert not any(s.font_family in V4_FONT_FAMILIES for s in specs)
    for sample in _samples(families=tuple(FONT_CATALOG)):
        if sample.spec.split == "test_layout_holdout":
            assert sample.spec.font_family not in V4_FONT_FAMILIES
        else:
            assert sample.spec.font_family not in FORBIDDEN_FONTS | set(DIAGNOSTIC_FONT_FAMILIES)
            assert not sample.spec.layout.startswith(("holdout_", "holdout_c_"))


def test_diagnostic_sets_never_use_v4_fonts() -> None:
    config = DiagnosticConfig(count=30, sets=tuple(DIAGNOSTIC_SETS))
    for sample in prepare_diagnostics(config, tuple(FONT_CATALOG)):
        assert sample.spec.font_family not in V4_FONT_FAMILIES
        assert sample.spec.variety != "v4"


def test_v4_core_works_without_new_fonts() -> None:
    samples = _samples(families=("DejaVu Sans", "DejaVu Serif"))
    assert {s.spec.font_family for s in _train(samples)} == {"DejaVu Sans"}
    assert sum(
        s.variant.variety.highlight is not None for s in _train(samples) if s.variant.variety
    )


def test_v4_fields_equal_printed_values(rendered: list[tuple[PreparedSample, BoxCanvas]]) -> None:
    seen: Counter[str] = Counter()
    for sample, canvas in rendered:
        variety = sample.variant.variety
        printed = " ".join(canvas.texts)
        for key, value in canvas.fields.items():
            if key not in {"document_type", "currency"}:
                assert value in printed, (sample.spec.sample_id, key, value)
        assert {"total", "invoice_number", "invoice_date"} <= set(canvas.fields)
        if variety is None:
            continue
        if variety.highlight is not None:
            seen[f"highlight:{variety.highlight.inline}"] += 1
            assert variety.highlight.label in printed or f"{variety.highlight.label}:" in printed
            assert printed.count(canvas.fields["total"]) >= 2
        if variety.totals_order is not None:
            seen[f"order:{variety.totals_order.label_above}"] += 1
        if variety.footer_ids is not None and sample.invoice.bank is not None:
            seen[f"footer:{variety.footer_ids.columns}"] += 1
            assert f"{variety.footer_ids.iban_label}: {canvas.fields['iban']}" in canvas.texts
    expected = {"highlight:True", "highlight:False", "order:True", "order:False"}
    assert expected | {"footer:2", "footer:3"} <= set(seen)


def _shrunk(box: Box) -> Box:
    """Rundungsfehler zwischen aufeinanderfolgenden Zeilen nicht als Überlappung werten."""
    return (box[0] + 0.01, box[1] + 0.01, box[2] - 0.01, box[3] - 0.01)


def _boxes(canvas: BoxCanvas, *phases: str) -> list[Box]:
    return [box for phase in phases for box in canvas.boxes.get(phase, [])]


def test_v4_blocks_do_not_overlap(rendered: list[tuple[PreparedSample, BoxCanvas]]) -> None:
    checked = Counter[str]()
    for sample, canvas in rendered:
        variety = sample.variant.variety
        if variety is None:
            continue
        sample_id = sample.spec.sample_id
        others = _boxes(canvas, "head", "table", "totals", "rest", "footer")
        for box in _boxes(canvas, "highlight"):
            assert box[0] >= 15 and box[2] <= 195, (sample_id, box)
            assert not any(_overlap(box, other) for other in others), sample_id
            checked["highlight"] += 1
        if variety.totals_order is not None:
            for box in _boxes(canvas, "totals"):
                assert box[0] >= 15 and box[2] <= 195, (sample_id, box)
                assert not any(_overlap(box, o) for o in _boxes(canvas, "head", "table"))
                checked["totals"] += 1
        footer = _boxes(canvas, "footer") if variety.footer_ids is not None else []
        for number, box in enumerate(footer):
            assert box[0] >= 15 and box[2] <= 195 and box[3] < 284, (sample_id, box)
            assert not any(_overlap(_shrunk(box), o) for o in footer[number + 1 :]), sample_id
            checked["footer"] += 1
    assert min(checked["highlight"], checked["totals"], checked["footer"]) > 40, checked


def test_v4_footer_moves_identifiers_to_footer() -> None:
    for sample in _train(_samples()):
        variety = sample.variant.variety
        if variety is not None and variety.footer_ids is not None:
            spec = effective_spec(sample.spec.layout, sample.variant)
            assert (spec.bank, spec.vat_id_place) == ("footer", "footer")


def test_v4_renderers_require_v4() -> None:
    sample = _samples("v3")[0]
    with pytest.raises(ValueError, match="v4"):
        layout_v4.footer_ids(BoxCanvas(), sample.invoice, sample.variant)
    spec = layouts.LAYOUTS["kopf_links"]
    with pytest.raises(ValueError, match="v4"):
        layout_v4.totals_ordered(BoxCanvas(), sample.invoice, sample.variant, spec, 120)
    assert layout_v4.highlight_stage(sample.variant, spec) is None


@pytest.mark.slow
def test_v4_build_is_deterministic(tmp_path: Path, fonts: FontSet) -> None:
    config = SynthConfig(
        counts={"train": 10, "validation": 1, "test_synthetic": 1, "test_layout_holdout": 2},
        variety="v4",
        dpi_choices=(72,),
    )
    first = build_dataset(config, tmp_path / "a", fonts)
    second = build_dataset(config, tmp_path / "b", fonts)
    assert first["dataset_hash"] == second["dataset_hash"]
    rows = load_split(tmp_path / "a", "train")
    keys = {"totals_place", "total_highlight", "totals_order", "footer_ids"}
    assert all(row["meta"]["variety"] == "v4" and keys <= set(row["meta"]) for row in rows)
    holdout = load_split(tmp_path / "a", "test_layout_holdout")
    assert all("variety" not in row["meta"] for row in holdout)
