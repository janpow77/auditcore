"""Erzeugt ``docs/eingabefelder.md`` aus allen Regelprofilen in ``profile_data``.

Je Profil entsteht eine Tabelle Feld | Regeln | Bedeutung | Pflicht/optional |
Verhalten bei fehlender Spalte oder leerem Wert. Welche Felder eine Regel liest,
ergibt sich aus den Parametern ihrer Regelart (``field``, ``amount_field``,
``id_field``, ``relevance.field``, ``thresholds.procurement_eu.date_field`` …);
das Verhalten bei fehlenden Daten wird aus ``requires``/``when_missing_columns``,
``missing_value``, ``missing_amount_reason``, ``column_missing_value``,
``id_column_missing``, ``relevance.column_missing`` und der Mechanik der
Regelart abgeleitet (``rules.py``, ``invoice_rules.py``, ``score_rules.py``).

Die Bedeutung der Felder stammt aus den genannten Quellen (Quellcode der
Anwendungen zum charakterisierten Stand, Profilinhalt, Paketdokumentation);
ohne Beleg steht „Bedeutung laut Quelle nicht dokumentiert“.

Aufruf (im Paketverzeichnis)::

    python tools/document_fields.py          # schreibt docs/eingabefelder.md
    python tools/document_fields.py --check  # Exit 1, wenn die Datei veraltet ist

``tests/test_eingabefelder.py`` prüft, dass die Datei aktuell ist.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from auditcore_risk.profiles import fingerprint, profile_from_dict
from auditcore_risk.rules import KINDS

ROOT = Path(__file__).resolve().parents[1]
PROFILE_DIR = ROOT / "src" / "auditcore_risk" / "profile_data"
OUTPUT = ROOT / "docs" / "eingabefelder.md"
UNDOCUMENTED = "Bedeutung laut Quelle nicht dokumentiert"

# --------------------------------------------------------------------------- Belege

RA = "riskanalysis@b5c523b"
RA_REPORT = f"{RA} `backend/app/services/report.py` (`FELD_ERKLAERUNG`)"
RA_LOADER = f"{RA} `backend/app/pipeline/mdb_loader.py` (`load_raw`)"
RA_LOADER_NET = "riskanalysis@9a5b624 `backend/app/pipeline/mdb_loader.py` (`load_raw`)"
RA_FLAGS = f"{RA} `backend/app/pipeline/red_flags.py`"
RA_PAYEE = f"{RA} `backend/app/pipeline/payee_normalizer.py` (`add_payee_columns`)"
RA_PSEUDO = f"{RA} `backend/app/services/pseudonymization.py`"
RA_SCHEMA = "Tabellenschema `t_Auswertung_Gesamt` der riskanalysis-Datenbank (nur Spaltennamen)"
DECISIONS = "`docs/behavior-changes.md` (K2, K2a)"
AD_BELEGLISTE = (
    "audit_designer@1254591 `backend/app/modules/flowstat/services/"
    "belegliste_analysis_service.py` (`ROLE_ALIASES`, `ROLE_CANONICAL_COLUMNS`, "
    "`normalize_belegliste`)"
)
FI_SCHEMA = "flowinvoice@fb2d185 `backend/app/schemas/risk.py`"
FI_WIBANK = "flowinvoice@fb2d185 `backend/app/verwk/pipeline/rbvk_wibank_scorer.py`"
FI_EXANTE = "flowinvoice@fb2d185 `backend/app/verwk/pipeline/exante_score.py`"
CAPTURE_VERWK = "`tools/capture_flowinvoice_verwk_scores.py`"


@dataclass(frozen=True)
class Meaning:
    """Bedeutung eines Eingabefelds mit Beleg."""

    text: str
    source: str


def _riskanalysis() -> dict[str, Meaning]:
    return {
        "bruttobetrag": Meaning(
            "Geltend gemachter Betrag eines Belegs (vor Prüfung). Quellspalte "
            "`bruttobetrag` in `t_Auswertung_Gesamt`.",
            f"{RA_REPORT}; {RA_LOADER}",
        ),
        "nettobetrag": Meaning(
            "Nettobetrag des Belegs. `t_Auswertung_Gesamt` hat keine Nettospalte; "
            "riskanalysis übernimmt die Spalte „Gesamt Netto“ der hessischen Belegliste "
            "als `nettobetrag` und leitet nichts aus dem Bruttobetrag ab.",
            f"{RA_LOADER_NET}; {DECISIONS}",
        ),
        "abweichungen_betrag": Meaning(
            "Kürzung = Bruttobetrag − anerkannter Betrag (finanzielle Feststellung).",
            RA_REPORT,
        ),
        "kostenart_auswertung_bezeichnung": Meaning(
            "Aggregierte Kostenart (z. B. „Bauliche Investitionen“, „Personalausgaben“).",
            RA_REPORT,
        ),
        "zahlungsempfaenger": Meaning(
            "Rechnungssteller / Auftragnehmer eines Belegs (≠ Begünstigter).",
            RA_REPORT,
        ),
        "Gruppennummer": Meaning(
            "Konzern-/Verflechtungsgruppe des Begünstigten; aus Tabelle `t_Namen` über "
            "die Antragsnummer zugeordnet.",
            f"{RA_REPORT}; {RA_LOADER}",
        ),
        "vergabenummer": Meaning("Vergabeverfahren-Referenz des Belegs.", RA_REPORT),
        "Name": Meaning(
            "Name des Begünstigten; aus Tabelle `t_Namen` über die Antragsnummer zugeordnet.",
            f"{RA_LOADER}; {RA_FLAGS} (`compute_red_flags`)",
        ),
        "antrag": Meaning(
            "Vorhaben-ID: `t_Auswertung_Antragsnummer` als Ganzzahl (eindeutige, "
            "8-stellige Vorhaben-ID).",
            f"{RA_LOADER}; {RA_REPORT}",
        ),
        "payee_canonical": Meaning(
            "Normalisierter Name des Zahlungsempfängers (`normalize_name` auf "
            "`zahlungsempfaenger`).",
            RA_PAYEE,
        ),
        "_pseudonym_rf09": Meaning(
            "In pseudonymisierten Beständen vor dem Ersetzen der Namen berechnetes "
            "RF09-Ergebnis (`_name_match(Name, zahlungsempfaenger) >= 0.85`).",
            RA_PSEUDO,
        ),
        "Anzahl_Versionen": Meaning(
            "Anzahl der Versionen in der Mittelabruf-Historie (RF11). Spalte der Tabelle "
            "`t_Auswertung_Gesamt`, von `load_raw` unverändert übernommen.",
            f"{RA_FLAGS} (`_compute_rf11`); {RA_SCHEMA}",
        ),
        "Anzahl_ungueltige_Versionen": Meaning(
            "Anzahl der ungültigen Versionen in der Mittelabruf-Historie (RF11). Spalte der "
            "Tabelle `t_Auswertung_Gesamt`, von `load_raw` unverändert übernommen.",
            f"{RA_FLAGS} (`_compute_rf11`); {RA_SCHEMA}",
        ),
        "rechnungsdatum_dt": Meaning(
            "Rechnungsdatum als Datum (`pd.to_datetime` der Quellspalte "
            "`rechnungsdatum`); Stichtag der jahresbezogenen EU-Schwelle.",
            RA_LOADER,
        ),
        "auszahlungsdauer_tage": Meaning(
            "Auszahlungsdauer des Mittelabrufs in Tagen. Im originalen MDB-Bestand nicht "
            "vorhanden; `load_raw` setzt dann `0.0`.",
            RA_LOADER,
        ),
        "indikator_erreichungsquote": Meaning(
            "Erreichungsquote des Indikators als Anteil. Im originalen MDB-Bestand nicht "
            "vorhanden; `load_raw` setzt dann `1.0`.",
            RA_LOADER,
        ),
        "sanktionslisten_status": Meaning(
            "Ergebnis der Sanktionslistenprüfung des Rechnungsstellers. Im originalen "
            "MDB-Bestand nicht vorhanden; `load_raw` setzt dann „nicht geprüft“.",
            RA_LOADER,
        ),
    }


#: Flowstat-Belegliste: Feld nach ``normalize_belegliste`` → (Rolle, Quellspalten).
_FLOWSTAT_ALIASES: dict[str, tuple[str, str, list[str]]] = {
    "projektbetrag": (
        "Projektbezogener Betrag des Belegs",
        "AMOUNT_PROJECT",
        ["projektbez. Betrag", "projektbezogener Betrag", "Projektbetrag"],
    ),
    "zahlungsdatum": (
        "Datum der Bezahlung",
        "DATE_PAYMENT",
        ["Datum der Bezahlung", "Zahlungsdatum", "Wertstellung", "Valuta"],
    ),
    "rechnungsdatum": (
        "Rechnungsdatum",
        "DATE_INVOICE",
        ["Rechnungsdatum", "Belegdatum", "Invoice Date"],
    ),
    "rechnungsnummer": (
        "Rechnungsnummer bzw. externe Referenz",
        "INVOICE_REFERENCE",
        [
            "Rechnungsnummer / ext. Referenz",
            "Rechnungsnummer",
            "ext. Referenz",
            "Externe Referenz",
            "Rechnung Nr",
        ],
    ),
    "rechnungssteller": (
        "Rechnungssteller",
        "VENDOR_NAME",
        ["Rechnungssteller", "Auftragnehmer", "Kreditor", "Lieferant", "Vendor"],
    ),
    "kuerzungsbetrag": (
        "Kürzungsbetrag",
        "AMOUNT_DEVIATION",
        ["Kuerzungsbetrag", "Kürzungsbetrag", "Abweichung", "Korrektur"],
    ),
    "kuerzungsgrund": (
        "Kürzungsgrund",
        "CUT_REASON",
        ["Kuerzungsgrund", "Kürzungsgrund", "Korrekturgrund", "Feststellungsgrund"],
    ),
    "anerkannter_betrag": (
        "Anerkannter Betrag",
        "AMOUNT_ACCEPTED",
        ["anerkannter Betrag", "anerkannt", "accepted amount"],
    ),
    "vergabe": (
        "Vergabeangabe",
        "PROCUREMENT_REFERENCE",
        ["Vergabe", "Vergabenummer", "Vergabe-ID"],
    ),
    "direktvergabe": (
        "Kennzeichen Direktvergabe",
        "DIRECT_AWARD_FLAG",
        ["Direktvergabe", "Freihändige Vergabe", "direct award"],
    ),
}


def _flowstat() -> dict[str, Meaning]:
    out = {}
    for name, (text, role, aliases) in _FLOWSTAT_ALIASES.items():
        columns = ", ".join(f"„{a}“" for a in aliases)
        out[name] = Meaning(f"{text}; Quellspalten {columns} (Rolle `{role}`).", AD_BELEGLISTE)
    return out


def _risk_checker() -> dict[str, Meaning]:
    request = f"{FI_SCHEMA} (`RiskAssessmentRequest`)"
    context = f"{FI_SCHEMA} (`RiskContext`, flach als `context.<feld>`)"
    return {
        "net_amount": Meaning("Nettobetrag (Pflichtfeld im Schema).", request),
        "invoice_date": Meaning("Rechnungsdatum (Pflichtfeld im Schema).", request),
        "description": Meaning("Leistungsbeschreibung (Pflichtfeld im Schema).", request),
        "vendor_name": Meaning("Lieferantenname (Pflichtfeld im Schema).", request),
        "service_period_start": Meaning("Beginn Leistungszeitraum.", request),
        "service_period_end": Meaning("Ende Leistungszeitraum.", request),
        "invoice_recipient": Meaning("Rechnungsempfänger.", request),
        "beneficiary_name": Meaning("Name des Begünstigten.", request),
        "beneficiary_vat_id": Meaning(
            "USt-IdNr. des Begünstigten (für Selbstrechnungs-Prüfung).", request
        ),
        "supplier_vat_id": Meaning("USt-IdNr. des Lieferanten.", request),
        "context.median_amount": Meaning("Median-Betrag vergleichbarer Rechnungen.", context),
        "context.std_deviation": Meaning("Standardabweichung der Beträge.", context),
        "context.vendor_frequency": Meaning("Anzahl Rechnungen dieses Lieferanten.", context),
        "context.total_vendor_count": Meaning(
            "Gesamtanzahl verschiedener Lieferanten (zur Deutung siehe Hinweis der Regel "
            "VENDOR_CLUSTERING).",
            context,
        ),
        "context.project_start": Meaning("Projektbeginn.", context),
        "context.project_end": Meaning("Projektende.", context),
        "context.vendor_invoices": Meaning(
            "Alle Rechnungen desselben Lieferanten im Projekt; je Eintrag "
            "(`VendorInvoiceSummary`) `net_amount` „Nettobetrag“ und `invoice_date` "
            "„Rechnungsdatum“.",
            context,
        ),
    }


def _wibank(version: str) -> dict[str, Meaning]:
    norm = f"{FI_WIBANK} (`_normalise_sources`)"
    score = f"{FI_WIBANK} (`score_mittelabrufe`)"
    kosten = "Kostenart-Text (`kostenart_auswertung_bezeichnung`, `kostenart_bezeichnung`, `KOWG`)"
    out = {
        "verbundvorhaben": Meaning(
            "Verbundvorhaben; Aliase `verbundvorhaben`, `verbund`, `AKTZEIEXT2`, auch auf "
            "Belegebene.",
            norm,
        ),
        "fpg": Meaning(
            "Förderprogrammgruppe (Maßnahme, z. B. 956/960/973).",
            f"{RA_REPORT}; {score}",
        ),
        "hat_bau": Meaning(
            f"Mittelabruf enthält einen Beleg, dessen {kosten} „bau|gebäude|anlage|"
            "infrastruktur“ enthält.",
            norm,
        ),
        "hat_absch": Meaning(
            f"Mittelabruf enthält einen Beleg, dessen {kosten} „abschreib|afa|wertminderung“ "
            "enthält.",
            norm,
        ),
        "hat_sachleist": Meaning(
            f"Mittelabruf enthält einen Beleg, dessen {kosten} „sachleist“ enthält.", norm
        ),
        "hat_sach": Meaning(
            "Mittelabruf enthält einen direkten Beleg (siehe `n_direct`), dessen Kostenart "
            "nicht „personal|gemeinkost|pauschal|einnahm“ enthält.",
            norm,
        ),
        "n_direct": Meaning(
            f"Anzahl direkter Belege des Mittelabrufs: {kosten} ohne „gemeinkost|pauschal|"
            "sek|standardeinheits|personal“.",
            norm,
        ),
        "beihilfefrei": Meaning(
            "Beihilfefrei; Aliase `beihilfefrei`, `STAATLBEIH`, `beihilfefreiheit`, "
            "ergänzt aus `beihilferegelung` („keine beihilfe|beihilfefrei“).",
            norm,
        ),
        "trennungsrechnung_erforderlich": Meaning(
            "Trennungsrechnung erforderlich; Aliase `trennungsrechnung_erforderlich`, "
            "`trennungsrechnung`, `TRENNRECH`.",
            norm,
        ),
        "projekt_budget": Meaning(
            "Projektbudget: Maximum von `bewilligungsrahmen` (sonst `bruttobetrag`) je "
            "Vorhaben, ersatzweise die Bruttosumme des Mittelabrufs.",
            norm,
        ),
        "offene_auflagen": Meaning(
            "Offene Auflagen; Aliase `offene_auflagen`, `OFFAUF`, `offene_auflage`.", norm
        ),
        "oeffentlich_rechtlich": Meaning(
            "Öffentlich-rechtlicher Träger; Aliase `oeffentlich_rechtlich`, "
            "`RECHTSTRAEGER`, `rechtsform_oeffentlich`, oder Hochschule.",
            norm,
        ),
        "oeffentlicher_auftraggeber": Meaning(
            "Öffentlicher Auftraggeber; Aliase `oeffentlicher_auftraggeber`, `oeff_auftraggeber`.",
            norm,
        ),
        "hat_vergabe": Meaning(
            "Mittelabruf enthält einen Beleg mit nicht leerer `vergabenummer`, oder er ist "
            "EU-vergaberelevant.",
            norm,
        ),
        "eu_vergaberelevant": Meaning(
            "EU-vergaberelevant; Aliase `eu_vergaberelevant`, `eu_vergabeverfahren`, "
            "`EU_VERGABE`, oder `vergabeverfahren` enthält „eu|europa|oberschwelle“, oder "
            "FPG aus `eu_vergaberelevante_fpg` bei Hochschule/Forschung.",
            norm,
        ),
        "abruf_anteil": Meaning(
            "Abrufanteil: Bruttobetrag des Mittelabrufs / `bewilligungsrahmen`; ohne "
            "Bewilligungsrahmen der übergebene Wert.",
            norm,
        ),
        "erstes_vorhaben": Meaning(
            "Der Begünstigte hatte kein früheres Vorhaben (`len(vh) == 0` im Bewertungsschritt).",
            f"{score}; {CAPTURE_VERWK}",
        ),
        "prior_k": Meaning(
            "Summe der Kürzungen früherer Mittelabrufe bzw. Vorjahre des Begünstigten und "
            "Vorhabens.",
            score,
        ),
        "prior_q": Meaning(
            "Frühere Kürzungsquote in Prozent: `prior_k / (prior_b + prior_k) · 100`.",
            score,
        ),
        "prior_families": Meaning(
            "Menge der Feststellungsfamilien früherer Kürzungen (z. B. „Vergaberecht“, "
            "„Beihilferecht“).",
            score,
        ),
    }
    if version != "fb2d18568d2e":
        decision = "Profil `open_decisions`; `docs/behavior-changes.md` (K11)"
        out.update(
            {
                "offene_auflagen_anzahl": Meaning(
                    "Anzahl offener Auflagen (Zahl); Aufbereitung beim Consumer.", decision
                ),
                "externe_kuerzung": Meaning(
                    "Kürzung aufgrund von Prüfungsfeststellungen der KOM, der Rechnungshöfe "
                    "oder der Prüfbehörde; Aufbereitung beim Consumer.",
                    decision,
                ),
                "vorherige_verwk_quote": Meaning(
                    "Quote aus eigenen früheren Verwaltungskontrollen (VerwK); Aufbereitung "
                    "beim Consumer.",
                    decision,
                ),
                "vorherige_kuerzungsgruende": Meaning(
                    "Kürzungsgrund-Codes früherer Kürzungen (z. B. „1.3“, „13.1“), auch aus "
                    "eigenen früheren Mittelabrufen; Aufbereitung beim Consumer.",
                    decision,
                ),
            }
        )
    return out


def _exante() -> dict[str, Meaning]:
    features = f"{FI_EXANTE} (`_features`)"
    heur = f"{FI_EXANTE} (`heuristik_score`); {CAPTURE_VERWK}"
    return {
        "brutto": Meaning(
            "Bruttobetrag je Vorhaben (Spalte `brutto` der Vorhabentabelle); Grundlage "
            "der Budget-Kriterien.",
            f"{features}; {heur}",
        ),
        "laufzeit_monate": Meaning(
            "Geplante Laufzeit des Vorhabens in Monaten.", f"{FI_EXANTE} (`erwartete_ma`)"
        ),
        "erw_ma": Meaning(
            "Erwartete Anzahl Mittelabrufe ex ante = OLS(realisierte MA ~ Laufzeit + log Budget).",
            f"{FI_EXANTE} (`erwartete_ma`)",
        ),
        "fpgq": Meaning(
            "Historische Kürzungsquote der Förderprogrammgruppe (`kuerzungsquote` der "
            "FPG-Tabelle), fehlend 0.",
            features,
        ),
        "grp_v": Meaning(
            "Anzahl Vorhaben der Gruppe des Begünstigten (`vorhaben` der Gruppentabelle), "
            "fehlend 1.",
            features,
        ),
        "an_risiko": Meaning(
            "Anteil des Vorhaben-Bruttos an historisch auffällige Auftragnehmer (leave-one-out).",
            f"{FI_EXANTE} (`an_risiko_loo`)",
        ),
        "kuerzungsquote": Meaning(
            "Kürzungsquote des Vorhabens (Spalte `kuerzungsquote` der Vorhabentabelle).", heur
        ),
        "ma": Meaning(
            "Realisierte Anzahl Mittelabrufe des Vorhabens.", f"{FI_EXANTE} (`erwartete_ma`)"
        ),
        "belege": Meaning(
            "Anzahl Belege des Vorhabens (Spalte `belege` der Vorhabentabelle).", heur
        ),
        "gruppe_vorhaben": Meaning(
            "Anzahl Vorhaben der Gruppe des Begünstigten (`grp_vorhaben.get(gruppe, 1)`).",
            heur,
        ),
        "fpg_quote": Meaning(
            "Kürzungsquote der Förderprogrammgruppe (`fpg_quote.get(fpg, 0)`).", heur
        ),
        "fpg_rueckgabequote": Meaning(
            "Rückgabequote der Förderprogrammgruppe (`fpg_ret.get(fpg, 0)`).", heur
        ),
    }


def meanings(profile_id: str, version: str) -> dict[str, Meaning]:
    """Belegte Bedeutungen der Eingabefelder eines Profils."""
    if profile_id.startswith("riskanalysis."):
        return _riskanalysis()
    if profile_id == "audit_designer.flowstat_belegliste":
        return _flowstat()
    if profile_id == "flowinvoice.risk_checker":
        return _risk_checker()
    if profile_id == "flowinvoice.rbvk_wibank":
        return _wibank(version)
    if profile_id.startswith("flowinvoice.exante_"):
        return _exante()
    return {}


# --------------------------------------------------------------------------- Mechanik


@dataclass(frozen=True)
class Use:
    """Ein Feld, wie es eine Regel liest."""

    field: str
    role: str
    absent: str | None  # Verhalten bei fehlender Spalte (None = wie leerer Wert)
    empty: str
    required: bool = False  # fehlende Spalte bricht ab (unabhängig von requires)
    value_required: bool = False  # leerer Wert bricht ab


Extractor = Callable[[Mapping[str, Any], Mapping[str, Any]], list[Use]]


def _code(value: Any) -> str:
    return f"`{json.dumps(value, ensure_ascii=False)}`"


def _amount(p: Mapping[str, Any], name_key: str, role: str, zero_outcome: str = "") -> Use:
    """Betragsfeld über ``_amounts`` (``parse``, ``missing_value``, ``missing_amount_reason``)."""
    reason = p.get("missing_amount_reason")
    if reason is not None:
        empty = f"unbestimmt („{reason}“)"
    else:
        empty = f"Ersatzwert {_code(p['missing_value'])}{zero_outcome}"
    if p["parse"] == "strict":
        empty += "; Text statt Zahl → Abbruch (`InputError`)"
    else:
        empty += "; nicht numerischer Text gilt als leer"
    return Use(p[name_key], role, None, empty)


def _relevance(p: Mapping[str, Any]) -> list[Use]:
    spec = p.get("relevance")
    if spec is None:
        return []
    required = spec["column_missing"] == "error"
    absent = "Abbruch (`InputError`)" if required else "alle Datensätze gelten als vergaberelevant"
    pattern = spec["exclude_pattern"]
    return [
        Use(
            spec["field"],
            f"Kostenart (nicht vergaberelevant bei Muster „{pattern}“)",
            absent,
            "gilt als vergaberelevant",
            required=required,
        )
    ]


def _round_multiple(p: Mapping[str, Any], r: Mapping[str, Any]) -> list[Use]:
    missing = p["missing_value"]
    flag = (missing > 0 or not p["positive_only"]) and missing % p["multiple"] == 0
    return [_amount(p, "field", "Betrag", "" if flag else " (kein Merkmal)")]


def _near_threshold(p: Mapping[str, Any], r: Mapping[str, Any]) -> list[Use]:
    missing = p["missing_value"]
    outcome = " (kein Merkmal)" if missing is not None and missing <= 0 else ""
    uses = [_amount(p, "field", "Betrag", outcome)]
    eu = p["thresholds"].get("procurement_eu")
    if eu is not None and eu["date_source"] == "record":
        uses.append(
            Use(
                eu["date_field"],
                f"Stichtag der EU-Schwelle ({eu['profile']} {eu['version']})",
                None,
                "EU-Schwelle nicht bestimmbar; trifft keine Profilschwelle → unbestimmt",
            )
        )
    return uses


def _missing_procurement(p: Mapping[str, Any], r: Mapping[str, Any]) -> list[Use]:
    reason = p.get("missing_amount_reason")
    if reason is not None:
        amount = Use(
            p["amount_field"],
            "Betrag",
            None,
            f"unbestimmt („{reason}“) nur ohne echte Vergabekennung bei vergaberelevanter "
            "Kostenart, sonst kein Merkmal"
            + (
                "; Text statt Zahl → Abbruch (`InputError`)"
                if p["parse"] == "strict"
                else "; nicht numerischer Text gilt als leer"
            ),
        )
    else:
        zero = " (kein Merkmal)" if p["missing_value"] <= p["amount_gt"] else ""
        amount = _amount(p, "amount_field", "Betrag", zero)
    blanks = ", ".join(_code(b) for b in p["blank_values"])
    empty = f"gilt als fehlende Vergabekennung (auch {blanks}"
    empty += ", ohne Groß-/Kleinschreibung)" if p["blank_casefold"] else ")"
    if p["placeholder_pattern"]:
        empty += f"; Platzhalter nach Muster `{p['placeholder_pattern']}` ebenso"
    required = p["id_column_missing"] == "error"
    absent = "Abbruch (`InputError`)" if required else "gilt als fehlende Vergabekennung"
    ident = Use(p["id_field"], "Vergabekennung", absent, empty, required=required)
    return [amount, ident, *_relevance(p)]


def _name_similarity(p: Mapping[str, Any], r: Mapping[str, Any]) -> list[Use]:
    empty = "Ähnlichkeit 0 (kein Merkmal aus dem Namensvergleich)"
    uses = [
        Use(p["left_field"], "Name links (Begünstigter)", None, empty),
        Use(p["right_field"], "Name rechts (Auftragnehmer)", None, empty),
    ]
    if p["override_field"]:
        uses.append(
            Use(
                p["override_field"],
                "übernommene Vorberechnung des Merkmals",
                "Ähnlichkeitsschwelle entscheidet",
                "kein Merkmal; sonst wird der Wahrheitswert übernommen (Text „False“ gilt "
                "als wahr, RK-L03)",
            )
        )
    return uses


def _concentration(p: Mapping[str, Any], r: Mapping[str, Any]) -> list[Use]:
    return [
        _amount(p, "amount_field", "Betrag (Summen)"),
        Use(
            p["payee_field"],
            "Auftragnehmer (kanonisch)",
            "kein Merkmal für alle Datensätze",
            "Beleg zählt nicht",
        ),
        Use(
            p["case_field"],
            "Vorhaben",
            "kein Merkmal für alle Datensätze",
            "Beleg nur im Gruppenkriterium (Betrag zählt, Vorhaben nicht)",
        ),
        Use(
            p["group_field"],
            "Gruppe",
            "nur das Kriterium je Vorhaben und Auftragnehmer",
            "Beleg nur im Kriterium je Vorhaben und Auftragnehmer",
        ),
        *_relevance(p),
    ]


def _ratio_history(p: Mapping[str, Any], r: Mapping[str, Any]) -> list[Use]:
    empty = "gilt als 0 (auch nicht numerischer Text)"
    return [
        Use(p["total_field"], "Anzahl gesamt", None, empty),
        Use(p["part_field"], "Anzahl Teilmenge", None, empty),
    ]


def _leave_one_out(p: Mapping[str, Any], r: Mapping[str, Any]) -> list[Use]:
    deduction = _code(p["deduction_missing_value"])
    return [
        _amount(p, "amount_field", "Betrag (Quote)"),
        Use(
            p["deduction_field"],
            "Kürzungsbetrag",
            f"Ersatzwert {deduction}",
            f"Ersatzwert {deduction} (auch nicht numerischer Text)",
        ),
        Use(p["group_field"], "Gruppe", None, "Beleg bleibt unberücksichtigt"),
        Use(p["case_field"], "Vorhaben", None, "Beleg zählt nur zur Gruppe, kein Merkmal"),
    ]


def _compare_outcome(value: Any, p: Mapping[str, Any]) -> str:
    left, right = float(value), float(p["value"])
    hit = {
        "gt": left > right,
        "ge": left >= right,
        "lt": left < right,
        "le": left <= right,
    }[p["op"]]
    return "Merkmal" if hit else "kein Merkmal"


def _numeric_compare(p: Mapping[str, Any], r: Mapping[str, Any]) -> list[Use]:
    col, val = p["column_missing_value"], p["missing_value"]
    return [
        Use(
            p["field"],
            "Zahl",
            f"Ersatzwert {_code(col)} ({_compare_outcome(col, p)})",
            f"Ersatzwert {_code(val)} ({_compare_outcome(val, p)}); nicht numerischer Text "
            "gilt als leer",
        )
    ]


def _text_equals(p: Mapping[str, Any], r: Mapping[str, Any]) -> list[Use]:
    col = p["column_missing_value"]
    outcome = "Merkmal" if col == p["value"] else "kein Merkmal"
    return [Use(p["field"], "Text", f"Ersatzwert {_code(col)} ({outcome})", "kein Merkmal")]


def _missing_value(p: Mapping[str, Any], r: Mapping[str, Any]) -> list[Use]:
    return [Use(p["field"], "Pflichtangabe", None, "Merkmal")]


def _date_before(p: Mapping[str, Any], r: Mapping[str, Any]) -> list[Use]:
    empty = "kein Merkmal; Text, der kein ISO-Datum ist → Abbruch (`InputError`)"
    return [
        Use(p["field"], "Datum (Merkmal, wenn vor dem Vergleichsdatum)", None, empty),
        Use(p["before_field"], "Vergleichsdatum", None, empty),
    ]


def _duplicate_key(p: Mapping[str, Any], r: Mapping[str, Any]) -> list[Use]:
    return [
        Use(f, "Schlüsselteil", None, "leere Werte gelten untereinander als gleich")
        for f in p["fields"]
    ]


def _nonzero_without_text(p: Mapping[str, Any], r: Mapping[str, Any]) -> list[Use]:
    return [
        _amount(p, "amount_field", "Betrag"),
        Use(p["text_field"], "Begründungstext", None, "gilt als fehlend (Merkmal bei Betrag ≠ 0)"),
    ]


def _balance_mismatch(p: Mapping[str, Any], r: Mapping[str, Any]) -> list[Use]:
    uses = [_amount({**p, "field": p["minuend"]}, "field", "Minuend")]
    uses += [_amount({**p, "field": s}, "field", "Subtrahend") for s in p["subtrahends"]]
    return uses


def _amount_with_marker(p: Mapping[str, Any], r: Mapping[str, Any]) -> list[Use]:
    outcome = "" if p["missing_value"] > p["amount_gt"] else " (kein Merkmal)"
    return [
        _amount(p, "amount_field", "Betrag", outcome),
        Use(
            p["marker_field"],
            f"Kennzeichen (Muster „{p['marker_pattern']}“)",
            None,
            "kein Treffer (kein Merkmal)",
        ),
    ]


def _top_share(p: Mapping[str, Any], r: Mapping[str, Any]) -> list[Use]:
    return [
        Use(
            p["amount_field"],
            "Betrag (Anteil)",
            None,
            "nicht gezählt (auch nicht numerischer Text)",
        ),
        Use(p["group_field"], "Gruppe", None, "eigene Gruppe „fehlend“"),
    ]


def _amount_or_statistic(p: Mapping[str, Any], r: Mapping[str, Any]) -> list[Use]:
    stat = "nur der absolute Schwellenwert wird geprüft (ebenso bei 0)"
    return [
        Use(
            p["amount_field"],
            "Betrag",
            None,
            "Abbruch (`InputError`, Zahl erwartet)",
            value_required=True,
        ),
        Use(p["median_field"], "Median", None, stat),
        Use(p["std_field"], "Standardabweichung", None, stat),
    ]


def _share_above(p: Mapping[str, Any], r: Mapping[str, Any]) -> list[Use]:
    empty = "kein Merkmal (ebenso bei 0)"
    return [
        Use(p["numerator_field"], "Zähler", None, empty),
        Use(p["denominator_field"], "Nenner", None, empty),
    ]


def _all_missing(p: Mapping[str, Any], r: Mapping[str, Any]) -> list[Use]:
    empty = 'zählt als fehlend (auch `""` oder 0); fehlen alle Felder → Merkmal'
    return [Use(f, "Angabe", None, empty) for f in p["fields"]]


def _round_amount_terms(p: Mapping[str, Any], r: Mapping[str, Any]) -> list[Use]:
    return [
        Use(
            p["amount_field"],
            "Betrag",
            None,
            "Abbruch (`InputError`, Zahl erwartet)",
            value_required=True,
        ),
        Use(
            p["text_field"],
            "Beschreibung (Pauschal-Begriffe)",
            None,
            f"keine Begriffe gefunden (Schwere {p['severity_without_terms']})",
        ),
    ]


def _date_outside_range(p: Mapping[str, Any], r: Mapping[str, Any]) -> list[Use]:
    range_empty = "keine Prüfung (kein Merkmal)"
    fallback = f"`{p['fallback_field']}` wird verwendet"
    return [
        Use(p["range_start_field"], "Beginn des Vergleichszeitraums", None, range_empty),
        Use(p["range_end_field"], "Ende des Vergleichszeitraums", None, range_empty),
        Use(p["start_field"], "Leistungsbeginn", None, fallback),
        Use(p["end_field"], "Leistungsende", None, fallback),
        Use(
            p["fallback_field"],
            "Ersatzdatum",
            None,
            "fehlt auch das Leistungsdatum und ist der Vergleichszeitraum angegeben → "
            "Abbruch (`InputError`)",
        ),
    ]


def _text_patterns(p: Mapping[str, Any], r: Mapping[str, Any]) -> list[Use]:
    return [Use(p["field"], "Text (Muster)", None, "kein Merkmal")]


def _pair(p: Mapping[str, Any], r: Mapping[str, Any]) -> list[Use]:
    empty = "kein Merkmal (ebenso, wenn der andere Wert fehlt)"
    return [
        Use(p["left_field"], "Vergleichswert links", None, empty),
        Use(p["right_field"], "Vergleichswert rechts", None, empty),
    ]


def _split_window(p: Mapping[str, Any], r: Mapping[str, Any]) -> list[Use]:
    uses = [
        Use(
            p["items_field"],
            f"Rechnungsliste (Einträge mit `{p['amount_key']}`, `{p['date_key']}`)",
            None,
            f"kein Merkmal (ebenso bei leerer Liste); Eintrag ohne `{p['amount_key']}` "
            f"oder `{p['date_key']}` → Abbruch (`InputError`)",
        )
    ]
    eu = p.get("procurement_eu")
    if eu is not None:
        uses.append(
            Use(
                eu["date_field"],
                f"Stichtag der EU-Schwelle ({eu['profile']} {eu['version']})",
                None,
                "EU-Schwelle nicht bestimmbar; ohne Treffer → unbestimmt",
            )
        )
    return uses


def _truthy_all(p: Mapping[str, Any], r: Mapping[str, Any]) -> list[Use]:
    return [Use(f, "Wahrheitswert", None, "nicht zutreffend (keine Punkte)") for f in p["fields"]]


def _hit(flag: bool) -> str:
    return "Treffer" if flag else "kein Treffer"


def _text_in_set(p: Mapping[str, Any], r: Mapping[str, Any]) -> list[Use]:
    values = set(p["values"])
    return [
        Use(
            p["field"],
            "Text",
            None,
            f"Schlüssel fehlt im Datensatz: Ersatztext {_code(p['missing_text'])} "
            f"({_hit(p['missing_text'] in values)}); Wert `None`: Text „None“ "
            f"({_hit('None' in values)})",
        )
    ]


def _number_range(p: Mapping[str, Any], r: Mapping[str, Any]) -> list[Use]:
    x, low, high = float(p["missing_value"]), p["lower"], p["upper"]
    above = low is None or (x >= low if p["lower_inclusive"] else x > low)
    below = high is None or (x <= high if p["upper_inclusive"] else x < high)
    return [
        Use(
            p["field"],
            "Zahl",
            None,
            f"Ersatzwert {_code(p['missing_value'])}, {_hit(above and below)} (ebenso bei "
            '`""` oder 0); NaN → kein Treffer; nicht numerischer Text → Abbruch '
            "(`InputError`)",
        )
    ]


def _set_overlap(p: Mapping[str, Any], r: Mapping[str, Any]) -> list[Use]:
    return [
        Use(
            p["field"],
            "Codeliste",
            None,
            "leere Menge (kein Treffer); keine Liste → Abbruch (`InputError`)",
        )
    ]


EXTRACTORS: dict[str, Extractor] = {
    "round_multiple": _round_multiple,
    "near_threshold": _near_threshold,
    "missing_procurement": _missing_procurement,
    "name_similarity": _name_similarity,
    "counterparty_concentration": _concentration,
    "ratio_history": _ratio_history,
    "leave_one_out_rate": _leave_one_out,
    "numeric_compare": _numeric_compare,
    "text_equals": _text_equals,
    "missing_value": _missing_value,
    "date_before": _date_before,
    "duplicate_key": _duplicate_key,
    "nonzero_without_text": _nonzero_without_text,
    "balance_mismatch": _balance_mismatch,
    "amount_with_marker": _amount_with_marker,
    "top_share": _top_share,
    "amount_or_statistic": _amount_or_statistic,
    "share_above": _share_above,
    "all_missing": _all_missing,
    "round_amount_terms": _round_amount_terms,
    "date_outside_range": _date_outside_range,
    "text_patterns": _text_patterns,
    "names_differ": _pair,
    "identifier_equal": _pair,
    "split_window": _split_window,
    "truthy_all": _truthy_all,
    "text_in_set": _text_in_set,
    "number_range": _number_range,
    "set_overlap": _set_overlap,
}

#: Parameter, die Feldnamen des Datensatzes tragen (Schutz gegen neue, nicht erfasste
#: Parameter). ``amount_key``/``date_key`` benennen Schlüssel in Listeneinträgen.
_FIELD_PARAM = re.compile(r"(^|_)(field|fields)$|^(minuend|subtrahends)$")

_GATE = {
    "error": "Abbruch (`InputError`)",
    "skip": "Regel wird übersprungen (`Evaluation.skipped`)",
    "all_false": "kein Merkmal für alle Datensätze",
}


def _field_params(params: Mapping[str, Any], prefix: str = "") -> set[str]:
    found = set()
    for key, value in params.items():
        if isinstance(value, Mapping):
            found |= _field_params(value, f"{prefix}{key}.")
        elif _FIELD_PARAM.search(key):
            names = value if isinstance(value, list) else [value]
            found |= {n for n in names if isinstance(n, str)}
    return found


@dataclass(frozen=True)
class Entry:
    """Ein Feld in einer Regel mit abgeleitetem Verhalten."""

    code: str
    label: str
    role: str
    absent: str
    empty: str
    required: bool
    value_required: bool


def rule_entries(rule: Mapping[str, Any]) -> list[tuple[str, Entry]]:
    """Felder einer Regel mit Pflicht und Verhalten bei fehlender Spalte / leerem Wert."""
    kind = rule["kind"]
    if kind not in EXTRACTORS:
        raise SystemExit(f"Regelart {kind!r} ist in document_fields.py nicht erfasst.")
    params = rule["params"]
    uses = EXTRACTORS[kind](params, rule)
    covered = {u.field for u in uses}
    requires = set(rule.get("requires", []))
    unknown = (_field_params(params) | requires) - covered
    if unknown:
        raise SystemExit(f"Regel {rule['code']}: Felder nicht erfasst: {sorted(unknown)}")
    when = rule.get("when_missing_columns", "error")
    out = []
    for use in uses:
        if use.field in requires:
            absent = "wie leerer Wert" if when == "undetermined" else _GATE[when]
            required = when == "error"
        else:
            absent = use.absent or "wie leerer Wert"
            required = use.required
        entry = Entry(
            rule["code"],
            rule["label"],
            use.role,
            absent,
            use.empty,
            required,
            use.value_required,
        )
        out.append((use.field, entry))
    for alias, name in (rule.get("echo_fields") or {}).items():
        out.append(
            (
                name,
                Entry(
                    rule["code"],
                    rule["label"],
                    f"Textbaustein `{alias}`",
                    "wie leerer Wert",
                    "erscheint als „None“ im Text",
                    False,
                    False,
                ),
            )
        )
    return out


def profile_entries(data: Mapping[str, Any]) -> dict[str, list[Entry]]:
    """Alle Felder eines Profils mit ihren Regeln (Reihenfolge wie im Profil)."""
    fields: dict[str, list[Entry]] = {}
    for rule in data["rules"]:
        for name, entry in rule_entries(rule):
            fields.setdefault(name, []).append(entry)
    summary = data["summary"]
    if summary.get("format") == "riskanalysis.red_flag_summary":
        fields.setdefault(summary["amount_field"], []).append(
            Entry(
                "Zusammenfassung",
                "Volumen je Merkmal (`red_flag_summary`)",
                "Betrag",
                "Volumen 0",
                "nicht gezählt; Text statt Zahl → Abbruch (`InputError`)",
                False,
                False,
            )
        )
    return fields


# --------------------------------------------------------------------------- Ausgabe


def _cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def _heading(data: Mapping[str, Any]) -> str:
    return f"{data['id']} {data['version']}"


def _anchor(data: Mapping[str, Any]) -> str:
    """Anker wie GitHub: klein, Satzzeichen außer ``-``/``_`` entfernt, Leerzeichen → ``-``."""
    return re.sub(r"[^\w\- ]", "", _heading(data).lower()).replace(" ", "-")


def _load() -> list[dict[str, Any]]:
    missing = sorted(set(KINDS) - set(EXTRACTORS))
    if missing:
        raise SystemExit(f"Regelarten ohne Felderfassung in document_fields.py: {missing}")
    profiles = []
    for path in sorted(PROFILE_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        profile_from_dict(data)  # gleiche Prüfung wie load_profile
        profiles.append(data)
    return sorted(profiles, key=lambda d: (d["id"], d["version"]))


def _field_row(name: str, entries: list[Entry], known: Mapping[str, Meaning]) -> str:
    rules = "<br>".join(f"{e.code} – {e.label} ({e.role})" for e in entries)
    meaning = known.get(name)
    text = f"{meaning.text} Beleg: {meaning.source}" if meaning else UNDOCUMENTED
    hard = [e.code for e in entries if e.required]
    value = [e.code for e in entries if e.value_required]
    if value:
        status = f"**Pflicht**, auch der Wert ({', '.join(value)})"
    elif hard:
        status = f"**Pflicht** ({', '.join(hard)})"
    else:
        status = "optional"
    behavior = "<br>".join(
        f"{e.code}: Spalte fehlt → {e.absent}; leer → {e.empty}" for e in entries
    )
    cells = [f"`{name}`", rules, text, status, behavior]
    return "| " + " | ".join(_cell(c) for c in cells) + " |"


def render() -> str:
    """Vollständiger Inhalt von ``docs/eingabefelder.md``."""
    profiles = _load()
    lines = [
        "# Eingabefelder der Regelprofile",
        "",
        "<!-- Erzeugt von tools/document_fields.py – nicht von Hand bearbeiten. -->",
        "",
        "Erzeugt mit `python tools/document_fields.py` aus allen Profilen in",
        "`src/auditcore_risk/profile_data`; `tests/test_eingabefelder.py` schlägt fehl,",
        "sobald Profile und diese Datei auseinanderlaufen. Welche Felder eine Regel liest,",
        "folgt aus den Parametern ihrer Regelart; das Verhalten bei fehlenden Daten aus",
        "`requires`/`when_missing_columns`, `missing_value`, `missing_amount_reason`,",
        "`column_missing_value`, `id_column_missing`, `relevance.column_missing` und der",
        "Mechanik der Regelart (`rules.py`, `invoice_rules.py`, `score_rules.py`).",
        "",
        "* **Spalte fehlt**: kein Datensatz hat den Schlüssel bzw. die Spalte steht nicht",
        "  in `columns` (beim DataFrame: nicht in `frame.columns`).",
        "* **leer**: `None`, `NaN`, `pandas.NA` oder `NaT` in einem Datensatz, bei",
        "  Datensätzen ohne den Schlüssel ebenso.",
        "* **Pflicht**: ohne die Spalte bricht die Auswertung mit `InputError` ab (bei",
        "  „auch der Wert“ ebenso bei einem leeren Wert). **optional**: die Auswertung",
        "  läuft, das Verhalten steht in der letzten Spalte (übersprungen, kein Merkmal,",
        "  unbestimmt oder Ersatzwert).",
        f"* „{UNDOCUMENTED}“: keine belegbare Beschreibung in der Quelle.",
        "",
        "Bedeutungen stammen aus dem Quellcode der Anwendungen zum charakterisierten",
        "Stand (Commit wie angegeben), dem Profil selbst oder der Paketdokumentation.",
        "",
        "## Profile",
        "",
        "| Profil | Version | Status | Felder | Regeln |",
        "|---|---|---|---|---|",
    ]
    tables: list[str] = []
    for data in profiles:
        entries = profile_entries(data)
        lines.append(
            f"| [`{data['id']}`](#{_anchor(data)}) | `{data['version']}` | "
            f"`{data['status']}` | {len(entries)} | {len(data['rules'])} |"
        )
        known = meanings(data["id"], data["version"])
        tables += [
            "",
            f"## {_heading(data)}",
            "",
            f"Status `{data['status']}`, Fingerabdruck `{fingerprint(data)}`.",
        ]
        contract = data["source"].get("input_contract")
        if contract:
            tables.append(f"Eingabevertrag laut Profil: {contract}")
        tables += [
            "",
            "| Feld | Regeln (Code – Bezeichnung, Rolle) | Bedeutung | Pflicht/optional "
            "| Verhalten bei fehlender Spalte / leerem Wert |",
            "|---|---|---|---|---|",
        ]
        for name in sorted(entries, key=lambda n: (n.lstrip("_").casefold(), n)):
            tables.append(_field_row(name, entries[name], known))
    return "\n".join([*lines, *tables, ""])


def main(argv: list[str] | None = None) -> int:
    """Schreibt die Datei oder prüft mit ``--check``, ob sie aktuell ist."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="nur prüfen, nicht schreiben")
    args = parser.parse_args(argv)
    content = render()
    current = OUTPUT.read_text(encoding="utf-8") if OUTPUT.exists() else None
    if args.check:
        if current != content:
            print(f"{OUTPUT} ist veraltet: python tools/document_fields.py", file=sys.stderr)
            return 1
        return 0
    if current != content:
        OUTPUT.write_text(content, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
