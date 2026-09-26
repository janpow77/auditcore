# REST-Vertrag VVT und DSFA

Vertrag `dataprotection_ui/1`. Serverseite: `auditcore_dataprotection.web`
(ab `auditcore_dataprotection` 0.5.0), Oberfläche: `<flowaudit-vvt>` und
`<flowaudit-dsfa>` aus `@flowaudit/ui` (Vue: `FaVvt`, `FaDsfa`) bzw. die
native React-Komponenten `FlowauditVvt` und `FlowauditDsfa` aus `@flowaudit/ui-react`
(beide auf den Zustandsautomaten aus `@flowaudit/ui-core`).

Alle fachlichen Regeln – Vollständigkeitsprüfung nach Art. 30 Abs. 1 DSGVO,
Schwellwertanalyse, Brutto-/Nettorisiko, Vorschlag, Vier-Augen-Prinzip,
Sperre freigegebener Fassungen – rechnet die Bibliothek. Die Schnittstelle
prüft nur die Hülle der Anfrage; die Oberfläche zeigt nur an.

## Einbindung

| Baustein | Herkunft | Pflicht des Consumers |
|---|---|---|
| `Storage` | Protocol (`registers`, `assessments`, `audit` aus `auditcore_dataprotection.ports`); `InMemoryStorage` nur für Tests/Demo | dauerhafte Ablage in der eigenen Transaktion, Unveränderlichkeit freigegebener Fassungen |
| `Authorizer` | Port der Bibliothek (`Permission`) | Rechte je Mandant und Rolle |
| `create_backend(profile, storage, authorizer)` | `web.backend` | Regelprofil ausdrücklich wählen (kein Standardprofil) |
| `DataProtectionApi` | `web.service`, ohne Web-Framework | – |
| `routes` / `create_app` | `web.http`, Extra `web` (Starlette ≥ 0.26.1) | Einhängen, `identify` |
| `create_router` | `web.fastapi_router`, Extra `fastapi` (FastAPI ≥ 0.92) | wie oben |

```python
from starlette.routing import Mount
from auditcore_dataprotection import Actor, load_profile
from auditcore_dataprotection.web import DataProtectionApi, Principal, create_backend
from auditcore_dataprotection.web.http import routes

api = DataProtectionApi(create_backend(load_profile("auditcore.dsgvo", "2026.10.3"), storage, authorizer))

def identify(request) -> Principal | None:          # Sitzung des Consumers
    user = request.scope.get("user")
    if user is None:
        return None
    return Principal(user.tenant, Actor(user.id, frozenset({user.tenant}), frozenset(user.roles)))

app_routes = [Mount("/api/dataprotection", routes=routes(api, identify))]
```

`identify` darf synchron oder `async` sein; `None` ergibt 401. Schreibende
Anfragen müssen `application/json` sein (415 sonst); das hält einfache
HTML-Formulare fremder Herkunft ab. Consumer mit Sitzungs-Cookies ergänzen
eine eigene CSRF-Prüfung (Middleware oder `identify`). Der FastAPI-Router
bindet dieselben Starlette-Endpunkte ein (`add_route`); sie erscheinen nicht
im OpenAPI-Schema, Router-`dependencies` greifen dort nicht.

## Fehler

Alle Fehler: `{"error": {"code": "…", "message": "…"}}` mit deutscher Meldung.

| Status | Code | Anlass |
|---|---|---|
| 400 | `invalid_request`, `invalid_json` | Hülle fehlerhaft, unbekannte Felder |
| 401 | `unauthenticated` | `identify` lieferte keine Person |
| 403 | `forbidden`, `vier_augen_verletzt` | Recht fehlt; Freigabe durch Bearbeitende |
| 404 | `not_found`, `tenant_mismatch` | nicht vorhanden oder anderer Mandant |
| 409 | `conflict`, `stale_revision`, `version_locked` | Verzeichnis unvollständig, veraltete Revision, gesperrte Fassung |
| 413 | `body_too_large` | Anfrage größer als `max_body_bytes` (Standard 6 MiB) |
| 415 | `unsupported_media_type` | kein JSON |
| 422 | `validation_error`, `profile_error` | Inhalt verletzt den Vertrag der Bibliothek |

## Endpunkte

| Methode, Pfad | Körper | Antwort |
|---|---|---|
| `GET /profile` | – | Formularbeschreibung aus dem Regelprofil: Spalten des Verzeichnisses (`key`, `title`, `reference`, `kind` = `text`/`flag`/`count`, `required`), Blöcke und Fragen der Schwellwertanalyse (`effect` = `hart`/`punkt`/`fria`), Skalen, Schutzziele, Maßnahmen, Risikostufen, Entscheidungen, Stammdaten der Abschätzung |
| `POST /calculate` | `{answers, scenarios}` | Vorschlag der Bibliothek (`propose(...).to_dict()`) für ungespeicherte Eingaben |
| `GET /register` | – | `{draft, released, versions}`; Fassungen mit `content`, `revision`, `editors`, `issues` |
| `POST /register/check` | `{content}` | `{issues}` – Vollständigkeitsprüfung ungespeicherter Inhalte |
| `POST /register/draft` | `{content, expected_revision}` | gespeicherter Entwurf; ohne offenen Entwurf `expected_revision: null` (neue Fassung) |
| `POST /register/release` | `{expected_revision}` | freigegebene Fassung; die bisherige wird `abgeloest` |
| `POST /register/export` | `{format: html\|markdown\|csv, source?: draft\|released}` | Datei; HTML ist die Druckansicht der Bibliothek, CSV mit Formelschutz |
| `GET /assessments?department=` | – | `{items}`: Tätigkeiten der maßgeblichen Fassung mit Stand der neuesten Abschätzung |
| `POST /assessments` | `{activity_id}` | neue Abschätzung (201) |
| `GET /assessments/{id}` | – | Abschätzung mit `answers`, `scenarios`, `proposal`, `open_points`, `release_blockers`, `versions` |
| `POST /assessments/{id}` | `{expected_revision, answers?, scenarios?, necessity?, proportionality?, dossier?, …}` | geänderte Abschätzung; die Bibliothek rechnet den Vorschlag neu |
| `POST /assessments/{id}/decide` | `{expected_revision, decision, justification?, conditions?}` | Entscheidung (Abweichung braucht Begründung) |
| `POST /assessments/{id}/dpo-request` | `{expected_revision, requested_from, requested_on}` | Einholung der DSB-Stellungnahme (Dokumentationsmodus) |
| `POST /assessments/{id}/release` | `{expected_revision}` | Freigabe nach dem Vier-Augen-Prinzip; offene Punkte werden mitgespeichert |
| `POST /assessments/{id}/reassess` | – | neue Fassung aus einer freigegebenen (201) |
| `POST /assessments/{id}/export` | `{format: html\|markdown}` | Bericht |

Antworten und Kennungen sind JSON mit ISO-Zeitstempeln. Die Oberfläche liest
`revision` und schickt sie beim Schreiben zurück (optimistische Sperre).

## CSV

Trenner `;`, UTF-8 mit BOM, Zeilenende CRLF, Präfix `'` vor Texten, die mit
`= + - @`, Tab oder CR beginnen – Verträge `csv-cell` und `csv-document` in
`contracts/common-cases`. Python (`web.csv_cell`) und TypeScript (`csvCell`)
werden gegen dieselben Fälle geprüft.
