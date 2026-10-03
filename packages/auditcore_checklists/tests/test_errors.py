"""Tests für Fehlerklassen und die JSON-Typumwandlung des Checklisten-Kerns."""

from __future__ import annotations

from auditcore_checklists import (
    ChecklistError,
    CycleDetectedError,
    InvalidBranchError,
    NodeNotFoundError,
    PackageFormatError,
    TreeStructureError,
)
from auditcore_checklists.errors import to_int, to_json_object, to_json_value


def test_to_json_value_wandelt_verschachtelte_strukturen() -> None:
    raw = {"betrag": 1500.5, 7: ("Beleg-1", None), "geprüft": True}
    assert to_json_value(raw) == {"betrag": 1500.5, "7": ["Beleg-1", None], "geprüft": True}


def test_to_json_value_faellt_auf_zeichenkette_zurueck() -> None:
    class Aktenzeichen:
        def __str__(self) -> str:
            return "PR-2026-0815"

    assert to_json_value(Aktenzeichen()) == "PR-2026-0815"
    assert to_json_value({1, 2}) in ("{1, 2}", "{2, 1}")


def test_to_json_object_nur_fuer_zuordnungen() -> None:
    assert to_json_object(["kein", "Objekt"]) == {}
    assert to_json_object(None) == {}
    assert to_json_object({1: ("a",)}) == {"1": ["a"]}


def test_to_int_robuste_umwandlung() -> None:
    assert to_int(4) == 4
    assert to_int("12") == 12
    assert to_int("zwölf", default=-1) == -1
    # Wahrheitswerte gelten nicht als Ganzzahl
    assert to_int(True, default=9) == 9
    assert to_int(3.7) == 0


def test_checklist_error_status_und_json() -> None:
    err = ChecklistError("VALIDATION_FAILED", "Prüfung fehlgeschlagen.", details={"feld": "titel"})
    assert err.status == 422
    assert str(err) == "[VALIDATION_FAILED] Prüfung fehlgeschlagen."
    assert err.to_json() == {
        "error": {
            "code": "VALIDATION_FAILED",
            "message": "Prüfung fehlgeschlagen.",
            "details": {"feld": "titel"},
        }
    }

    # Unbekannter Code ohne Details: Status 400, kein details-Schlüssel
    unbekannt = ChecklistError("SONSTIGES", "Unbekannter Fehler.")
    assert unbekannt.status == 400
    assert unbekannt.to_json() == {"error": {"code": "SONSTIGES", "message": "Unbekannter Fehler."}}


def test_fachliche_fehlerklassen_tragen_code_und_status() -> None:
    nf = NodeNotFoundError("q-42")
    assert nf.node_id == "q-42"
    assert nf.code == "NODE_NOT_FOUND"
    assert nf.status == 404

    cyc = CycleDetectedError("h1", "d1")
    assert isinstance(cyc, TreeStructureError)
    assert (cyc.node_id, cyc.target_parent_id) == ("h1", "d1")
    assert cyc.status == 409

    branch = InvalidBranchError("Ungültiger Zweig.")
    assert branch.code == "INVALID_BRANCH"
    assert branch.status == 400

    pkg = PackageFormatError("Prüfsumme weicht ab.", code="CHECKSUM_MISMATCH")
    assert pkg.code == "CHECKSUM_MISMATCH"
    assert pkg.status == 422
    assert PackageFormatError("Defekt.").code == "INVALID_PACKAGE"
