"""Helpers taken over from the applications, against their verbatim copies (differential)."""

from __future__ import annotations

import asyncio
import os
import string
from collections.abc import Callable
from decimal import Decimal

import legacy_apps as apps
import pytest
from samples import SAMPLES, TEXTS, assert_same_outcome, random_float, random_value, rng

from auditcore_common import aio, filenames
from auditcore_common.numeric import as_float, as_float_comma, share_percent

SHARES: dict[str, tuple[Callable[[int, int], float], Callable[[int, int], float]]] = {
    "audit_designer._anteil": (
        apps.audit_designer_anteil,
        lambda p, t: share_percent(p, t, digits=1, multiply_first=True),
    ),
    "flowinvoice._anteil": (apps.flowinvoice_anteil, lambda p, t: share_percent(p, t)),
    "riskanalysis._anteil": (apps.riskanalysis_anteil, lambda p, t: share_percent(p, t)),
    "regulierung._quote_pct": (apps.regulierung_quote_pct, lambda p, t: share_percent(p, t)),
}


def test_computation_order_matters_for_some_grid_pairs() -> None:
    assert round(1953 * 100.0 / 240, 1) != round(1953 / 240 * 100.0, 1)
    assert round(1633 * 100.0 / 160, 2) != round(1633 / 160 * 100.0, 2)


@pytest.mark.parametrize("variant", sorted(SHARES))
def test_share_percent_matches_every_app(variant: str) -> None:
    old, new = SHARES[variant]
    r = rng(len(variant))
    # Grid includes pairs where the two orders round differently, e.g. (1953, 240).
    grid = [(p, t) for p in range(0, 2000, 7) for t in range(1, 400)]
    pairs = [(0, 0), (1, 0), (5, -1), (1953, 240), (1633, 160), *grid] + [
        (r.randint(-50, 10**6), r.randint(-5, 10**6)) for _ in range(SAMPLES * 5)
    ]
    for part, total in pairs:
        assert_same_outcome(lambda: old(part, total), lambda: new(part, total))


FLOATS: dict[str, tuple[Callable[[object], object], Callable[[object], object]]] = {
    "audit_designer.state_aid._als_float": (apps.audit_designer_als_float, as_float),
    "audit_designer.pdb_import._float": (apps.audit_designer_pdb_float, as_float),
    "flowinvoice.modellguete._zahl": (apps.flowinvoice_zahl, as_float),
    "versteigerung.auctions._money_float": (apps.versteigerung_money_float, as_float),
    "versteigerung.data_quality._to_float": (apps.versteigerung_to_float, as_float),
    "audit_designer.state_aid._als_zahl": (
        apps.audit_designer_als_zahl,
        lambda v: as_float(v, blank_as_none=True),
    ),
    "audit-portal.read_model._to_float": (
        apps.audit_portal_to_float,
        lambda v: as_float(v, blank_as_none=True),
    ),
    "regulierung.tankerkoenig._safe_float": (
        apps.regulierung_safe_float,
        lambda v: as_float(v, blank_as_none=True, catch_type_error=False),
    ),
    "audit_designer.beneficiaries._als_float": (
        apps.audit_designer_beneficiaries_als_float,
        as_float_comma,
    ),
}
TEXT_NUMBERS = ["", " ", "1", "1,5", "1.5", " 2,0 ", "nan", "inf", "-0", "1e3", "x", "1.234,5", "٣"]


def _float_inputs(seed: int) -> list[object]:
    r = rng(seed)
    values: list[object] = [None, True, False, 0, -1, Decimal("1.10"), Decimal("NaN"), 1 + 2j]
    values += TEXT_NUMBERS + [[1], {"a": 1}, b"1", bytearray(b"2")]
    for _ in range(SAMPLES):
        choice = r.random()
        if choice < 0.4:
            values.append(random_float(r))
        elif choice < 0.7:
            values.append(r.choice(TEXT_NUMBERS) + r.choice(["", "0", " ", ","]))
        else:
            values.append(random_value(r))
    return values


@pytest.mark.parametrize("variant", sorted(FLOATS))
def test_as_float_matches_every_app(variant: str) -> None:
    old, new = FLOATS[variant]
    for value in _float_inputs(len(variant)):
        assert_same_outcome(lambda: old(value), lambda: new(value))


FILENAMES: dict[str, tuple[Callable[[str], str], Callable[[str], str]]] = {
    "audit_designer.document_comparisons._safe_filename": (
        apps.audit_designer_comparison_filename,
        filenames.unicode_filename,
    ),
    "audit_designer.jupyter._safe_filename": (
        apps.audit_designer_jupyter_filename,
        filenames.path_component,
    ),
    "audit_designer.presentation._safe_filename": (
        apps.audit_designer_presentation_filename,
        filenames.replace_reserved,
    ),
    "audit-portal.vvt_templates._safe_filename": (
        apps.audit_portal_vvt_filename,
        lambda v: filenames.underscore_slug(v, "vvt"),
    ),
    "regulierung.vollzug._safe_filename_part": (
        apps.regulierung_filename_part,
        lambda v: filenames.dashed_slug(v, "tankstelle"),
    ),
    "audit-portal.help_export.safe_filename": (
        lambda v: apps.audit_portal_help_filename(v, "pdf"),
        lambda v: filenames.export_filename(v, "pdf"),
    ),
}
PARTS = list(TEXTS) + ["/", "\\", "..", ".", "a b", "Ä-ß_", '<>:"|?*', "\x01", "\x7f", "x" * 300]
PARTS += list(string.punctuation)


@pytest.mark.parametrize("variant", sorted(FILENAMES))
def test_filenames_match_every_app(variant: str) -> None:
    old, new = FILENAMES[variant]
    r = rng(len(variant) + 1)
    names = ["", " ", ".", "..", "a/b/../c.txt", "C:\\x\\y.pdf"] + [
        "".join(r.choice(PARTS) for _ in range(r.randint(0, 8))) for _ in range(SAMPLES)
    ]
    for name in names:
        assert_same_outcome(lambda: old(name), lambda: new(name))
    if "jupyter" in variant or "comparisons" in variant:
        assert_same_outcome(lambda: old(None), lambda: new(None))  # type: ignore[arg-type]


async def _answer(value: int) -> tuple[int, asyncio.AbstractEventLoop]:
    return value, asyncio.get_running_loop()


def test_thread_loop_runner_behaves_like_flowinvoice(monkeypatch: pytest.MonkeyPatch) -> None:
    runner = aio.ThreadLoopRunner()
    old = [apps.flowinvoice_run_async(_answer(i)) for i in range(3)]
    new = [runner.run(_answer(i)) for i in range(3)]
    assert [v for v, _ in old] == [v for v, _ in new] == [0, 1, 2]
    assert len({id(loop) for _, loop in old}) == len({id(loop) for _, loop in new}) == 1
    old[0][1].close()
    new[0][1].close()
    after_close_old = apps.flowinvoice_run_async(_answer(4))
    after_close_new = runner.run(_answer(4))
    assert after_close_old[1] is not old[0][1] and after_close_new[1] is not new[0][1]
    monkeypatch.setattr(os, "getpid", lambda: -1)
    forked_old = apps.flowinvoice_run_async(_answer(5))
    forked_new = runner.run(_answer(5))
    assert forked_old[1] is not after_close_old[1] and forked_new[1] is not after_close_new[1]


def test_separate_runners_keep_separate_loops() -> None:
    first, second = aio.ThreadLoopRunner(), aio.ThreadLoopRunner()
    assert first.run(_answer(1))[1] is not second.run(_answer(1))[1]
    assert aio.run_sync(_answer(2))[0] == 2


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_run_on_current_loop_matches_designer_and_flowaudit() -> None:
    asyncio.set_event_loop(None)
    old = apps.audit_designer_run_async_in_thread(_answer(1))
    again = apps.flowaudit_run_async(_answer(2))
    new = aio.run_on_current_loop(_answer(3))
    assert old[1] is again[1] is new[1], "all reuse the thread's current loop"
    asyncio.get_event_loop().close()
    asyncio.set_event_loop(None)
    assert aio.run_on_current_loop(_answer(4))[0] == 4
