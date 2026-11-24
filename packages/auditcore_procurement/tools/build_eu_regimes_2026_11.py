"""Build ``procurement.hvtg`` 2026.11.1 from the released 2026.10.1 (schema 3).

Changes against 2026.10.1, nothing else:

- The thresholds for social and other specific services (Art. 4 point (d)
  Directive 2014/24/EU: 750 000 EUR; Art. 15 point (c) Directive 2014/25/EU:
  1 000 000 EUR) are fixed in the directives and are not revised every two
  years (Art. 6(1) and Art. 17(1) name only the other points; Art. 6(3) and
  Art. 17(2) second subparagraph only convert them into national currencies).
  Their rows therefore run from 18.04.2016 without end date (``valid_to: null``
  with ``open_end``) instead of ending on 31.12.2027.
- The note on central government authorities quotes § 106 Abs. 2 Nr. 1 GWB in
  the version in force from 01.07.2026 and names the earlier version.
- ``not_entered`` and ``legal_status`` say so.

The review provisions are quoted from the same Cellar documents whose SHA-256
the profile already holds (``sources[...]["retrieved_sha256"]``). Amending acts
were listed again on 23.11.2026 from the Cellar SPARQL endpoint
(``cdm:resource_legal_amends_resource_legal``): Directive 2014/24/EU is also
amended by Directive (EU) 2026/806 (CELEX 32026L0806, SHA-256 ``e51485e6…``),
which only adds point (k) to Art. 10 and leaves Art. 4 and Art. 6 untouched;
Directive 2014/25/EU has no amending act beyond the delegated regulations.

    python tools/build_eu_regimes_2026_11.py \\
        src/auditcore_procurement/profiles/procurement.hvtg-2026.10.1.json \\
        src/auditcore_procurement/profiles [--official <dir with <CELEX>.xhtml>]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

VERSION = "2026.11.1"
CHECKED_ON = "2026-11-23"
D24, D25 = "32014L0024", "32014L0025"

#: CELEX -> (review provision, verbatim fragments of the official wording).
REVIEW: dict[str, tuple[str, tuple[str, ...]]] = {
    D24: (
        "Art. 6 Abs. 1 Unterabs. 1 und Abs. 3 Unterabs. 2 RL 2014/24/EU",
        (
            "(1) Die Kommission überprüft die in Artikel 4 Buchstaben a, b und c genannten "
            "Schwellenwerte alle zwei Jahre ab dem 30. Juni 2013 auf Übereinstimmung mit dem "
            "Übereinkommen über das öffentliche Beschaffungswesen (Government Procurement "
            "Agreement, im Folgenden „GPA“) der Welthandelsorganisation und setzt sie "
            "erforderlichenfalls gemäß dem vorliegenden Artikel neu fest.",
            "Gleichzeitig legt die Kommission den Wert des in Artikel 4 Buchstabe d genannten "
            "Schwellenwerts in den nationalen Währungen der Mitgliedstaaten fest, deren "
            "Währung nicht der Euro ist.",
        ),
    ),
    D25: (
        "Art. 17 Abs. 1 Unterabs. 1 und Abs. 2 Unterabs. 2 RL 2014/25/EU",
        (
            "(1) Die Kommission überprüft die in Artikel 15 Buchstaben a und b genannten "
            "Schwellenwerte alle zwei Jahre ab dem 30. Juni 2013 auf Übereinstimmung mit dem "
            "Übereinkommen über das öffentliche Beschaffungswesen (Government Procurement "
            "Agreement, im Folgenden „GPA“) der Welthandelsorganisation und setzt sie "
            "erforderlichenfalls gemäß dem vorliegenden Artikel neu fest.",
            "Gleichzeitig legt die Kommission den Wert des in Artikel 15 Buchstabe c genannten "
            "Schwellenwerts in den nationalen Währungen der Mitgliedstaaten fest, deren "
            "Währung nicht der Euro ist.",
        ),
    ),
}
AMENDMENTS = {
    D24: (
        "Cellar-Abfrage vom 23.11.2026: geändert durch 32015R2170, 32017R2365, 32019R1828, "
        "32021R1952, 32023R2495, 32025R2152 (Art. 4 Buchst. a bis c) und 32026L0806 "
        "(Richtlinie (EU) 2026/806, fügt nur Art. 10 Buchst. k an); Art. 4 Buchst. d und "
        "Art. 6 sind unverändert."
    ),
    D25: (
        "Cellar-Abfrage vom 23.11.2026: geändert durch 32015R2171, 32017R2364, 32019R1829, "
        "32021R1953, 32023R2496, 32025R2150 (Art. 15 Buchst. a und b); Art. 15 Buchst. c "
        "und Art. 17 sind unverändert."
    ),
}
OPEN_END = (
    "Fester Wert der Richtlinie ohne Enddatum: Nach {review} setzt die Kommission nur die "
    "übrigen Schwellenwerte alle zwei Jahre neu fest; für diesen Wert legt sie lediglich den "
    "Gegenwert in nationalen Währungen fest. Er gilt bis zu einer Änderung der Richtlinie "
    "(Änderungsrechtsakte geprüft am 23.11.2026)."
)
CENTRAL = {
    "de": (
        "(Fassung vom 13.10.2026) vom Bundeskanzleramt und den Bundesministerien anzuwenden.",
        "in der Fassung ab 01.07.2026 vom Bundeskanzleramt und den Bundesministerien "
        "anzuwenden; vom 18.04.2016 bis 30.06.2026 war er von allen obersten Bundesbehörden "
        "sowie allen oberen Bundesbehörden und vergleichbaren Bundeseinrichtungen anzuwenden "
        "(Abfrage je Stichtag: central_government_rule).",
    ),
    "en": (
        "(Section 106(2) no. 1 GWB as at 13 October 2026).",
        "(Section 106(2) no. 1 GWB as in force from 1 July 2026); from 18 April 2016 to "
        "30 June 2026 it applied to all supreme and higher federal authorities and comparable "
        "federal bodies (query by date: central_government_rule).",
    ),
}
STATUS = (
    "nur belegte Zeiträume sind eingetragen.",
    "nur belegte Zeiträume sind eingetragen; die festen Richtlinienwerte für soziale und "
    "andere besondere Dienstleistungen (Art. 4 Buchst. d RL 2014/24/EU, Art. 15 Buchst. c "
    "RL 2014/25/EU) gelten ab dem 18.04.2016 ohne Enddatum (Änderungsrechtsakte geprüft am "
    "23.11.2026).",
)
NOT_ENTERED = (
    (
        "Nicht eingetragen sind Zeiträume vor 2014 und ab 2028.",
        "Nicht eingetragen sind Zeiträume vor 2014 und ab 2028; ausgenommen sind die festen "
        "Richtlinienwerte für soziale und andere besondere Dienstleistungen, die nicht neu "
        "festgesetzt werden und ohne Enddatum eingetragen sind.",
    ),
    (
        "Subventionierte Aufträge (Art. 13 RL 2014/24/EU) und die Regeln zur Schätzung des "
        "Auftragswerts einschließlich der Losregelungen sind nicht abgebildet.",
        "Subventionierte Aufträge (Art. 13 RL 2014/24/EU) sind nicht abgebildet. Die Regeln "
        "zur Schätzung des Auftragswerts (§ 3 VgV) sind nicht Teil dieser Tabelle; Hinweise "
        "und die Prüfung der Ausnahme für kleine Lose (§ 3 Abs. 9 VgV) liefert das Modul "
        "auditcore_procurement.lot_rules.",
    ),
)


def _replace(text: str, old: str, new: str) -> str:
    if text.count(old) != 1:
        raise SystemExit(f"Ausgangstext nicht eindeutig gefunden: {old[:60]}…")
    return text.replace(old, new)


def _open_rows(regimes: list[dict[str, Any]]) -> None:
    for regime in regimes:
        for kind in regime["contract_types"]:
            if kind["id"] != "social_services":
                continue
            (row,) = kind["thresholds"]
            if row["valid_to"] != "2027-12-31" or row["source"] not in REVIEW:
                raise SystemExit(f"{regime['id']}: unerwartete Zeile {row}.")
            review = REVIEW[row["source"]][0]
            row["valid_to"] = None
            row["open_end"] = OPEN_END.format(review=review)


def _central_note(regimes: list[dict[str, Any]]) -> None:
    public = next(r for r in regimes if r["id"] == "public_contracts")
    kind = next(c for c in public["contract_types"] if c["id"] == "supplies_services")
    central = next(a for a in kind["authority_types"] if a["id"] == "central")
    for lang, (old, new) in CENTRAL.items():
        central["note"][lang] = _replace(central["note"][lang], old, new)


def build(base: dict[str, Any]) -> dict[str, Any]:
    """Profile 2026.11.1 from the released 2026.10.1 document."""
    document: dict[str, Any] = json.loads(json.dumps(base))
    if document.get("version") != "2026.10.1":
        raise SystemExit("Ausgangsprofil muss procurement.hvtg 2026.10.1 sein.")
    document["version"] = VERSION
    document["legal_status"] = _replace(document["legal_status"], *STATUS)
    block = document["eu_regimes"]
    block["amendments_checked_on"] = CHECKED_ON
    for old, new in NOT_ENTERED:
        block["not_entered"] = _replace(block["not_entered"], old, new)
    _open_rows(block["regimes"])
    _central_note(block["regimes"])
    for celex, (provision, fragments) in REVIEW.items():
        block["sources"][celex]["review_provision"] = provision
        block["sources"][celex]["review_quote"] = " […] ".join(fragments)
        block["sources"][celex]["amendments_checked"] = AMENDMENTS[celex]
    return document


def check_official(directory: Path, base: dict[str, Any]) -> None:
    """Fragments must stand in the retrieved document with the recorded checksum."""
    sys.path.insert(0, str(Path(__file__).parent))
    from build_eu_regimes_profile import plain_text

    for celex, (_provision, fragments) in REVIEW.items():
        raw = (directory / f"{celex}.xhtml").read_bytes()
        recorded = base["eu_regimes"]["sources"][celex]["retrieved_sha256"]
        if hashlib.sha256(raw).hexdigest() != recorded:
            raise SystemExit(f"{celex}: Prüfsumme weicht vom Profil ab.")
        text = plain_text(raw.decode("utf-8"))
        for fragment in fragments:
            if fragment not in text:
                raise SystemExit(f"{celex}: Wortlaut nicht gefunden: {fragment[:60]}…")
    print("Wortlaut und Prüfsummen bestätigt.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base_profile", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--official", type=Path, help="Verzeichnis mit <CELEX>.xhtml")
    args = parser.parse_args()
    base = json.loads(args.base_profile.read_text(encoding="utf-8"))
    if args.official:
        check_official(args.official, base)
    output = args.output_dir / f"procurement.hvtg-{VERSION}.json"
    output.write_text(json.dumps(build(base), indent=1, ensure_ascii=False) + "\n", "utf-8")
    print(output)


if __name__ == "__main__":
    main()
