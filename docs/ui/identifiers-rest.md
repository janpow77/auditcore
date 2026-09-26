# REST-Vertrag „Kennung prüfen“ (`identifiers_ui/1`, `auditcore_identifiers.web`)

Stand 2026-09-26. Vertrag zwischen `auditcore_identifiers.web` und der
Oberflächenkomponente `<flowaudit-identifier-check>` aus `@auditcore/ui`
(Vue `IdentifierCheck`, React `FlowauditIdentifierCheck`). Geprüft wird
ausschließlich in der Bibliothek; die Oberfläche rechnet keine Prüfziffern.
Kein Profil wird still angenommen: `GET /catalogue` empfiehlt `strict`, die
Oberfläche übernimmt die Empfehlung sichtbar als Vorauswahl und sendet das
Profil in jeder Anfrage ausdrücklich mit.

Ungültige Kennungen sind **Ergebnisse**, keine Fehler (HTTP 200 mit
`status` `INVALID` oder `MISSING`). Fehlercodes gibt es nur für Anfragen,
die den Vertrag verletzen.

## Einbinden

| Extra | Paket (pip) | Debian (optional, „Suggests“) |
|---|---|---|
| `auditcore_identifiers[web]` | `starlette>=0.26.1,<2` | `python3-starlette (>= 0.26.1)` |
| `auditcore_identifiers[fastapi]` | `fastapi>=0.92` | `python3-fastapi (>= 0.92)` |

```python
from starlette.routing import Mount
from auditcore_identifiers.web import Limits, create_app, create_router, routes

app = create_app("/api/kennungen")                                   # eigenständig (Starlette)
fastapi_app.include_router(create_router("/api/kennungen"))          # FastAPI
starlette_app.router.routes.append(Mount("/api/kennungen", routes=routes(limits=Limits(max_items=5_000))))
```

`catalogue`, `check_one` und `check_batch` sind ohne Web-Framework
aufrufbar (nur Standardbibliothek). Starlette und FastAPI liefern
byteidentische Antworten. Authentisierung, CORS und Ratenbegrenzung sind
Sache der Anwendung.

`Limits`: `max_items` (10 000 Zeilen je Stapel), `max_value_length`
(200 Zeichen je Wert), `max_body_bytes` (4 MiB).

## Endpunkte

| Methode | Pfad | Zweck |
|---|---|---|
| GET | `/catalogue` | Vertrag, Kennungsarten, Profile, Bezeichnungen, Grenzen |
| POST | `/check` | eine Kennung prüfen |
| POST | `/check/batch` | viele Kennungen (z. B. aus einer Tabelle) unter einem Profil prüfen |

### `GET /catalogue`

```json
{"contract": "identifiers_ui/1", "library": "auditcore_identifiers 0.1.0",
 "recommended_profile": "strict",
 "kinds": [{"id": "iban", "label": "IBAN", "description": "…", "country": false},
           {"id": "vat_id", "label": "USt-IdNr.", "description": "…", "country": true}, "…"],
 "profiles": [{"id": "strict", "title": "Streng (Standard)", "rationale": "…",
               "origin": "auditcore_identifiers", "legacy": false,
               "kinds": ["iban", "bic", "vat_id", "tax_id", "tax_number", "lei", "register_number"]},
              {"id": "flowworkshop.legacy", "title": "…", "legacy": true, "kinds": ["lei"], "…": "…"}],
 "reasons": [{"id": "invalid_checksum", "label": "Prüfziffer falsch"}, "…"],
 "detail_labels": {"checksum": "Prüfziffer", "bban": "BBAN", "…": "…"},
 "value_labels": {"verified": "geprüft", "not_checked": "nicht geprüft", "land": "Landesformat", "federal": "Bundesformat"},
 "limits": {"max_items": 10000, "max_value_length": 200, "max_body_bytes": 4194304}}
```

Kennungsarten: `iban`, `bic`, `vat_id`, `tax_id` (Steuer-ID), `tax_number`
(Steuernummer, nur grobe Formatprüfung), `lei`, `register_number`
(Handelsregisternummer, nur Format). `country: true` heißt: ein Land kann
mitgegeben werden (USt-IdNr. ohne Länderpräfix). Legacy-Profile prüfen nur
die in `kinds` genannten Arten; die Oberfläche bietet je Profil nur diese an.
Nicht enthalten: Abfragen externer Register (VIES, GLEIF, BZSt) und
nationale Kontoprüfziffern.

### `POST /check`

Anfrage: `kind` (Pflicht), `value` (Text ≤ 200 Zeichen oder `null`),
`profile` (Pflicht), `country` (optional, ≤ 3 Zeichen).

```json
{"contract": "identifiers_ui/1",
 "result": {"kind": "iban", "status": "INVALID", "raw": "DE89370400440532013001",
            "normalized": null, "reason": "invalid_checksum",
            "message": "IBAN-Prüfziffer ist falsch", "country": "DE", "profile": "strict",
            "details": {}, "kind_label": "IBAN", "reason_label": "Prüfziffer falsch"}}
```

`result` ist `CheckResult.to_dict()` der Bibliothek plus `kind_label` und
`reason_label`. `status`: `VALID`, `INVALID`, `MISSING`; `message` ist die
Begründung (Profil `strict` deutsch, Legacy-Profile im Originalwortlaut);
`details` enthält z. B. `bban`, `checksum` (`verified`/`not_checked`),
`format`, `land`. Ein leerer Wert (`null`) ergibt `MISSING`.

### `POST /check/batch`

Anfrage: `profile` (Pflicht), `items` (1 … `max_items` Einträge) mit `kind`,
`value`, optional `country` und `ref` (Text oder ganze Zahl; ohne `ref` gilt
die laufende Nummer ab 1). Die Oberfläche sendet als `ref` die gewählte
Bezugsspalte oder die Zeilennummer der Datei.

```json
{"contract": "identifiers_ui/1", "profile": "strict",
 "results": [{"index": 0, "ref": "B-1", "error": null, "kind": "iban", "status": "VALID", "…": "…"},
             {"index": 4, "ref": "B-5", "error": {"code": "unknown_kind", "message": "…"}}],
 "summary": {"total": 5, "valid": 2, "invalid": 1, "missing": 1, "not_checked": 1}}
```

Zeilen mit unbekannter Kennungsart (`unknown_kind`) oder einer Art, die das
Profil nicht prüft (`unsupported_kind`), werden je Zeile gemeldet
(`error`), statt die ganze Tabelle abzulehnen. Andere Vertragsverstöße einer
Zeile (z. B. `value` keine Zeichenkette) lehnen die Anfrage mit Feldpfad ab
(`items[3].value`).

## Fehler

`{"error": {"code": "…", "message": "…"}}` mit deutscher Meldung:
400 `invalid_json`, 413 `too_large` (Körper oder Zeilenzahl),
422 `invalid_input`, `unknown_profile`, `unknown_kind`, `unsupported_kind`
(nur `/check`).

## Oberfläche

`createIdentifiersRestPort({ baseUrl: '/api/kennungen' })` aus
`@auditcore/ui-core` (auch über `@auditcore/ui` und `@auditcore/ui-react`).
Die Komponente zeigt Profilwahl (Empfehlung und Altverhalten gekennzeichnet,
Herkunft und Zweck aufklappbar), die Einzelprüfung mit Status, Begründung,
Grund, Normalform und Einzelheiten sowie die Stapelprüfung: Datei (CSV, TSV,
Text) über den gemeinsamen TableImport-Controller lesen, Wertspalte,
Kennungsart (fest oder aus einer Spalte; Kennung oder Bezeichnung, z. B.
„USt-IdNr.“), Bezugs- und Landspalte zuordnen, Ergebnis filtern
(„Nur Auffälligkeiten“) und als CSV (Excel-DE) speichern.
Ereignisse: `identifier-checked`, `batch-checked`, `error` (React
`onIdentifierChecked`, `onBatchChecked`, `onError`).
