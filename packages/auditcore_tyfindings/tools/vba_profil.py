"""Erzeugt bzw. prüft das ToF-Profil aus dem VBA-Modul ``modAKB_ToF.bas``.

Der Katalog (``ToFEintrag``), die Kennziffertabelle (``ToFStandard``) und die
Formalregeln (``ToFFormalStandard``) werden aus den VBA-Ausdrücken gelesen
(Textliterale, ``ChrW(n)``, ``&``, ``Array(...)``), nicht von Hand abgeschrieben.

    python tools/vba_profil.py /pfad/zu/modAKB_ToF.bas --check
    python tools/vba_profil.py /pfad/zu/modAKB_ToF.bas --write

``--check`` vergleicht Katalog und Regeln mit dem verpackten Profil;
``--write`` schreibt Katalog und Regeln in das Profil und lässt die
Metadaten (Kennung, Version, Status, Quelle) unverändert.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

PROFIL = (
    Path(__file__).resolve().parents[1]
    / "src/auditcore_tyfindings/profile_data/efre.tof_2021_2027-2026.10.1.json"
)
_TOKEN = re.compile(
    r'\s*(?:(?P<text>"(?:[^"]|"")*")|(?P<zahl>\d+)|(?P<name>[A-Za-z]+)|(?P<zeichen>[(),&]))'
)

Wert = str | int | list["Wert"]


def _tokens(ausdruck: str) -> list[tuple[str, str]]:
    ergebnis: list[tuple[str, str]] = []
    position = 0
    ausdruck = ausdruck.rstrip()
    while position < len(ausdruck):
        treffer = _TOKEN.match(ausdruck, position)
        if treffer is None or treffer.lastgroup is None:
            raise ValueError(f"Unbekannter VBA-Ausdruck ab {ausdruck[position : position + 40]!r}")
        ergebnis.append((treffer.lastgroup, treffer.group(treffer.lastgroup)))
        position = treffer.end()
    return ergebnis


class _Parser:
    """Rekursiver Abstieg über ``ausdruck := term ('&' term)*``."""

    def __init__(self, ausdruck: str) -> None:
        self.tokens = _tokens(ausdruck)
        self.i = 0

    def _nimm(self, erwartet: str | None = None) -> tuple[str, str]:
        art, wert = self.tokens[self.i]
        if erwartet is not None and wert != erwartet:
            raise ValueError(f"Erwartet {erwartet!r}, gefunden {wert!r}")
        self.i += 1
        return art, wert

    def ausdruck(self) -> Wert:
        wert = self._term()
        while self.i < len(self.tokens) and self.tokens[self.i][1] == "&":
            self._nimm("&")
            rechts = self._term()
            if not isinstance(wert, str) or not isinstance(rechts, str):
                raise ValueError("& verbindet nur Texte")
            wert += rechts
        return wert

    def _term(self) -> Wert:
        art, wert = self._nimm()
        if art == "text":
            return wert[1:-1].replace('""', '"')
        if art == "zahl":
            return int(wert)
        if wert == "(":
            innen = self.ausdruck()
            self._nimm(")")
            return innen
        if wert == "ChrW":
            self._nimm("(")
            _, code = self._nimm()
            self._nimm(")")
            return chr(int(code))
        if wert == "Array":
            return self._liste()
        raise ValueError(f"Nicht unterstützt: {wert!r}")

    def _liste(self) -> list[Wert]:
        self._nimm("(")
        elemente: list[Wert] = []
        while self.tokens[self.i][1] != ")":
            elemente.append(self.ausdruck())
            if self.tokens[self.i][1] == ",":
                self._nimm(",")
        self._nimm(")")
        return elemente


def _logische_zeilen(quelle: str) -> list[str]:
    return re.sub(r" _\r?\n\s*", " ", quelle).splitlines()


def _funktionswert(zeilen: list[str], name: str) -> Wert:
    for zeile in zeilen:
        treffer = re.match(rf"\s*{name} = (.*)$", zeile)
        if treffer:
            return _Parser(treffer.group(1)).ausdruck()
    raise ValueError(f"{name} nicht gefunden")


def _katalog(zeilen: list[str]) -> list[dict[str, str]]:
    eintraege: list[dict[str, str]] = []
    for zeile in zeilen:
        treffer = re.match(r"\s*Case (\d+): ToFEintrag = (.*)$", zeile)
        if treffer:
            werte = _Parser(treffer.group(2)).ausdruck()
            assert isinstance(werte, list) and int(treffer.group(1)) == len(eintraege) + 1
            nummer, kategorie, original, kurz = (str(w) for w in werte)
            eintraege.append(
                {"nummer": nummer, "kategorie": kategorie, "original": original}
                | {"kurzbezeichnung": kurz}
            )
    return eintraege


def _regeln(kennziffer: str, text: str) -> list[dict[str, object]]:
    regeln: list[dict[str, object]] = []
    for nummer, teil in enumerate((t for t in text.split(";") if t.count("=>") == 1), start=1):
        wort, ziel = (s.strip() for s in teil.split("=>"))
        gold_plating = ziel.endswith("!GP")
        regeln.append(
            {
                "id": f"kennziffer:{kennziffer}:regel:{nummer}",
                "suchwort": wort.lower(),
                "tof": ziel.removesuffix("!GP"),
                "gold_plating": gold_plating,
            }
        )
    return regeln


def _kennziffern(wert: Wert) -> list[dict[str, object]]:
    assert isinstance(wert, list)
    tabelle: list[dict[str, object]] = []
    for zeile in wert:
        assert isinstance(zeile, list) and len(zeile) == 7
        code, tof, finanziell, mehrdeutig, regeln, gold_plating, bemerkung = zeile
        tabelle.append(
            {
                "kennziffer": code,
                "tof": tof or None,
                "finanziell": finanziell == 1,
                "mehrdeutig": mehrdeutig == 1,
                "regeln": _regeln(str(code), str(regeln)),
                "gold_plating": gold_plating == 1,
                "bemerkung": bemerkung,
            }
        )
    return tabelle


def _formal(wert: Wert) -> list[dict[str, str]]:
    assert isinstance(wert, list)
    return [
        {"id": f"formal:{i}", "suchwort": str(w[0]).lower(), "tof": str(w[1])}  # type: ignore[index]
        for i, w in enumerate(wert, start=1)
    ]


def aus_vba(pfad: Path) -> dict[str, object]:
    """Katalog, Kennziffertabelle und Formalregeln aus dem VBA-Modul."""
    zeilen = _logische_zeilen(pfad.read_text(encoding="latin-1"))
    return {
        "katalog": _katalog(zeilen),
        "kennziffern": _kennziffern(_funktionswert(zeilen, "ToFStandard")),
        "formalregeln": _formal(_funktionswert(zeilen, "ToFFormalStandard")),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("vba", type=Path)
    modus = parser.add_mutually_exclusive_group(required=True)
    modus.add_argument("--check", action="store_true")
    modus.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    teile = aus_vba(args.vba)
    profil = json.loads(PROFIL.read_text(encoding="utf-8"))
    if args.check:
        abweichend = [k for k, v in teile.items() if profil.get(k) != v]
        print("PASS" if not abweichend else f"ABWEICHUNG: {', '.join(abweichend)}")
        return 1 if abweichend else 0
    profil.update(teile)
    text = json.dumps(profil, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    PROFIL.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
