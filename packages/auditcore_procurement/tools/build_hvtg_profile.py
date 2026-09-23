"""Build ``procurement.hvtg`` 2026.09.2: year-bound EU thresholds plus separate national tiers.

EU values are entered only with a verified official source (EUR-Lex text of the
delegated regulation; German publication in the Bundesanzeiger). Periods
without a verified source are not entered. The national tiers (1.000/25.000 EUR,
procedures, minimum bids, required documents) come unchanged from the
application ruleset of the legacy profile and keep status REVIEW_REQUIRED.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

VERSION = "2026.09.2"
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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("legacy_profile", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    legacy = json.loads(args.legacy_profile.read_text())
    profile = {
        "schema": "auditcore_procurement.precheck-profile/2",
        "id": "procurement.hvtg",
        "version": VERSION,
        "status": "SOURCE_CHARACTERIZED",
        "legal_status": (
            "EU-Schwellenwerte je Geltungszeitraum mit amtlicher Fundstelle; nur belegte "
            "Zeiträume sind eingetragen. Nationale Stufen, Verfahren, Mindestangebote und "
            "Pflichtdokumente stammen aus dem Regelwerk PROCUREMENT_HVTG der Anwendungen und "
            "sind fachlich nicht bestätigt: REVIEW_REQUIRED."
        ),
        "source": legacy["source"],
        "construction_marker": legacy["construction_marker"],
        "tiers": legacy["tiers"],
        "fallback_tier": legacy["fallback_tier"],
        "required_documents": legacy["required_documents"],
        "bid_document_type": legacy["bid_document_type"],
        "default_min_bids": legacy["default_min_bids"],
        "value_deviation": legacy["value_deviation"],
        "eu_thresholds": {
            "legal_basis": (
                "Art. 4 Richtlinie 2014/24/EU in der jeweils durch Delegierte Verordnung "
                "geänderten Fassung; § 106 Abs. 1 und 2 Nr. 1 GWB"
            ),
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
            "periods": EU_PERIODS,
            "not_entered": (
                "Zeiträume vor 2024 und ab 2028 sind nicht eingetragen (kein im Profil "
                "belegter Wert); Konzessionen und Sektorenaufträge sind im Quellregelwerk nicht "
                "abgebildet und daher nicht enthalten."
            ),
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
    args.output.write_text(json.dumps(profile, indent=1, ensure_ascii=False) + "\n")
    print(args.output)


if __name__ == "__main__":
    main()
