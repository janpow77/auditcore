"""Write the packaged rule profiles from the executed source constants.

Every threshold, proximity, pattern and label is taken from the recorded
fixtures (``tests/fixtures/*_observed.json``), which the capture tools read
from the blob-verified sources. Parameters that exist only as literals inside
the source functions (for example ``> 20`` Belege in RF10) are written here
with their exact source lines; the boundary frames of the replay fixtures
(``rf10-paar-20``/``-21``, ``rf12-genau-zehn-prozent`` …) prove each of them.

    python tools/build_profiles.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "src" / "auditcore_risk" / "profile_data"
FIXTURES = ROOT / "tests" / "fixtures"
RA_PATH = "backend/app/pipeline/red_flags.py"
FS_PATH = "backend/app/modules/flowstat/services/belegliste_analysis_service.py"
LEGAL = (
    "Aus der Quellanwendung übernommenes, charakterisiertes Softwareverhalten zur "
    "Stichprobenpriorisierung; keine rechtliche Bewertung, keine Fehlerquote und keine "
    "fachliche Freigabe der Schwellen oder Muster."
)


def ra_origin(symbol: str, lines: str) -> dict[str, Any]:
    return {
        "repository": "janpow77/riskanalysis",
        "path": RA_PATH,
        "symbol": symbol,
        "lines": lines,
    }


def fs_origin(lines: str) -> dict[str, Any]:
    return {"path": FS_PATH, "symbol": "_red_flags", "lines": lines}


def relevance(pattern: str) -> dict[str, Any]:
    return {
        "field": "kostenart_auswertung_bezeichnung",
        "exclude_pattern": pattern,
        "ignore_case": True,
        "column_missing": "relevant",
    }


def riskanalysis_rules(c: dict[str, Any], rf02_thresholds: dict[str, Any]) -> list[dict[str, Any]]:
    labels = c["RED_FLAG_LABELS"]
    amount = {"parse": "strict", "missing_value": 0.0}
    descriptive = (
        "[deskriptiv] Auffälligkeitshinweis zur Stichprobenpriorisierung; keine Fehlerquote, "
        "nie neben der 2-%-Wesentlichkeit interpretieren."
    )
    return [
        {
            "code": "RF01",
            "label": labels["RF01"],
            "kind": "round_multiple",
            "column": "rf01",
            "requires": ["bruttobetrag"],
            "when_missing_columns": "error",
            "params": {"field": "bruttobetrag", "multiple": 1000, "positive_only": True, **amount},
            "origin": ra_origin("compute_red_flags", "251-254"),
        },
        {
            "code": "RF02",
            "label": labels["RF02"],
            "kind": "near_threshold",
            "column": "rf02",
            "requires": ["bruttobetrag"],
            "when_missing_columns": "error",
            "params": {
                "field": "bruttobetrag",
                "thresholds": rf02_thresholds,
                "lower": {"proximity": c["_PROXIMITY"]},
                "count": "first",
                **amount,
            },
            "note": "Quelle: Schwellen 'netto' kommentiert, angewandt auf den Bruttobetrag "
            "(HUMAN_DECISION_REQUIRED).",
            "origin": ra_origin(
                "_near_threshold, VERGABE_SCHWELLEN, _PROXIMITY", "36-38, 69-75, 255-256"
            ),
        },
        {
            "code": "RF08",
            "label": labels["RF08"],
            "kind": "missing_procurement",
            "column": "rf08",
            "requires": ["bruttobetrag"],
            "when_missing_columns": "error",
            "params": {
                "amount_field": "bruttobetrag",
                "amount_gt": c["RF08_BAGATELLGRENZE"],
                "id_field": "vergabenummer",
                "id_column_missing": "counts_as_missing",
                "blank_values": ["", "nan"],
                "blank_casefold": True,
                "placeholder_pattern": c["_PLATZHALTER_VERGABE"],
                "relevance": relevance(c["_NICHT_VERGABERELEVANT"]),
                **amount,
            },
            "origin": ra_origin(
                "_hat_echte_vergabe, RF08_BAGATELLGRENZE, _PLATZHALTER_VERGABE, "
                "_NICHT_VERGABERELEVANT",
                "40-47, 78-89, 258-268",
            ),
        },
        {
            "code": "RF09",
            "label": labels["RF09"],
            "kind": "name_similarity",
            "column": "rf09",
            "requires": ["Name", "zahlungsempfaenger"],
            "when_missing_columns": "error",
            "params": {
                "left_field": "Name",
                "right_field": "zahlungsempfaenger",
                "normalization": {"profile": "riskanalysis.payee", "version": "2026.09.1"},
                "min_length": 4,
                "containment_score": 1.0,
                "scorer": "token_set_ratio",
                "scale": 100.0,
                "threshold": 0.85,
                "override_field": "_pseudonym_rf09",
                "value_name": "name_match",
            },
            "note": "Ohne rapidfuzz fiel die Quelle still auf difflib zurück; hier ist rapidfuzz "
            "Pflicht (Extra fuzzy).",
            "origin": ra_origin("_name_match, compute_red_flags", "92-102, 270-277"),
        },
        {
            "code": "RF10",
            "label": labels["RF10"],
            "kind": "counterparty_concentration",
            "column": "rf10",
            "interpretation": "descriptive_prior",
            "note": descriptive,
            "requires": ["bruttobetrag"],
            "when_missing_columns": "error",
            "params": {
                "amount_field": "bruttobetrag",
                "payee_field": "payee_canonical",
                "case_field": "antrag",
                "group_field": "Gruppennummer",
                "relevance": relevance(c["_NICHT_VERGABERELEVANT"]),
                "pair": {"count_gt": 20, "sum_gt": 50000},
                "group": {"cases_gt": 3, "sum_gt": 50000},
                **amount,
            },
            "origin": ra_origin("_compute_rf10", "105-161"),
        },
        {
            "code": "RF11",
            "label": labels["RF11"],
            "kind": "ratio_history",
            "column": "rf11",
            "interpretation": "descriptive_prior",
            "note": descriptive,
            "requires": ["Anzahl_Versionen", "Anzahl_ungueltige_Versionen"],
            "when_missing_columns": "all_false",
            "params": {
                "total_field": "Anzahl_Versionen",
                "part_field": "Anzahl_ungueltige_Versionen",
                "ratio_gt": 0.5,
                "total_min": 4,
            },
            "origin": ra_origin("_compute_rf11", "164-181"),
        },
        {
            "code": "RF12",
            "label": labels["RF12"],
            "kind": "leave_one_out_rate",
            "column": "rf12",
            "interpretation": "descriptive_prior",
            "note": descriptive + " Schwelle 10 % aus rbvk-Kriterium 19, nicht datenkalibriert.",
            "requires": ["bruttobetrag", "Gruppennummer", "antrag"],
            "when_missing_columns": "all_false",
            "params": {
                "group_field": "Gruppennummer",
                "case_field": "antrag",
                "amount_field": "bruttobetrag",
                "deduction_field": "abweichungen_betrag",
                "deduction_missing_value": 0.0,
                "rate_gt": 10.0,
                "percent_factor": 100.0,
                "min_cases_gt": 1,
                **amount,
            },
            "origin": ra_origin("_compute_rf12", "184-240"),
        },
        {
            "code": "RF13",
            "label": labels["RF13"],
            "kind": "numeric_compare",
            "column": "rf13",
            "params": {
                "field": "auszahlungsdauer_tage",
                "column_missing_value": 0,
                "missing_value": 0,
                "op": "gt",
                "value": 80,
            },
            "origin": ra_origin("compute_red_flags", "285-286"),
        },
        {
            "code": "RF14",
            "label": labels["RF14"],
            "kind": "numeric_compare",
            "column": "rf14",
            "params": {
                "field": "indikator_erreichungsquote",
                "column_missing_value": 1.0,
                "missing_value": 1.0,
                "op": "lt",
                "value": 0.8,
            },
            "origin": ra_origin("compute_red_flags", "287-288"),
        },
        {
            "code": "RF15",
            "label": labels["RF15"],
            "kind": "text_equals",
            "column": "rf15",
            "params": {
                "field": "sanktionslisten_status",
                "column_missing_value": "kein Treffer",
                "value": "möglicher Treffer",
            },
            "origin": ra_origin("compute_red_flags", "289"),
        },
    ]


def riskanalysis_source(fixture: dict[str, Any]) -> dict[str, Any]:
    files = fixture["source"]["files"]
    return {
        "repository": fixture["source"]["repository"],
        "commit": fixture["source"]["commit"],
        "path": RA_PATH,
        "git_blob": files[RA_PATH],
        "symbols": fixture["source"]["symbols"],
        "rights": "USER_AUTHORIZED_MIT",
        "characterization": "tests/fixtures/riskanalysis_observed.json",
    }


def build() -> list[tuple[str, dict[str, Any]]]:
    ra = json.loads((FIXTURES / "riskanalysis_observed.json").read_text())
    fs = json.loads((FIXTURES / "flowstat_observed.json").read_text())
    c = ra["constants"]
    if c["_NICHT_VERGABERELEVANT_flags"] & 2 != 2:  # re.IGNORECASE
        raise SystemExit("RF08 pattern is expected to be case-insensitive")
    static = [float(t) for t in c["VERGABE_SCHWELLEN"]]
    annotations = {
        "221000": "Entspricht der EU-Schwelle Liefer-/Dienstleistungen subzentraler "
        "Auftraggeber 2024–2025 (auditcore_procurement procurement.hvtg 2026.09.2); "
        "seit 01.01.2026 gilt 216.000. Legacyprofil bleibt unverändert."
    }
    legacy = {
        "schema": "auditcore_risk.profile/1",
        "id": "riskanalysis.legacy",
        "version": ra["source"]["commit"][:12],
        "kind": "record_red_flags",
        "status": "LEGACY_CHARACTERIZED",
        "legal_status": LEGAL,
        "source": riskanalysis_source(ra),
        "rules": riskanalysis_rules(c, {"static": static, "annotations": annotations}),
        "output": {"codes_column": "red_flag_codes", "value_columns": ["name_match"]},
        "summary": {
            "format": "riskanalysis.red_flag_summary",
            "amount_field": "bruttobetrag",
            "origin": ra_origin("red_flag_summary", "298-319"),
        },
        "open_decisions": [
            "RF02: Schwellen sind als netto kommentiert, werden aber auf den Bruttobetrag "
            "angewandt.",
            "RF02: 221.000 ist die EU-Schwelle 2024–2025; ab 2026 gilt 216.000 "
            "(Kandidatenprofil riskanalysis.year_bound).",
            "RF09: Umlautzerlegung der Rechnungssteller-Normalisierung (Müller → mu ller).",
            "RF12: gleiche Vorhabenkennung in anderer Gruppe erbt das Merkmal.",
        ],
    }
    year_bound = json.loads(json.dumps(legacy))
    year_bound.update(
        {
            "id": "riskanalysis.year_bound",
            "version": "2026.09.1",
            "status": "CANDIDATE_HUMAN_DECISION_REQUIRED",
            "legal_status": LEGAL + " Kandidat nach der Nutzerentscheidung 'Vergabeschwellen "
            "sollen pro Jahr hinterlegt sein'; Anwendung erst nach fachlicher Freigabe der "
            "offenen Punkte.",
        }
    )
    year_bound["source"] = {
        **year_bound["source"],
        "derived_from": {"profile": "riskanalysis.legacy", "version": legacy["version"]},
        "change": "RF02: statische Schwelle 221.000 ersetzt durch die jahresbezogene EU-Schwelle "
        "aus auditcore_procurement; übrige Regeln unverändert.",
    }
    rf02 = next(r for r in year_bound["rules"] if r["code"] == "RF02")
    rf02["params"]["thresholds"] = {
        "static": [t for t in static if t != 221000.0],
        "procurement_eu": {
            "profile": "procurement.hvtg",
            "version": "2026.09.2",
            "category": "supply_service",
            "authority_type": "sub_central",
            "date_source": "record",
            "date_field": "rechnungsdatum_dt",
        },
    }
    rf02["label"] = "Beleg knapp unter Vergabe-/Schwellenwert (EU-Schwelle jahresbezogen)"
    rf02["note"] = (
        "Maßgebliches Datum (hier Rechnungsdatum), Auftraggebertyp (subzentral) und "
        "Liefer-/Dienstleistungskategorie sind fachlich festzulegen; Brutto/Netto wie Legacy. "
        "Fehlt ein belegter Zeitraum, bleibt der Beleg unbestimmt."
    )
    year_bound["open_decisions"] = [
        "Freigabe dieses Kandidaten statt riskanalysis.legacy.",
        "Stichtag der Schwelle: Rechnungsdatum, Vergabedatum oder Geschäftsjahr.",
        "Auftraggebertyp und Leistungskategorie je Beleg statt pauschal subzentral/Liefer-DL.",
        "Brutto- oder Nettobetrag gegen Nettoschwellen.",
        "Ob die nationalen Wertgrenzen (1.000 … 100.000) ebenfalls jahresbezogen gepflegt werden.",
    ]
    fs_amount = {"parse": "coerce", "missing_value": 0.0}
    fs_rules = [
        {
            "code": "BL_RF01_ROUND_AMOUNT",
            "label": "Runder Tausenderbetrag",
            "kind": "round_multiple",
            "requires": ["projektbetrag"],
            "when_missing_columns": "skip",
            "params": {
                "field": "projektbetrag",
                "multiple": 1000,
                "positive_only": True,
                **fs_amount,
            },
            "origin": fs_origin("452-473"),
        },
        {
            "code": "BL_RF02_NEAR_THRESHOLD",
            "label": "Betrag knapp unter Vergabeschwelle",
            "kind": "near_threshold",
            "requires": ["projektbetrag"],
            "when_missing_columns": "skip",
            "params": {
                "field": "projektbetrag",
                "thresholds": {
                    "static": [float(t) for t in fs["constants"]["PROCUREMENT_THRESHOLDS"]]
                },
                "lower": {"factor": 0.9},
                "count": "all",
                **fs_amount,
            },
            "note": "Zählt Treffer je Schwelle (Summe über alle Schwellen).",
            "origin": fs_origin("147, 474-483"),
        },
        {
            "code": "BL_RF03_MISSING_PAYMENT_DATE",
            "label": "Zahlungsdatum fehlt",
            "kind": "missing_value",
            "requires": ["zahlungsdatum"],
            "when_missing_columns": "skip",
            "params": {"field": "zahlungsdatum"},
            "origin": fs_origin("484-487"),
        },
        {
            "code": "BL_RF04_PAYMENT_BEFORE_INVOICE",
            "label": "Zahlung vor Rechnungsdatum",
            "kind": "date_before",
            "requires": ["rechnungsdatum", "zahlungsdatum"],
            "when_missing_columns": "skip",
            "params": {"field": "zahlungsdatum", "before_field": "rechnungsdatum"},
            "origin": fs_origin("488-491"),
        },
        {
            "code": "BL_RF05_DUPLICATE_INVOICE",
            "label": "Doppelte Rechnung",
            "kind": "duplicate_key",
            "requires": ["rechnungsnummer", "rechnungssteller", "projektbetrag"],
            "when_missing_columns": "skip",
            "params": {"fields": ["rechnungsnummer", "rechnungssteller", "projektbetrag"]},
            "origin": fs_origin("492-501"),
        },
        {
            "code": "BL_RF06_CUT_WITHOUT_REASON",
            "label": "Kürzung ohne Kürzungsgrund",
            "kind": "nonzero_without_text",
            "requires": ["kuerzungsbetrag", "kuerzungsgrund"],
            "when_missing_columns": "skip",
            "params": {
                "amount_field": "kuerzungsbetrag",
                "text_field": "kuerzungsgrund",
                **fs_amount,
            },
            "origin": fs_origin("502-513"),
        },
        {
            "code": "BL_RF07_ACCEPTED_MISMATCH",
            "label": "Anerkannter Betrag ≠ Projektbetrag − Kürzung",
            "kind": "balance_mismatch",
            "requires": ["projektbetrag", "kuerzungsbetrag", "anerkannter_betrag"],
            "when_missing_columns": "skip",
            "params": {
                "minuend": "projektbetrag",
                "subtrahends": ["kuerzungsbetrag", "anerkannter_betrag"],
                "tolerance": 0.01,
                **fs_amount,
            },
            "origin": fs_origin("514-521"),
        },
        {
            "code": "BL_RF08_PROCUREMENT_MISSING",
            "label": "Betrag > 25.000 ohne Vergabeangabe",
            "kind": "missing_procurement",
            "requires": ["projektbetrag", "vergabe"],
            "when_missing_columns": "skip",
            "params": {
                "amount_field": "projektbetrag",
                "amount_gt": 25000,
                "id_field": "vergabe",
                "id_column_missing": "error",
                "blank_values": ["", "nan", "None"],
                "blank_casefold": False,
                "placeholder_pattern": None,
                "relevance": None,
                **fs_amount,
            },
            "origin": fs_origin("522-534"),
        },
        {
            "code": "BL_RF09_DIRECT_AWARD_HIGH_AMOUNT",
            "label": "Direktvergabe über 25.000",
            "kind": "amount_with_marker",
            "requires": ["projektbetrag", "direktvergabe"],
            "when_missing_columns": "skip",
            "params": {
                "amount_field": "projektbetrag",
                "amount_gt": 25000,
                "marker_field": "direktvergabe",
                "marker_pattern": "ja|true|1",
                "lowercase": True,
                **fs_amount,
            },
            "note": "Muster trifft Teilzeichenketten (z. B. '10 Angebote', 'Jahresvertrag').",
            "origin": fs_origin("535-549"),
        },
        {
            "code": "BL_RF10_VENDOR_CONCENTRATION",
            "label": "Konzentration auf einen Rechnungssteller (≥ 50 % der Summe)",
            "kind": "top_share",
            "requires": ["rechnungssteller", "projektbetrag"],
            "when_missing_columns": "skip",
            "params": {
                "group_field": "rechnungssteller",
                "amount_field": "projektbetrag",
                "share_ge": 0.5,
            },
            "origin": fs_origin("550-566"),
        },
    ]
    flowstat = {
        "schema": "auditcore_risk.profile/1",
        "id": "audit_designer.flowstat_belegliste",
        "version": fs["sources"][0]["commit"][:12],
        "kind": "belegliste_red_flag_counts",
        "status": "LEGACY_CHARACTERIZED",
        "legal_status": LEGAL + " Die Quelle liefert nur Codes; die Bezeichnungen sind ergänzt.",
        "source": {
            "sources": [{**s, "rights": "USER_AUTHORIZED_MIT"} for s in fs["sources"]],
            "input_contract": "Spalten wie nach normalize_belegliste (Beträge als Zahl, "
            "Datumsfelder als Datum).",
            "characterization": "tests/fixtures/flowstat_observed.json",
        },
        "rules": fs_rules,
        "output": {},
        "summary": {"format": "flowstat.counts", "origin": fs_origin("451-567")},
        "open_decisions": [
            "BL_RF08 verwendet ≥/> 25.000 anders als RF08 (riskanalysis) und prüft keine "
            "Platzhalter oder Kostenarten; keine Vereinheitlichung ohne Entscheidung.",
            "BL_RF09 trifft Teilzeichenketten ('Jahresvertrag', '10').",
        ],
    }
    return [
        flowinvoice_risk_checker(),
        (f"{legacy['id']}-{legacy['version']}.json", legacy),
        (f"{year_bound['id']}-{year_bound['version']}.json", year_bound),
        (f"{flowstat['id']}-{flowstat['version']}.json", flowstat),
    ]


FI_PATH = "backend/app/services/risk_checker.py"


def fi_origin(symbol: str, lines: str) -> dict[str, Any]:
    return {"repository": "janpow77/flowinvoice", "path": FI_PATH, "symbol": symbol, "lines": lines}


def flowinvoice_risk_checker() -> tuple[str, dict[str, Any]]:
    """flowinvoice ``RiskChecker`` (audit-portal: identical except formatting)."""
    fx = json.loads((FIXTURES / "flowinvoice_risk_checker_observed.json").read_text())
    c = fx["constants"]
    project_check = "Förderfähigkeit der Leistung prüfen"
    rules: list[dict[str, Any]] = [
        {
            "code": "HIGH_AMOUNT",
            "label": "Ungewöhnlich hoher Einzelbetrag",
            "kind": "amount_or_statistic",
            "severity": "MEDIUM",
            "requires": ["net_amount"],
            "params": {
                "amount_field": "net_amount",
                "absolute_gt": c["HIGH_AMOUNT_ABSOLUTE"],
                "median_field": "context.median_amount",
                "std_field": "context.std_deviation",
                "sigma": c["HIGH_AMOUNT_SIGMA"],
            },
            "messages": {
                "absolute": {
                    "description": "Ungewöhnlich hoher Einzelbetrag: {amount:.2f} EUR",
                    "evidence": "Betrag überschreitet absoluten Schwellenwert von {limit:.2f} EUR",
                    "recommendation": "Prüfung der Wirtschaftlichkeit und Vergleich mit "
                    "Marktpreisen empfohlen",
                },
                "relative": {
                    "description": "Betrag weicht signifikant vom Median ab: {amount:.2f} EUR",
                    "evidence": "Median: {median:.2f} EUR, Schwellenwert (Median + 2σ): "
                    "{threshold:.2f} EUR",
                    "recommendation": "Statistische Auffälligkeit prüfen",
                },
            },
            "origin": fi_origin("RiskChecker._check_high_amount, HIGH_AMOUNT_*", "33-34, 119-146"),
        },
        {
            "code": "VENDOR_CLUSTERING",
            "label": "Auffällige Lieferantenhäufung",
            "kind": "share_above",
            "severity": "LOW",
            "params": {
                "numerator_field": "context.vendor_frequency",
                "denominator_field": "context.total_vendor_count",
                "ratio_gt": c["VENDOR_CONCENTRATION_THRESHOLD"],
            },
            "echo_fields": {"vendor_name": "vendor_name"},
            "messages": {
                "default": {
                    "description": "Auffällige Häufung von Lieferant '{vendor_name}'",
                    "evidence": "{numerator} von {denominator} Rechnungen ({ratio:.0%})",
                    "recommendation": "Prüfung auf wirtschaftliche Abhängigkeit oder fehlende "
                    "Ausschreibung",
                }
            },
            "note": "Quelle: total_vendor_count ist laut Schema die Zahl verschiedener "
            "Lieferanten, im Text aber 'Rechnungen' (HUMAN_DECISION_REQUIRED).",
            "origin": fi_origin("RiskChecker._check_vendor_clustering", "35, 148-169"),
        },
        {
            "code": "MISSING_PERIOD",
            "label": "Fehlender Leistungszeitraum",
            "kind": "all_missing",
            "severity": "LOW",
            "params": {"fields": ["service_period_start", "service_period_end"]},
            "messages": {
                "default": {
                    "description": "Fehlende Angabe des Leistungszeitraums",
                    "evidence": "Weder Start- noch Enddatum des Leistungszeitraums auf Rechnung",
                    "recommendation": "Leistungszeitraum nachfordern für zeitliche Zuordnung",
                }
            },
            "origin": fi_origin("RiskChecker._check_missing_period", "171-181"),
        },
        {
            "code": "ROUND_AMOUNT",
            "label": "Runder Pauschalbetrag",
            "kind": "round_amount_terms",
            "requires": ["net_amount"],
            "params": {
                "amount_field": "net_amount",
                "min_amount": c["ROUND_AMOUNT_THRESHOLD"],
                "multiple": 100,
                "text_field": "description",
                "terms": ["pauschale", "pauschal", "festpreis", "einmalzahlung"],
                "severity_with_terms": "INFO",
                "severity_without_terms": "LOW",
            },
            "messages": {
                "with_terms": {
                    "description": "Runder Pauschalbetrag: {amount:.2f} EUR",
                    "evidence": "Betrag ist ein glatter Hunderter-Betrag mit Pauschal-Hinweis",
                    "recommendation": "Pauschalvereinbarung dokumentieren",
                },
                "without_terms": {
                    "description": "Runder Pauschalbetrag: {amount:.2f} EUR",
                    "evidence": "Betrag ist ein glatter Hunderter-Betrag ohne detaillierte "
                    "Aufschlüsselung",
                    "recommendation": "Kalkulation oder Aufschlüsselung des Betrags anfordern",
                },
            },
            "origin": fi_origin(
                "RiskChecker._check_round_amount, ROUND_AMOUNT_THRESHOLD", "36, 183-215"
            ),
        },
        {
            "code": "OUTSIDE_PROJECT_PERIOD",
            "label": "Leistung außerhalb des Projektzeitraums",
            "kind": "date_outside_range",
            "severity": "HIGH",
            "params": {
                "start_field": "service_period_start",
                "end_field": "service_period_end",
                "fallback_field": "invoice_date",
                "range_start_field": "context.project_start",
                "range_end_field": "context.project_end",
            },
            "messages": {
                "before_start": {
                    "description": "Leistung beginnt vor Projektstart",
                    "evidence": "Leistungsbeginn: {check_start}, Projektstart: {range_start}",
                    "recommendation": project_check,
                },
                "after_end": {
                    "description": "Leistung endet nach Projektende",
                    "evidence": "Leistungsende: {check_end}, Projektende: {range_end}",
                    "recommendation": project_check,
                },
            },
            "origin": fi_origin("RiskChecker._check_outside_project_period", "217-246"),
        },
        {
            "code": "NO_PROJECT_REFERENCE",
            "label": "Leistungsbeschreibung ohne Projektbezug",
            "kind": "text_patterns",
            "severity": "LOW",
            "params": {
                "field": "description",
                "lower": True,
                "patterns": [
                    r"^diverse[rs]?\s",
                    r"^sonstige[rs]?\s",
                    r"^verschiedene\s",
                    r"^allgemeine\s",
                    r"\bnach aufwand\b",
                    r"\bpauschale\s+leistung",
                ],
            },
            "messages": {
                "default": {
                    "description": "Generische Leistungsbeschreibung ohne erkennbaren Projektbezug",
                    "evidence": "Erkanntes Muster: '{pattern_display}' in Beschreibung",
                    "recommendation": "Konkrete Projektbezug in Leistungsbeschreibung anfordern",
                }
            },
            "origin": fi_origin("RiskChecker._check_project_reference", "248-272"),
        },
        {
            "code": "RECIPIENT_MISMATCH",
            "label": "Rechnungsempfänger weicht vom Begünstigten ab",
            "kind": "names_differ",
            "severity": "MEDIUM",
            "params": {"left_field": "invoice_recipient", "right_field": "beneficiary_name"},
            "messages": {
                "default": {
                    "description": "Rechnungsempfänger weicht vom Begünstigten ab",
                    "evidence": "Empfänger: '{left}', Begünstigter: '{right}'",
                    "recommendation": "Prüfung ob Rechnung dem richtigen Projekt zugeordnet ist",
                }
            },
            "origin": fi_origin("RiskChecker._check_recipient_mismatch", "274-296"),
        },
        {
            "code": "SELF_INVOICE",
            "label": "Selbstrechnung (gleiche USt-IdNr.)",
            "kind": "identifier_equal",
            "severity": "CRITICAL",
            "params": {
                "left_field": "supplier_vat_id",
                "right_field": "beneficiary_vat_id",
                "upper": True,
                "remove_chars": [" ", ".", "-", "/", "\\"],
            },
            "messages": {
                "default": {
                    "description": "SELBSTRECHNUNG: Lieferant und Begünstigter haben gleiche "
                    "USt-IdNr.",
                    "evidence": "Lieferant-USt-ID: '{left}' = Begünstigter-USt-ID: '{right}'",
                    "recommendation": "KRITISCH: Selbstrechnungen sind nicht förderfähig. "
                    "Sofortige Prüfung erforderlich.",
                }
            },
            "origin": fi_origin(
                "RiskChecker._check_self_invoice, _normalize_vat_id", "298-322, 398-406"
            ),
        },
        {
            "code": "SPLIT_INVOICE",
            "label": "Verdacht auf Rechnungssplitting",
            "kind": "split_window",
            "severity": "HIGH",
            "params": {
                "items_field": "context.vendor_invoices",
                "amount_key": "net_amount",
                "date_key": "invoice_date",
                "thresholds": c["SPLIT_INVOICE_THRESHOLDS"],
                "proximity": c["SPLIT_INVOICE_PROXIMITY"],
                "min_items": c["SPLIT_INVOICE_MIN_INVOICES"],
                "window_days": c["SPLIT_INVOICE_TIME_WINDOW_DAYS"],
            },
            "echo_fields": {"vendor_name": "vendor_name"},
            "messages": {
                "default": {
                    "description": "Verdacht auf Rechnungssplitting: {count} Rechnungen von "
                    "'{vendor_name}' im Bereich {lower:.0f}-{threshold:.0f} EUR (Schwelle: "
                    "{threshold:.0f} EUR)",
                    "evidence": "{count} Rechnungen mit Gesamtvolumen {total:.2f} EUR innerhalb "
                    "von {window_days} Tagen, alle knapp unterhalb der Vergabeschwelle von "
                    "{threshold:.0f} EUR",
                    "recommendation": "Prüfung ob eine absichtliche Aufteilung zur Umgehung von "
                    "Vergabeschwellen vorliegt. Gegebenenfalls zusammengefasste Beauftragung "
                    "prüfen.",
                }
            },
            "note": "Die zu prüfende Rechnung wird nicht automatisch ergänzt; Lieferantenfilter "
            "und Vollständigkeit der Liste liegen beim Aufrufer (wie in der Quelle).",
            "origin": fi_origin(
                "RiskChecker._check_split_invoices, SPLIT_INVOICE_*", "38-42, 324-396"
            ),
        },
    ]
    profile = {
        "schema": "auditcore_risk.profile/1",
        "id": "flowinvoice.risk_checker",
        "version": fx["source"]["commit"][:12],
        "kind": "invoice_risk_indicators",
        "status": "LEGACY_CHARACTERIZED",
        "legal_status": "Aus der Quellanwendung übernommenes, charakterisiertes Softwareverhalten "
        "(didaktische Hinweise für den Seminarbetrieb laut Quelle); keine rechtliche Bewertung. "
        "Der Score ist ausschließlich der Legacy-Score dieses Profils.",
        "source": {
            "repository": fx["source"]["repository"],
            "commit": fx["source"]["commit"],
            "path": FI_PATH,
            "git_blob": fx["source"]["files"][FI_PATH],
            "symbols": fx["source"]["symbols"],
            "rights": "USER_AUTHORIZED_MIT",
            "also_identical_in": fx["also_identical_in"],
            "input_contract": "Ein Datensatz je Rechnung wie RiskAssessmentRequest, Kontext "
            "flach als context.<feld> (flatten_record).",
            "characterization": "tests/fixtures/flowinvoice_risk_checker_observed.json",
        },
        "rules": rules,
        "output": {},
        "summary": {"format": "none"},
        "assessment": {
            "kind": "severity_weighted_sum",
            "weights": {"INFO": 0.1, "LOW": 0.2, "MEDIUM": 0.4, "HIGH": 0.7, "CRITICAL": 1.0},
            "fallback_weight": 0.5,
            "divisor": 5.0,
            "cap": 1.0,
            "severity_order": ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"],
            "summary": {
                "none": "Keine besonderen Risiken erkannt",
                "one": "1 Risiko mit {level} Priorität erkannt",
                "many": "{count} Risiken erkannt, höchste Priorität: {level}",
                "level_words": {
                    "INFO": "informativer",
                    "LOW": "geringer",
                    "MEDIUM": "mittlerer",
                    "HIGH": "hoher",
                    "CRITICAL": "kritischer",
                },
                "unknown_level": "unbekannter",
            },
            "source_version": "1.0.0",
        },
        "open_decisions": [
            "Kein Laufzeit-Consumer: RiskChecker wird in flowinvoice und audit-portal nicht "
            "aufgerufen; RiskCheckerConfig (ruleset) ist nicht angebunden.",
            "Score = Summe der Schweregewichte / 5, gedeckelt auf 1 – nur für dieses Profil; "
            "keine Vereinheitlichung mit anderen Profilen.",
            "VENDOR_CLUSTERING: Bezugsgröße (Rechnungen oder Lieferanten) fachlich klären.",
            "SPLIT_INVOICE: Schwellenliste 1.000–50.000 weicht von RF02 und den "
            "jahresbezogenen EU-Schwellen ab.",
        ],
    }
    return f"{profile['id']}-{profile['version']}.json", profile


FRAUD = ROOT / "src" / "auditcore_risk" / "fraud_profiles"
FD = "backend/app/services/fraud_detection/"


def fraud_profiles() -> list[tuple[str, dict[str, Any]]]:
    """flowinvoice fraud_detection: manager score, TED checker, duplicate detector."""
    fx = json.loads((FIXTURES / "flowinvoice_fraud_observed.json").read_text())
    commit = fx["source"]["commit"]
    files = fx["source"]["files"]
    ted_c = fx["constants"]["ted"]
    cfg = fx["constants"]["config"]

    def source(path: str, symbols: list[str]) -> dict[str, Any]:
        return {
            "repository": "janpow77/flowinvoice",
            "commit": commit,
            "path": FD + path,
            "git_blob": files[FD + path],
            "symbols": symbols,
            "rights": "USER_AUTHORIZED_MIT",
            "characterization": "tests/fixtures/flowinvoice_fraud_observed.json",
        }

    base = {
        "schema": "auditcore_risk.fraud-profile/1",
        "version": commit[:12],
        "status": "LEGACY_CHARACTERIZED",
    }
    signals = {
        **base,
        "id": "flowinvoice.fraud_signals",
        "kind": "signal_score",
        "legal_status": "Legacy-Score des FraudDetectionManager; Sanktions-, PEP- und "
        "Firmenergebnisse werden nur als Eingaben verarbeitet. Kein übergreifender Score.",
        "source": source(
            "manager.py",
            [
                "FraudDetectionManager.analyze_invoice",
                "_calculate_risk_score",
                "_determine_risk_level",
            ],
        ),
        "parameters": {
            "order": ["duplicate", "sanctions", "pep", "company", "ted"],
            "derivation": {
                "duplicate": {
                    "performed": "duplicate_check",
                    "exact_blocker": "EXACT_DUPLICATE_FOUND",
                    "fuzzy_warning": "POTENTIAL_DUPLICATE_FOUND",
                    "failed_warning": "DUPLICATE_CHECK_FAILED",
                },
                "sanctions": {
                    "performed": "sanctions_check",
                    "hit_blocker": "SANCTIONED_ENTITY",
                    "error_warning": "SANCTIONS_CHECK_ERROR",
                    "failed_warning": "SANCTIONS_CHECK_FAILED",
                },
                "pep": {
                    "performed": "pep_check",
                    "hit_warning": "PEP_HIT_FOUND",
                    "error_warning": "PEP_CHECK_ERROR",
                    "failed_warning": "PEP_CHECK_FAILED",
                },
                "company": {
                    "performed": "company_verification",
                    "blocker_indicators": ["INVALID_VAT_ID", "COMPANY_DISSOLVED"],
                    "ignored_indicators": ["NOT_IN_REGISTER", "VIES_SERVICE_UNAVAILABLE"],
                    "failed_warning": "COMPANY_CHECK_FAILED",
                },
                "ted": {
                    "performed": "ted_check",
                    "warning_severities": ["critical", "high"],
                    "default_severity": "low",
                    "warning_prefix": "TED_",
                    "unknown_type": "UNKNOWN",
                    "failed_warning": "TED_CHECK_FAILED",
                },
            },
            "score": {
                "per_blocker": 0.4,
                "per_warning": 0.1,
                "company_weight": 0.2,
                "duplicate_weight": 0.3,
                "sanctions_weight": 0.5,
                "pep_weight": 0.4,
                "ted_weight": 0.2,
                "cap": 1.0,
                "output_digits": 3,
            },
            "levels": {
                "blocker_level": "critical",
                "thresholds": [{"min": 0.7, "level": "high"}, {"min": 0.4, "level": "medium"}],
                "default": "low",
            },
        },
        "open_decisions": [
            "TED-Legitimität: Die Quelle übergibt ein Wörterbuch (Skala 0–100) statt einer Zahl "
            "0–1; mit TED-Merkmalen bricht die Quelle ab (RK-C09).",
            "Warnungen werden vor der Deduplizierung gezählt (Legacy).",
            "Pipeline-Regel FraudDetectionRule liest nicht vorhandene Attribute "
            "(risk_factors, hit_count) – Consumer-Fehler, nicht Teil dieses Profils.",
        ],
    }
    ted = {
        **base,
        "id": "flowinvoice.ted_contractor",
        "kind": "ted_contractor",
        "legal_status": "Legacy-Auswertung öffentlicher Aufträge eines Auftragnehmers; "
        "Zeitfenster 12/24/60 Monate sind in der Quelle nicht umgesetzt (alle = Gesamtzahl).",
        "source": source(
            "ted_checker.py",
            [
                "TedChecker._calculate_statistics",
                "_detect_red_flags",
                "_calculate_legitimacy_score",
                "_load_contracts",
            ],
        ),
        "parameters": {
            "top_n": 3,
            "empty_statistics": {
                "total_value_eur": 0,
                "avg_value_eur": 0,
                "contract_count_12m": 0,
                "contract_count_24m": 0,
                "contract_count_60m": 0,
                "top_authorities": [],
                "concentration_ratio": 0,
            },
            "unknown_authority": "Unbekannt",
            "flags": [
                {
                    "flag_type": "HIGH_CONTRACT_COUNT",
                    "severity": "medium",
                    "when": [
                        {
                            "metric": "contract_count_12m",
                            "op": "gt",
                            "value": ted_c["WARNING_CONTRACT_COUNT_12M"],
                        }
                    ],
                    "description": "Ungewöhnlich hohe Auftragsanzahl: {contract_count_12m} in "
                    "12 Monaten",
                    "evidence": {"contract_count_12m": "contract_count_12m"},
                },
                {
                    "flag_type": "HIGH_CONCENTRATION",
                    "severity": "medium",
                    "when": [
                        {
                            "metric": "concentration_ratio",
                            "op": "gt",
                            "value": ted_c["WARNING_CONCENTRATION_THRESHOLD"],
                        }
                    ],
                    "description": "Hohe Konzentration: {concentration_percent:.1f}% der Aufträge "
                    "bei einem Auftraggeber ({top1_name})",
                    "evidence": {
                        "concentration_ratio": "concentration_ratio",
                        "top_authorities": "top_authorities",
                    },
                },
                {
                    "flag_type": "EXTREME_CONCENTRATION",
                    "severity": "high",
                    "when": [
                        {
                            "metric": "concentration_ratio",
                            "op": "gt",
                            "value": ted_c["WARNING_EXTREME_CONCENTRATION_THRESHOLD"],
                        }
                    ],
                    "description": "Kritische Konzentration: {concentration_percent:.1f}% bei nur "
                    "einem Auftraggeber ({top1_name}) - mögliches Insider-Betrugsmuster",
                    "evidence": {
                        "concentration_ratio": "concentration_ratio",
                        "top_authorities": "top_authorities",
                    },
                },
                {
                    "flag_type": "LOW_AUTHORITY_DIVERSITY",
                    "severity": "low",
                    "when": [
                        {
                            "metric": "authority_count",
                            "op": "lt",
                            "value": ted_c["WARNING_MIN_AUTHORITY_COUNT"],
                        },
                        {"metric": "contract_count_12m", "op": "ge", "value": 3},
                    ],
                    "description": "Nur {authority_count} unterschiedliche Auftraggeber bei "
                    "{contract_count_12m} Aufträgen (begrenzte Diversifikation)",
                    "evidence": {
                        "authority_count": "authority_count",
                        "contract_count": "contract_count_12m",
                    },
                },
            ],
            "legitimacy": {
                "start": 50.0,
                "count_cap": 100,
                "count_divisor": 5,
                "count_max_points": 20,
                "distribution_points": 20,
                "concentration_factor": 20,
                "severity_penalties": {"low": 5, "medium": 15, "high": 30, "critical": 50},
                "clamp": [0, 100],
                "ratings": [{"min": 70, "rating": "HOCH"}, {"min": 40, "rating": "MITTEL"}],
                "default_rating": "NIEDRIG",
                "digits": 1,
            },
        },
        "open_decisions": [
            "Zeitfenster 12/24/60 Monate fehlen in der Quelle (TODO); WARNING_GROWTH_THRESHOLD "
            f"= {ted_c['WARNING_GROWTH_THRESHOLD']} ungenutzt.",
            "audit-portal nutzt eine abweichende Variante (ILIKE-Teilstring, echte Zeitfenster); "
            "sie ist nicht Teil dieses Profils.",
            "Datengrundlage: TED-Bekanntmachungen im notice/1-Vertrag von auditcore_procurement.",
        ],
    }
    duplicates = {
        **base,
        "id": "flowinvoice.duplicates",
        "kind": "duplicates",
        "legal_status": "Legacy-Dublettenprüfung; Kandidatenvorauswahl (SQL-Zeitfenster über "
        "created_at, LIMIT 500) bleibt in der Anwendung.",
        "source": source(
            "duplicate_detector.py",
            [
                "DuplicateDetector._find_exact_duplicates",
                "_find_fuzzy_duplicates",
                "_names_similar",
                "_parse_date",
                "_compute_hash",
            ],
        ),
        "parameters": {
            "exact": {
                "tolerance": "0.01",
                "confidence": 1.0,
                "missing_amount": "0",
                "invalid_amount": "0",
                "amount_replacements": [[",", "."], [" ", ""]],
            },
            "fuzzy": {
                "amount_tolerance": cfg["duplicate_fuzzy_tolerance"],
                "date_range_days": 7,
                "missing_amount": "0",
                "amount_replacements": [[",", "."], [" ", ""], ["€", ""]],
                "date_formats": [
                    "%Y-%m-%d",
                    "%d.%m.%Y",
                    "%d/%m/%Y",
                    "%m/%d/%Y",
                    "%d-%m-%Y",
                    "%Y/%m/%d",
                ],
                "min_containment": 5,
                "leading_words": 3,
                "amount_weight": 0.5,
                "date_weight": 0.5,
                "digits": 3,
                "name_chars": 100,
            },
        },
        "open_decisions": [
            "Namensheuristik: ein gemeinsames Wort unter den ersten drei genügt (z. B. 'gmbh').",
            "USt-IdNr. wird trotz Parameter nicht verwendet; der berechnete Hash ist ungenutzt.",
            "Mehrdeutige Datumsangaben: europäisches Format vor US-Format.",
        ],
    }
    return [(f"{d['id']}-{d['version']}.json", d) for d in (signals, ted, duplicates)]


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    for name, document in build():
        (DATA / name).write_text(
            json.dumps(document, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
        )
        print(name)
    for name, document in fraud_profiles():
        (FRAUD / name).write_text(
            json.dumps(document, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
        )
        print(name)


if __name__ == "__main__":
    main()
