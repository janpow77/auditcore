# REST-Vertrag PDF schwärzen

Vertrag `pdf_redaction/1`. Serverseite: `auditcore_pdf.web` (ab
`auditcore_pdf` 0.3.0, Extras `web` bzw. `fastapi`). Oberfläche:
`<flowaudit-pdf-redaction>` / `PdfRedaction` aus `@auditcore/ui` und
`FlowauditPdfRedaction` aus `@auditcore/ui-react`
([redaction.md](redaction.md)).

Der Dienst hält **keinen Zustand**. Jede Anfrage bringt die PDF erneut mit,
und der Plan wird weder gespeichert noch protokolliert, weil er Klartext der
Fundstellen enthält. Geschwärzt wird erst nach ausdrücklicher Bestätigung.
Die Datei wird nur ausgeliefert, wenn die Nachprüfung keine ausgewählte
Fundstelle mehr lesbar findet.

## Einbindung

| Baustein | Herkunft | Pflicht des Consumers |
|---|---|---|
| `RedactionService(ner=None, limits=None)` | Kern, ohne Web-Framework | Namenserkennung (`NerFn`) und Grenzen (`Limits`) festlegen |
| `routes(service, prefix="")` / `create_app(service, prefix="")` | Extra `web` (Starlette ≥ 0.47.2, python-multipart) | Einhängen, Anmeldung, CORS, Ratenbegrenzung |
| `create_router(service, prefix="")` | Extra `fastapi` (FastAPI ≥ 0.116.1) | wie oben |

```python
import spacy
from starlette.routing import Mount
from auditcore_pdf.web import Limits, RedactionService, routes
from auditcore_pdf.redaction import spacy_ner  # Extra [ner], optional

ner = spacy_ner(spacy.load("de_core_news_lg"))  # oder None ohne KI-Namenserkennung
service = RedactionService(ner=ner, limits=Limits(max_upload_bytes=20 * 1024 * 1024))
app_routes = [Mount("/api/redaction", routes=routes(service))]
```

Ohne `ner` meldet der Katalog die KI-Namenserkennung als nicht verfügbar, und
Anfragen mit dem Muster `ki_namen` erhalten 503.

## Pflichten des Consumers

- **Anmeldung und Berechtigung:** Die Bibliothek authentisiert nicht. Sie
  wird hinter der Anmeldung der Anwendung eingehängt.
- **CORS:** Bei Aufruf von einer anderen Herkunft müssen die Kopfzeilen des
  Berichts freigegeben werden: `Access-Control-Expose-Headers:
  Content-Disposition, X-Redactions, X-Redaction-Areas, X-Redaction-Hidden,
  X-Redaction-Deselected, X-Redaction-Pages, X-Redaction-Sanitized,
  X-Redaction-Verified`. Ohne diese Freigabe zeigt die Oberfläche einen
  Bericht mit Nullen, ohne den Hinweis „nachgeprüft“, und den Ersatznamen
  `geschwärzt.pdf`.
- **Ressourcen:** Plan, Vorschau und Schwärzung laufen synchron und
  CPU-lastig. Eine Ratenbegrenzung und, wo nötig, ein Prozess-Pool sind
  Sache der Anwendung.
- **Protokollierung:** Anfragekörper (PDF, Kriterien, Auswahl) gehören nicht
  ins Zugriffsprotokoll.

## Grenzen (`Limits`)

| Feld | Vorgabe | Wirkung |
|---|---|---|
| `max_upload_bytes` | 50 MiB | größere Datei → 413 `too_large` (auch nach `Content-Length`) |
| `max_pages` | 500 | mehr Seiten → 413 `too_many_pages` |
| `max_selection_bytes` | 8 MiB | Feld `selection` größer → 413 `too_large` |
| `max_criteria_bytes` | 256 KiB | Feld `criteria` größer → 413 `too_large` |
| `preview_dpi` | 110 | Auflösung der Seitenvorschau |
| `preview_max_edge` | 1800 | längste Kante der Vorschau in Pixeln |

Fest in der Bibliothek: höchstens 200 Begriffe zu je 200 Zeichen, 500 Bereiche
insgesamt und 100 je Seite. Der Katalog meldet alle Grenzen.

## Endpunkte

Alle Pfade gelten relativ zum Einhängepunkt. Die POST-Anfragen sind
`multipart/form-data` mit dem Feld `file` (PDF) und den unten genannten
Textfeldern.

| Methode | Pfad | Felder | Antwort |
|---|---|---|---|
| GET | `/catalogue` | – | JSON: `contract`, `library`, `ner_available`, `patterns[]` (`id`, `label`, `hint`, `ai`, `available`), `limits` |
| POST | `/plan` | `criteria` (JSON) | JSON: Plan (ändert nichts an der Datei) |
| POST | `/preview` | `page` (1-basiert) | `image/png` einer Seite |
| POST | `/apply` | `selection` (JSON) | `application/pdf` (Anhang `<name>_geschwärzt.pdf`), Bericht in Kopfzeilen |

### `criteria`

```json
{"patterns": ["email", "iban", "ki_namen"], "terms": ["Prüfvermerk"],
 "case_sensitive": false, "whole_word": true}
```

Muster-Kennungen: `iban`, `email`, `telefon`, `steuer_id`, `ust_id`,
`kreditkarte`, `geburtsdatum`, `ip_adresse`, `aktenzeichen`, `ki_namen`.
Mindestens ein Muster oder Begriff ist nötig. Die Typen werden streng geprüft:
Listen von Texten, Wahrheitswerte. JSON mit `NaN` oder `Infinity` wird
abgelehnt.

### Plan (`POST /plan`)

```json
{"contract": "pdf_redaction/1", "version": 1, "sha256": "…", "criteria": {…},
 "page_count": 3,
 "pages": [{"page": 1, "width": 595.0, "height": 842.0, "rotation": 0, "has_text": true}],
 "pages_without_text": [3], "total": 9, "by_source": {"email": 3, …},
 "candidates": [{"id": "d2ca468f171ccd46", "kind": "text", "source": "begriff:Prüfvermerk",
   "label": "Begriff „Prüfvermerk“", "text": "Prüfvermerk", "page": 1,
   "rects": [[0.379, 0.093, 0.480, 0.111]], "pdf_rect": [225.4, 78.2, 285.3, 93.3],
   "location": "Seitentext", "outside_view": false, "selected": true}],
 "cleanup": […]}
```

`rects` sind Anteile 0…1 der gedrehten Seitenansicht und passen damit direkt
auf die Vorschau. `kind` ist `text` (sichtbar auf der Seite) oder `hidden`
(Metadaten, Lesezeichen, Formularfelder, Anhänge und Ähnliches).
`outside_view` kennzeichnet Text außerhalb der sichtbaren Seite, der trotzdem
geschwärzt wird.

### `selection` (`POST /apply`)

```json
{"sha256": "…", "criteria": {…}, "selected": ["d2ca468f171ccd46", …],
 "areas": [{"page": 1, "rect": [0.1, 0.1, 0.4, 0.25]}], "sanitize": true}
```

`sha256` und `criteria` stammen unverändert aus dem Plan. `selected` nennt die
bestätigten Kennungen, abgewählte Fundstellen bleiben stehen. `areas` sind
eigene Bereiche in Anteilen der Seitenansicht. `sanitize` entfernt Metadaten,
XMP, Anhänge, JavaScript und Anwendungsdaten.

### Bericht (Kopfzeilen von `POST /apply`)

| Kopfzeile | Inhalt |
|---|---|
| `Content-Disposition` | `attachment` mit ASCII-Ersatz und `filename*` (RFC 5987) |
| `Cache-Control` | `no-store` |
| `X-Redactions` | geschwärzte Fundstellen |
| `X-Redaction-Areas` | eigene Bereiche |
| `X-Redaction-Hidden` | entfernte versteckte Fundstellen |
| `X-Redaction-Deselected` | bewusst abgewählte Fundstellen |
| `X-Redaction-Pages` | Seiten mit Schwärzung |
| `X-Redaction-Sanitized` | `true` / `false` |
| `X-Redaction-Verified` | immer `true` (sonst keine Datei, sondern 422) |

Der Bericht enthält keinen Klartext.

## Fehler

Jeder Fehler wird als JSON `{"error": {"code": "…", "message": "…"}}` mit
deutscher Meldung zurückgegeben.

| Status | `code` | Anlass |
|---|---|---|
| 400 | `missing_file`, `missing_field`, `bad_request`, `invalid_json` | Formular unvollständig oder fehlerhaft |
| 409 | `stale_plan` | Datei oder Kennungen passen nicht mehr zum Plan |
| 413 | `too_large`, `too_many_pages` | Grenzen überschritten |
| 422 | `invalid_pdf`, `invalid_criteria`, `empty_criteria`, `invalid_page`, `invalid_selection` | Inhalt nicht verwendbar |
| 422 | `verification_failed` | Nachprüfung fand eine ausgewählte Fundstelle noch lesbar; es wird keine Datei ausgeliefert |
| 502 | `ner_failed` | Namenserkennung ist ausgefallen |
| 503 | `ner_unavailable` | `ki_namen` angefordert, aber nicht eingerichtet |

## Nicht enthalten

- **Stapelverarbeitung:** eine Datei je Anfrage. Stapel baut die Anwendung
  aus `auditcore_pdf.redaction` (`redact_all`) oder aus mehreren Anfragen.
- **Ablage:** Weder Pläne noch Ergebnisse werden gespeichert.
