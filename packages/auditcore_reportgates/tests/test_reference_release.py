"""Wertegate gegen Referenztabellen und fail-closed-Freigabe."""

import pytest

from auditcore_reportgates import (
    Finding,
    GateResult,
    Table,
    Verdict,
    compare_tables,
    decide,
    normalise_label,
    release,
)

V = "2025-05-14"


def _table(headers: tuple[str, ...], *rows: tuple[object, ...], vintage: str | None = V) -> Table:
    return Table(headers, tuple(rows), vintage)


def test_gleich_nach_rundung_und_einheit() -> None:
    actual = _table(
        ("Bereich", "Anzahl", "Euro"), ("Nord", 3, 1_254_000.0), ("Summe", 3, 1_254_000.0)
    )
    expected = _table(
        ("Bereich", "Anzahl", "Mio. Euro"), ("Nord", "3", "1,3"), ("Summe", "3", "1,3")
    )
    result = compare_tables(actual, expected)
    assert result.verdict is Verdict.PASSED
    assert result.checked == 4


def test_zaehlzeile_wird_verglichen() -> None:
    actual = _table(("Merkmal", "2024"), ("Anzahl Vorhaben", 12))
    expected = _table(("Merkmal", "2024"), ("Anzahl Vorhaben", "13"))
    result = compare_tables(actual, expected)
    assert result.verdict is Verdict.FAILED
    assert result.findings[0].code == "abweichung"


def test_null_gegen_fehlwert() -> None:
    actual = _table(("Bereich", "Wert"), ("A", "0,00"), ("B", "k. A."), ("C", "–"))
    expected = _table(("Bereich", "Wert"), ("A", "k. A."), ("B", "0,00"), ("C", "k. A."))
    codes = [f.code for f in compare_tables(actual, expected).findings]
    assert codes == ["fehlend_vs_wert", "wert_fehlt"]


def test_prozent_gegen_prozentpunkte() -> None:
    actual = _table(("Bereich", "Veränderung (%)"), ("A", 2.5))
    expected = _table(("Bereich", "Veränderung (Prozentpunkte)"), ("A", "2,5"))
    result = compare_tables(actual, expected)
    assert result.findings[0].code == "einheit_unvertraeglich"


def test_zeilen_und_spalten() -> None:
    actual = _table(("Bereich", "Wert"), ("A", 1), ("Z", 9), ("B", "Text"))
    expected = _table(
        ("Bereich", "Wert", "Fehlt"), ("A", "1", "2"), ("B", "4", "x"), ("C", "1", "1")
    )
    codes = sorted(f.code for f in compare_tables(actual, expected).findings)
    assert codes == ["kein_zahlwert", "spalte_fehlt", "zeile_fehlt", "zeile_zusaetzlich"]


def test_textzellen_werden_nicht_gezaehlt() -> None:
    actual = _table(("Bereich", "Art"), ("A", "x"))
    expected = _table(("Bereich", "Art"), ("A", "x"))
    assert compare_tables(actual, expected).verdict is Verdict.NOT_RUN


def test_kurze_zeile_gilt_als_fehlwert() -> None:
    actual = _table(("Bereich", "Wert"), ("A",))
    expected = _table(("Bereich", "Wert"), ("A", "5"))
    assert compare_tables(actual, expected).findings[0].code == "wert_fehlt"


@pytest.mark.parametrize(
    ("actual_vintage", "reason"),
    [(None, "datenstand_nicht_deklariert"), ("2024", "datenstand_abweichend")],
)
def test_datenstand(actual_vintage: str | None, reason: str) -> None:
    actual = _table(("B", "W"), ("A", 2), vintage=actual_vintage)
    expected = _table(("B", "W"), ("A", "1"))
    result = compare_tables(actual, expected)
    assert result.verdict is Verdict.NOT_RUN
    assert result.reason == reason
    assert result.findings


def test_doppelte_beschriftung_in_reihenfolge() -> None:
    actual = _table(("B", "W"), ("davon", 1), ("davon", 2))
    expected = _table(("B", "W"), ("davon", "1"), ("davon", "2"))
    assert compare_tables(actual, expected).passed
    assert normalise_label("Ver\xadände-rung ") == "veränderung"


def test_decide() -> None:
    assert decide("g", 0, []).verdict is Verdict.NOT_RUN
    assert decide("g", 3, []).verdict is Verdict.PASSED
    assert decide("g", 3, [Finding("x", "y")]).verdict is Verdict.FAILED


def test_freigabe_fail_closed() -> None:
    ok = GateResult("a", Verdict.PASSED, checked=1)
    nicht = GateResult("b", Verdict.NOT_RUN, "x")
    fehler = GateResult("c", Verdict.FAILED, "x")
    assert release([ok], ["a"]).released
    assert release([ok, nicht], ["a", "b"]).verdict is Verdict.NOT_RUN
    assert release([ok, nicht, fehler], ["a", "b", "c"]).failed == ("c",)
    missing = release([ok], ["a", "d"])
    assert missing.verdict is Verdict.NOT_RUN and missing.missing == ("d",)
    with pytest.raises(ValueError):
        release([ok], [])
