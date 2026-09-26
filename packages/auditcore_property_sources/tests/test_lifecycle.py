"""Pure ZVG lifecycle functions: boundaries and input contract."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from auditcore_property_sources.zvg_lifecycle import (
    CaseState,
    close_vanished,
    mark_seen,
    reappear,
    status_for_date,
)

NOW = datetime(2026, 9, 23, 12, 0, tzinfo=UTC)


def case(
    name: str,
    status: str = "terminiert",
    days: float | None = 5.0,
    dates: tuple[int, ...] = (),
    deleted: bool = False,
) -> CaseState:
    return CaseState(
        file_number=name,
        status=status,
        last_seen_at=None if days is None else NOW - timedelta(days=days),
        deleted=deleted,
        dates=tuple(NOW + timedelta(days=d) for d in dates),
    )


def test_grace_boundary_is_strict() -> None:
    exactly, older = case("genau", days=3.0), case("älter", days=3.0 + 1e-6)
    result, closed = close_vanished([exactly, older], NOW, 3)
    assert closed == 1 and [c.status for c in result] == ["terminiert", "aufgehoben"]
    assert result[1].closed_at == NOW


def test_status_depends_on_past_and_upcoming_dates() -> None:
    cases = [
        case("vorbei", dates=(-1,)),
        case("heute", dates=(0,)),
        case("beides", dates=(-9, 2)),
        case("keiner"),
    ]
    result, closed = close_vanished(cases, NOW, 3)
    assert closed == 4
    assert [c.status for c in result] == ["abgehalten", "aufgehoben", "aufgehoben", "aufgehoben"]


def test_untouched_cases() -> None:
    cases = [
        case("nie", days=None),
        case("gelöscht", deleted=True),
        case("zu", status="abgehalten"),
        case("frisch", days=1),
    ]
    result, closed = close_vanished(cases, NOW, 3)
    assert closed == 0 and result == cases


def test_mark_seen_and_reappear() -> None:
    cases = [case("a"), case("b", status="aufgehoben")]
    assert mark_seen(cases, [], NOW) == cases
    seen = mark_seen(cases, ["b", "fremd", ""], NOW)
    assert seen[0] == cases[0] and seen[1].last_seen_at == NOW
    reopened = reappear(seen[1], NOW + timedelta(days=4), NOW)
    assert (reopened.status, reopened.closed_at) == ("terminiert", None)
    assert reappear(seen[1], None, NOW).status == "erfasst"
    assert status_for_date(NOW, NOW) == "terminiert"
    assert status_for_date(NOW - timedelta(seconds=1), NOW) == "erfasst"


@pytest.mark.parametrize(
    "build",
    [
        lambda: CaseState("x", "offen", NOW),
        lambda: CaseState("x", "erfasst", datetime(2026, 1, 1)),
        lambda: close_vanished([], NOW, -1),
        lambda: close_vanished([], NOW, True),  # type: ignore[arg-type]
        lambda: mark_seen([], [], datetime(2026, 1, 1)),
    ],
)
def test_invalid_input_is_rejected(build: object) -> None:
    with pytest.raises(ValueError):
        build()  # type: ignore[operator]
