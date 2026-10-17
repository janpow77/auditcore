#!/usr/bin/env python3
"""DelVO-Sollwerte für die Zellen, an denen die Webfassung bewusst nach der DelVO rechnet.

    python3 scripts/delvo_soll.py            # schreibt test/golden-delvo/*.json
    python3 scripts/delvo_soll.py --check    # prüft, ob die Dateien aktuell sind

Entscheidung des Inhabers vom 17.10.2026 (docs/abweichungen.md Nr. 16): Bei den
Abweichungen 1 und 2 des DelVO-Abgleichs rechnet die Webfassung nach der DelVO
(EU) 2023/67. Dieses Skript rechnet die Sollwerte unabhängig vom Rechenkern aus
den Excel-Sollwerten (test/golden) und den Eingaben der Fälle nach:

1. Blatt 18, Ersetzung bei Tabelle 2 (Anhang III Tabelle 2): Genauigkeit für die
   reduzierte Grundgesamtheit, angepasst mit BV ursprünglich / BV reduziert:
   SE = SE_Methodenblatt · (N − N_Art80) / N · BV / BV_r. Daraus obere
   Fehlergrenze (C28) und Würdigung (C30).
2. Globale Neuberechnung bei AE ≥ TE (Anhang II): Der Umfang ist nicht
   bestimmbar; die Zelle zeigt den Text, die Folgegrößen bleiben offen
   (`others: null` – jede weitere abweichende Zelle des Falls muss leer sein).

Vergleiche wie in Excel nach Rundung auf 15 geltende Stellen.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent.parent
GOLDEN = PACKAGE / "test" / "golden"
TARGET = PACKAGE / "test" / "golden-delvo"

GLOBAL_TEXT = (
    "✖ nicht anwendbar: der voraussichtliche Fehler muss kleiner sein "
    "als der zulässige Fehler (Anhang II)"
)

# Blatt: (Zelle des Ansatzes, [(Umfang, TE, AE), ...]) – Zellen der Vorlage.
GLOBAL = {
    "05_MUS_2Z": ("C26", [("C59", "C53", "C54")]),
    "06_MUS_2Z_S": ("C28", [("C65", "C56", "C57")]),
    "07_MUS_3Z": ("C28", [("C69", "C59", "C60"), ("C101", "C95", "C96")]),
    "10_SRS_2Z": ("C32", [("C66", "C59", "C60")]),
    "11_SRS_2Z_S": ("C33", [("C72", "C62", "C63")]),
    "12_SRS_3Z": ("C35", [("C77", "C66", "C67"), ("C109", "C102", "C103")]),
}


def r15(value: float) -> float:
    return float(f"{value:.14e}") if value else 0.0


def number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def n(value: object) -> float:
    return float(value) if number(value) else 0.0  # type: ignore[arg-type]


def global_entry(sheet: str, case: dict) -> dict | None:
    """Globale Neuberechnung mit AE ≥ TE (AE > 0; bei TE = AE = 0 ist die Formel ein Fehlerwert)."""
    _, recalculations = GLOBAL[sheet]
    expected = case["erwartet"]
    cells = {}
    for size, tolerable, anticipated in recalculations:
        te, ae = expected.get(f"{sheet}!{tolerable}"), expected.get(f"{sheet}!{anticipated}")
        if number(te) and number(ae) and r15(ae) != 0 and r15(te) <= r15(ae):
            cells[size] = GLOBAL_TEXT
    return {"cells": cells, "others": None, "rule": "Anhang II: AE ≥ TE"} if cells else None


def row_total(get, row: int) -> float | None:
    """Summe einer Schichtzeile (Spalten D–J, AA–AM); ohne Zahl keine Summe."""
    values = [get(f"{column}{row}") for column in [*"DEFGHIJ", *(f"A{c}" for c in "ABCDEFGHIJKLM")]]
    found = [float(value) for value in values if number(value)]
    return sum(found) if found else None


def method_margins(method: str, inputs: dict) -> list[tuple[float | None, float | None]]:
    """TE und AE der globalen Neuberechnung(en) eines Methodenblatts, aus seinen Eingaben."""
    get = lambda cell: inputs.get(f"{method}!{cell}")  # noqa: E731

    def total(*cells: object) -> float | None:
        return sum(float(v) for v in cells) if all(number(v) for v in cells) else None

    def rate(*cells: str) -> object:
        return next((get(cell) for cell in cells if number(get(cell))), None)

    def pair(threshold: str, book_value: float | None, anticipated: object) -> tuple:
        if book_value is None or not number(get(threshold)) or not number(anticipated):
            return (None, None)
        return (get(threshold) * book_value, anticipated * book_value)

    if method == "05_MUS_2Z":
        return [pair("C17", total(get("C7"), get("C48")), rate("C51", "C20"))]
    if method == "06_MUS_2Z_S":
        return [pair("C17", total(row_total(get, 8), row_total(get, 51)), rate("C54", "C20"))]
    if method == "07_MUS_3Z":
        first = rate("C57", "C21")
        return [
            pair("C18", total(get("C7"), get("C51"), get("C53")), first),
            pair("C18", total(get("C7"), get("C51"), get("C90")), rate("C93") or first),
        ]
    if method == "10_SRS_2Z":
        return [pair("C23", total(get("C7"), get("C49")), rate("C57", "C26"))]
    if method == "11_SRS_2Z_S":
        book_value = total(row_total(get, 12), row_total(get, 58))
        book_value = None if book_value is None else book_value + n(get("C7")) + n(get("C53"))
        return [pair("C22", book_value, rate("C60", "C25"))]
    if method == "12_SRS_3Z":
        first = rate("C64", "C28")
        return [
            pair("C25", total(get("C7"), get("C53"), get("C60")), first),
            pair("C25", total(get("C7"), get("C53"), get("C92")), rate("C100") or first),
        ]
    return []


def method_entry(case: dict, method: str | None) -> dict | None:
    """Blatt 18 und 20: Das Verfahren rechnet global mit AE ≥ TE und liefert keine Werte."""
    if method not in GLOBAL:
        return None
    approach = case["eingaben"].get(f"{method}!{GLOBAL[method][0]}")
    if not (isinstance(approach, str) and approach.lower().startswith("global")):
        return None
    for te, ae in method_margins(method, case["eingaben"]):
        if te is not None and ae is not None and r15(ae) != 0 and r15(te) <= r15(ae):
            return {
                "cells": {},
                "others": None,
                "rule": f"Anhang II: AE ≥ TE im Verfahren {method}",
            }
    return None


def population_units(inputs: dict) -> tuple[float | None, float]:
    """N zur Auswahl (02 C52, bei Ersetzung C38) und berührte Einheiten nach Art. 80 (C47)."""
    get = lambda cell, default=None: inputs.get(f"02_Grundgesamtheit!{cell}", default)  # noqa: E731
    # Leere Eingaben zählen wie in der Vorlage 0 (Golden-Fälle mit Lücken).
    resubmitted = str(get("C36", "Ja") or "").lower() == "nein"
    units = n(get("C24")) - n(get("C32")) + (n(get("C34")) if resubmitted else 0.0)
    return units, n(get("C42")) + n(get("C45"))


def assessment(rate: float, upper: float, threshold: float) -> str:
    if r15(rate) > r15(threshold):
        return "✖ Gesamtfehlerquote über der Signifikanzschwelle"
    if r15(upper) > r15(threshold):
        return "⚠ GFQ unter, obere Fehlergrenze über der Schwelle"
    return "✔ unter der Signifikanzschwelle"


def replacement_entry(case: dict) -> dict | None:
    e = {
        key.split("!")[1]: value
        for key, value in case["erwartet"].items()
        if key.startswith("18_GFQ_AnhIII!")
    }
    if not (
        isinstance(e.get("C15"), str)
        and e["C15"].startswith("Ersetzung")
        and str(e.get("C11") or "").startswith("Tabelle 2")
    ):
        return None
    if not number(e.get("C8")):
        return None
    units, affected = population_units(case["eingaben"])
    if units is None or not number(e.get("C18")) or not number(e.get("C14")) or units == 0:
        return {
            "cells": {"C25": None, "C28": None},
            "others": None,
            "rule": "Anhang III Tabelle 2: Angabe fehlt",
        }
    precision = e["C8"] * (units - affected) / units * e["C18"]
    cells: dict = {"C25": precision}
    if number(e.get("C24")):
        upper = (e["C24"] + precision + n(e.get("C9")) + n(e.get("C10"))) / e["C14"]
        cells["C28"] = upper
        threshold = case["eingaben"].get("C29", 0.02)
        if number(e.get("C26")) and number(threshold):
            cells["C30"] = assessment(e["C26"], upper, threshold)
    return {"cells": cells, "rule": "Anhang III Tabelle 2: Ersetzung"}


def report_entry(case: dict) -> dict | None:
    """Blatt 20: Genauigkeit G34 und obere Fehlergrenze G35 aus Blatt 18 (Ersetzung, Tabelle 2)."""
    inputs = case["eingaben"]
    method = str(inputs.get("18_GFQ_AnhIII!C4") or "")
    treatment = str(inputs.get("02_Grundgesamtheit!C49") or "")
    e = {key.split("!")[1]: value for key, value in case["erwartet"].items()}
    table2 = method and "MUS" not in method.upper() and "PPS" not in method.upper()
    if not (treatment.startswith("Ersetzung") and table2 and number(e.get("G34"))):
        return None
    units, affected = population_units(inputs)
    get = lambda cell: inputs.get(f"02_Grundgesamtheit!{cell}")  # noqa: E731
    if units is None or units == 0:
        return {"cells": {"G34": None, "G35": None}, "rule": "Anhang III Tabelle 2: Angabe fehlt"}
    resubmitted = str(get("C36") or "Ja").lower() == "nein"
    book_value = n(get("C25")) - n(get("C33")) + (n(get("C35")) if resubmitted else 0.0)
    reduced = book_value - (n(get("C43")) + n(get("C46")))
    if reduced == 0 or book_value == 0:
        return {
            "cells": {"G34": None, "G35": None},
            "rule": "Anhang III Tabelle 2: Division durch 0",
        }
    precision = e["G34"] * (units - affected) / units * book_value / reduced
    cells: dict = {"G34": precision}
    if number(e.get("G35")):
        cells["G35"] = e["G35"] + (precision - e["G34"]) / book_value
    return {"cells": cells, "rule": "Anhang III Tabelle 2: Ersetzung"}


def entries(path: Path) -> list[dict]:
    sheet = path.name.split(".")[0]
    result = []
    for position, case in enumerate(json.loads(path.read_text(encoding="utf-8"))):
        entry = (
            global_entry(sheet, case)
            if sheet in GLOBAL
            else method_entry(case, case["eingaben"].get("C4")) or replacement_entry(case)
            if sheet == "18_GFQ_AnhIII"
            else method_entry(case, case["eingaben"].get("18_GFQ_AnhIII!C4")) or report_entry(case)
            if sheet == "20_Druck_KOM"
            else None
        )
        if entry:
            result.append({"position": position, "name": case["name"], **entry})
    return result


def main() -> int:
    check = "--check" in sys.argv
    stale = []
    for path in sorted(GOLDEN.glob("*.golden.json")):
        found = entries(path)
        target = TARGET / path.name.replace(".golden.json", ".delvo.json")
        text = json.dumps(found, ensure_ascii=False, indent=1) + "\n"
        if not found:
            if target.exists():
                stale.append(target.name) if check else target.unlink()
            continue
        if check:
            if not target.exists() or target.read_text(encoding="utf-8") != text:
                stale.append(target.name)
        else:
            TARGET.mkdir(exist_ok=True)
            target.write_text(text, encoding="utf-8")
    if stale:
        print("nicht aktuell:", ", ".join(stale))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
