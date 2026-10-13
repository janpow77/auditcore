"""Build ``procurement.hvtg`` 2026.10.1: EU thresholds of all regimes (schema 3).

2026.10.1 keeps everything of 2026.09.3 (application rules, year table of the
prechecks) and adds the block ``eu_regimes``: public contracts (Directive
2014/24/EU), utilities (2014/25/EU), concessions (2014/23/EU) and defence and
security (2009/81/EC), each with contract types, authority types and one
threshold row per validity period.

No value is entered from memory. Every row names the official text it was read
in; ``eu_threshold_sources.json`` holds, per CELEX number, the SHA-256 of the
document retrieved from the Publications Office and the wording of its
operative articles. The build fails if a value is not part of that wording.

Retrieval (13.10.2026; eur-lex.europa.eu answers automated requests with a
challenge page, the Cellar of the Publications Office does not)::

    curl -L -H "Accept: application/xhtml+xml" -H "Accept-Language: de" \
        -o <dir>/<CELEX>.xhtml http://publications.europa.eu/resource/celex/<CELEX>

The list of amending acts per directive was taken from the Cellar SPARQL
endpoint (``cdm:resource_legal_amends_resource_legal``), not from memory.

    python tools/build_eu_regimes_profile.py --official <dir>    # refresh quotes
    python tools/build_eu_regimes_profile.py \
        src/auditcore_procurement/profiles/procurement.hvtg-2026.09.3.json \
        src/auditcore_procurement/profiles
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
from pathlib import Path
from typing import Any

VERSION = "2026.10.1"
RETRIEVED_ON = "2026-10-13"
CELLAR = "http://publications.europa.eu/resource/celex/"
SOURCES_FILE = Path(__file__).with_name("eu_threshold_sources.json")
D24, D25, D23, D81 = "32014L0024", "32014L0025", "32014L0023", "32009L0081"

#: CELEX -> (title, Official Journal, applies from); wording and checksum come
#: from ``eu_threshold_sources.json`` and are cross-checked against the title.
ACTS: dict[str, tuple[str, str, str]] = {
    "32013R1336": (
        "Verordnung (EU) Nr. 1336/2013 der Kommission vom 13. Dezember 2013",
        "ABl. L 335 vom 14.12.2013, S. 17",
        "2014-01-01",
    ),
    "32015R2170": (
        "Delegierte Verordnung (EU) 2015/2170 der Kommission vom 24. November 2015",
        "ABl. L 307 vom 25.11.2015, S. 5",
        "2016-01-01",
    ),
    "32015R2171": (
        "Delegierte Verordnung (EU) 2015/2171 der Kommission vom 24. November 2015",
        "ABl. L 307 vom 25.11.2015, S. 7",
        "2016-01-01",
    ),
    "32015R2172": (
        "Delegierte Verordnung (EU) 2015/2172 der Kommission vom 24. November 2015",
        "ABl. L 307 vom 25.11.2015, S. 9",
        "2016-01-01",
    ),
    "32015R2340": (
        "Verordnung (EU) 2015/2340 der Kommission vom 15. Dezember 2015",
        "ABl. L 330 vom 16.12.2015, S. 14",
        "2016-01-01",
    ),
    "32015R2341": (
        "Verordnung (EU) 2015/2341 der Kommission vom 15. Dezember 2015",
        "ABl. L 330 vom 16.12.2015, S. 16",
        "2016-01-01",
    ),
    "32015R2342": (
        "Verordnung (EU) 2015/2342 der Kommission vom 15. Dezember 2015",
        "ABl. L 330 vom 16.12.2015, S. 18",
        "2016-01-01",
    ),
    "32017R2364": (
        "Delegierte Verordnung (EU) 2017/2364 der Kommission vom 18. Dezember 2017",
        "ABl. L 337 vom 19.12.2017, S. 17",
        "2018-01-01",
    ),
    "32017R2365": (
        "Delegierte Verordnung (EU) 2017/2365 der Kommission vom 18. Dezember 2017",
        "ABl. L 337 vom 19.12.2017, S. 19",
        "2018-01-01",
    ),
    "32017R2366": (
        "Delegierte Verordnung (EU) 2017/2366 der Kommission vom 18. Dezember 2017",
        "ABl. L 337 vom 19.12.2017, S. 21",
        "2018-01-01",
    ),
    "32017R2367": (
        "Verordnung (EU) 2017/2367 der Kommission vom 18. Dezember 2017",
        "ABl. L 337 vom 19.12.2017, S. 22",
        "2018-01-01",
    ),
    "32019R1827": (
        "Delegierte Verordnung (EU) 2019/1827 der Kommission vom 30. Oktober 2019",
        "ABl. L 279 vom 31.10.2019, S. 23",
        "2020-01-01",
    ),
    "32019R1828": (
        "Delegierte Verordnung (EU) 2019/1828 der Kommission vom 30. Oktober 2019",
        "ABl. L 279 vom 31.10.2019, S. 25",
        "2020-01-01",
    ),
    "32019R1829": (
        "Delegierte Verordnung (EU) 2019/1829 der Kommission vom 30. Oktober 2019",
        "ABl. L 279 vom 31.10.2019, S. 27",
        "2020-01-01",
    ),
    "32019R1830": (
        "Delegierte Verordnung (EU) 2019/1830 der Kommission vom 30. Oktober 2019",
        "ABl. L 279 vom 31.10.2019, S. 29",
        "2020-01-01",
    ),
    "32021R1950": (
        "Delegierte Verordnung (EU) 2021/1950 der Kommission vom 10. November 2021",
        "ABl. L 398 vom 11.11.2021, S. 19",
        "2022-01-01",
    ),
    "32021R1951": (
        "Delegierte Verordnung (EU) 2021/1951 der Kommission vom 10. November 2021",
        "ABl. L 398 vom 11.11.2021, S. 21",
        "2022-01-01",
    ),
    "32021R1952": (
        "Delegierte Verordnung (EU) 2021/1952 der Kommission vom 10. November 2021",
        "ABl. L 398 vom 11.11.2021, S. 23",
        "2022-01-01",
    ),
    "32021R1953": (
        "Delegierte Verordnung (EU) 2021/1953 der Kommission vom 10. November 2021",
        "ABl. L 398 vom 11.11.2021, S. 25",
        "2022-01-01",
    ),
    "32023R2495": (
        "Delegierte Verordnung (EU) 2023/2495 der Kommission vom 15. November 2023",
        "ABl. L, 2023/2495, 16.11.2023",
        "2024-01-01",
    ),
    "32023R2496": (
        "Delegierte Verordnung (EU) 2023/2496 der Kommission vom 15. November 2023",
        "ABl. L, 2023/2496, 16.11.2023",
        "2024-01-01",
    ),
    "32023R2497": (
        "Delegierte Verordnung (EU) 2023/2497 der Kommission vom 15. November 2023",
        "ABl. L, 2023/2497, 16.11.2023",
        "2024-01-01",
    ),
    "32023R2510": (
        "Delegierte Verordnung (EU) 2023/2510 der Kommission vom 15. November 2023",
        "ABl. L, 2023/2510, 16.11.2023",
        "2024-01-01",
    ),
    "32025R2150": (
        "Delegierte Verordnung (EU) 2025/2150 der Kommission vom 22. Oktober 2025",
        "ABl. L, 2025/2150, 23.10.2025",
        "2026-01-01",
    ),
    "32025R2151": (
        "Delegierte Verordnung (EU) 2025/2151 der Kommission vom 22. Oktober 2025",
        "ABl. L, 2025/2151, 23.10.2025",
        "2026-01-01",
    ),
    "32025R2152": (
        "Delegierte Verordnung (EU) 2025/2152 der Kommission vom 22. Oktober 2025",
        "ABl. L, 2025/2152, 23.10.2025",
        "2026-01-01",
    ),
    "32025R2487": (
        "Delegierte Verordnung (EU) 2025/2487 der Kommission vom 2. Dezember 2025",
        "ABl. L, 2025/2487, 4.12.2025",
        "2026-01-01",
    ),
    D24: (
        "Richtlinie 2014/24/EU des Europäischen Parlaments und des Rates vom 26. Februar 2014",
        "ABl. L 94 vom 28.3.2014, S. 65",
        "2016-04-18",
    ),
    D25: (
        "Richtlinie 2014/25/EU des Europäischen Parlaments und des Rates vom 26. Februar 2014",
        "ABl. L 94 vom 28.3.2014, S. 243",
        "2016-04-18",
    ),
}
#: Directives: the quoted article (regex start, regex end); regulations: operative part.
ARTICLES = {
    D24: (r"Artikel 4 Höhe der Schwellenwerte", r" Artikel 5 Methoden"),
    D25: (r"Artikel 15 Höhe der Schwellenwerte", r" Artikel 16 Methoden"),
}
OPERATIVE = ("HAT FOLGENDE VERORDNUNG ERLASSEN:", "Diese Verordnung ist in allen ihren Teilen")

#: Validity periods; 2016 is split where the directive in force changed on 18.04.2016.
PERIODS = {
    "2014": ("2014-01-01", "2015-12-31"),
    "2016a": ("2016-01-01", "2016-04-17"),
    "2016b": ("2016-04-18", "2017-12-31"),
    "2016": ("2016-01-01", "2017-12-31"),
    "2018": ("2018-01-01", "2019-12-31"),
    "2020": ("2020-01-01", "2021-12-31"),
    "2022": ("2022-01-01", "2023-12-31"),
    "2024": ("2024-01-01", "2025-12-31"),
    "2026": ("2026-01-01", "2027-12-31"),
    "since2016": ("2016-04-18", "2027-12-31"),
}
A24 = "Artikel 1: ändert Art. 4 Buchst. {} RL 2014/24/EU"
A18_2013 = "Artikel 2: ändert Art. 7 Buchst. {} RL 2004/18/EG"
A18_2015 = "Artikel 1: ändert Art. 7 Buchst. {} RL 2004/18/EG"
A25 = "Artikel 1: ändert Art. 15 Buchst. {} RL 2014/25/EU"
A17 = "Artikel 1: ändert Art. 16 Buchst. {} RL 2004/17/EG"
A23 = "Artikel 1: ändert Art. 8 Abs. 1 RL 2014/23/EU"
A81 = "Artikel 1: ändert Art. 8 Buchst. {} RL 2009/81/EG"
A81_2013 = "Artikel 3: ändert Art. 8 Buchst. {} RL 2009/81/EG"
UNCHANGED = "{} (Ursprungsfassung; von keiner Änderungsverordnung berührt)"


def _public(old: str, new: str, values: tuple[int, ...]) -> list[tuple[str, int, str, str]]:
    """Rows of Art. 7 letter ``old`` (2004/18/EC) and Art. 4 letter ``new`` (2014/24/EU)."""
    regs = ("32017R2365", "32019R1828", "32021R1952", "32023R2495", "32025R2152")
    return [
        ("2014", values[0], "32013R1336", A18_2013.format(old)),
        ("2016a", values[1], "32015R2342", A18_2015.format(old)),
        ("2016b", values[1], "32015R2170", A24.format(new)),
        *[
            (period, value, celex, A24.format(new))
            for period, value, celex in zip(
                ("2018", "2020", "2022", "2024", "2026"), values[2:], regs, strict=True
            )
        ],
    ]


def _utilities(letter: str, values: tuple[int, ...]) -> list[tuple[str, int, str, str]]:
    """Rows of Art. 16 (2004/17/EC) and Art. 15 (2014/25/EU), same letter in both."""
    regs = ("32017R2364", "32019R1829", "32021R1953", "32023R2496", "32025R2150")
    return [
        ("2014", values[0], "32013R1336", A17.format(letter)),
        ("2016a", values[1], "32015R2341", A17.format(letter)),
        ("2016b", values[1], "32015R2171", A25.format(letter)),
        *[
            (period, value, celex, A25.format(letter))
            for period, value, celex in zip(
                ("2018", "2020", "2022", "2024", "2026"), values[2:], regs, strict=True
            )
        ],
    ]


def _defence(letter: str, values: tuple[int, ...]) -> list[tuple[str, int, str, str]]:
    """Rows of Art. 8 Directive 2009/81/EC (in force throughout, no change of directive)."""
    regs = ("32015R2340", "32017R2367", "32019R1830", "32021R1950", "32023R2510", "32025R2487")
    return [
        ("2014", values[0], "32013R1336", A81_2013.format(letter)),
        *[
            (period, value, celex, A81.format(letter))
            for period, value, celex in zip(
                ("2016", "2018", "2020", "2022", "2024", "2026"), values[1:], regs, strict=True
            )
        ],
    ]


WORKS = (5186000, 5225000, 5548000, 5350000, 5382000, 5538000, 5404000)
UTILITIES_SUPPLY = (414000, 418000, 443000, 428000, 431000, 443000, 432000)
CONCESSIONS = [
    ("2016b", 5225000, "32015R2172", A23),
    ("2018", 5548000, "32017R2366", A23),
    ("2020", 5350000, "32019R1827", A23),
    ("2022", 5382000, "32021R1951", A23),
    ("2024", 5538000, "32023R2497", A23),
    ("2026", 5404000, "32025R2151", A23),
]
TRANSITION_NOTE = {
    "de": (
        "Bis 17.04.2016 galt die Richtlinie {old} (aufgehoben zum 18.04.2016 durch "
        "Art. {art} der Richtlinie {new}); die Werte bis dahin stammen aus Art. {old_art} "
        "dieser Richtlinie. Ab 01.01.2016 setzen die Änderungsverordnungen zu beiden "
        "Richtlinien dieselben Werte fest."
    ),
    "en": (
        "Until 17 April 2016 Directive {old_en} applied (repealed with effect from "
        "18 April 2016 by Article {art} of Directive {new}); the values up to that date "
        "are those of Article {old_art} of that Directive. From 1 January 2016 the "
        "amending regulations set the same values in both Directives."
    ),
}


def _note(old: str, old_en: str, new: str, art: int, old_art: int) -> dict[str, str]:
    fields = {"old": old, "old_en": old_en, "new": new, "art": art, "old_art": old_art}
    return {lang: text.format(**fields) for lang, text in TRANSITION_NOTE.items()}


def _rows(spec: list[tuple[str, int, str, str]]) -> list[dict[str, Any]]:
    return [
        {
            "valid_from": PERIODS[period][0],
            "valid_to": PERIODS[period][1],
            "value": value,
            "source": celex,
            "provision": provision,
        }
        for period, value, celex, provision in spec
    ]


def _series(
    ident: str,
    de: str,
    en: str,
    legal_basis: str,
    spec: list[tuple[str, int, str, str]],
    note: dict[str, str] | None = None,
) -> dict[str, Any]:
    series: dict[str, Any] = {
        "id": ident,
        "label": {"de": de, "en": en},
        "legal_basis": legal_basis,
    }
    if note:
        series["note"] = note
    return {**series, "thresholds": _rows(spec)}


def regimes() -> list[dict[str, Any]]:
    """The four regimes with labels in the terms of the directives."""
    return [
        _public_contracts(),
        _utilities_regime(),
        _concessions_regime(),
        _defence_regime(),
    ]


def _public_contracts() -> dict[str, Any]:
    central_note = {
        "de": (
            "Bei Lieferaufträgen öffentlicher Auftraggeber im Verteidigungsbereich gilt "
            "dieser Schwellenwert nur für Waren nach Anhang III; für andere Waren gilt der "
            "Schwellenwert der subzentralen öffentlichen Auftraggeber (Art. 4 Buchst. b und c "
            "RL 2014/24/EU). Der Wert gilt auch für Wettbewerbe dieser Behörden. In "
            "Deutschland ist er nach § 106 Abs. 2 Nr. 1 GWB (Fassung vom 13.10.2026) vom "
            "Bundeskanzleramt und den Bundesministerien anzuwenden."
        ),
        "en": (
            "For supply contracts awarded by contracting authorities operating in the field "
            "of defence this threshold applies only to products covered by Annex III; for "
            "other products the threshold for sub-central contracting authorities applies "
            "(Article 4(b) and (c) of Directive 2014/24/EU). The value also applies to "
            "design contests organised by these authorities. In Germany it is applied by "
            "the Federal Chancellery and the federal ministries (Section 106(2) no. 1 GWB "
            "as at 13 October 2026)."
        ),
    }
    return {
        "id": "public_contracts",
        "directive": "Richtlinie 2014/24/EU",
        "celex": D24,
        "label": {
            "de": "Öffentliche Aufträge (Richtlinie 2014/24/EU)",
            "en": "Public contracts (Directive 2014/24/EU)",
        },
        "buyer": {"de": "öffentliche Auftraggeber", "en": "contracting authorities"},
        "legal_basis": (
            "Art. 4 Richtlinie 2014/24/EU (ab 18.04.2016) bzw. Art. 7 Richtlinie 2004/18/EG "
            "(bis 17.04.2016) in der jeweils durch (Delegierte) Verordnung der Kommission "
            "geänderten Fassung"
        ),
        "national_reference": "§ 106 Abs. 2 Nr. 1 GWB",
        "note": _note("2004/18/EG", "2004/18/EC", "2014/24/EU", 91, 7),
        "contract_types": [
            _series(
                "works",
                "Öffentliche Bauaufträge",
                "Public works contracts",
                "Art. 4 Buchst. a RL 2014/24/EU; bis 17.04.2016 Art. 7 Buchst. c RL 2004/18/EG",
                _public("c", "a", WORKS),
            ),
            {
                "id": "supplies_services",
                "label": {
                    "de": "Öffentliche Liefer- und Dienstleistungsaufträge",
                    "en": "Public supply and service contracts",
                },
                "legal_basis": (
                    "Art. 4 Buchst. b und c RL 2014/24/EU; bis 17.04.2016 Art. 7 Buchst. a "
                    "und b RL 2004/18/EG"
                ),
                "authority_types": [
                    _series(
                        "central",
                        "zentrale Regierungsbehörden",
                        "central government authorities",
                        "Art. 4 Buchst. b RL 2014/24/EU; bis 17.04.2016 Art. 7 Buchst. a "
                        "RL 2004/18/EG",
                        _public("a", "b", (134000, 135000, 144000, 139000, 140000, 143000, 140000)),
                        central_note,
                    ),
                    _series(
                        "sub_central",
                        "subzentrale öffentliche Auftraggeber",
                        "sub-central contracting authorities",
                        "Art. 4 Buchst. c RL 2014/24/EU; bis 17.04.2016 Art. 7 Buchst. b "
                        "RL 2004/18/EG",
                        _public("b", "c", (207000, 209000, 221000, 214000, 215000, 221000, 216000)),
                    ),
                ],
            },
            _series(
                "social_services",
                "Soziale und andere besondere Dienstleistungen (Anhang XIV)",
                "Social and other specific services (Annex XIV)",
                "Art. 4 Buchst. d RL 2014/24/EU",
                [("since2016", 750000, D24, UNCHANGED.format("Artikel 4 Buchst. d"))],
            ),
        ],
    }


def _utilities_regime() -> dict[str, Any]:
    return {
        "id": "utilities",
        "directive": "Richtlinie 2014/25/EU",
        "celex": D25,
        "label": {
            "de": "Sektorenaufträge (Richtlinie 2014/25/EU)",
            "en": "Utilities contracts (Directive 2014/25/EU)",
        },
        "buyer": {
            "de": (
                "Auftraggeber im Bereich der Wasser-, Energie- und Verkehrsversorgung sowie "
                "der Postdienste (Sektorenauftraggeber)"
            ),
            "en": (
                "contracting entities operating in the water, energy, transport and postal "
                "services sectors"
            ),
        },
        "legal_basis": (
            "Art. 15 Richtlinie 2014/25/EU (ab 18.04.2016) bzw. Art. 16 Richtlinie 2004/17/EG "
            "(bis 17.04.2016) in der jeweils durch (Delegierte) Verordnung der Kommission "
            "geänderten Fassung"
        ),
        "national_reference": "§ 106 Abs. 2 Nr. 2 GWB",
        "note": _note("2004/17/EG", "2004/17/EC", "2014/25/EU", 107, 16),
        "contract_types": [
            _series(
                "works",
                "Bauaufträge",
                "Works contracts",
                "Art. 15 Buchst. b RL 2014/25/EU; bis 17.04.2016 Art. 16 Buchst. b RL 2004/17/EG",
                _utilities("b", WORKS),
            ),
            _series(
                "supplies_services",
                "Liefer- und Dienstleistungsaufträge",
                "Supply and service contracts",
                "Art. 15 Buchst. a RL 2014/25/EU; bis 17.04.2016 Art. 16 Buchst. a RL 2004/17/EG",
                _utilities("a", UTILITIES_SUPPLY),
            ),
            _series(
                "social_services",
                "Soziale und andere besondere Dienstleistungen (Anhang XVII)",
                "Social and other specific services (Annex XVII)",
                "Art. 15 Buchst. c RL 2014/25/EU",
                [("since2016", 1000000, D25, UNCHANGED.format("Artikel 15 Buchst. c"))],
            ),
        ],
    }


def _concessions_regime() -> dict[str, Any]:
    return {
        "id": "concessions",
        "directive": "Richtlinie 2014/23/EU",
        "celex": D23,
        "label": {
            "de": "Konzessionen (Richtlinie 2014/23/EU)",
            "en": "Concessions (Directive 2014/23/EU)",
        },
        "buyer": {
            "de": "Konzessionsgeber (öffentliche Auftraggeber und Auftraggeber)",
            "en": "contracting authorities and contracting entities",
        },
        "legal_basis": (
            "Art. 8 Abs. 1 Richtlinie 2014/23/EU in der jeweils durch Delegierte Verordnung "
            "der Kommission geänderten Fassung"
        ),
        "national_reference": "§ 106 Abs. 2 Nr. 4 GWB",
        "note": {
            "de": (
                "Eingetragen ab dem Ablauf der Umsetzungsfrist am 18.04.2016 (Art. 51 Abs. 1 "
                "RL 2014/23/EU). Der Schwellenwert bezieht sich auf den Vertragswert der "
                "Konzession (geschätzter Gesamtumsatz ohne MwSt., Art. 8 Abs. 2)."
            ),
            "en": (
                "Entered from the end of the transposition period on 18 April 2016 "
                "(Article 51(1) of Directive 2014/23/EU). The threshold refers to the value "
                "of the concession (estimated total turnover net of VAT, Article 8(2))."
            ),
        },
        "contract_types": [
            _series(
                "concession",
                "Bau- und Dienstleistungskonzessionen",
                "Works and services concessions",
                "Art. 8 Abs. 1 RL 2014/23/EU",
                CONCESSIONS,
            ),
        ],
    }


def _defence_regime() -> dict[str, Any]:
    return {
        "id": "defence",
        "directive": "Richtlinie 2009/81/EG",
        "celex": D81,
        "label": {
            "de": "Aufträge in den Bereichen Verteidigung und Sicherheit (Richtlinie 2009/81/EG)",
            "en": "Contracts in the fields of defence and security (Directive 2009/81/EC)",
        },
        "buyer": {
            "de": "öffentliche Auftraggeber und Auftraggeber",
            "en": "contracting authorities and contracting entities",
        },
        "legal_basis": (
            "Art. 8 Richtlinie 2009/81/EG in der jeweils durch (Delegierte) Verordnung der "
            "Kommission geänderten Fassung"
        ),
        "national_reference": "§ 106 Abs. 2 Nr. 3 GWB",
        "contract_types": [
            _series(
                "works",
                "Bauaufträge",
                "Works contracts",
                "Art. 8 Buchst. b RL 2009/81/EG",
                _defence("b", WORKS),
            ),
            _series(
                "supplies_services",
                "Liefer- und Dienstleistungsaufträge",
                "Supply and service contracts",
                "Art. 8 Buchst. a RL 2009/81/EG",
                _defence("a", UTILITIES_SUPPLY),
            ),
        ],
    }


def plain_text(markup: str) -> str:
    """Wording of an official XHTML document: markup removed, whitespace collapsed."""
    markup = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", markup, flags=re.S)
    text = html.unescape(re.sub(r"<[^>]+>", " ", markup))
    return re.sub(r"[ \t\xa0\r\n]+", " ", text).strip()


def read_official(directory: Path) -> dict[str, dict[str, str]]:
    """Checksum and quoted wording of every act in ``ACTS`` from ``<CELEX>.xhtml``."""
    found: dict[str, dict[str, str]] = {}
    for celex, (title, _journal, _applies) in ACTS.items():
        raw = (directory / f"{celex}.xhtml").read_bytes()
        text = plain_text(raw.decode("utf-8"))
        head = text[:600].casefold()
        at = head.find(title.casefold())
        if at < 0 or head[:at].endswith("delegierte "):
            raise SystemExit(f"{celex}: Titel '{title}' steht nicht im Kopf des Dokuments.")
        if celex in ARTICLES:
            start = re.search(ARTICLES[celex][0], text)
            end = re.search(ARTICLES[celex][1], text[start.start() :]) if start else None
            if start is None or end is None:
                raise SystemExit(f"{celex}: Artikel nicht gefunden.")
            quote = text[start.start() : start.start() + end.start()]
        else:
            begin = text.index(OPERATIVE[0]) + len(OPERATIVE[0])
            quote = text[begin : text.index(OPERATIVE[1], begin)]
        found[celex] = {
            "retrieved_sha256": hashlib.sha256(raw).hexdigest(),
            "quote": quote.strip(),
        }
    return found


def sources() -> dict[str, dict[str, str]]:
    """Source entries of the profile: title, Official Journal, checksum and wording."""
    official = json.loads(SOURCES_FILE.read_text(encoding="utf-8"))
    return {
        celex: {
            "regulation": title,
            "official_journal": journal,
            "celex": celex,
            "url": f"https://eur-lex.europa.eu/legal-content/DE/TXT/HTML/?uri=CELEX:{celex}",
            "retrieved_from": CELLAR + celex,
            "retrieved_sha256": official[celex]["retrieved_sha256"],
            "retrieved_on": RETRIEVED_ON,
            "applies_from": applies,
            "quote": official[celex]["quote"],
        }
        for celex, (title, journal, applies) in ACTS.items()
    }


LEGAL_STATUS = (
    "EU-Schwellenwerte je Geltungszeitraum 2014–2027 mit amtlicher Fundstelle für öffentliche "
    "Aufträge, Sektorenaufträge, Konzessionen sowie Verteidigung und Sicherheit (Block "
    "eu_regimes, abgerufen am 13.10.2026); nur belegte Zeiträume sind eingetragen. Nationale "
    "Stufen, Verfahren, Mindestangebote und Pflichtdokumente stammen aus dem Regelwerk "
    "PROCUREMENT_HVTG der Anwendungen und sind fachlich nicht bestätigt: REVIEW_REQUIRED."
)
YEAR_TABLE_NOT_ENTERED = (
    "Zeiträume vor 2014 und ab 2028 sind nicht eingetragen (kein im Profil belegter Wert). "
    "Diese Jahrestabelle dient der Vorprüfung und führt nur öffentliche Bau-, Liefer- und "
    "Dienstleistungsaufträge (RL 2014/24/EU); Sektorenaufträge (RL 2014/25/EU), Konzessionen "
    "(RL 2014/23/EU), Verteidigung und Sicherheit (RL 2009/81/EG) sowie soziale und andere "
    "besondere Dienstleistungen stehen im Block eu_regimes."
)
NOT_ENTERED = (
    "Nicht eingetragen sind Zeiträume vor 2014 und ab 2028. Konzessionen sind erst ab dem "
    "18.04.2016 eingetragen; Baukonzessionen nach Art. 56 RL 2004/18/EG für die Zeit davor "
    "sind nicht enthalten. Der Schwellenwert für soziale und andere besondere "
    "Dienstleistungen besteht erst seit den Richtlinien von 2014 und ist ab dem 18.04.2016 "
    "eingetragen. Wettbewerbe werden nicht gesondert geführt (Art. 4 Buchst. b und c "
    "RL 2014/24/EU und Art. 15 Buchst. a RL 2014/25/EU nennen sie beim Schwellenwert für "
    "Liefer- und Dienstleistungsaufträge). Subventionierte Aufträge (Art. 13 RL 2014/24/EU) "
    "und die Regeln zur Schätzung des Auftragswerts einschließlich der Losregelungen sind "
    "nicht abgebildet."
)
COMPARISON_REFERENCE = (
    "Die Richtlinien gelten für Aufträge, deren geschätzter Wert ohne Mehrwertsteuer den "
    "Schwellenwert „nicht unterschreitet“ (Art. 4 RL 2014/24/EU, Art. 15 RL 2014/25/EU, "
    "Art. 8 RL 2009/81/EG), und für Konzessionen, deren Vertragswert „mindestens“ den "
    "Schwellenwert beträgt (Art. 8 Abs. 1 RL 2014/23/EU); § 106 Abs. 1 Satz 1 GWB: Anwendung, "
    "wenn der geschätzte Auftrags- oder Vertragswert den Schwellenwert erreicht oder "
    "überschreitet."
)
RETRIEVAL = (
    "Amtlicher deutscher Text vom Amt für Veröffentlichungen (Cellar), "
    "http://publications.europa.eu/resource/celex/<CELEX> mit Accept: application/xhtml+xml "
    "und Accept-Language: de; retrieved_sha256 ist die SHA-256 der abgerufenen Datei, quote "
    "der Wortlaut der einschlägigen Artikel ohne Auszeichnung mit zusammengefasstem Leerraum. "
    "Die Liste der Änderungsrechtsakte je Richtlinie stammt aus der Cellar-Abfrage "
    "(cdm:resource_legal_amends_resource_legal); danach ändern bis zum Abruftag nur die "
    "genannten Verordnungen die Schwellenwerte."
)


def build(base: dict[str, Any]) -> dict[str, Any]:
    """Profile 2026.10.1 from the released 2026.09.3 document."""
    document = json.loads(json.dumps(base))
    document["schema"] = "auditcore_procurement.precheck-profile/3"
    document["version"] = VERSION
    document["legal_status"] = LEGAL_STATUS
    document["eu_thresholds"]["not_entered"] = YEAR_TABLE_NOT_ENTERED
    table = sources()
    document["eu_regimes"] = {
        "comparison": "reached_or_exceeded",
        "comparison_reference": COMPARISON_REFERENCE,
        "verified_on": RETRIEVED_ON,
        "retrieval": RETRIEVAL,
        "precheck_view": {
            "regime": "public_contracts",
            "categories": {"construction": "works", "supply_service": "supplies_services"},
        },
        "regimes": regimes(),
        "sources": table,
        "not_entered": NOT_ENTERED,
    }
    for regime in document["eu_regimes"]["regimes"]:
        for kind in regime["contract_types"]:
            for series in kind.get("authority_types", [kind]):
                for row in series["thresholds"]:
                    amount = f"{row['value']:,}".replace(",", " ") + " EUR"
                    if amount not in table[row["source"]]["quote"]:
                        raise SystemExit(f"{amount} steht nicht im Wortlaut von {row['source']}.")
    return document


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base_profile", type=Path, nargs="?")
    parser.add_argument("output_dir", type=Path, nargs="?")
    parser.add_argument("--official", type=Path, help="Verzeichnis mit <CELEX>.xhtml")
    args = parser.parse_args()
    if args.official:
        found = read_official(args.official)
        SOURCES_FILE.write_text(
            json.dumps(found, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        print(SOURCES_FILE)
    if args.base_profile and args.output_dir:
        base = json.loads(args.base_profile.read_text(encoding="utf-8"))
        output = args.output_dir / f"procurement.hvtg-{VERSION}.json"
        output.write_text(
            json.dumps(build(base), indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        print(output)


if __name__ == "__main__":
    main()
