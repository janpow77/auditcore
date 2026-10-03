# Changelog – auditcore_risk

## 0.4.0 – 2026-10-03 – BL_RF07/BL_RF10 in ganzen Cent, Spaltenpfad (noch nicht veröffentlicht)

**Neue Profilversion `audit_designer.flowstat_belegliste` 2026.10.1
(RK-C12, Nutzerentscheidung vom 03.10.2026, `APPROVED`, abgeleitet von
1254591156d3, eigener Fingerabdruck):** BL_RF07 (anerkannter Betrag ≠
Projektbetrag − Kürzung) und BL_RF10 (Anteil des größten Rechnungsstellers)
rechnen in ganzen Cent; die Regelarten `balance_mismatch` und `top_share`
haben dafür den optionalen Parameter `arithmetic: "cents"`. Das Legacy-Profil
1254591156d3 bleibt abrufbar und bitgleich (Gleitkomma der Quelle, alle
112 Frames wie aufgezeichnet). Jeder Betrag wird zuerst mit `auditcore_compute.to_cents` kaufmännisch
(`ROUND_HALF_UP` über `Decimal(str(x))`) gerundet; die Toleranz 0,01 ist
1 Cent. Ein Betrag, der nicht endlich ist oder 10 Mrd. € übersteigt (bei
BL_RF07 auch die Summe der Abzüge), macht BL_RF07 für den Beleg unbestimmt
(`None` mit Grund) bzw. den BL_RF10-Anteil nicht bestimmbar (kein Treffer,
`value` `None`). Mit `arithmetic: "cents"` muss `tolerance` ganze Cent
angeben (Profilprüfung). Alle bestehenden Profile liefern bitgleich dieselben
Ergebnisse wie 0.3.4.

Charakterisierung der Version 2026.10.1 gegen die 112 Flowstat-Frames
(`tools/flowstat_cent_deviations.py`, `tests/fixtures/flowstat_cent_deviations.json`;
`flowstat_observed.json` bleibt die Aufzeichnung des Originals):

- BL_RF07, 41 Treffer entfallen (alt `True`, neu `False`): Differenz genau
  −1 Cent, als Gleitkommazahl knapp über 0,01 (z. B. 6.544,26 − 0 − 6.544,27 =
  −0,010000000000218279). random-20260923-001 Zeile 6; -002 Zeile 11, 15;
  -003 Zeile 2; -005 Zeile 8; -006 Zeile 3; -012 Zeile 18; -019 Zeile 2;
  -020 Zeile 13; -023 Zeile 5, 19; -025 Zeile 4; -026 Zeile 21, 22; -030
  Zeile 0; -031 Zeile 7; -032 Zeile 0; -033 Zeile 1; -036 Zeile 8; -038
  Zeile 24; -039 Zeile 5; -041 Zeile 1, 6; -043 Zeile 5; -044 Zeile 5; -047
  Zeile 0; -052 Zeile 1; -054 Zeile 2, 7, 14; -055 Zeile 0; -057 Zeile 12;
  -067 Zeile 6; -069 Zeile 7, 8; -078 Zeile 15; -082 Zeile 0, 5, 22; -088
  Zeile 16, 25. Die Zähler BL_RF07 sinken in 31 Frames entsprechend.
- BL_RF07, 1 Beleg unbestimmt (alt `False`, neu `None`): rf01-rf02 Zeile 6,
  Projektbetrag und anerkannter Betrag unendlich (Gleitkomma: inf − inf = NaN,
  kein Treffer); der Zähler bleibt 0.
- BL_RF10: keine Entscheidung geändert; in 6 Frames weicht der Anteil in den
  letzten beiden Binärstellen ab (exakter Quotient der Cent-Summen).

**Spaltenpfad:** `auditcore_risk.columns.evaluate_columns(columns, profile, *,
reference_date=None) -> ColumnEvaluation` und
`auditcore_risk.frame.evaluate_frame_columns(frame, profile, *,
reference_date=None)` werten Spalten (Listen, ndarrays, pandas-/polars-Serien)
ohne `to_dict("records")` aus. Vektorisiert über `auditcore_compute`
(`to_cents_buffer`, `reconcile`, `factorize`) bzw. NumPy: `round_multiple`,
`near_threshold` (feste Schwellen), `missing_value`, `date_before`
(`datetime64`), `duplicate_key`, `nonzero_without_text`, `balance_mismatch`,
`missing_procurement`, `amount_with_marker`, `top_share`; alle übrigen
Regelarten und Parameter laufen über die Regelart je Datensatz auf denselben
Spalten. Merkmale, Zähler, Werte, Datensatzbefunde und Übersicht sind gleich
`evaluate` (Abgleich auf allen 112 Flowstat- und 173 riskanalysis-Frames und
mit Hypothesis); Begründungen je Treffer liefert weiterhin `evaluate`. Profile
mit Bewertung je Datensatz (`assessment`) lehnt der Spaltenpfad ab.
Im Legacy-Profil (Gleitkomma) läuft BL_RF10 über die Regelart je Datensatz
(`math.fsum` ist nicht bitgleich vektorisierbar), BL_RF07 vektorisiert in
derselben Rechenreihenfolge. `tools/benchmark_columns.py` (Profil 2026.10.1):
500.000 Belege 0,9 s statt 21,9 s.

Neue Laufzeitabhängigkeiten `auditcore_compute==0.1.0` und `numpy>=1.24`
(`import auditcore_risk` lädt beide nicht; der Datensatzpfad importiert
`to_cents` erst bei BL_RF07/BL_RF10).

## Unreleased (vor 0.4.0)

Keine Verhaltensänderung. Fachliche Spezifikation `docs/spezifikation.md` (Zweck, Verträge, Invarianten, Fehlerfälle, Abgrenzung, bewusste Abweichungen vom Altverhalten mit benannten Legacy-Varianten); Status im Paketkatalog „spezifiziert“. 11 Invarianten (I1–I11) als Hypothesis-Eigenschaftstests in `tests/test_spezifikation.py`; keine Befunde. `hypothesis` im Extra `dev`.

Keine Versionsanhebung (Release-Ablauf). Abwärtskompatible Erweiterung.

- Betrugsprüfsignale als Risiko-Merkmale: `web.signal_evaluation`,
  `GET /fraud-profiles`, `POST /fraud-signals/evaluate`; `GET /profiles/{id}/{version}`
  beschreibt auch `signal_score`-Profile. Blocker/Warnungen von `score_signals`
  werden Treffer, abgebrochene Teilprüfungen machen ihre Codes unbestimmt.
- `signal_score`-Profile dürfen einen Block `display` (Bezeichnungen je Code und
  Teilprüfung) tragen. Neue Fassung `flowinvoice.fraud_signals` 2026.09.3 = 2026.09.2
  plus Bezeichnungen (Status `CANDIDATE_HUMAN_DECISION_REQUIRED`, Texte offen).
- Parität: 268 ausgeführte Läufe des flowinvoice-`FraudDetectionManager`
  (fb2d185) und `score_signals` mit 2026.09.2 (`tests/test_web_signals.py`).

## 0.3.4 – 2026-09-26 – Paketstand für Release v0.4.2

Keine Verhaltensänderung. README mit den Installationsangaben aus Release v0.4.1. Pins: `auditcore_common==0.2.0`, `auditcore_entity_matching==0.2.4`, `auditcore_procurement==0.2.4`.

## 0.3.3 – 2026-09-26 – Paketstand für Release v0.4.1

Keine Verhaltensänderung. Pins `auditcore_common==0.1.1`, `auditcore_entity_matching==0.2.3` (auch Extra `fuzzy`) und Extra `procurement` `auditcore_procurement==0.2.3`; README nach der Vorlage.

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
