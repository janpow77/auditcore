#!/usr/bin/env python3
"""Sollwerte nach KOM für Zellen, an denen die Webfassung bewusst anders rechnet als die Vorlage.

    python3 scripts/delvo_soll.py            # schreibt test/golden-delvo/*.delvo.json
    python3 scripts/delvo_soll.py --check    # prüft, ob die Dateien aktuell sind (npm test)

Entscheidung des Inhabers vom 17.10.2026: „Es gelten die Vorgaben der KOM“
(DelVO (EU) 2023/67 und KOM-Leitfaden EGESIF_16-0014-01; docs/abweichungen.md
Nr. 16). Dieses Skript rechnet die Sollwerte unabhängig vom Rechenkern aus den
Excel-Sollwerten (test/golden), den Eingaben der Fälle und den
LibreOffice-Kontrollwerten (test/golden-delvo/lo, erzeugt mit scripts/kom_lo.py):

1. Planung bei AE > TE (Leitfaden 7.1, S. 183): Umfang mit |TE − AE|. Erster
   Zeitraum: Prüfhinweis und Umfang samt Folgegrößen aus test/golden-delvo/lo.
   Bei AE = TE ist der Umfang nicht anwendbar (Division durch null); in der
   globalen Neuberechnung bleiben die Folgegrößen offen (`others: null`).
   AE > TE in der globalen Neuberechnung rechnet die Vorlage ebenso.
2. Blatt 18, Ersetzung bei Tabelle 2 (Anhang III Tabelle 2): Genauigkeit für die
   reduzierte Grundgesamtheit, angepasst mit BV ursprünglich / BV reduziert:
   SE = SE_Methodenblatt · (N − A) / N · BV / BV_r (Gesamt-Näherung; die
   Golden-Fälle erfassen keine Lage der berührten Einheiten). Daraus obere
   Fehlergrenze (C28) und Würdigung (C30); Blatt 20 G34/G35.

Vergleiche wie in Excel nach Rundung auf 15 geltende Stellen.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent.parent
GOLDEN = PACKAGE / "test" / "golden"
TARGET = PACKAGE / "test" / "golden-delvo"

LO = TARGET / "lo"

SIZE_NOT_APPLICABLE = "✖ nicht anwendbar (Division durch null)"
ABOVE = (
    "⚠ AE > TE: Umfang mit der geplanten Genauigkeit |TE − AE| "
    "(KOM-Leitfaden EGESIF_16-0014-01, 7.1)"
)
EQUAL_RULE = "Anhang II: TE = AE (Division durch null)"
EQUAL = "✖ TE = AE: Stichprobenumfang nicht bestimmbar (Division durch null)"

# Erster Zeitraum, Blatt: (Umfang, [Faktoren in der Reihenfolge der Vorlagenformel],
# TE, AE, Prüfzelle, Fehlerquote).
FIRST = {
    "03_MUS_1Z": ("C21", ("C12", "C7", "C20"), "C16", "C18", "C19", "C17"),
    "04_MUS_1Z_S": ("C27", ("C15", "C9", "C26"), "C19", "C21", "C22", "C20"),
    "05_MUS_2Z": ("C27", ("C15", "C11", "C25"), "C19", "C21", "C22", "C20"),
    "06_MUS_2Z_S": ("C29", ("C15", "C11", "C27"), "C19", "C21", "C22", "C20"),
    "07_MUS_3Z": ("C29", ("C16", "C12", "C27"), "C20", "C22", "C23", "C21"),
    "08_SRS_1Z": ("C26", ("C13", "C17", "C25"), "C21", "C23", "C24", "C22"),
    "09_SRS_1Z_S": ("C31", ("C12", "C19", "C30"), "C23", "C25", "C26", "C24"),
    "10_SRS_2Z": ("C33", ("C21", "C17", "C31"), "C25", "C27", "C28", "C26"),
    "11_SRS_2Z_S": ("C34", ("C20", "C16", "C32"), "C24", "C26", "C27", "C25"),
    "12_SRS_3Z": ("C36", ("C23", "C19", "C34"), "C27", "C29", "C30", "C28"),
}

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


def equal(te: object, ae: object) -> bool:
    """TE = AE ≠ 0 (bei TE = AE = 0 ist die Formel der Vorlage ein Fehlerwert)."""
    return number(te) and number(ae) and r15(ae) != 0 and r15(te) == r15(ae)


def global_entry(sheet: str, case: dict) -> dict | None:
    """Globale Neuberechnung bei AE = TE: nicht anwendbar, Folgegrößen offen."""
    _, recalculations = GLOBAL[sheet]
    expected = case["erwartet"]
    cells = {}
    for size, tolerable, anticipated in recalculations:
        if equal(expected.get(f"{sheet}!{tolerable}"), expected.get(f"{sheet}!{anticipated}")):
            cells[size] = SIZE_NOT_APPLICABLE
    if not cells:
        return None
    return {"cells": cells, "others": None, "rule": EQUAL_RULE}


# Würdigung der Methodenblätter: (Zelle, Gesamtfehlerquote, obere Fehlergrenze, Schwelle).
ASSESSMENT = {
    "03_MUS_1Z": ("C52", "C50", "C51", "C14"),
    "04_MUS_1Z_S": ("C63", "C61", "C62", "C17"),
    "05_MUS_2Z": ("C95", "C93", "C94", "C17"),
    "06_MUS_2Z_S": ("C99", "C97", "C98", "C17"),
    "07_MUS_3Z": ("C138", "C136", "C137", "C18"),
    "08_SRS_1Z": ("C53", "C51", "C52", "C19"),
    "09_SRS_1Z_S": ("C62", "C60", "C61", "C21"),
    "10_SRS_2Z": ("C94", "C92", "C93", "C23"),
    "11_SRS_2Z_S": ("C102", "C100", "C101", "C22"),
    "12_SRS_3Z": ("C138", "C136", "C137", "C25"),
}
TEMPLATE_ASSESSMENT = (
    "✖ Gesamtfehlerquote über der Wesentlichkeitsschwelle",
    "⚠ GFQ unter, obere Fehlergrenze über der Schwelle – weitere Würdigung",
    "✔ GFQ und obere Fehlergrenze unter der Schwelle",
)


def excel_assessment(sheet: str, values: dict, cells: dict) -> None:
    """Würdigung aus LibreOffice mit der Vergleichsregel von Excel (15 Stellen) nachziehen.

    LibreOffice vergleicht mit Toleranz; an der Schwelle (Fälle „GFQ = Schwelle
    ± 3e-15“) wiche die Würdigung sonst von Excel ab (Toleranzkante).
    """
    cell, rate, upper, threshold = ASSESSMENT[sheet]
    if cell not in cells or not isinstance(cells[cell], str):
        return
    found = [cells.get(name, values.get(f"{sheet}!{name}")) for name in (rate, upper)]
    limit = values.get(f"{sheet}!{threshold}", 0.02)
    if not (all(number(value) for value in found) and number(limit)):
        return
    over_rate, over_upper = (r15(value) > r15(limit) for value in found)
    cells[cell] = TEMPLATE_ASSESSMENT[0 if over_rate else 1 if over_upper else 2]


def first_entry(sheet: str, case: dict, recalculated: dict | None) -> dict | None:
    """Erster Zeitraum: AE = TE nicht anwendbar; AE > TE Umfang mit |TE − AE| (Leitfaden 7.1)."""
    size, _, tolerable, anticipated, check, rate = FIRST[sheet]
    own = {f"{sheet}!{k}": v for k, v in case["eingaben"].items() if "!" not in k}
    values = {**own, **case["erwartet"]}
    get = lambda cell: values.get(f"{sheet}!{cell}")  # noqa: E731
    te, ae = get(tolerable), get(anticipated)
    if get(size) != "TE ≤ AE" or not number(get(rate)):
        return None
    if not (number(te) and number(ae)) or r15(te) == 0:
        return None
    if r15(te) == r15(ae):
        return {"cells": {size: SIZE_NOT_APPLICABLE, check: EQUAL}, "rule": EQUAL_RULE}
    cells = {check: ABOVE, **(recalculated or {})}
    excel_assessment(sheet, values, cells)
    return {"cells": cells, "rule": "KOM-Leitfaden 7.1: AE > TE, Umfang mit |TE − AE|"}


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
    """Blatt 18 und 20: Das Verfahren rechnet global mit AE = TE und liefert keine Werte."""
    if method not in GLOBAL:
        return None
    approach = case["eingaben"].get(f"{method}!{GLOBAL[method][0]}")
    if not (isinstance(approach, str) and approach.lower().startswith("global")):
        return None
    for te, ae in method_margins(method, case["eingaben"]):
        if equal(te, ae):
            return {
                "cells": {},
                "others": None,
                "rule": f"Anhang II: TE = AE im Verfahren {method}",
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
        inputs = case["eingaben"]
        threshold = inputs.get("C29", inputs.get("18_GFQ_AnhIII!C29", 0.02))
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


def recalculated(path: Path) -> dict[int, dict]:
    """LibreOffice-Kontrollwerte (scripts/kom_lo.py) je Position, nur Zellen des eigenen Blatts."""
    sheet = path.name.split(".")[0]
    source = LO / path.name.replace(".golden.json", ".json")
    if not source.exists():
        return {}
    found = json.loads(source.read_text(encoding="utf-8"))
    own = f"{sheet}!"
    return {
        entry["position"]: {
            key[len(own) :]: value for key, value in entry["cells"].items() if key.startswith(own)
        }
        for entry in found
    }


def merge(*found: dict | None) -> dict | None:
    """Einträge eines Falls zusammenführen; die Regeln werden verbunden."""
    present = [entry for entry in found if entry]
    if not present:
        return None
    cells: dict = {}
    for entry in present:
        cells.update(entry["cells"])
    merged: dict = {"cells": cells, "rule": "; ".join(entry["rule"] for entry in present)}
    if any("others" in entry for entry in present):
        merged["others"] = None
    return merged


def lo_entry(cells: dict | None) -> dict | None:
    return {"cells": cells, "rule": "KOM-Leitfaden 7.1: AE > TE im Verfahren"} if cells else None


def case_entry(sheet: str, case: dict, lo: dict | None) -> dict | None:
    if sheet in FIRST:
        first = first_entry(sheet, case, lo)
        return merge(first, global_entry(sheet, case) if sheet in GLOBAL else None)
    if sheet == "18_GFQ_AnhIII":
        method = case["eingaben"].get("C4")
        return merge(lo_entry(lo), method_entry(case, method), replacement_entry(case))
    if sheet == "20_Druck_KOM":
        method = case["eingaben"].get("18_GFQ_AnhIII!C4")
        return merge(lo_entry(lo), method_entry(case, method), report_entry(case))
    return None


def entries(path: Path) -> list[dict]:
    sheet = path.name.split(".")[0]
    controls = recalculated(path)
    result = []
    for position, case in enumerate(json.loads(path.read_text(encoding="utf-8"))):
        entry = case_entry(sheet, case, controls.get(position))
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
