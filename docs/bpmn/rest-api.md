# REST-Vertrag für Web Component und eigenständige App

Dieser Vertrag beschreibt die HTTP-Schnittstelle, gegen die die Web Component
`<flowaudit-bpmn-editor>` (Attribut `api-base`) und die eigenständige App
(`dist-standalone/`) arbeiten. Die Bibliotheken selbst greifen nie aufs Netz zu;
die REST-Anbindung liegt ausschließlich in `@flowaudit/bpmn-vue/src/rest/restPorts.ts`
(`RestStorage`, `RestLegalSearch`, `RestProfiles`, `RestCatalogue`,
`RestValidation`, `RestEsi`). Ein Server (z. B. eine spätere FastAPI-Anbindung
von `auditcore_bpmn`) muss nur diese Endpunkte bereitstellen.

## Grundsätze

- **Basis-URL** frei wählbar, z. B. `https://intranet.example/api/bpmn`. Alle Pfade
  unten sind relativ dazu. Die eigenständige App nimmt standardmäßig `./api`.
- **JSON** folgt dem Datenmodell von `auditcore_bpmn`: englische Feldnamen in
  `snake_case` (`folder_id`, `valid_from`, `key_requirement`, `short_title`).
  Die Umwandlung nach camelCase erledigt `fromWire`/`toWire`
  (`@flowaudit/bpmn-flowaudit`). Wörterbuchfelder (`keys`, `params`,
  `status_distribution`, `key_requirement_coverage`, `sha256`) bleiben
  unverändert, ihre Schlüssel sind Daten.
- **XML** wird als `application/xml; charset=utf-8` übertragen, unverändert
  (der Server darf nichts umformatieren, sonst stimmen Freigabe-Hashes nicht).
- **Anmeldung** ist Sache des Hosts: Cookies (`credentials: 'same-origin'`) oder
  Kopfzeilen über `restPorts({ headers })`.
- **Fehler**: HTTP-Status ≥ 400 mit JSON `{"detail": "…"}` (FastAPI-Stil, auch
  Liste `[{"msg": "…"}]`) oder `{"message": "…"}`. Der Text wird in der
  Oberfläche angezeigt, also deutsch formulieren.
- **Nebenläufigkeit**: `GET /collection` darf ein `ETag` senden; der Client
  schickt es bei `PUT /collection` als `If-Match` zurück. Passt es nicht,
  antwortet der Server mit `412 Precondition Failed`; die Oberfläche meldet
  „Die Daten wurden zwischenzeitlich geändert; bitte neu laden.“

## Endpunkte

| Methode | Pfad | Anfrage | Antwort | Genutzt von |
|---|---|---|---|---|
| GET | `/collection` | – | Sammlung (JSON) oder `204` | Sammlung |
| PUT | `/collection` | Sammlung (JSON), optional `If-Match` | `204`, optional neues `ETag` | Sammlung |
| GET | `/diagrams/{id}/xml` | – | BPMN-XML | Editor |
| PUT | `/diagrams/{id}/xml` | BPMN-XML | `204` | Editor (Speichern) |
| DELETE | `/diagrams/{id}` | – | `204` | Sammlung |
| PUT | `/diagrams/{id}/approvals/{version}` | BPMN-XML des freigegebenen Stands | `204` | Freigabe |
| GET | `/diagrams/{id}/approvals/{version}` | – | BPMN-XML | Freigabe (optional) |
| GET | `/diagrams/{id}/comments` | – | Liste `Comment` | Notizen |
| PUT | `/diagrams/{id}/comments` | Liste `Comment` | `204` | Notizen |
| GET | `/legal-bases?q=…&limit=…&profile=…&locale=de` | – | Liste Rechtsgrundlagen-Treffer | Rechtsgrundlagen-Suche |
| GET | `/profiles` | – | Liste Profil-Kurzinfo | Diagramm-Infos |
| GET | `/profiles/{id}?version=…` | – | Profil (Schema `auditcore_bpmn.profile/1`) | Rollen, KA/BK, Regeln |
| GET | `/profiles/{id}/key-requirements?locale=de` | – | Liste Kernanforderungen mit BK | KA/BK-Auswahl |
| POST | `/validation` | `{"xml", "profile", "reference_date", "locale"}` | Prüfbericht | „Serverprüfung“ |
| POST | `/esi-requirements` | `{"xml", "diagram_id"}` | ESI-Anforderungen je Element | ESI-Abgleich |

`{id}` und `{version}` werden URL-kodiert. IDs erfüllen
`^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$` (wie in `auditcore_bpmn`).

Ordner, Tags, Reihenfolge und Freigabe-Hashes sind Teil des Sammlungsdokuments
(ein PUT pro Änderung); es gibt bewusst keine Einzel-Endpunkte je Ordner, damit
Server und Browser dieselbe Datenstruktur pflegen. Diagramm-Infos stehen im XML
(`flowaudit:diagrammInfo`) und zusätzlich als Auszug im Sammlungseintrag
(`diagrams[].info`).

## Datenformate

### Sammlung (`GET/PUT /collection`)

Schema `auditcore_bpmn.diagram-collection/1`, maßgeblich ist
`packages/auditcore_bpmn/src/auditcore_bpmn/schemas/diagram-collection-1.schema.json`.
Ein Test (`packages-js/bpmn-flowaudit/test/pythonSchemas.spec.ts`) prüft die vom
Browser geschriebene Sammlung gegen dieses Schema.

```json
{
  "schema": "auditcore_bpmn.diagram-collection/1",
  "id": "sammlung",
  "name": "Diagrammsammlung",
  "folders": [{ "id": "antrag", "name": "Antragsverfahren", "parent_id": "vks", "position": 0 }],
  "tags": [{ "id": "kern", "name": "Kernprozess", "color": "#1976d2" }],
  "diagrams": [{
    "id": "bewilligung",
    "name": "Bewilligung und Auszahlung",
    "folder_id": "antrag",
    "tags": ["kern"],
    "position": 0,
    "info": { "title": "Bewilligung und Auszahlung", "status": "freigegeben", "version": "1.2" },
    "excerpt": {
      "process_ids": ["Process_1"], "calls": [], "link_throws": [], "link_catches": [],
      "activities": 12, "activities_with_legal_basis": 9,
      "keys": { "ka": { "2": ["Task_Pruefen"] }, "rolle": { "zgs": ["Lane_ZGS"] } }
    },
    "approvals": [{ "version": "1.2", "sha256": "…64 Hex-Zeichen…", "approved_by": "Referatsleitung", "approved_on": "2026-09-01" }]
  }]
}
```

Der Auszug (`excerpt`) wird immer aus dem XML abgeleitet und nie von Hand
gepflegt. Freigaben sind unveränderlich: dieselbe Version mit anderem Hash
lehnen Browser und `auditcore_bpmn` ab.

### Kommentar (`Comment`)

```json
{ "id": "c1", "element_id": "Task_Pruefen", "text": "Frist klären", "author": "Prüferin", "timestamp": "2026-09-25T10:00:00Z", "resolved": false }
```

### Rechtsgrundlagen-Treffer

Felder von `flowaudit:rechtsgrundlage` (`act`, `article`, `section`, `annex`,
`paragraph`, `subparagraph`, `sentence`, `point`, `number`, `version`, `eli`,
`celex`, `url`, `short_title`, `note`) plus Anzeigehilfen `title`, `excerpt`,
`origin` (z. B. „EUR-Lex“, „Profil“). Die Anzeigehilfen werden beim Übernehmen
verworfen.

### Profil-Kurzinfo und Kernanforderungen

```json
[{ "id": "foerderperiode-2021-2027", "version": "2026.09.1", "title": "Förderperiode 2021-2027", "programming_period": "2021-2027" }]
```

```json
[{ "number": 2, "title": "Angemessene Auswahlverfahren …", "bodies": "VB, ZGS", "criteria": [{ "code": "2.3", "title": "…" }] }]
```

### Prüfbericht (`POST /validation`)

Schema `auditcore_bpmn.validation-report/1`
(`schemas/validation-report-1.schema.json`); dieselbe Form erzeugt
`reportToWire()` im Browser.

```json
{
  "schema": "auditcore_bpmn.validation-report/1",
  "ruleset_version": "2026.09.1",
  "profile": "foerderperiode-2021-2027@2026.09.1",
  "reference_date": "2026-09-25",
  "valid": false,
  "counts": { "fehler": 1, "warnung": 0, "hinweis": 3 },
  "issues": [{ "rule_id": "BPMN-S010", "severity": "fehler", "severity_label": "Fehler", "message": "Prozess „Antrag“ hat kein Startereignis.", "params": { "name": "Antrag" }, "element_id": "Process_1" }]
}
```

Die Oberfläche liest `issues` und zeigt bei vorhandenen Serverhinweisen diese
statt der Browserprüfung an (gleiche Regel-IDs und Texte).

### ESI-Anforderungen (`POST /esi-requirements`)

Wie im audit_designer: eine Liste, ein Objekt je Element oder
`{ "requirements": […] }`/`{ "elements": […] }`. Je Anforderung `element_id`,
`element_name`, `requirement_id`, `expected`, `actual` und optional `status`
(`fulfilled|unclear|missing`; sonst aus Soll/Ist abgeleitet). Die
Normalisierung übernimmt `normalizeEsiResponse`.

## Einbettung der eigenständigen App

`dist-standalone/` enthält `index.html` und `assets/` mit relativen Pfaden; ein
Server liefert die Dateien unter beliebigem Pfad aus und setzt die API-Basis
auf eine der drei Arten (Vorrang von unten nach oben):

1. `<meta name="flowaudit-api-base" content="/api/bpmn">` in `index.html`,
2. `window.FLOWAUDIT_CONFIG = { apiBase: '/api/bpmn', locale: 'de', profile: '…', author: '…', title: '…' }`
   vor dem Laden der App,
3. Abfrageparameter `?api=/api/bpmn&locale=en&profile=…`.

Ohne Profil-Endpunkte nutzt die App die mitgebündelten Profile von
`auditcore_bpmn`.
