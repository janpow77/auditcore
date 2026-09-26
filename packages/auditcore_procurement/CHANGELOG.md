# Changelog auditcore_procurement

## Unreleased

Keine Verhaltensänderung. Fachliche Spezifikation `docs/spezifikation.md` (Zweck, Verträge, Invarianten, Fehlerfälle, Abgrenzung, bewusste Abweichungen vom Altverhalten mit benannten Legacy-Varianten); Status im Paketkatalog „spezifiziert“. 12 Invarianten (I1–I12) als Hypothesis-Eigenschaftstests in `tests/test_spezifikation.py`; keine Befunde. `hypothesis` im Extra `dev`.

## 0.2.4 – 2026-09-26 – Paketstand für Release v0.4.2

Keine Verhaltensänderung. README mit den Installationsangaben aus Release v0.4.1. Pins: `auditcore_common==0.2.0`, `auditcore_harvest==0.1.3`.

## 0.2.3 – 2026-09-26 – Paketstand für Release v0.4.1

Keine Verhaltensänderung. Pflichtabhängigkeit `auditcore_common==0.1.1`, Extra `sources` pinnt `auditcore_harvest==0.1.2`; README nach der Vorlage.

## 0.2.2 – Hilfsfunktionen aus auditcore_common

Keine fachliche Änderung. Neue Laufzeitabhängigkeit `auditcore_common==0.1.0`
(APT `python3-auditcore-common`).

- Profil-Fingerprint → `hashing.canonical_sha256`, `load_profile` →
  `profiles.load_packaged_profile(invalid_name="missing")` (ohne Typprüfung
  wie bisher). Das Laden der EU-Jahrestabelle (`_packaged_eu_block`) bleibt
  wegen eigener Meldung und Schemaprüfung im Paket.
- Meldungen und Ergebnisse unverändert; 241 Tests grün.

## 0.2.1 – Refaktorierung ohne Verhaltensänderung

Keine fachliche Änderung: Alle 241 Tests (Replays der beobachteten
Originalausgaben – 57 Normalisierungs-/Datei-/Query-Fälle, 13 Abrufszenarien,
27 Precheck-Fälle, 30 Company-Client-Fälle –, Jahresschwellen-, Policy- und
Architekturtests) laufen unverändert grün. Zusätzlich lokal alte und neue
Implementierung verglichen: 20 000 zufällig erzeugte TED-Notices
(`normalize_notice` mit/ohne Auftragnehmerpflicht, `inspect_notice`,
`extract_*`, `to_iso_date`, `to_ted_date`), 3 000 Datei-Importe und Queries,
18 000 Precheck-Läufe über alle drei Profile in beiden Modi sowie 3 000
fehlerhafte Profile (Fehlermeldungen) und `profile_from_ruleset` – Ergebnisse
identisch.

- `ted.py` geteilt: Werteextraktion (`extract_text`, `extract_list`,
  `extract_amount`, `to_iso_date`, `first_present`) in `ted_values.py`;
  `ted` stellt alle öffentlichen Namen weiter bereit. `extract_text` über die
  Hilfen `_language_text`/`_first_text`, `normalize_notice` über
  `_field_value`, `inspect_notice` über `_amount_issues`.
- `prechecks.py` geteilt: Profilmodell, Profilprüfung, mitgelieferte Profile und
  EU-Zeiträume in `precheck_profile.py`; Status und Ergebniszeile in
  `precheck_common.py`; Schwellenwertprüfung (Legacy und strict) in
  `precheck_threshold.py`. `prechecks` re-exportiert alle öffentlichen Namen
  (`__all__`); Klassen sind dieselben Objekte.
- `_schema2` in `_eu_periods`/`_eu_period_row` zerlegt, die strikte
  Schwellenprüfung in `_case_threshold`, `_strict_tier`, `_strict_verdict`;
  Reihenfolge der Prüfungen und Fehlermeldungen unverändert.
- Typen: Eingaben der TED-Funktionen `object` statt `Any`; benannte Grenztypen
  `ProfileData` (Profil-/Regelwerk-JSON), `CheckResult` (Ergebniszeile) und
  `Mapping[str, object]` für Belege.

Abhängige Pakete: `auditcore_risk` pinnt `auditcore_procurement==0.2.1`
(Extra `procurement` und `dev`), `packaging/library-extras.json` entsprechend.

| Messung (nur `src/`) | 0.2.0 | 0.2.1 |
|---|---|---|
| Funktionen mit McCabe > 10 | 4 | 0 |
| Module > 400 Zeilen | 2 (`prechecks.py` 787, `ted.py` 472) | 0 (größtes: `ted.py` 364) |
| Funktionen > 60 Zeilen (Code-Gate) | 1 | 0 |
| `Any` (Textvorkommen / Code-Gate `any_usages`) | 71 / 66 | 42 / 34 |
| mypy --strict | sauber | sauber |

Keine Umbenennungen öffentlicher Namen. Private Hilfen (`_result`,
`_category`, `_tier`, `_missing`, `_first_present`) heißen in den neuen
Modulen `result`, `category_of`, `find_tier`, `is_missing`, `first_present`.

Befund (nicht korrigiert): `inspect_notice` durchläuft die Datumsfelder als
`frozenset`; bei mehreren unlesbaren Datumsangaben hängt die Reihenfolge der
`unparsed_date`-Meldungen vom Hash-Seed des Prozesses ab (`PYTHONHASHSEED`).
Inhalt der Meldungen ist stabil.

## 0.2.0 – 2026-09-23

- EU-Vergabeschwellen je Geltungszeitraum 2014–2027 mit amtlicher Fundstelle
  (Profil `procurement.hvtg 2026.09.3`, `eu_period`, `ThresholdUnavailable`,
  `authority_type`); Profil 2026.09.2 bleibt ladbar.
- Abweichungsschritt und Gesamtstatus der Prechecks ausgelagert.

## 0.1.0 – 2026-09-22

Erstausgabe: Datensatzvertrag `auditcore_procurement.notice/1`,
verhaltensgleiche TED-Normalisierung und Dateiimport, getrennte Varianten der
Unternehmenssuche, versioniertes Precheck-Profil aus dem Regelwerk der
Anwendung (`legacy`/`strict`), TED- und HAD-Adapter auf `auditcore_harvest`
mit Quellenkatalog. Characterization der Quellanwendungen
(`tests/fixtures/procurement_legacy_observed.json`).
