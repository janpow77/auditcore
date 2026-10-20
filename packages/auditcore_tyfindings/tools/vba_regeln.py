"""Erzeugt bzw. prüft das Regelwerk ``efre.uebersicht_vue`` aus ``modAKB_Regeln.bas``.

Die Vorgaben stehen in der VBA-Funktion ``RegelnStandard`` als Zeilen
``c.Add Array(Bereich, Regel, Stichwörter, Zusatz, Ausschluss, Kennziffern,
ausgenommene Kennziffern, Wert, Bewertung, ToF, Quelle, Status)``; Texte nutzen
``#a``/``#o``/``#u``/``#A``/``#O``/``#U``/``#s`` für Umlaute und die
``Private Const``-Texte des Moduls. Die Regeln werden aus den VBA-Ausdrücken
gelesen, nicht von Hand abgeschrieben.

    python tools/vba_regeln.py /pfad/zu/modAKB_Regeln.bas --check
    python tools/vba_regeln.py /pfad/zu/modAKB_Regeln.bas --write

``--check`` vergleicht die Regeln mit dem verpackten Regelwerk; ``--write``
schreibt die Regeln und lässt die Metadaten (Kennung, Version, Status, Quelle)
unverändert.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from vba_profil import Wert, _Parser

REGELWERK = (
    Path(__file__).resolve().parents[1]
    / "src/auditcore_tyfindings/uebersichtsregeln_data/efre.uebersicht_vue-2026.10.1.json"
)
_UMLAUTE = (
    ("#a", "ä"),
    ("#o", "ö"),
    ("#u", "ü"),
    ("#A", "Ä"),
    ("#O", "Ö"),
    ("#U", "Ü"),
    ("#s", "ß"),
)
_FELDER = ("stichwoerter", "zusatz", "ausschluss", "kennziffern", "ausgenommene_kennziffern")


def _umlaute(text: str) -> str:
    for kurz, lang in _UMLAUTE:
        text = text.replace(kurz, lang)
    return text


def _konstanten(quelle: str) -> dict[str, str]:
    konstanten: dict[str, str] = {}
    for name, ausdruck in re.findall(r"^Private Const (\w+) As String = (.+)$", quelle, re.M):
        wert = _Parser(ausdruck, konstanten).ausdruck()
        if isinstance(wert, str):
            konstanten[name] = wert
    return konstanten


def _liste(text: str) -> list[str]:
    return [w.strip().lower() for w in text.split(";") if w.strip()]


def _regel(felder: list[Wert], nummern: dict[str, int]) -> dict[str, object]:
    texte = [_umlaute(f) if isinstance(f, str) else f for f in felder]
    bereich = str(texte[0])
    nummern[bereich] = nummern.get(bereich, 0) + 1
    regel: dict[str, object] = {
        "id": f"{bereich}:{nummern[bereich]}",
        "bereich": bereich,
        "name": texte[1],
    }
    for feld, wert in zip(_FELDER, texte[2:7], strict=True):
        regel[feld] = _liste(str(wert))
    wert = texte[7]
    regel["wert"] = None if bereich != "SCHWELLE" else wert
    for feld, wert in zip(("bewertung", "tof", "quelle", "status"), texte[8:12], strict=True):
        regel[feld] = str(wert)
    return regel


def regeln_aus_vba(pfad: Path) -> list[dict[str, object]]:
    """Regeln aus ``RegelnStandard`` in der Reihenfolge des Moduls."""
    quelle = pfad.read_text(encoding="utf-8")
    konstanten = _konstanten(quelle)
    rumpf = re.search(
        r"Public Function RegelnStandard\(\) As Collection\n(.*?)\nEnd Function", quelle, re.S
    )
    if rumpf is None:
        raise ValueError("RegelnStandard nicht gefunden")
    nummern: dict[str, int] = {}
    regeln = []
    for zeile in rumpf.group(1).splitlines():
        treffer = re.match(r"\s*c\.Add (Array\(.*\))\s*$", zeile)
        if treffer:
            felder = _Parser(treffer.group(1), konstanten).ausdruck()
            if not isinstance(felder, list) or len(felder) != 12:
                raise ValueError(f"Regel mit 12 Feldern erwartet: {zeile.strip()[:60]}")
            regeln.append(_regel(felder, nummern))
    return regeln


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("vba", type=Path)
    modus = parser.add_mutually_exclusive_group(required=True)
    modus.add_argument("--check", action="store_true")
    modus.add_argument("--write", action="store_true")
    argumente = parser.parse_args()
    regeln = regeln_aus_vba(argumente.vba)
    dokument = json.loads(REGELWERK.read_text(encoding="utf-8"))
    if argumente.write:
        dokument["regeln"] = regeln
        REGELWERK.write_text(
            json.dumps(dokument, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
        )
        print(f"{len(regeln)} Regeln geschrieben")
        return 0
    if dokument.get("regeln") == regeln:
        print("PASS")
        return 0
    alt = {r["id"]: r for r in dokument.get("regeln", [])}
    for regel in regeln:
        if alt.get(str(regel["id"])) != regel:
            print(f"ABWEICHUNG {regel['id']}: {regel['name']}")
    print("FAIL")
    return 1


if __name__ == "__main__":
    sys.exit(main())
