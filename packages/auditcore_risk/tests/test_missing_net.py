"""riskanalysis.year_bound 2026.09.5: Quellen ohne Nettobetrag (Nutzerentscheidung 24.09.2026).

„Nettodaten sollen nur im Code vorgesehen sein“: Fehlt die Spalte ``nettobetrag``
oder ist der Wert eines Belegs leer, sind RF02 und RF08 je Beleg unbestimmt mit
der Begründung „Nettobetrag fehlt in der Quelle“ – kein Abbruch, kein
Ersatzbetrag 0 und kein Rückfall auf brutto (K2). RF08 bleibt ``False``, wo der
Betrag nicht entscheidet. Liegt der Nettobetrag vor, rechnet 2026.09.5 exakt wie
2026.09.4; 2026.09.4 selbst bleibt unverändert (Replay).
"""

from __future__ import annotations

import json
import math
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from auditcore_risk import InputError, ProfileError, evaluate, load_profile, profile_from_dict
from auditcore_risk.frame import compute_red_flags, red_flag_summary

DATA = Path(__file__).parents[1] / "src" / "auditcore_risk" / "profile_data"
OLD = load_profile("riskanalysis.year_bound", "2026.09.4")
NEW = load_profile("riskanalysis.year_bound", "2026.09.5")
REASON = "Nettobetrag fehlt in der Quelle"


def row(**kw: Any) -> dict[str, Any]:
    base = {
        "bruttobetrag": 29_750.0,
        "nettobetrag": 25_000.0,
        "Name": "Stadtwerke Beispielstadt",
        "zahlungsempfaenger": "Muster Bau GmbH",
        "vergabenummer": "",
        "kostenart_auswertung_bezeichnung": "Bauleistungen",
        "rechnungsdatum_dt": date(2025, 5, 1),
        "antrag": 1,
        "Gruppennummer": 1,
    }
    base.update(kw)
    return base


def rows() -> list[dict[str, Any]]:
    return [
        # RF02 (24.000 € netto knapp unter 25.000 €), ohne Vergabekennung
        row(bruttobetrag=28_560.0, nettobetrag=24_000.0),
        # RF08: 40.000 € netto, Platzhalter statt Vergabekennung
        row(bruttobetrag=47_600.0, nettobetrag=40_000.0, vergabenummer="0=ni"),
        # echte Vergabekennung
        row(bruttobetrag=47_600.0, nettobetrag=40_000.0, vergabenummer="V-2025-17"),
        # nicht vergaberelevante Kostenart
        row(nettobetrag=40_000.0, kostenart_auswertung_bezeichnung="Personalkosten"),
        # glatter Bruttobetrag (RF01) und Namensgleichheit (RF09)
        row(
            bruttobetrag=5_000.0,
            nettobetrag=4_201.68,
            zahlungsempfaenger="Stadtwerke Beispielstadt",
        ),
    ]


def test_profile_changes_only_the_missing_amount_handling_of_rf02_and_rf08() -> None:
    assert NEW.status == "APPROVED"
    assert NEW.source["derived_from"] == {"profile": OLD.id, "version": OLD.version}
    assert NEW.source["decision"]["decided_on"] == "2026-09-24"
    assert NEW.source["decision"]["quote"] == "nur im Code vorgesehen sein"
    for old, new in zip(OLD.rules, NEW.rules, strict=True):
        if old.code not in ("RF02", "RF08"):
            assert old == new
            continue
        assert new.when_missing_columns == "undetermined"
        assert new.params["missing_value"] is None
        assert new.params["missing_amount_reason"] == REASON
        rest = {
            k: v
            for k, v in new.params.items()
            if k not in ("missing_value", "missing_amount_reason")
        }
        assert rest == {k: v for k, v in old.params.items() if k != "missing_value"}
        assert new.requires == old.requires == ("nettobetrag",)


def test_superseded_version_is_unchanged() -> None:
    document = json.loads((DATA / "riskanalysis.year_bound-2026.09.4.json").read_text())
    assert OLD.fingerprint == load_profile("riskanalysis.year_bound", "2026.09.4").fingerprint
    for rule in document["rules"]:
        if rule["code"] in ("RF02", "RF08"):
            assert rule["params"]["missing_value"] == 0.0
            assert rule["when_missing_columns"] == "error"
            assert "missing_amount_reason" not in rule["params"]
    # 2026.09.4 bricht bei fehlender Spalte weiter ab und setzt leere Werte auf 0
    with pytest.raises(InputError, match="nettobetrag"):
        evaluate([{k: v for k, v in r.items() if k != "nettobetrag"} for r in rows()], OLD)
    empty = evaluate([row(nettobetrag=math.nan, bruttobetrag=47_600.0)], OLD).records[0]
    assert empty.flags["RF02"] is False and empty.flags["RF08"] is False


def test_with_net_amounts_the_new_version_equals_the_old_one() -> None:
    old = evaluate(rows(), OLD)
    new = evaluate(rows(), NEW)
    assert [dict(r.flags) for r in old.records] == [dict(r.flags) for r in new.records]
    assert [r.codes for r in old.records] == [r.codes for r in new.records]
    assert [r.codes for r in new.records] == [("RF02",), ("RF08",), (), (), ("RF01", "RF09")]
    assert not any(r.undetermined for r in new.records)


def expected_rf08() -> list[bool | None]:
    # unbestimmt nur ohne echte Vergabekennung und bei vergaberelevanter Kostenart
    return [None, None, False, False, None]


def test_missing_column_leaves_rf02_rf08_undetermined_and_the_rest_unchanged() -> None:
    reference = evaluate(rows(), NEW)
    without = [{k: v for k, v in r.items() if k != "nettobetrag"} for r in rows()]
    result = evaluate(without, NEW, columns=list(without[0]))
    assert [r.flags["RF02"] for r in result.records] == [None] * 5
    assert [r.flags["RF08"] for r in result.records] == expected_rf08()
    for rec, ref in zip(result.records, reference.records, strict=True):
        assert rec.undetermined["RF02"] == REASON
        if rec.flags["RF08"] is None:
            assert rec.undetermined["RF08"] == REASON
        others = {k: v for k, v in rec.flags.items() if k not in ("RF02", "RF08")}
        assert others == {k: v for k, v in ref.flags.items() if k not in ("RF02", "RF08")}
        assert "RF02" not in rec.codes and "RF08" not in rec.codes
    assert result.records[4].flags["RF01"] is True and result.records[4].flags["RF09"] is True
    assert "RF02" not in result.skipped and "RF08" not in result.skipped
    summary = {s["code"]: s for s in result.summary}
    assert summary["RF02"]["unbestimmt"] == 5 and summary["RF08"]["unbestimmt"] == 3


def test_empty_value_is_undetermined_only_for_that_record() -> None:
    data = rows()
    data[0]["nettobetrag"] = math.nan
    data[1]["nettobetrag"] = None
    data[2]["nettobetrag"] = math.nan  # echte Vergabekennung
    data[3]["nettobetrag"] = pd.NA  # nicht vergaberelevant
    result = evaluate(data, NEW).records
    assert [r.flags["RF02"] for r in result] == [None, None, None, None, False]
    assert [r.flags["RF08"] for r in result] == [None, None, False, False, False]
    assert result[0].undetermined == {"RF02": REASON, "RF08": REASON}
    assert result[2].undetermined == {"RF02": REASON}
    assert result[4].codes == evaluate(rows(), NEW).records[4].codes
    # kein Rückfall auf brutto: brutto 47.600 € mit Platzhalter wäre sonst ein RF08-Treffer
    assert result[1].hits == ()


def test_frame_adapter_marks_undetermined_as_missing() -> None:
    frame = pd.DataFrame(rows()).drop(columns=["nettobetrag"])
    out = compute_red_flags(frame, NEW)
    assert str(out["rf02"].dtype) == "boolean" and bool(out["rf02"].isna().all())
    assert out["rf08"].isna().tolist() == [True, True, False, False, True]
    assert not any("RF02" in c or "RF08" in c for c in out["red_flag_codes"])
    assert out["rf01"].tolist() == [False, False, False, False, True]
    summary = {s["code"]: s for s in red_flag_summary(out, NEW)}
    assert summary["RF02"]["treffer"] == 0 and summary["RF08"]["treffer"] == 0
    assert summary["RF01"]["treffer"] == 1
    with_net = compute_red_flags(pd.DataFrame(rows()), NEW)
    assert with_net["rf02"].dtype == bool and with_net["rf02"].tolist()[0] is True


def _document() -> dict[str, Any]:
    data: dict[str, Any] = json.loads((DATA / "riskanalysis.year_bound-2026.09.5.json").read_text())
    return data


def _change(
    code: str, *, when: str | None = None, requires: list[str] | None = None, **params: Any
) -> dict[str, Any]:
    data = _document()
    for rule in data["rules"]:
        if rule["code"] == code:
            rule["params"].update(params)
            if when is not None:
                rule["when_missing_columns"] = when
            if requires is not None:
                rule["requires"] = requires
    return data


def test_validation_of_missing_amount_handling() -> None:
    assert profile_from_dict(_document()).fingerprint == NEW.fingerprint
    for broken in (
        _change("RF02", missing_value=0.0),  # Ersatzbetrag und Begründung zugleich
        _change("RF02", missing_amount_reason=""),
        _change("RF02", missing_amount_reason=5),
        _change("RF08", missing_value=None, missing_amount_reason=None),
        _change("RF02", requires=["nettobetrag", "rechnungsdatum_dt"]),
        _change("RF01", when="undetermined"),  # Regelart ohne missing_amount_reason
        _change("RF10", when="undetermined"),
        _change("RF01", missing_value=None, missing_amount_reason=REASON),  # Parameter unbekannt
    ):
        with pytest.raises(ProfileError):
            profile_from_dict(broken)
    # undetermined ohne Begründung ist unzulässig, auch bei einer Betragsregel
    legacy = _change("RF02", missing_value=0.0)
    for rule in legacy["rules"]:
        if rule["code"] == "RF02":
            del rule["params"]["missing_amount_reason"]
    with pytest.raises(ProfileError, match="undetermined"):
        profile_from_dict(legacy)
