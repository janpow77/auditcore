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
        *verwk_profiles(),
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


VK = "backend/app/verwk/pipeline/"
TRUTHY = [
    "1",
    "true",
    "ja",
    "j",
    "x",
    "yes",
    "y",
    "eu",
    "eu-weit",
    "europaweit",
    "hochschule",
    "forschung",
]


def _truthy(code: str, label: str, fields: list[str], points: int, lines: str) -> dict[str, Any]:
    return {
        "code": code,
        "label": label,
        "kind": "truthy_all",
        "points": points,
        "params": {"fields": fields, "truthy_values": TRUTHY},
        "origin": {
            "path": VK + "rbvk_wibank_scorer.py",
            "symbol": "score_mittelabrufe, _bool",
            "lines": lines,
        },
    }


def _range(
    code: str,
    label: str,
    field: str,
    lower: float | None,
    upper: float | None,
    points: int,
    origin: dict[str, Any],
    *,
    lower_inclusive: bool = False,
    upper_inclusive: bool = False,
    missing: float = 0,
) -> dict[str, Any]:
    return {
        "code": code,
        "label": label,
        "kind": "number_range",
        "points": points,
        "params": {
            "field": field,
            "lower": lower,
            "lower_inclusive": lower_inclusive,
            "upper": upper,
            "upper_inclusive": upper_inclusive,
            "missing_value": missing,
        },
        "origin": origin,
    }


def verwk_profiles() -> list[tuple[str, dict[str, Any]]]:
    """flowinvoice VerwK: WIBANK-RBVK points, ex-ante heuristic and ex-ante basis weights."""
    fx = json.loads((FIXTURES / "flowinvoice_verwk_scores_observed.json").read_text())
    commit = fx["source"]["commit"]
    files = fx["source"]["files"]
    legal = (
        "Aus der Quellanwendung übernommenes, charakterisiertes Softwareverhalten der "
        "Verwaltungskontrolle (VerwK); Punkte und Stufen ausschließlich dieses Profils, "
        "keine Vereinheitlichung mit anderen Scores."
    )

    def src(path: str, symbols: list[str]) -> dict[str, Any]:
        return {
            "repository": "janpow77/flowinvoice",
            "commit": commit,
            "path": VK + path,
            "git_blob": files[VK + path],
            "symbols": symbols,
            "rights": "USER_AUTHORIZED_MIT",
            "also_present_in": fx["also_present_in"],
            "characterization": "tests/fixtures/flowinvoice_verwk_scores_observed.json",
        }

    wb = {"path": VK + "rbvk_wibank_scorer.py", "symbol": "score_mittelabrufe"}
    rules = [
        _truthy("K1", "Verbundvorhaben", ["verbundvorhaben"], 1, "237"),
        {
            "code": "K2",
            "label": "FPG 1008/1009/1010",
            "kind": "text_in_set",
            "points": 1,
            "params": {"field": "fpg", "values": ["1008", "1009", "1010"], "missing_text": ""},
            "origin": {**wb, "lines": "238"},
        },
        _truthy("K3", "Bau", ["hat_bau"], 1, "239"),
        _truthy("K4", "Abschreibung", ["hat_absch"], 2, "240"),
        _truthy("K5", "Sachleistung", ["hat_sachleist"], 1, "241"),
        _truthy(
            "K7",
            "Beihilfefrei und Trennungsrechnung",
            ["beihilfefrei", "trennungsrechnung_erforderlich"],
            1,
            "242",
        ),
        _range(
            "K8",
            "Projektbudget 1,5 Mio – 5 Mio",
            "projekt_budget",
            1_500_000,
            5_000_000,
            1,
            {**wb, "lines": "243-244"},
            upper_inclusive=True,
        ),
        _range(
            "K9",
            "Projektbudget > 5 Mio",
            "projekt_budget",
            5_000_000,
            None,
            1,
            {**wb, "lines": "243, 245"},
        ),
        _truthy("K10", "Offene Auflagen", ["offene_auflagen"], 1, "246"),
        _truthy("K11", "Kein früheres Vorhaben des Begünstigten", ["erstes_vorhaben"], 3, "247"),
        _range("K12", "Frühere Kürzung > 0", "prior_k", 0, None, 2, {**wb, "lines": "224, 248"}),
        _truthy("K13", "Öffentlich-rechtlich", ["oeffentlich_rechtlich"], -1, "249"),
        _truthy("K14", "Öffentlicher Auftraggeber", ["oeffentlicher_auftraggeber"], 2, "250"),
        _range("K16", "Frühere Quote > 0", "prior_q", 0, None, 2, {**wb, "lines": "225, 251"}),
        _range(
            "K17",
            "Frühere Quote 25–50",
            "prior_q",
            25,
            50,
            1,
            {**wb, "lines": "252"},
            upper_inclusive=True,
        ),
        _range("K18", "Frühere Quote > 50", "prior_q", 50, None, 1, {**wb, "lines": "253"}),
        _range("K19", "Frühere Quote unter 5", "prior_q", 0, 5, -2, {**wb, "lines": "254"}),
        {
            "code": "K20",
            "label": "Frühere Familie Vergabe",
            "kind": "set_overlap",
            "points": 1,
            "params": {
                "field": "prior_families",
                "values": ["Vergaberecht", "Vergabe"],
                "mode": "any",
            },
            "origin": {**wb, "lines": "255"},
        },
        {
            "code": "K21",
            "label": "Frühere Familie Beihilfe",
            "kind": "set_overlap",
            "points": 1,
            "params": {
                "field": "prior_families",
                "values": ["Beihilferecht", "Beihilfe"],
                "mode": "any",
            },
            "origin": {**wb, "lines": "256"},
        },
        {
            "code": "K22",
            "label": "Sonstige frühere Familie",
            "kind": "set_overlap",
            "points": 1,
            "params": {
                "field": "prior_families",
                "values": ["Vergaberecht", "Vergabe", "Beihilferecht", "Beihilfe"],
                "mode": "outside",
            },
            "origin": {**wb, "lines": "257"},
            "note": "Eigene frühere Mittelabrufe tragen die Familie '' (prior_familie wird nie "
            "gesetzt) und lösen K22 aus (HUMAN_DECISION_REQUIRED).",
        },
        _truthy("K23", "Vergabe vorhanden", ["hat_vergabe"], 1, "258"),
        _truthy("K24", "EU-weite Vergabe", ["eu_vergaberelevant"], 1, "259"),
        _range("K25", "Direkte Belege > 80", "n_direct", 80, None, 1, {**wb, "lines": "260"}),
        _truthy("K26", "Sachkosten", ["hat_sach"], 1, "261"),
        _range("K28", "Abrufanteil > 0,5", "abruf_anteil", 0.5, None, 2, {**wb, "lines": "262"}),
    ]
    wibank = {
        "schema": "auditcore_risk.profile/1",
        "id": "flowinvoice.rbvk_wibank",
        "version": commit[:12],
        "kind": "points_score",
        "status": "LEGACY_CHARACTERIZED",
        "legal_status": legal + " Bildet das Codeverhalten ab, nicht die Profildatei "
        "rbvk_wibank.json (V1.21), die die Quelle nicht liest.",
        "source": src("rbvk_wibank_scorer.py", ["score_mittelabrufe"]),
        "rules": rules,
        "output": {},
        "summary": {"format": "none"},
        "assessment": {
            "kind": "points_stages",
            "stages": [{"min": 19, "stage": "vollpruefung"}, {"min": 8, "stage": "teilpruefung"}],
            "default_stage": "keine_pruefung",
            "cap": None,
            "detail_template": None,
            "points_override": "forbidden",
            "source_version": "WIBANK-RBVK V1.21 (Code)",
        },
        "open_decisions": [
            "Code weicht von rbvk_wibank.json ab: K10 +1 statt score_max 2; 13.* zählt als "
            "Beihilfe (K21) statt Sonstige (K22); K12 und K16 greifen praktisch gleich.",
            "K22 greift für jeden Begünstigten mit früherem Mittelabruf (Familie '').",
            "Merkmalsaufbereitung (_normalise_sources), Vorhistorie (CSV, MA-Versionen) und "
            "'nicht abbildbar' bleiben in der Anwendung; Eingaben sind aufbereitete Merkmale.",
            "Stufengrenzen 8/19 (Parameter wibank_score_teil_ab/voll_ab); andere Werte = eigene "
            "Profilversion.",
        ],
    }
    ex = {"path": VK + "exante_score.py"}
    heur_origin = {**ex, "symbol": "heuristik_score"}
    heuristik = {
        **{k: v for k, v in wibank.items() if k not in ("rules", "assessment", "open_decisions")},
        "id": "flowinvoice.exante_heuristik",
        "legal_status": legal + " Bisherige gesetzte Vergleichsheuristik (nur Validierung).",
        "source": src("exante_score.py", ["heuristik_score"]),
        "rules": [
            _range(
                "H1",
                "Budget > 1 Mio",
                "brutto",
                1_000_000,
                None,
                20,
                {**heur_origin, "lines": "88-89"},
            ),
            _range(
                "H2",
                "Budget 500 T – 1 Mio",
                "brutto",
                500_000,
                1_000_000,
                15,
                {**heur_origin, "lines": "90-91"},
                upper_inclusive=True,
            ),
            _range(
                "H3",
                "Kürzungsquote > 20",
                "kuerzungsquote",
                20,
                None,
                15,
                {**heur_origin, "lines": "92-93"},
            ),
            _range(
                "H4",
                "Kürzungsquote 10–20",
                "kuerzungsquote",
                10,
                20,
                8,
                {**heur_origin, "lines": "94-95"},
                upper_inclusive=True,
            ),
            _range(
                "H5",
                "Laufzeit > 36 Monate",
                "laufzeit_monate",
                36,
                None,
                10,
                {**heur_origin, "lines": "96-98"},
            ),
            _range(
                "H6",
                "Laufzeit 24–36 Monate",
                "laufzeit_monate",
                24,
                36,
                6,
                {**heur_origin, "lines": "99-100"},
                upper_inclusive=True,
            ),
            _range(
                "H7", "Mittelabrufe > 5", "ma", 5, None, 10, {**heur_origin, "lines": "101-102"}
            ),
            _range(
                "H8", "Belege > 200", "belege", 200, None, 15, {**heur_origin, "lines": "103-104"}
            ),
            _range(
                "H9",
                "Belege 100–200",
                "belege",
                100,
                200,
                10,
                {**heur_origin, "lines": "105-106"},
                upper_inclusive=True,
            ),
            _range(
                "H10",
                "Gruppe mit höchstens einem Vorhaben",
                "gruppe_vorhaben",
                None,
                1,
                20,
                {**heur_origin, "lines": "107-109"},
                upper_inclusive=True,
                missing=1,
            ),
            _range(
                "H11",
                "Gruppe mit mehr als drei Vorhaben",
                "gruppe_vorhaben",
                3,
                None,
                15,
                {**heur_origin, "lines": "110-111"},
                missing=1,
            ),
            _range(
                "H12",
                "FPG-Quote > 15",
                "fpg_quote",
                15,
                None,
                20,
                {**heur_origin, "lines": "112-113"},
            ),
            _range(
                "H13",
                "FPG-Quote 2–15",
                "fpg_quote",
                2,
                15,
                10,
                {**heur_origin, "lines": "114-115"},
                upper_inclusive=True,
            ),
            _range(
                "H14",
                "FPG-Rückgabequote > 40",
                "fpg_rueckgabequote",
                40,
                None,
                10,
                {**heur_origin, "lines": "116-117"},
            ),
        ],
        "assessment": {
            "kind": "points_stages",
            "stages": [],
            "default_stage": None,
            "cap": 100,
            "detail_template": None,
            "points_override": "forbidden",
            "source_version": "heuristik_score",
        },
        "open_decisions": ["Nur Vergleichsbasis der Kalibrierung; kein produktiver Score."],
    }
    feat = {**ex, "symbol": "_features, kalibriere_und_score"}
    basis = {
        **{k: v for k, v in wibank.items() if k not in ("rules", "assessment", "open_decisions")},
        "id": "flowinvoice.exante_basis",
        "legal_status": legal + " Sieben ex-ante-Indikatoren mit den dokumentierten "
        "Basisgewichten (Fallback); kalibrierte Gewichte kann der Consumer ausdrücklich übergeben.",
        "source": src("exante_score.py", ["_features", "kalibriere_und_score"]),
        "rules": [
            _range(
                "E1",
                "Budget > 1 Mio €",
                "brutto",
                1_000_000,
                None,
                20,
                {**feat, "lines": "143, 245-253"},
            ),
            _range(
                "E2",
                "Budget 500 T€–1 Mio €",
                "brutto",
                500_000,
                1_000_000,
                15,
                {**feat, "lines": "144"},
                upper_inclusive=True,
            ),
            _range(
                "E3",
                "Geplante Laufzeit > 24 M",
                "laufzeit_monate",
                24,
                None,
                6,
                {**feat, "lines": "145-147"},
            ),
            _range(
                "E4",
                "Erwartete Mittelabrufe hoch (> 4)",
                "erw_ma",
                4,
                None,
                10,
                {**feat, "lines": "148-150"},
            ),
            _range(
                "E5",
                "FPG-Fehlerquote historisch hoch (> 15 %)",
                "fpgq",
                15,
                None,
                10,
                {**feat, "lines": "151"},
            ),
            _range(
                "E6",
                "Erstantragsteller",
                "grp_v",
                None,
                1,
                10,
                {**feat, "lines": "152"},
                upper_inclusive=True,
                missing=1,
            ),
            _range(
                "E7",
                "Auftragnehmer-Risiko (> 30 %)",
                "an_risiko",
                0.3,
                None,
                15,
                {**feat, "lines": "153"},
            ),
        ],
        "assessment": {
            "kind": "points_stages",
            "stages": [{"min": 55, "stage": "hoch"}, {"min": 30, "stage": "mittel"}],
            "default_stage": "niedrig",
            "cap": None,
            "detail_template": "{label} (+{points})",
            "points_override": "allowed",
            "source_version": "kalibriere_und_score (Basisgewichte)",
        },
        "open_decisions": [
            "Produktive Gewichte entstehen zur Laufzeit per Logit-Kalibrierung (statsmodels); die "
            "Kalibrierung bleibt beim Consumer, übergebene Gewichte werden unverändert "
            "angewandt.",
            "Klassengrenzen 30/55 gelten für kalibrierte und Basisgewichte gleichermaßen.",
            "Eingaben erwartete Mittelabrufe (OLS) und Auftragnehmer-Risiko (leave-one-out) "
            "berechnet der Consumer.",
        ],
    }
    return [(f"{d['id']}-{d['version']}.json", d) for d in (wibank, heuristik, basis)]


DECIDED_ON = "2026-09-23"
DECISION_QUOTE = "alle empfehlungen"
EU_SUPPLY = {
    "profile": "procurement.hvtg",
    "version": "2026.09.2",
    "category": "supply_service",
    "authority_type": "sub_central",
    "date_source": "record",
}


def _decision(ids: list[str], text: str) -> dict[str, Any]:
    return {"decided_on": DECIDED_ON, "quote": DECISION_QUOTE, "decisions": ids, "effect": text}


def decided_profiles(
    built: dict[str, dict[str, Any]],
) -> tuple[list[tuple[str, dict[str, Any]]], list[tuple[str, dict[str, Any]]]]:
    """Recommended profiles implementing the user decisions of 23.09.2026.

    Legacy profiles stay bit-identical; every decision becomes a new, approved
    profile version derived from the legacy document.
    """

    def clone(doc: dict[str, Any]) -> dict[str, Any]:
        copied: dict[str, Any] = json.loads(json.dumps(doc))
        return copied

    legacy = built["riskanalysis.legacy"]
    ra = clone(legacy)
    ra.update(
        {
            "id": "riskanalysis.year_bound",
            "version": "2026.09.2",
            "status": "APPROVED",
            "legal_status": LEGAL + " Freigegeben durch Nutzerentscheidung vom 23.09.2026 "
            "('alle empfehlungen'): Schwellen netto (K2), jahresbezogene EU-Schwellen (K3), RF12 "
            "nur innerhalb der Gruppe (K5).",
        }
    )
    ra["source"]["derived_from"] = {"profile": legacy["id"], "version": legacy["version"]}
    ra["source"]["decision"] = _decision(
        ["K2", "K3", "K5"],
        "RF02/RF08 auf Nettobetrag, RF02 mit EU-Schwelle des Rechnungsjahres, RF12 gruppenintern.",
    )
    for rule in ra["rules"]:
        if rule["code"] == "RF02":
            rule["label"] = (
                "Beleg (netto) knapp unter Vergabe-/Schwellenwert (EU-Schwelle jahresbezogen)"
            )
            rule["requires"] = ["nettobetrag"]
            rule["params"]["field"] = "nettobetrag"
            rule["params"]["thresholds"] = {
                "static": [t for t in rule["params"]["thresholds"]["static"] if t != 221000.0],
                "procurement_eu": {**EU_SUPPLY, "date_field": "rechnungsdatum_dt"},
            }
            rule["note"] = (
                "Nettobetrag (K2) gegen nationale Wertgrenzen und die EU-Schwelle des "
                "Rechnungsjahres aus auditcore_procurement (K3; 2026: 216.000 €). Ohne "
                "belegten Zeitraum bleibt der Beleg unbestimmt."
            )
        if rule["code"] == "RF08":
            rule["label"] = (
                "Beleg netto > 25 T€ ohne echte Vergabe-Kennung (vergaberelevante Kostenart)"
            )
            rule["requires"] = ["nettobetrag"]
            rule["params"]["amount_field"] = "nettobetrag"
            rule["note"] = "Bagatellgrenze gegen den Nettobetrag (K2)."
        if rule["code"] == "RF12":
            rule["params"]["propagation"] = "same_group"
            rule["note"] = (
                rule.get("note", "") + " Merkmal nur innerhalb derselben Gruppe übertragen (K5)."
            ).strip()
    ra["open_decisions"] = [
        "RF09: Umschrift 'mueller' (K4) folgt, sobald auditcore_entity_matching das neue Profil "
        "riskanalysis.payee bereitstellt.",
        "Stichtag der EU-Schwelle ist das Rechnungsdatum (rechnungsdatum_dt); Auftraggebertyp "
        "subzentral und Kategorie Liefer-/Dienstleistungen je Beleg sind Profilvorgaben.",
    ]

    rc_legacy = built["flowinvoice.risk_checker"]
    rc = clone(rc_legacy)
    rc.update({"version": "2026.09.2", "status": "APPROVED"})
    rc["source"]["derived_from"] = {"profile": rc_legacy["id"], "version": rc_legacy["version"]}
    rc["source"]["decision"] = _decision(
        ["K7", "K9"],
        "Splitting-Schwellen um die EU-Schwelle "
        "des Rechnungsjahres ergänzt; RiskChecker wird nicht "
        "aktiviert.",
    )
    for rule in rc["rules"]:
        if rule["code"] == "SPLIT_INVOICE":
            rule["params"]["procurement_eu"] = {**EU_SUPPLY, "date_field": "invoice_date"}
            rule["note"] = (
                "Schwellenliste 1.000–50.000 plus EU-Schwelle des Rechnungsjahres aus "
                "auditcore_procurement (K9). Fehlt der belegte Zeitraum und trifft keine "
                "nationale Schwelle, bleibt die Rechnung unbestimmt."
            )
    rc["open_decisions"] = ["Nicht aktiviert (K7): kein Laufzeit-Consumer vorgesehen."]

    wb_legacy = built["flowinvoice.rbvk_wibank"]
    wb = clone(wb_legacy)
    wb.update(
        {
            "version": "2026.09.2",
            "status": "APPROVED",
            "legal_status": wb_legacy["legal_status"].split(" Bildet")[0] + " Nach Profildatei "
            "RBVK WIBANK V1.21 korrigiert (Entscheidung K11 vom 23.09.2026).",
        }
    )
    wb["source"]["derived_from"] = {"profile": wb_legacy["id"], "version": wb_legacy["version"]}
    wb["source"]["profile_file"] = {
        "path": "backend/app/verwk/data/rbvk_wibank.json",
        "git_blob": "f1434e6eeaa6b257cc3b6ed11623cb118af3ffd9",
        "version": "1.21",
        "stand": "2025-01-07",
    }
    wb["source"]["decision"] = _decision(
        ["K11"],
        "K10 je offene Auflage bis 2 Punkte, K12 "
        "externe Prüfungsfeststellungen getrennt von K16 "
        "Verwaltungskontrolle, K20–K22 nach Kürzungsgrund-Codes.",
    )
    origin = {"path": "backend/app/verwk/data/rbvk_wibank.json", "symbol": "scoring.kriterien"}
    codes_1 = [f"1.{i}" for i in range(1, 25)]

    def overlap(code: str, label: str, values: list[str]) -> dict[str, Any]:
        return {
            "code": code,
            "label": label,
            "kind": "set_overlap",
            "points": 1,
            "params": {"field": "vorherige_kuerzungsgruende", "values": values, "mode": "any"},
            "origin": {**origin, "lines": f"nr {code[1:]}"},
        }

    replaced = {
        "K10": [
            _range(
                "K10",
                "Bewilligte offene Auflagen (1. Auflage)",
                "offene_auflagen_anzahl",
                1,
                None,
                1,
                {**origin, "lines": "nr 10"},
                lower_inclusive=True,
            ),
            _range(
                "K10b",
                "Bewilligte offene Auflagen (2. Auflage, score_max 2)",
                "offene_auflagen_anzahl",
                2,
                None,
                1,
                {**origin, "lines": "nr 10"},
                lower_inclusive=True,
            ),
        ],
        "K12": [
            _range(
                "K12",
                "Kürzung aufgrund von Feststellungen der KOM, Rechnungshöfe oder Prüfbehörde",
                "externe_kuerzung",
                0,
                None,
                2,
                {**origin, "lines": "nr 12"},
            )
        ],
        "K16": [
            _range(
                "K16",
                "Schlechte Ergebnisse vorheriger Verwaltungskontrollen",
                "vorherige_verwk_quote",
                0,
                None,
                2,
                {**origin, "lines": "nr 16"},
            )
        ],
        "K17": [
            _range(
                "K17",
                "Historische Differenz über 25 Prozent",
                "vorherige_verwk_quote",
                25,
                50,
                1,
                {**origin, "lines": "nr 17"},
                upper_inclusive=True,
            )
        ],
        "K18": [
            _range(
                "K18",
                "Historische Differenz über 50 Prozent",
                "vorherige_verwk_quote",
                50,
                None,
                1,
                {**origin, "lines": "nr 18"},
            )
        ],
        "K19": [
            _range(
                "K19",
                "Historische Differenz unter 5 Prozent",
                "vorherige_verwk_quote",
                0,
                5,
                -2,
                {**origin, "lines": "nr 19"},
            )
        ],
        "K20": [overlap("K20", "Vorherige Kürzungsgründe 1.1 bis 1.24", codes_1)],
        "K21": [overlap("K21", "Vorherige Kürzungsgründe 5.1 oder 5.2", ["5.1", "5.2"])],
        "K22": [
            overlap(
                "K22",
                "Vorherige Kürzungsgründe 8.1–8.3, 8.8 oder 13.1",
                ["8.1", "8.2", "8.3", "8.8", "13.1"],
            )
        ],
    }
    rules = []
    for rule in wb["rules"]:
        rules.extend(replaced.get(rule["code"], [rule]))
    wb["rules"] = rules
    wb["assessment"]["source_version"] = "WIBANK-RBVK V1.21 (Profildatei)"
    wb["open_decisions"] = [
        "Eingaben: offene_auflagen_anzahl (Zahl), externe_kuerzung (Prüfungsfeststellungen "
        "KOM/ERH/PB), vorherige_verwk_quote (eigene frühere Verwaltungskontrollen), "
        "vorherige_kuerzungsgruende (Codes wie '1.3', '13.1', auch aus eigenen früheren "
        "Mittelabrufen – prior_familie korrekt setzen). Aufbereitung beim Consumer.",
        "K8/K9 und K17/K18 wie im Code (1,5–5 Mio bzw. 25–50 % ohne Überlappung).",
    ]

    fraud_sig = clone(built["flowinvoice.fraud_signals"])
    fraud_sig.update({"version": "2026.09.2", "status": "APPROVED"})
    fraud_sig["source"]["derived_from"] = {
        "profile": "flowinvoice.fraud_signals",
        "version": built["flowinvoice.fraud_signals"]["version"],
    }
    fraud_sig["source"]["decision"] = _decision(
        ["K8"], "TED-Legitimität 0–1, Warnungen nach Dublettenentfernung zählen."
    )
    fraud_sig["parameters"]["policy"] = {
        "warning_count": "after_dedup",
        "ted_legitimacy_scale": "unit_interval",
    }
    fraud_sig["open_decisions"] = []
    ted = clone(built["flowinvoice.ted_contractor"])
    ted.update({"version": "2026.09.2", "status": "APPROVED"})
    ted["source"]["derived_from"] = {
        "profile": "flowinvoice.ted_contractor",
        "version": built["flowinvoice.ted_contractor"]["version"],
    }
    ted["source"]["decision"] = _decision(
        ["K8"], "Legitimitätswert als Anteil 0–1 (Rating unverändert auf der 0–100-Skala bestimmt)."
    )
    ted["parameters"]["legitimacy"]["unit"] = "fraction"
    ted["parameters"]["legitimacy"]["digits"] = 3
    ra3 = clone(ra)
    ra3["version"] = "2026.09.3"
    ra3["legal_status"] = ra["legal_status"].replace(
        "RF12 nur innerhalb der Gruppe (K5).",
        "RF12 nur innerhalb der Gruppe (K5), RF09 mit Umschrift 'mueller' (K4).",
    )
    ra3["source"]["derived_from"] = {"profile": ra["id"], "version": ra["version"]}
    ra3["source"]["decision"] = _decision(
        ["K2", "K3", "K4", "K5"],
        "Wie 2026.09.2; RF09 normalisiert mit riskanalysis.payee 2026.09.2 "
        "(Müller → mueller, auch zerlegte Umlaute).",
    )
    for rule in ra3["rules"]:
        if rule["code"] == "RF09":
            rule["params"]["normalization"] = {
                "profile": "riskanalysis.payee",
                "version": "2026.09.2",
            }
            rule["note"] = (
                "Rechnungssteller-Normalisierung riskanalysis.payee 2026.09.2 "
                "(auditcore_entity_matching, Umschrift ä → ae, K4); rapidfuzz Pflicht."
            )
    ra3["open_decisions"] = [
        "Stichtag der EU-Schwelle ist das Rechnungsdatum (rechnungsdatum_dt); Auftraggebertyp "
        "subzentral und Kategorie Liefer-/Dienstleistungen je Beleg sind Profilvorgaben.",
    ]
    risk = [(f"{d['id']}-{d['version']}.json", d) for d in (ra, ra3, rc, wb)]
    fraud = [(f"{d['id']}-{d['version']}.json", d) for d in (fraud_sig, ted)]
    return risk, fraud


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    built_risk = build()
    built_fraud = fraud_profiles()
    decided_risk, decided_fraud = decided_profiles(
        {d["id"]: d for _, d in [*built_risk, *built_fraud] if d["version"] != "2026.09.1"}
    )
    for name, document in [*built_risk, *decided_risk]:
        (DATA / name).write_text(
            json.dumps(document, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
        )
        print(name)
    for name, document in [*built_fraud, *decided_fraud]:
        (FRAUD / name).write_text(
            json.dumps(document, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
        )
        print(name)


if __name__ == "__main__":
    main()
