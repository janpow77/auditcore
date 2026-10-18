#!/usr/bin/env python3
"""Kontrollwerte nach KOM für den ersten Zeitraum bei AE > TE, mit LibreOffice.

    AUDITCORE_SAMPLING_TEMPLATES_DIR=… python3 scripts/kom_lo.py

Entscheidung des Inhabers vom 17.10.2026 („Es gelten die Vorgaben der KOM“,
docs/abweichungen.md Nr. 16): Bei AE > TE plant die Webfassung nach
KOM-Leitfaden EGESIF_16-0014-01 (7.1, S. 183) mit der geplanten Genauigkeit
|TE − AE|; die Vorlage zeigt „TE ≤ AE“ und keinen Umfang. Dieses Skript rechnet
den Umfang unabhängig vom Rechenkern nach (n = ROUNDUP((z·BV·σ/(TE − AE))²; 0)
in der Reihenfolge der Vorlagenformel, vor dem Aufrunden auf 15 geltende Stellen
gerundet), setzt ihn in einer Kopie der Vorlage an die Stelle der Formel und
lässt LibreOffice die Mappe neu berechnen. Abgelegt werden je Fall die Zellen,
die sich gegenüber derselben Neuberechnung ohne Eingriff ändern (so bleiben
Unterschiede zwischen LibreOffice und Excel außen vor), unter
``test/golden-delvo/lo/<Golden>.json``. ``scripts/delvo_soll.py`` liest sie;
für ``--check`` ist LibreOffice nicht nötig.

Blätter 18 und 20 übernehmen Werte aus dem Methodenblatt: Für sie liest ein
erster Lauf das Methodenblatt aus, ein zweiter rechnet die betroffenen Fälle mit
dem gesetzten Umfang. ``--auswahl DATEI`` (JSON ``{Golden-Datei: [Positionen]}``)
beschränkt den ersten Lauf für 18 und 20 auf vorausgewählte Fälle; die Auswahl
spart nur Rechenzeit. Ein übersehener Fall fiele im Golden-Abgleich als
unbegründete Abweichung auf.
"""

from __future__ import annotations

import json
import math
import shutil
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import golden_recalc  # noqa: E402
import openpyxl  # noqa: E402
from delvo_soll import FIRST, number, r15  # noqa: E402

PACKAGE = Path(__file__).resolve().parent.parent
GOLDEN = PACKAGE / "test" / "golden"
TARGET = PACKAGE / "test" / "golden-delvo" / "lo"

COMBINED = ("18_GFQ_AnhIII", "20_Druck_KOM")


def kom_size(sheet: str, values: dict[str, Any]) -> int | None:
    """Umfang nach KOM bei AE > TE (TE ≠ 0), sonst ``None``; ``values`` mit ``Blatt!Zelle``."""
    size, factors, tolerable, anticipated, _, _ = FIRST[sheet]
    get = lambda cell: values.get(f"{sheet}!{cell}")  # noqa: E731
    te, ae = get(tolerable), get(anticipated)
    if get(size) != "TE ≤ AE" or not (number(te) and number(ae)) or r15(te) == 0:
        return None
    if r15(te) >= r15(ae) or not all(number(get(cell)) for cell in factors):
        return None
    first, second, third = (float(get(cell)) for cell in factors)
    return math.ceil(r15((first * second * third / (te - ae)) ** 2))


def changed(base: dict[str, Any], kom: dict[str, Any]) -> dict[str, Any]:
    """Zellen, deren Wert sich durch den gesetzten Umfang ändert."""

    def key(value: object) -> object:
        return r15(float(value)) if number(value) else value  # type: ignore[arg-type]

    return {cell: value for cell, value in kom.items() if key(value) != key(base.get(cell))}


def defaults(template: Path) -> dict[str, Any]:
    """Vorgaben der Eingabezellen unter den Faktoren (leer wie in Excel als 0)."""
    workbook = openpyxl.load_workbook(template)
    found: dict[str, Any] = {}
    for sheet, (_, factors, *_rest) in FIRST.items():
        for cell in factors:
            value = workbook[sheet][cell].value
            if not (isinstance(value, str) and value.startswith("=")):
                found[f"{sheet}!{cell}"] = 0.0 if value is None else value
    return found


DEFAULTS: dict[str, Any] = {}


def known(case: dict[str, Any], sheet: str, computed: dict[str, Any]) -> dict[str, Any]:
    """Vorgaben, Eingaben (``Blatt!Zelle``, leer = 0 wie in Excel) und berechnete Werte."""
    inputs = {(key if "!" in key else f"{sheet}!{key}"): v for key, v in case["eingaben"].items()}
    blank = {key: 0.0 for key, value in inputs.items() if value is None and key in DEFAULTS}
    return {**DEFAULTS, **inputs, **blank, **computed}


def relevant(sheet: str, case: dict[str, Any], method: str) -> bool:
    """Blatt 18/20: immer (Werte erst aus dem ersten Lauf); Methodenblatt: nur bei AE > TE."""
    return method != sheet or kom_size(sheet, known(case, sheet, case["erwartet"])) is not None


def method_of(case: dict[str, Any], sheet: str) -> str | None:
    if sheet in FIRST:
        return sheet
    method = case["eingaben"].get("C4" if sheet == COMBINED[0] else f"{COMBINED[0]}!C4")
    return method if method in FIRST else None


def recalc(template: Path, cases: list[dict[str, Any]], sheets: list[str]) -> list[dict[str, Any]]:
    if not cases:
        return []
    return [case["erwartet"] for case in golden_recalc.build(template, cases, sheets)]


def process(template: Path, path: Path, chosen: list[int] | None = None) -> list[dict[str, Any]]:
    """Fälle einer Golden-Datei mit AE > TE im ersten Zeitraum; Blätter wie in der Golden-Datei."""
    golden = json.loads(path.read_text(encoding="utf-8"))
    sheet = path.name.split(".")[0]
    picked = [(position, case, method_of(case, sheet)) for position, case in enumerate(golden)]
    # Methodenblatt: Die Excel-Werte stehen in der Golden-Datei; nur Fälle mit AE > TE neu rechnen.
    picked = [entry for entry in picked if entry[2] and relevant(sheet, entry[1], entry[2])]
    if chosen is not None:
        picked = [entry for entry in picked if entry[0] in chosen]
    sheets = sorted({key.split("!")[0] for case in golden for key in case["erwartet"]})
    reads = sorted({*sheets, *(method for _, _, method in picked)})
    # Lauf ohne Eingriff: Werte des Methodenblatts und Vergleichsbasis.
    base = recalc(template, [{**case, "blatt": sheet} for _, case, _ in picked], reads)
    jobs = []
    for (position, case, method), values in zip(picked, base, strict=True):
        size = kom_size(method, known(case, sheet, values))
        if size is not None:
            inputs = {**case["eingaben"], f"{method}!{FIRST[method][0]}": size}
            jobs.append((position, case, values, {**case, "blatt": sheet, "eingaben": inputs}))
    kom = recalc(template, [job[3] for job in jobs], reads)
    result = []
    for (position, case, values, _), recalculated in zip(jobs, kom, strict=True):
        cells = changed(values, recalculated)
        shown = {key: value for key, value in cells.items() if key.split("!")[0] in sheets}
        result.append({"position": position, "name": case["name"], "cells": shown})
    return result


def main() -> int:
    if shutil.which("soffice") is None:
        raise SystemExit("LibreOffice (soffice) fehlt im PATH.")
    template = golden_recalc.find_template(None)
    DEFAULTS.update(defaults(template))
    arguments = sys.argv[1:]
    selection: dict[str, list[int]] = {}
    if "--auswahl" in arguments:
        index = arguments.index("--auswahl")
        selection = json.loads(Path(arguments[index + 1]).read_text(encoding="utf-8"))
        del arguments[index : index + 2]
    only = arguments
    TARGET.mkdir(parents=True, exist_ok=True)
    for path in sorted(GOLDEN.glob("*.golden.json")):
        sheet = path.name.split(".")[0]
        if sheet not in FIRST and sheet not in COMBINED or (only and path.name not in only):
            continue
        found = process(template, path, selection.get(path.name) if sheet in COMBINED else None)
        target = TARGET / path.name.replace(".golden.json", ".json")
        if found:
            text = json.dumps(found, ensure_ascii=False, indent=1) + "\n"
            target.write_text(text, encoding="utf-8")
        elif target.exists():
            target.unlink()
        print(f"{path.name}: {len(found)} Fälle", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
