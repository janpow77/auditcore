"""Build ``procurement.hvtg`` 2026.09.2 and 2026.09.3: year-bound EU thresholds
plus separate national tiers.

EU values are entered only with a verified official source (EUR-Lex text of the
(delegated) regulation; German publication in the Bundesanzeiger). Periods
without a verified source are not entered. The national tiers (1.000/25.000 EUR,
procedures, minimum bids, required documents) come unchanged from the
application ruleset of the legacy profile and keep status REVIEW_REQUIRED.

2026.09.2 (released, unchanged): 2024–2027. 2026.09.3 adds 2014–2023 (user
decision of 23.09.2026, "c2. ja"). The official texts were retrieved from the
Publications Office (Cellar, ``http://publications.europa.eu/resource/celex/<CELEX>``,
German XHTML), because eur-lex.europa.eu answers automated requests with a
challenge page; ``retrieved_sha256`` binds each value to the document read.

    python tools/build_hvtg_profile.py \
        src/auditcore_procurement/profiles/procurement.hvtg-legacy-2026.09.1.json \
        src/auditcore_procurement/profiles
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

VERSION = "2026.09.2"
VERSION_HISTORIC = "2026.09.3"
VERIFIED_ON = "2026-09-23"

EU_PERIODS = [
    {
        "valid_from": "2024-01-01",
        "valid_to": "2025-12-31",
        "values": {
            "works": 5538000,
            "supplies_services_central": 143000,
            "supplies_services_sub_central": 221000,
        },
        "source": {
            "regulation": (
                "Delegierte Verordnung (EU) 2023/2495 der Kommission vom 15. November 2023"
            ),
            "amends": "Richtlinie 2014/24/EU, Artikel 4 Buchstaben a bis c",
            "official_journal": "ABl. L, 2023/2495, 16.11.2023",
            "url": "https://eur-lex.europa.eu/legal-content/DE/TXT/HTML/?uri=OJ:L_202302495",
            "applies_from": "2024-01-01",
            "verified_on": VERIFIED_ON,
            "verification": "Wortlaut von Artikel 1 und 2 auf EUR-Lex gelesen",
            "legacy_note": (
                "Die Quellwerte 221.000 EUR (supply_service BELOW_EU) und 5.538.000 EUR "
                "(construction BELOW_EU) entsprechen dieser Periode; der Wert für zentrale "
                "Regierungsbehörden (143.000 EUR) war im Quellregelwerk nicht abgebildet."
            ),
        },
    },
    {
        "valid_from": "2026-01-01",
        "valid_to": "2027-12-31",
        "values": {
            "works": 5404000,
            "supplies_services_central": 140000,
            "supplies_services_sub_central": 216000,
        },
        "source": {
            "regulation": (
                "Delegierte Verordnung (EU) 2025/2152 der Kommission vom 22. Oktober 2025"
            ),
            "amends": "Richtlinie 2014/24/EU, Artikel 4 Buchstaben a bis c",
            "official_journal": "ABl. L, 2025/2152, 23.10.2025",
            "url": "https://eur-lex.europa.eu/legal-content/DE/TXT/HTML/?uri=OJ:L_202502152",
            "national_publication": (
                "Bekanntmachung des BMWE vom 9. Dezember 2025, BAnz AT 18.12.2025 B4 "
                "(§ 106 Abs. 3 GWB)"
            ),
            "applies_from": "2026-01-01",
            "verified_on": VERIFIED_ON,
            "verification": "Artikel 1 auf EUR-Lex und Bundesanzeiger-Bekanntmachung gelesen",
        },
    },
]


CELLAR = "http://publications.europa.eu/resource/celex/"
HISTORIC_VERIFICATION = (
    "Artikel 1 bis 4 im amtlichen deutschen Text gelesen (Amt für Veröffentlichungen, Cellar-XHTML)"
)


def _eurlex(celex: str) -> str:
    return f"https://eur-lex.europa.eu/legal-content/DE/TXT/HTML/?uri=CELEX:{celex}"


#: 2014–2023, each value read in the official German text (Art. 1/2 of the
#: amending regulation); ``retrieved_sha256`` is the Cellar XHTML read on VERIFIED_ON.
HISTORIC_PERIODS = [
    {
        "valid_from": "2014-01-01",
        "valid_to": "2015-12-31",
        "values": {
            "works": 5186000,
            "supplies_services_central": 134000,
            "supplies_services_sub_central": 207000,
        },
        "source": {
            "regulation": "Verordnung (EU) Nr. 1336/2013 der Kommission vom 13. Dezember 2013",
            "amends": "Richtlinie 2004/18/EG, Artikel 7 Buchstaben a bis c (Artikel 2 Nr. 1)",
            "official_journal": "ABl. L 335 vom 14.12.2013, S. 17",
            "celex": "32013R1336",
            "url": _eurlex("32013R1336"),
            "retrieved_from": CELLAR + "32013R1336",
            "retrieved_sha256": "742dba08cadb29ec56acaf6f0335a29fa4b2e4c1974f6190c900946b4b844146",
            "applies_from": "2014-01-01",
            "verified_on": VERIFIED_ON,
            "verification": HISTORIC_VERIFICATION,
            "note": (
                "Bis 17.04.2016 galt die Richtlinie 2004/18/EG (Aufhebung durch Art. 91 "
                "RL 2014/24/EU zum 18.04.2016). Artikel 7 Buchstabe a betrifft die in Anhang IV "
                "genannten zentralen Regierungsbehörden, Buchstabe b die übrigen öffentlichen "
                "Auftraggeber; die Werte stimmen mit der Ursprungsfassung von Art. 4 "
                "Buchstaben a bis c RL 2014/24/EU (ABl. L 94 vom 28.3.2014, S. 65) überein."
            ),
        },
    },
    {
        "valid_from": "2016-01-01",
        "valid_to": "2017-12-31",
        "values": {
            "works": 5225000,
            "supplies_services_central": 135000,
            "supplies_services_sub_central": 209000,
        },
        "source": {
            "regulation": (
                "Delegierte Verordnung (EU) 2015/2170 der Kommission vom 24. November 2015"
            ),
            "amends": "Richtlinie 2014/24/EU, Artikel 4 Buchstaben a bis c",
            "official_journal": "ABl. L 307 vom 25.11.2015, S. 5",
            "celex": "32015R2170",
            "url": _eurlex("32015R2170"),
            "retrieved_from": CELLAR + "32015R2170",
            "retrieved_sha256": "a13e12ebc9091340cf7ad83c8c37831a1ecc94da6e11051730c4e19dc2a73dd4",
            "applies_from": "2016-01-01",
            "verified_on": VERIFIED_ON,
            "verification": HISTORIC_VERIFICATION,
            "concurrent_source": {
                "regulation": "Verordnung (EU) 2015/2342 der Kommission vom 15. Dezember 2015",
                "amends": "Richtlinie 2004/18/EG, Artikel 7 Buchstaben a bis c",
                "official_journal": "ABl. L 330 vom 16.12.2015, S. 18",
                "celex": "32015R2342",
                "url": _eurlex("32015R2342"),
                "retrieved_from": CELLAR + "32015R2342",
                "retrieved_sha256": (
                    "989cac3a9f939f65b99784d3549730cf4e20f87034fd49627bdff4d26f375e32"
                ),
                "applies_from": "2016-01-01",
            },
            "note": (
                "01.01.–17.04.2016 galt RL 2004/18/EG in der Fassung der VO (EU) 2015/2342, ab "
                "18.04.2016 RL 2014/24/EU in der Fassung der Delegierten VO (EU) 2015/2170; "
                "beide setzen dieselben Werte fest, der Zeitraum ist daher durchgehend."
            ),
        },
    },
    {
        "valid_from": "2018-01-01",
        "valid_to": "2019-12-31",
        "values": {
            "works": 5548000,
            "supplies_services_central": 144000,
            "supplies_services_sub_central": 221000,
        },
        "source": {
            "regulation": (
                "Delegierte Verordnung (EU) 2017/2365 der Kommission vom 18. Dezember 2017"
            ),
            "amends": "Richtlinie 2014/24/EU, Artikel 4 Buchstaben a bis c",
            "official_journal": "ABl. L 337 vom 19.12.2017, S. 19",
            "celex": "32017R2365",
            "url": _eurlex("32017R2365"),
            "retrieved_from": CELLAR + "32017R2365",
            "retrieved_sha256": "4a9cdce02e59ea8e4f73398c0f77f5ee2a25821e206e483debdea7a5b1d9cb8b",
            "applies_from": "2018-01-01",
            "verified_on": VERIFIED_ON,
            "verification": HISTORIC_VERIFICATION,
        },
    },
    {
        "valid_from": "2020-01-01",
        "valid_to": "2021-12-31",
        "values": {
            "works": 5350000,
            "supplies_services_central": 139000,
            "supplies_services_sub_central": 214000,
        },
        "source": {
            "regulation": (
                "Delegierte Verordnung (EU) 2019/1828 der Kommission vom 30. Oktober 2019"
            ),
            "amends": "Richtlinie 2014/24/EU, Artikel 4 Buchstaben a bis c",
            "official_journal": "ABl. L 279 vom 31.10.2019, S. 25",
            "celex": "32019R1828",
            "url": _eurlex("32019R1828"),
            "retrieved_from": CELLAR + "32019R1828",
            "retrieved_sha256": "f7685bad87f95b205ce07d2343c4778b5529cc3ece0f7f115794b58ff3da29c0",
            "applies_from": "2020-01-01",
            "verified_on": VERIFIED_ON,
            "verification": HISTORIC_VERIFICATION,
        },
    },
    {
        "valid_from": "2022-01-01",
        "valid_to": "2023-12-31",
        "values": {
            "works": 5382000,
            "supplies_services_central": 140000,
            "supplies_services_sub_central": 215000,
        },
        "source": {
            "regulation": (
                "Delegierte Verordnung (EU) 2021/1952 der Kommission vom 10. November 2021"
            ),
            "amends": "Richtlinie 2014/24/EU, Artikel 4 Buchstaben a bis c",
            "official_journal": "ABl. L 398 vom 11.11.2021, S. 23",
            "celex": "32021R1952",
            "url": _eurlex("32021R1952"),
            "retrieved_from": CELLAR + "32021R1952",
            "retrieved_sha256": "7b612376694b1312d8475faf2c5313d0c607ae0bc924a6346cd74bddee6184ca",
            "applies_from": "2022-01-01",
            "verified_on": VERIFIED_ON,
            "verification": HISTORIC_VERIFICATION,
        },
    },
]

#: Re-check of the 2024–2027 values of 2026.09.2 against the same official texts.
RECHECK = {
    "2024-01-01": {
        "celex": "32023R2495",
        "retrieved_sha256": "ca2ef5aa1411ce71a330a3ececda60c1a777c841f2b99844222930249c06e8f1",
    },
    "2026-01-01": {
        "celex": "32025R2152",
        "retrieved_sha256": "42a76b2d440449e63dd40d78ffe8db3c197dad35baefd0d63de198969f897c97",
    },
}


def _periods(version: str) -> list[dict[str, Any]]:
    if version == VERSION:
        return EU_PERIODS
    current = json.loads(json.dumps(EU_PERIODS))
    for period in current:
        extra = RECHECK[period["valid_from"]]
        period["source"].update(
            {
                "celex": extra["celex"],
                "retrieved_from": CELLAR + extra["celex"],
                "retrieved_sha256": extra["retrieved_sha256"],
                "rechecked_on": VERIFIED_ON,
            }
        )
    return [*HISTORIC_PERIODS, *current]


LEGAL_BASIS = {
    VERSION: (
        "Art. 4 Richtlinie 2014/24/EU in der jeweils durch Delegierte Verordnung "
        "geänderten Fassung; § 106 Abs. 1 und 2 Nr. 1 GWB"
    ),
    VERSION_HISTORIC: (
        "Art. 4 Richtlinie 2014/24/EU (ab 18.04.2016) bzw. Art. 7 Richtlinie 2004/18/EG "
        "(bis 17.04.2016) in der jeweils durch (Delegierte) Verordnung der Kommission "
        "geänderten Fassung; § 106 Abs. 1 und 2 Nr. 1 GWB"
    ),
}
LEGAL_STATUS = {
    VERSION: (
        "EU-Schwellenwerte je Geltungszeitraum mit amtlicher Fundstelle; nur belegte "
        "Zeiträume sind eingetragen. Nationale Stufen, Verfahren, Mindestangebote und "
        "Pflichtdokumente stammen aus dem Regelwerk PROCUREMENT_HVTG der Anwendungen und "
        "sind fachlich nicht bestätigt: REVIEW_REQUIRED."
    ),
    VERSION_HISTORIC: (
        "EU-Schwellenwerte je Geltungszeitraum 2014–2027 mit amtlicher Fundstelle (Nachtrag "
        "2014–2023 nach Nutzerentscheidung vom 23.09.2026); nur belegte Zeiträume sind "
        "eingetragen. Nationale Stufen, Verfahren, Mindestangebote und Pflichtdokumente "
        "stammen aus dem Regelwerk PROCUREMENT_HVTG der Anwendungen und sind fachlich nicht "
        "bestätigt: REVIEW_REQUIRED."
    ),
}
NOT_ENTERED = {
    VERSION: (
        "Zeiträume vor 2024 und ab 2028 sind nicht eingetragen (kein im Profil "
        "belegter Wert); Konzessionen und Sektorenaufträge sind im Quellregelwerk nicht "
        "abgebildet und daher nicht enthalten."
    ),
    VERSION_HISTORIC: (
        "Zeiträume vor 2014 und ab 2028 sind nicht eingetragen (kein im Profil belegter "
        "Wert). Konzessionen (RL 2014/23/EU), Sektorenaufträge (RL 2014/25/EU), soziale und "
        "andere besondere Dienstleistungen (Art. 4 Buchst. d RL 2014/24/EU) und "
        "Wettbewerbe kennt das Profilschema nicht; sie sind daher nicht enthalten."
    ),
}


def build(legacy: dict[str, Any], version: str) -> dict[str, Any]:
    """Profile document of ``version`` from the legacy profile's application rules."""
    return {
        "schema": "auditcore_procurement.precheck-profile/2",
        "id": "procurement.hvtg",
        "version": version,
        "status": "SOURCE_CHARACTERIZED",
        "legal_status": LEGAL_STATUS[version],
        "source": legacy["source"],
        "construction_marker": legacy["construction_marker"],
        "tiers": legacy["tiers"],
        "fallback_tier": legacy["fallback_tier"],
        "required_documents": legacy["required_documents"],
        "bid_document_type": legacy["bid_document_type"],
        "default_min_bids": legacy["default_min_bids"],
        "value_deviation": legacy["value_deviation"],
        "eu_thresholds": {
            "legal_basis": LEGAL_BASIS[version],
            "comparison": "reached_or_exceeded",
            "comparison_reference": (
                "§ 106 Abs. 1 Satz 1 GWB: Anwendung, wenn der geschätzte Auftragswert den "
                "Schwellenwert erreicht oder überschreitet"
            ),
            "tier": "BELOW_EU",
            "categories": {
                "construction": "works",
                "supply_service": {
                    "central": "supplies_services_central",
                    "sub_central": "supplies_services_sub_central",
                },
            },
            "periods": _periods(version),
            "not_entered": NOT_ENTERED[version],
        },
        "national_tiers": {
            "status": "REVIEW_REQUIRED",
            "tiers": ["BELOW_1K", "BELOW_25K"],
            "comparison": "inclusive_maximum",
            "source": (
                "Regelwerk PROCUREMENT_HVTG der Anwendungen (threshold_rules), "
                "siehe source.repositories; keine Norm im Regelwerk angegeben"
            ),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("legacy_profile", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    legacy = json.loads(args.legacy_profile.read_text())
    for version in (VERSION, VERSION_HISTORIC):
        output = args.output_dir / f"procurement.hvtg-{version}.json"
        document = build(legacy, version)
        output.write_text(json.dumps(document, indent=1, ensure_ascii=False) + "\n")
        print(output)


if __name__ == "__main__":
    main()
