# REST-Vertrag Risiko-Merkmale (`auditcore_risk.web`)

Stand 2026-09-25. Vertrag zwischen dem Python-Router `auditcore_risk.web` und
den Oberflächenkomponenten `@flowaudit/ui` (`<flowaudit-risk-flags>`, Vue und
React). Die Schnittstelle wertet genau **ein ausdrücklich benanntes Profil** aus;
es gibt kein Standardprofil, keinen profilübergreifenden Score und keine
stille Änderung von Schwellen. Unbestimmte Merkmale bleiben unbestimmt.

## Einbinden

| Extra | Paket (pip) | Debian (optional, „Suggests“) |
|---|---|---|
| `auditcore_risk[web]` | `starlette>=0.26.1` | `python3-starlette (>= 0.26.1)` |
| `auditcore_risk[fastapi]` | `fastapi>=0.92` | `python3-fastapi (>= 0.92.0)` |

```python
# eigenständig (Starlette, z. B. mit uvicorn)
from auditcore_risk.web import create_app
app = create_app("/risk", max_records=20_000, max_body_bytes=20 * 1024 * 1024)

# in eine bestehende FastAPI-Anwendung
from auditcore_risk.web import build_fastapi_router
app.include_router(build_fastapi_router("/api/risk"))

# in eine bestehende Starlette-Anwendung
from starlette.routing import Mount
from auditcore_risk.web import routes
app.router.routes.append(Mount("/risk", routes=routes()))
```

Die Handler (`handle_profiles`, `handle_profile`, `handle_check_columns`,
`handle_evaluate`) sind ohne Web-Framework aufrufbar und liefern dieselben
JSON-Daten; das installierte Paket braucht die Werkzeuge im Repository nicht.
Die FastAPI-Variante hängt die Starlette-Endpunkte unverändert ein (Antworten
byteidentisch); sie erscheinen deshalb nicht im OpenAPI-Schema von FastAPI –
maßgeblich ist dieses Dokument. Authentisierung, CORS und Ratenbegrenzung sind
Sache der einbindenden Anwendung.

## Endpunkte

Pfade relativ zum Einhängepunkt (Standard `/risk`).

| Methode | Pfad | Zweck |
|---|---|---|
| GET | `/profiles` | alle mitgelieferten Profile (Kurzform) |
| GET | `/profiles/{id}/{version}` | Profil mit Regeln, Parametern und Eingabefeldern |
| POST | `/profiles/{id}/{version}/check-columns` | Folgen fehlender Spalten vor der Auswertung |
| POST | `/evaluate` | Auswertung von Datensätzen mit einem Profil |

Alle Antworten sind `application/json` (UTF-8). Zahlen, die in JSON nicht
darstellbar sind, erscheinen als Text `"NaN"`, `"Infinity"`, `"-Infinity"`;
Datumswerte als ISO-Text.

### `GET /profiles`

```json
{"profiles": [{"id": "riskanalysis.year_bound", "version": "2026.09.5",
  "fingerprint": "dd32ede2…", "status": "APPROVED", "kind": "record_red_flags",
  "legal_status": "…", "rule_count": 10, "field_count": 17, "open_decision_count": 1}]}
```

`status` ist einer von `LEGACY_CHARACTERIZED`, `CANDIDATE_HUMAN_DECISION_REQUIRED`,
`APPROVED`. Welche Fassung empfohlen ist, steht im Paket-README, nicht in der
Schnittstelle; die Oberfläche zeigt den Status unverändert an.

### `GET /profiles/{id}/{version}`

Kurzform wie oben, zusätzlich:

| Feld | Inhalt |
|---|---|
| `source` | `repository`, `path`, `commit`, `symbols`, `decision`, `derived_from`, `rights` (soweit im Profil) |
| `input_contract` | Eingabevertrag laut Profil (Text oder `null`) |
| `open_decisions` | offene fachliche Entscheidungen (Liste von Texten) |
| `output`, `summary_format`, `assessment` | Ausgabeformat, Format der Zusammenfassung, Art der Bewertung (`null`, `severity_weighted_sum`, `points_stages`) |
| `rules[]` | je Regel: `code`, `label`, `kind`, `scope` (`record`/`dataset`), `severity`, `interpretation`, `note`, `requires`, `when_missing_columns` (`error`, `skip`, `all_false`, `undetermined`), `column`, `points`, `inputs` (gelesene Felder), `parameters` (Schwellen und Faktoren, Punktnotation, z. B. `"thresholds.static": [1000.0, …]`), `params` (vollständige Parameter), `origin` (Fundstelle in der Quelle) |
| `fields[]` | je Eingabefeld: `name`, `meaning`, `meaning_source`, `requirement` (`required`, `value_required`, `optional`), `required_by`, `value_required_by`, `uses[]` mit `code`, `label`, `role`, `absent` (Folge bei fehlender Spalte), `empty` (Folge bei leerem Wert) |

`fields` ist die JSON-Fassung von
[`packages/auditcore_risk/docs/eingabefelder.md`](../../packages/auditcore_risk/docs/eingabefelder.md)
(gleiche Ableitung, `tools/export_field_catalog.py`, Test hält beides synchron).
Weicht der Fingerabdruck eines Profils vom Katalog ab, ist `fields` leer.

### `POST /profiles/{id}/{version}/check-columns`

Anfrage `{"columns": ["bruttobetrag", "Name", "zahlungsempfaenger"]}`, Antwort:

```json
{"profile": {…}, "columns": […], "complete": false, "aborts": false,
 "rules": [{"code": "RF02", "label": "…", "missing": ["nettobetrag"],
            "when_missing_columns": "undetermined"}]}
```

`aborts` ist `true`, wenn eine fehlende Spalte die Auswertung mit
`input_error` abbrechen würde (`when_missing_columns = error`). `skip` heißt:
Regel wird übersprungen (`skipped` der Auswertung), `all_false`: kein Merkmal
für alle Datensätze, `undetermined`: je Datensatz unbestimmt mit Begründung.

### `POST /evaluate`

Anfrage:

| Feld | Pflicht | Inhalt |
|---|---|---|
| `profile` | ja | `{"id": "…", "version": "…"}` |
| `records` | ja | Liste von Objekten (Spalte → Wert); ein fehlender Schlüssel ist ein fehlender Wert |
| `columns` | nein | Spaltenmenge; Standard: Vereinigung der Schlüssel. Maßgeblich für „Spalte fehlt“ |
| `reference_date` | nein | ISO-Datum für Profile mit Stichtag statt Belegdatum |
| `record_key` | nein | Feld, dessen Wert je Datensatz als `key` zurückkommt (z. B. `belegnummer`) |
| `flatten` | nein | `true`: verschachtelte Objekte eine Ebene tief als `eltern.kind` |
| `points` | nein | Punkte je Code (nur Profile, deren Bewertung übergebene Punkte erlaubt) |

Andere Felder werden abgewiesen. Beträge sind JSON-Zahlen (Text ist bei
`parse = strict` ein Eingabefehler), Datumswerte ISO-Text.

Antwort: `Evaluation.to_dict()` der Bibliothek, ergänzt um Anzeigedaten:

| Feld | Inhalt |
|---|---|
| `library`, `profile` | Bibliotheksstand und Profilidentität (`id`, `version`, `fingerprint`, `status`) |
| `records[]` | `index`, `key`, `flags` (Code → `true`/`false`/`null`; `null` = unbestimmt), `codes` (Treffer in Profilreihenfolge), `undetermined` (Code → Begründung), `values` (z. B. `name_match`), `assessment`, `hits[]`, `inputs` |
| `records[].hits[]` | `code`, `label`, `reason`, `interpretation`, `note`, `severity`, `messages`, `evidence` (Belegwerte inkl. angewandter Schwelle), `origin`, `inputs` (gelesene Eingabefelder mit Werten) |
| `records[].inputs` | für jeden Treffer **und jedes unbestimmte Merkmal**: Code → Feld → Wert |
| `dataset[]` | datensatzübergreifende Befunde (`code`, `label`, `triggered`, `value`, `reason`, `evidence`) |
| `skipped` | übersprungene Regeln: Code → Grund (z. B. „Spalten fehlen: zahlungsdatum“) |
| `summary[]` | Zusammenfassung im Format des Profils (riskanalysis: `code`, `bezeichnung`, `treffer`, `basis`, `anteil_prozent`, `volumen`, ggf. `unbestimmt`; Flowstat: `code`, `count` bzw. `share`) |
| `rules[]` | wie beim Profilabruf |
| `columns` | verwendete Spaltenmenge |
| `missing_columns` | Code → fehlende Pflichtspalten (Planungshilfe) |

Zustände je Datensatz und Regel, wie die Oberfläche sie zeigt:

| Zustand | Bedingung |
|---|---|
| Treffer | `flags[code] === true` |
| kein Merkmal | `flags[code] === false` |
| unbestimmt | `flags[code] === null`, Begründung in `undetermined[code]` |
| übersprungen | Code in `skipped` (Regel lief nicht; `flags` enthält den Code nicht) |
| Datensatzebene | `scope = dataset`: Befund in `dataset[]`, nicht je Datensatz |

Beispiel (Profil `riskanalysis.year_bound` 2026.09.5, Nettobetrag fehlt):

```json
{"records": [{"index": 0, "key": "B1",
  "flags": {"RF01": true, "RF02": null, "RF08": null, "RF09": false, "…": false},
  "codes": ["RF01"],
  "undetermined": {"RF02": "Nettobetrag fehlt in der Quelle",
                   "RF08": "Nettobetrag fehlt in der Quelle"},
  "hits": [{"code": "RF01", "reason": "Betrag 40.000,00 ist ein glattes Vielfaches von 1.000,00.",
            "evidence": {"amount": 40000.0, "multiple": 1000.0},
            "inputs": {"bruttobetrag": 40000.0}, "…": "…"}],
  "inputs": {"RF01": {"bruttobetrag": 40000.0},
             "RF02": {"nettobetrag": null, "rechnungsdatum_dt": "2025-03-01"},
             "RF08": {"kostenart_auswertung_bezeichnung": null, "nettobetrag": null,
                      "vergabenummer": "0=ni"}}}],
 "summary": [{"code": "RF02", "treffer": 0, "basis": 1, "unbestimmt": 1, "…": "…"}]}
```

## Fehler

Fehlerantworten haben immer die Form `{"error": {"code": "…", "message": "…"}}`
(Meldung deutsch).

| Status | `code` | Anlass |
|---|---|---|
| 400 | `invalid_json` | Anfrage ist kein JSON |
| 400 | `invalid_request` | Form verletzt (fehlendes `profile`, unbekannte Felder, falsche Typen, kein ISO-Datum) |
| 400 | `input_error` | Datensätze verletzen den Vertrag des Profils (Pflichtspalte fehlt, Betrag als Text …) |
| 404 | `profile_not_found` | Profil oder Version unbekannt (kein Rückfall auf eine andere Fassung) |
| 413 | `too_many_records`, `body_too_large` | Grenzen `max_records` (Standard 20 000) bzw. `max_body_bytes` (Standard 20 MiB) |
| 422 | `profile_error` | Profil lässt die Anfrage nicht zu (z. B. `points` ohne Erlaubnis) |
| 503 | `missing_optional_dependency` | Profil braucht ein nicht installiertes Extra (z. B. `procurement`, `fuzzy`) |

## Versionierung

Das Schema ist Teil von `auditcore_risk`; neue Felder kommen additiv hinzu.
Bestehende Felder ändern Bedeutung oder Typ nur mit neuer Hauptversion der
Bibliothek. Die Komponenten werten unbekannte Felder nicht aus.
