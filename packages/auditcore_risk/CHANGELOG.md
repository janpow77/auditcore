# Changelog – auditcore_risk

## 0.3.2 – Hilfsfunktionen aus auditcore_common

Keine fachliche Änderung außer der Bibliothekskennung `LIBRARY`
(„auditcore_risk 0.3.2“). Neue Laufzeitabhängigkeit `auditcore_common==0.1.0`
(APT `python3-auditcore-common`); `auditcore_entity_matching==0.2.2`.

- `fingerprint` → `hashing.canonical_sha256`, `_freeze` → `frozen.freeze`,
  Profil- und Betrugsprofilverzeichnis → `profiles.packaged_profile_entries`
  (Suche über den Dateiinhalt bleibt), `_pandas` → `optional.require_module`.
- `results.plain` ist veraltet (`DeprecationWarning`) und liefert
  `auditcore_common.json_values.jsonable(value)`; intern wird `jsonable`
  genutzt. Alle 2 497 Tests grün (Replays unverändert).

Zusätzlich enthält 0.3.2 die bisher unveröffentlichte Web-Schnittstelle:

- **`auditcore_risk.web`** (Extras `web`: starlette ≥ 0.26.1, `fastapi`:
  fastapi ≥ 0.92): `create_app`/`routes` (Starlette) und `build_fastapi_router`
  mit `GET /profiles`, `GET /profiles/{id}/{version}`,
  `POST /profiles/{id}/{version}/check-columns`, `POST /evaluate`; die Handler
  sind ohne Web-Framework aufrufbar. Auswertungen nennen je Treffer und je
  unbestimmtem Merkmal die gelesenen Eingabefelder mit Werten.
- **`web/field_catalog.json`**: Eingabefelder je Profil (Bedeutung, Pflicht,
  Folge bei fehlender Spalte/leerem Wert) als JSON, erzeugt mit
  `tools/export_field_catalog.py` aus derselben Ableitung wie
  `docs/eingabefelder.md`.

## 0.3.1 – Refaktorierung ohne Verhaltensänderung

Alle Profile, Fingerprints, Meldungstexte, Ergebnisschlüssel und die
Reihenfolge der Profilprüfungen bleiben unverändert; die Charakterisierungs-
und Replay-Tests (riskanalysis, Flowstat, flowinvoice RiskChecker/VerwK/Fraud)
laufen unverändert grün.

- **Regelarten nach Verantwortung geschnitten:** `amount_rules`
  (Betragsregeln, Schwellennähe, Vergabekennung), `field_rules`
  (Vergleiche, fehlende Werte, Datumsfolge, doppelte Schlüssel),
  `group_rules` (Konzentration, Leave-one-out, größter Anteil),
  `rule_checks` (Parameterprüfungen als Tabelle `COMMON_CHECKS`/`KIND_CHECKS`),
  `invoice_checks` (Prüfungen der Einzelrechnungsregeln). `rules` enthält nur
  noch den Namensabgleich, die Registry `KINDS` und `validate_params`.
- **Auswertung zerlegt:** `results` (Ergebnistypen, `LIBRARY`), `assessment`
  (Textvorlagen, Punkte- und Gewichtsbewertung je Profil), `summary`
  (Übersicht je Format; `red_flag_entry` nutzen Engine und pandas-Adapter
  gemeinsam), `engine` (Ablauf).
- **Betrugsprüfung zerlegt:** `fraud_profile`, `fraud_signals`
  (Ableitung und Score als Tabellen je Teilprüfung), `fraud_ted`,
  `fraud_duplicates`; `fraud` lädt und prüft die Profile und exportiert alles
  wie bisher.
- **Profilprüfung zerlegt:** `profiles` (Regel- und Profilprüfung in kurzen
  Schritten, gleiche Reihenfolge), `assessment_schema`, `templates`.
- **Typen:** Zellwerte als `object`, Nachweise als `dict[str, object]`,
  Datensatzergebnis der Datensatzregeln als TypedDict `DatasetOutcome`;
  validierte Profil-JSON-Objekte tragen den dokumentierten Grenztyp
  `JsonObject` (`Mapping[str, Any]`).
- **Aliase:** keine öffentliche Umbenennung. Private Hilfen in `base` heißen
  jetzt `amount_values`, `present_amounts`, `relevance`, `correct_sum`,
  `compare`, `OPERATOR_SYMBOLS`, `MISSING_KEY` (vorher `_amounts`,
  `_relevance`, `_sum`, `_compare`, `_OPS`, `_MISSING_KEY`; nicht öffentlich).
- **Neue Tests** (`tests/test_structure.py`): alte Importpfade, Registry
  (Arten, Reihenfolge, optionale Parameter) und die erste Fehlermeldung von
  97 fehlerhaften Profil- und 16 fehlerhaften Betrugsprofildokumenten,
  aufgezeichnet mit 0.3.0 (`tests/fixtures/validation_errors_0.3.0.json`).

| Messung (src) | 0.3.0 | 0.3.1 |
|---|---|---|
| Funktionen mit McCabe > 10 | 11 | 0 |
| Module > 400 Zeilen | 5 | 0 (größtes 383) |
| Funktionen > 60 Zeilen | 9 | 0 |
| `Any`-Vorkommen | 192 | 42 (+ `JsonObject`-Grenztyp) |
| mypy --strict | sauber | sauber |
| Tests / Abdeckung | 2380 / 96 % | 2496 / 98 % |
