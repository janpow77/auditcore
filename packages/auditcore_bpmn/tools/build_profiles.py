"""Erzeugt die Förderperioden-Profile aus den amtlichen EUR-Lex-Fassungen.

Quellen sind die XHTML-Manifestationen des Amtsblatts aus dem
Publications-Office-Cellar (Inhaltsaushandlung, keine Web-Oberfläche)::

    for celex in 32021R1060 32014R0480 32013R1303; do
      for lang in deu eng; do
        curl -sSL -H 'Accept: application/xhtml+xml' -H "Accept-Language: $lang" \
          -o "$celex"_"$lang".bin "https://publications.europa.eu/resource/celex/$celex"
      done
    done
    python tools/build_profiles.py <quellordner> src/auditcore_bpmn/profiles/data

Jede Datei wird gegen den festgehaltenen SHA-256 geprüft. Übernommen werden
ausschließlich Nummern, Titel und betroffene Stellen der Kernanforderungen
(Anhang XI VO (EU) 2021/1060, Anhang IV Delegierte VO (EU) Nr. 480/2014) und
die Überschriften ausgewählter Artikel. Bewertungskriterien stehen in keinem
der beiden Rechtstexte (sie stammen aus Leitlinien der Kommission) und
bleiben deshalb leer; die Anwendung speist sie bei Bedarf ein.

Läuft mit lxml (nur Entwicklungswerkzeug, nicht Laufzeit des Pakets).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from lxml import etree

ABGERUFEN = "2026-09-25"
QUELLEN: dict[str, dict[str, Any]] = {
    "32021R1060": {
        "titel": "Verordnung (EU) 2021/1060 (Dachverordnung, CPR)",
        "norm": "Verordnung (EU) 2021/1060",
        "fundstelle": "ABl. L 231 vom 30.6.2021, S. 159",
        "eli": "http://data.europa.eu/eli/reg/2021/1060/oj",
        "sha256": {
            "deu": "d0031a9d7fd4d2e28ebc45e806331f7b2be3e4b34b76293cefbeae8242724ceb",
            "eng": "6bf81cf3ccfc5326a2095c2d40b0aef28d80a78098b2f9927ed26c692be5b8e2",
        },
    },
    "32014R0480": {
        "titel": "Delegierte Verordnung (EU) Nr. 480/2014",
        "norm": "Delegierte Verordnung (EU) Nr. 480/2014",
        "fundstelle": "ABl. L 138 vom 13.5.2014, S. 5",
        "eli": "http://data.europa.eu/eli/reg_del/2014/480/oj",
        "sha256": {
            "deu": "35c39c302dbb80fcf3b87fb1005c543486031c5f9cecb71cfffee782321f1412",
            "eng": "8235630d44b96223be2ff16537f3557209a72a59c8d5eb4df6f2d81b4dd2393c",
        },
    },
    "32013R1303": {
        "titel": "Verordnung (EU) Nr. 1303/2013 (Dachverordnung 2014-2020)",
        "norm": "Verordnung (EU) Nr. 1303/2013",
        "fundstelle": "ABl. L 347 vom 20.12.2013, S. 320",
        "eli": "http://data.europa.eu/eli/reg/2013/1303/oj",
        "sha256": {
            "deu": "89a2a7304dc47b804cda1f1f7cb22a815b0be2b3673c4a39043ec696c7b304ea",
            "eng": "2ecb388c66abf149901a1e953c47c4a0bf9c83f635ec43a2f05f27af97ff7123",
        },
    },
}

#: Häufig zitierte Artikel je Profil (Nummer; Überschrift wird aus dem Text gelesen).
ARTIKEL = {
    "32021R1060": [
        38,
        40,
        49,
        50,
        53,
        63,
        65,
        69,
        71,
        72,
        73,
        74,
        75,
        76,
        77,
        78,
        79,
        80,
        82,
        94,
        95,
        98,
        103,
        104,
    ],
    "32013R1303": [65, 71, 72, 74, 122, 123, 124, 125, 126, 127, 137, 140, 143, 144],
}

#: Anhänge, deren Überschrift als Rechtsgrundlage angeboten wird.
ANHAENGE = {"32021R1060": ["XI", "XIII"], "32013R1303": ["XIII"]}

#: Funktionstrennung (fachliche Vorgabe der Bibliothek, kein Rechtstext; je Profil änderbar).
FUNKTIONSTRENNUNG: list[dict[str, Any]] = [
    {
        "id": "FT01",
        "kind": "separate_bodies",
        "severity": "warnung",
        "a": {"markers": ["bewilligung"]},
        "b": {"markers": ["zahlung"]},
        "title": {
            "de": "Bewilligung und Auszahlung in derselben Stelle",
            "en": "Approval and payment in the same body",
        },
    },
    {
        "id": "FT02",
        "kind": "separate_bodies",
        "severity": "fehler",
        "a": {"audit_types": ["verwk"]},
        "b": {"audit_types": ["systempruefung", "vorhabenpruefung", "rechnungslegungspruefung"]},
        "title": {
            "de": "Verwaltungskontrolle und Prüfung in derselben Stelle",
            "en": "Management verification and audit in the same body",
        },
    },
    {
        "id": "FT03",
        "kind": "excluded_role",
        "severity": "fehler",
        "selection": {"audit_types": ["verwk"]},
        "roles": ["pb", "gdp"],
        "title": {
            "de": "Verwaltungskontrolle durch die Prüfbehörde",
            "en": "Management verification by the audit authority",
        },
    },
    {
        "id": "FT04",
        "kind": "excluded_role",
        "severity": "fehler",
        "selection": {"audit_types": ["systempruefung", "vorhabenpruefung", "rechnungslegungspruefung"]},
        "roles": ["vb", "zgs", "fb", "rfs", "bb", "beg"],
        "title": {
            "de": "Prüfung durch eine Stelle der Programmverwaltung",
            "en": "Audit by a programme management body",
        },
    },
    {
        "id": "FT05",
        "kind": "four_eyes",
        "severity": "warnung",
        "title": {
            "de": "Vier-Augen-Prinzip ohne zweite Stelle oder Rolle",
            "en": "Four-eyes principle without a second body or role",
        },
    },
]

#: Allgemeine Aliasse Lane-Name/Aufgabenpräfix → Rolle (Teilzeichenfolge, ohne Groß-/Kleinschreibung).
#: Keine Behörden- oder Programmnamen; solche Aliasse ergänzt die Anwendung.
ROLLEN_ALIASE: list[dict[str, str]] = [
    {"pattern": "Bescheinigungsbehörde", "role": "bb"},
    {"pattern": "Rechnungsführung", "role": "rfs"},
    {"pattern": "Verwaltungsbehörde", "role": "vb"},
    {"pattern": "zwischengeschaltete Stelle", "role": "zgs"},
    {"pattern": "ZGS", "role": "zgs"},
    {"pattern": "Prüfbehörde", "role": "pb"},
    {"pattern": "Gruppe von Prüfern", "role": "gdp"},
    {"pattern": "Gemeinsames Sekretariat", "role": "gs"},
    {"pattern": "Kommission", "role": "kom"},
    {"pattern": "Begleitausschuss", "role": "bga"},
    {"pattern": "Begünstigte", "role": "beg"},
    {"pattern": "Antragstell", "role": "beg"},
    {"pattern": "fachtechnische", "role": "ftd"},
    {"pattern": "Gutachter", "role": "gut"},
    {"pattern": "Sachverständig", "role": "gut"},
    {"pattern": "Expertinnen", "role": "gut"},
    {"pattern": "Gremium", "role": "gre"},
    {"pattern": "Ausschuss", "role": "gre"},
    {"pattern": "Fachreferat", "role": "fr"},
    {"pattern": "Bewilligungsstelle", "role": "fb"},
    {"pattern": "Fachbehörde", "role": "fb"},
    {"pattern": "Datenschutz", "role": "ds"},
    {"pattern": "IT-System", "role": "it"},
    {"pattern": "Fachanwendung", "role": "it"},
]

#: Vorlagen (``tools/build_templates.py``) – synthetisch, nicht aus Nutzerdiagrammen.
VORLAGEN_2021 = [
    (
        "antragsverfahren",
        "Antragsverfahren und Auswahl der Vorhaben",
        "Application procedure and selection of operations",
    ),
    (
        "verwaltungskontrolle",
        "Verwaltungsüberprüfung (VerwK) eines Auszahlungsantrags",
        "Management verification of a payment claim",
    ),
    ("zahlungsantrag", "Zahlungsantrag an die Kommission", "Payment application to the Commission"),
    ("rechnungslegung", "Rechnungslegung und Gewährpaket", "Accounts and assurance package"),
    ("unregelmaessigkeiten", "Unregelmäßigkeiten: Behandlung und Meldung", "Irregularities: treatment and reporting"),
    ("vorhabenpruefung", "Vorhabenprüfung", "Audit of operations"),
    ("systempruefung", "Systemprüfung", "System audit"),
]

ROLLEN_2021 = [
    "vb",
    "zgs",
    "rfs",
    "pb",
    "pbs",
    "kom",
    "beg",
    "bga",
    "gs",
    "gdp",
    "fb",
    "ftd",
    "gut",
    "gre",
    "fr",
    "ds",
    "it",
    "sonstige",
]
ROLLEN_2014 = [
    "vb",
    "zgs",
    "bb",
    "pb",
    "pbs",
    "kom",
    "beg",
    "bga",
    "gs",
    "gdp",
    "fb",
    "ftd",
    "gut",
    "gre",
    "fr",
    "ds",
    "it",
    "sonstige",
]
FONDS_2021 = ["efre", "esf_plus", "kf", "jtf", "emfaf", "amif", "isf", "bmvi", "interreg"]
FONDS_2014 = ["efre", "esf", "kf", "eler", "emff", "interreg"]


def load(source: Path, celex: str, lang: str) -> etree._Element:
    path = source / f"{celex}_{lang}.bin"
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != QUELLEN[celex]["sha256"][lang]:
        raise SystemExit(f"{path}: SHA-256 {digest} weicht von der festgehaltenen Fassung ab")
    parser = etree.XMLParser(resolve_entities=False, no_network=True, load_dtd=False, huge_tree=False)
    return etree.fromstring(raw, parser=parser)


def text(node: etree._Element) -> str:
    return re.sub(r"\s+", " ", "".join(node.itertext())).strip()


XH = "{http://www.w3.org/1999/xhtml}"


def annex_rows(root: etree._Element, annex: str) -> tuple[list[list[str]], list[str]]:
    """Zeilen der ersten Tabelle des Anhangs mit aufgelösten rowspan-Zellen, Fußnoten.

    Der Anhang wird über seine Überschrift gefunden (``ANHANG XI``/``ANNEX XI``);
    die ``id``-Attribute der englischen Fassung sind nicht eindeutig.
    """
    container = next(
        n
        for n in root.iter(f"{XH}div")
        if "eli-container" in (n.get("class") or "")
        and (first := n.find(f"{XH}p")) is not None
        and text(first) in (f"ANHANG {annex}", f"ANNEX {annex}")
    )
    table = next(container.iter(f"{XH}table"))
    rows: list[list[str]] = []
    carry: dict[int, tuple[str, int]] = {}
    for tr in table.iter(f"{XH}tr"):
        cells: list[str] = []
        tds = list(tr.findall(f"{XH}td"))
        column = 0
        while tds or column in carry:
            if column in carry:
                value, remaining = carry[column]
                cells.append(value)
                if remaining > 1:
                    carry[column] = (value, remaining - 1)
                else:
                    del carry[column]
                column += 1
                continue
            td = tds.pop(0)
            value = text(td)
            span = int(td.get("rowspan", "1"))
            for _ in range(int(td.get("colspan", "1"))):
                cells.append(value)
                if span > 1:
                    carry[column] = (value, span - 1)
                column += 1
        rows.append(cells)
    notes = [
        re.sub(r"^\(\s*\d+\s*\)\s*", "", text(p))
        for p in container.iter(f"{XH}p")
        if "oj-note" in (p.get("class") or "")
    ]
    return rows, notes


def kernanforderungen(source: Path, celex: str, annex: str) -> list[dict[str, Any]]:
    result: dict[int, dict[str, Any]] = {}
    for lang, key in (("deu", "de"), ("eng", "en")):
        rows, notes = annex_rows(load(source, celex, lang), annex)
        for cells in rows:
            if not cells or not re.fullmatch(r"\d+", cells[0]):
                continue
            number = int(cells[0])
            entry = result.setdefault(number, {"number": number, "title": {}, "bodies": {}, "assessment_criteria": []})
            title = cells[1].rstrip(".")
            bodies = cells[2]
            marker = re.search(r"\s*\((\d+)\)$", bodies)
            if marker:
                bodies = bodies[: marker.start()]
                entry.setdefault("footnote", {})[key] = notes[int(marker.group(1)) - 1]
            entry["title"][key] = title
            entry["bodies"][key] = bodies
            if len(cells) > 3:
                entry.setdefault("scope", {})[key] = cells[3]
    return [result[number] for number in sorted(result)]


def artikel(source: Path, celex: str) -> list[dict[str, Any]]:
    headings: dict[str, dict[int, str]] = {}
    for lang, word in (("deu", "Artikel"), ("eng", "Article")):
        root = load(source, celex, lang)
        found: dict[int, str] = {}
        current: int | None = None
        for node in root.iter(f"{XH}p"):
            css = node.get("class") or ""
            if css == "oj-ti-art":
                match = re.fullmatch(rf"{word} (\d+)", text(node))
                current = int(match.group(1)) if match else None
            elif css == "oj-sti-art" and current is not None:
                found.setdefault(current, text(node))
                current = None
        headings[lang] = found
    norm = QUELLEN[celex]["norm"]
    entries: list[dict[str, Any]] = []
    for number in ARTIKEL[celex]:
        de = headings["deu"].get(number)
        en = headings["eng"].get(number)
        if not de or not en:
            raise SystemExit(f"{celex}: Überschrift zu Artikel {number} nicht gefunden")
        entries.append(
            {
                "act": norm,
                "article": str(number),
                "short_title": {"de": de, "en": en},
                "celex": celex,
                "eli": QUELLEN[celex]["eli"],
            }
        )
    for annex in ANHAENGE.get(celex, []):
        titles = {}
        for lang, key in (("deu", "de"), ("eng", "en")):
            root = load(source, celex, lang)
            container = next(
                n
                for n in root.iter(f"{XH}div")
                if "eli-container" in (n.get("class") or "")
                and (first := n.find(f"{XH}p")) is not None
                and text(first) in (f"ANHANG {annex}", f"ANNEX {annex}")
            )
            titles[key] = re.split(r" [–—-] Arti", text(container.findall(f"{XH}p")[1]))[0]
        entries.append(
            {
                "act": norm,
                "annex": annex,
                "short_title": titles,
                "celex": celex,
                "eli": QUELLEN[celex]["eli"],
            }
        )
    return entries


def quelle(celex: str, bereich: str) -> dict[str, Any]:
    info = QUELLEN[celex]
    return {
        "celex": celex,
        "eli": info["eli"],
        "title": info["titel"],
        "publication": info["fundstelle"],
        "part": bereich,
        "retrieved": ABGERUFEN,
        "retrieval": f"https://publications.europa.eu/resource/celex/{celex} (application/xhtml+xml)",
        "sha256": info["sha256"],
    }


def profile(source: Path, periode: str) -> dict[str, Any]:
    if periode == "2021-2027":
        ka_celex, annex, fonds, rollen = "32021R1060", "XI", FONDS_2021, ROLLEN_2021
        rg_celex = "32021R1060"
        bereich = "Anhang XI Tabelle 1"
    else:
        ka_celex, annex, fonds, rollen = "32014R0480", "IV", FONDS_2014, ROLLEN_2014
        rg_celex = "32013R1303"
        bereich = "Anhang IV Tabelle 1"
    ka = kernanforderungen(source, ka_celex, annex)
    return {
        "schema": "auditcore_bpmn.profile/1",
        "id": f"foerderperiode-{periode}",
        "version": "2026.09.1",
        "title": {
            "de": f"Förderperiode {periode} (geteilte Mittelverwaltung)",
            "en": f"Programming period {periode} (shared management)",
        },
        "programming_period": periode,
        "roles": rollen,
        "funds": fonds,
        "key_requirements": {
            "source": quelle(ka_celex, bereich),
            "entries": ka,
            "assessment_criteria_note": {
                "de": "Der Rechtstext enthält keine Bewertungskriterien; sie stammen aus "
                "Leitlinien der Kommission und werden von der Anwendung eingespeist.",
                "en": "The legal text contains no assessment criteria; they stem from "
                "Commission guidance and are supplied by the application.",
            },
        },
        "role_aliases": [a for a in ROLLEN_ALIASE if a["role"] in rollen],
        "segregation_rules": FUNKTIONSTRENNUNG,
        "templates": [
            {
                "id": tid,
                "title": {"de": de, "en": en},
                "file": f"{tid}.bpmn",
                "origin": "synthetisch aus VO (EU) 2021/1060 (tools/build_templates.py), ohne Nutzerdiagramme",
            }
            for tid, de, en in (VORLAGEN_2021 if periode == "2021-2027" else [])
        ],
        "legal_bases": {
            "source": quelle(rg_celex, "Artikelüberschriften"),
            "entries": artikel(source, rg_celex),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    for periode in ("2021-2027", "2014-2020"):
        data = profile(args.source, periode)
        target = args.output / f"foerderperiode-{periode}-{data['version']}.json"
        target.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(target, len(data["key_requirements"]["entries"]), "KA")


if __name__ == "__main__":
    main()
