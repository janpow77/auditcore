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
        (f"{legacy['id']}-{legacy['version']}.json", legacy),
        (f"{year_bound['id']}-{year_bound['version']}.json", year_bound),
        (f"{flowstat['id']}-{flowstat['version']}.json", flowstat),
    ]


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    for name, document in build():
        (DATA / name).write_text(
            json.dumps(document, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
        )
        print(name)


if __name__ == "__main__":
    main()
