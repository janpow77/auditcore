# Changelog auditcore_procurement

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
