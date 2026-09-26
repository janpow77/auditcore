# REST-Vertrag „Synopse / Versionsvergleich“

Stand: 25.09.2026 · Paket `auditcore_documents` ≥ 0.3.0 · Modul `auditcore_documents.web`
· Oberflächen `<flowaudit-synopsis>` (Anzeige) und `<flowaudit-comparisons>`
(Hochladen, Liste, Import, Löschen) aus `@flowaudit/ui`

Der Vertrag verbindet die wiederverwendbare Oberfläche mit dem Vergleichskern.
Die JSON-Formen sind die Ergebnisobjekte von `auditcore_documents`
(`ComparisonResult.to_dict()`); die Oberfläche kennt keine zweite Datenform.
Ein Vergleich ist eine Arbeitshilfe: Er stellt Unterschiede fest und trifft
keine Prüfungsentscheidung.

## Einbinden

```bash
python -m pip install 'auditcore_documents[docx,fuzzy,docx-render,pdf-render,web]==0.3.0'
# FastAPI-Anwendungen: Extra fastapi statt web
```

```python
from auditcore_documents.web import SynopsisService, ServiceSettings, create_app

service = SynopsisService(settings=ServiceSettings(max_upload_bytes=10 * 1024 * 1024))
app.mount("/api/synopsis", create_app(service, identify=lambda request: request.user.username))
```

```python
from auditcore_documents.web import create_router

app.include_router(
    create_router(service, identify=aktueller_benutzer, dependencies=[Depends(anmeldung)]),
    prefix="/api/synopsis",
)
```

| Baustein | Abhängigkeit | Aufgabe |
|---|---|---|
| `SynopsisService` | Standardbibliothek | Hochladen prüfen, vergleichen, speichern, Zeilen ändern, ausgeben |
| `ComparisonStore` / `InMemoryComparisonStore` | Standardbibliothek | Ablage als Port; die Referenz hält höchstens 100 Vergleiche im Arbeitsspeicher |
| `create_app` | Extra `web` (Starlette ≥ 0.47.2, python-multipart ≥ 0.0.20) | eigenständige ASGI-Anwendung |
| `create_router` | Extra `fastapi` (FastAPI ≥ 0.116.1) | dieselben Endpunkte als `APIRouter` |

**Anmeldung und Mandanten:** Die Bibliothek authentifiziert nicht. `identify(request)`
liefert den Eigentümer oder `None` (dann 401). Jeder Zugriff ist auf den Eigentümer
beschränkt; fremde Kennungen ergeben 404 wie in ecohesion. Die Vorgabe
`single_user` ordnet alle Anfragen einem Eigentümer zu und ist nur für
Einzelplatz-Werkzeuge und Demos gedacht. CSRF-Schutz, Rate-Limits und
Protokollierung bleiben bei der Anwendung.

## Endpunkte

Alle Pfade relativ zum Einhängepunkt. Fehler haben immer die Form
`{"detail": "<deutsche Meldung>"}` (wie FastAPI).

| Methode | Pfad | Anfrage | Antwort |
|---|---|---|---|
| GET | `/profiles` | – | 200 `{"items": [Profile]}` |
| GET | `/comparisons` | – | 200 `{"items": [ComparisonSummary]}`, neueste zuerst |
| POST | `/comparisons` | `multipart/form-data`: `old_file`, `new_file`, Felder siehe unten | 201 `Comparison` |
| POST | `/comparisons/import` | JSON `{"title"?: str, "result": ComparisonResult}` | 201 `Comparison` |
| GET | `/comparisons/{id}` | – | 200 `Comparison` |
| PATCH | `/comparisons/{id}/rows` | JSON `{"rows": [RowUpdate]}` | 200 `Comparison` |
| DELETE | `/comparisons/{id}` | – | 204 |
| GET | `/comparisons/{id}/export?format=json\|markdown\|docx\|pdf` | – | 200 Datei (`Content-Disposition: attachment`, `Cache-Control: no-store`) |

Der Vergleich läuft synchron in einem Worker-Thread. Große Dokumente oder
KI-Begründungen gehören in die Auftragssteuerung der Anwendung
(audit_designer: Celery, ecohesion: eigener Prozess); die Anwendung legt das
Ergebnis dann über `POST /comparisons/import` oder direkt im `ComparisonStore` ab.

### Formularfelder von `POST /comparisons`

| Feld | Werte | Vorgabe |
|---|---|---|
| `old_file`, `new_file` | DOCX, DOCM oder PDF, je höchstens `max_upload_bytes` (Vorgabe 20 MiB) | Pflicht |
| `title` | höchstens 255 Zeichen | „Vergleich von ALT mit NEU“ |
| `comparison_type` | `standard` · `article_law` (Artikelgesetz auf Stammgesetz anwenden) | `standard` |
| `mode` | `auto` · `checklist` · `text` | `auto` (PDF immer `text`) |
| `threshold` | 70–100 | 85 |
| `include_answers`, `include_notes`, `highlight_words` | `true`/`false` | `true` |
| `include_editorial` | `true`/`false` | `false` |
| `output_sections` | kommagetrennt aus `changed,removed,added,moved,unchanged` | `changed,removed,added,moved` |
| `profile` | Kennung aus `GET /profiles` | Standardprofil (`auditcore.document_compare`) |

Unbekannte Felder werden mit 422 abgewiesen. Dateinamen werden auf den letzten
Namensteil ohne Steuerzeichen gekürzt; hochgeladene Dateien liegen nur während
des Vergleichs in einem privaten Temporärverzeichnis und werden danach gelöscht.

## JSON-Formen

### `Comparison`

```json
{
  "id": "5f0c…",
  "title": "Vergleich von Richtlinie_2025.docx mit Richtlinie_2026.docx",
  "created_at": "2026-09-25T10:00:00+00:00",
  "result": { "…": "ComparisonResult" }
}
```

### `ComparisonResult` (= `ComparisonResult.to_dict()`)

| Feld | Typ | Bedeutung |
|---|---|---|
| `version` | str | Vergleichsmodul, z. B. `1.1.0+auditcore.2026.09.2` |
| `mode` | `checklist` \| `text` | erkannte Dokumentart |
| `old_filename`, `new_filename` | str | Dateinamen |
| `old_sha256`, `new_sha256` | str | Prüfsummen der Eingaben |
| `old_count`, `new_count`, `matched_count` | int | Einheiten und Zuordnungen |
| `changed_count`, `removed_count`, `added_count`, `moved_count` | int | Änderungen je Art |
| `rows` | `[CompareRow]` | Zeilen in Ergebnisreihenfolge |
| `created_at` | ISO-8601 | Zeitpunkt des Vergleichs |
| `metadata` | Objekt | siehe unten |

`CompareRow`: `row_id`, `status` (`changed`, `removed`, `added`, `moved`,
`unchanged`), `location` (Fundstelle), `old_text`, `new_text`, `old_answer`,
`new_answer`, `old_comment`, `new_comment`, `old_note`, `new_note`, `reason`,
`reason_source` (`""`, `flowagent`, `article_law`), `reason_verified`
(bool oder null), `reason_warning`, `selected` (bool, geht in die Ausgabe ein),
`diff` (`{"text"|"answer"|"comment"|"note": [str]}`, Wortdifferenz im Format
von `difflib.ndiff`: Präfix `"  "` gleich, `"- "` entfallen, `"+ "` neu,
`"? "` Hinweiszeile – die Oberfläche ignoriert sie).

`metadata` (Auswahl, alle optional):

| Schlüssel | Standardvergleich | Gesetzessynopse |
|---|---|---|
| `comparison_type` | `standard` | `article_law` |
| `detected_mode`, `threshold`, `include_*`, `highlight_words` | ja | `highlight_words` |
| `output_sections` | ja | ja |
| `pdf_notice` | Hinweis bei PDF-Eingaben | – |
| `profile` | `{"id","version","fingerprint"}` (nicht im Legacy-Profil) | ebenso |
| `old_label`, `new_label`, `reason_label` | – | „Geltende Fassung“, „Fassung nach dem Entwurf“, „Änderungsbefehl“ |
| `recognised_commands`, `open_commands`, `open_command_count` | – | erkannte und offene Änderungsbefehle mit Grund |
| `consolidated_text` | – | `[{"section","paragraph","text","repealed","inserted"}]` konsolidierte Arbeitsfassung |
| `work_aid_notice` | – | „Arbeitshilfe ohne amtlichen Charakter …“ |

In der Gesetzessynopse steht der Änderungsbefehl je Zeile in `reason`
(`reason_source = "article_law"`); `diff` ist dort leer, die Oberfläche
berechnet die Wortdifferenz dann selbst.

### `ComparisonSummary`

```json
{"id": "…", "title": "…", "created_at": "…", "old_filename": "…", "new_filename": "…",
 "comparison_type": "standard", "counts": {"changed": 3, "removed": 1, "added": 2, "moved": 0}}
```

### `Profile`

```json
{"id": "auditcore.document_compare", "version": "2026.09.2", "fingerprint": "…",
 "status": "DECIDED_RECOMMENDED", "default": true}
```

### `RowUpdate`

`{"row_id": str, "selected"?: bool, "reason"?: str (≤ 4000 Zeichen)}`. Unbekannte
Zeilen oder Felder ergeben 422; die Änderung ist atomar (alle oder keine).

## Oberfläche `<flowaudit-comparisons>`

`FaComparisons` (Vue) bzw. `<flowaudit-comparisons>` nutzt denselben
REST-Client (`createSynopsisRestClient`) für `GET /profiles`,
`GET /comparisons`, `POST /comparisons`, `POST /comparisons/import` und
`DELETE /comparisons/{id}`; ein geöffneter Vergleich erscheint als
eingebettete Synopse (`GET /comparisons/{id}`, `PATCH …/rows`, Ausgaben).
Die Oberfläche prüft Endung, Größe (`maxUploadBytes` wie
`ServiceSettings.max_upload_bytes`), Schwelle, Titel und Ausgabeabschnitte
vor dem Hochladen; der Server prüft erneut und seine Meldung (`detail`) wird
angezeigt. Für die Gesetzessynopse sendet sie nur `comparison_type`,
`highlight_words`, `output_sections`, `title` und `profile`. Importiert werden
die JSON-Ausgabe (`export?format=json`), ein gespeicherter Vergleich oder
`{"title"?, "result"}`. Logik und Texte liegen framework-frei in
`@flowaudit/ui-core` (`createComparisonsController`), damit die React-Fassung
dieselben Paritätsfälle (`ui-core/test/parity/cases-documents.ts`) erfüllt.

## Ausgaben

| `format` | Inhalt | Voraussetzung |
|---|---|---|
| `json` | vollständiges `ComparisonResult` | – |
| `markdown` | Kopf mit Dateien, Prüfsummen und Zählwerten; je ausgewählter Zeile Fundstelle, alte/neue Fassung, Antworten/Bemerkungen/Hinweise und Grund bzw. Änderungsbefehl; offene Befehle | – |
| `docx` | Synopse wie im audit_designer (`render_docx_bytes`, Profil „Vermerk“) | Extra `docx-render`, sonst 501 |
| `pdf` | Tabelle wie ecohesion `comparison.pdf` (`render_synopsis_pdf`), Kopfzeile „Synopse“ | Extra `pdf-render`, sonst 501 |

Alle Ausgaben berücksichtigen `selected` und `output_sections`. Die HTML- und
Druckansicht erzeugt die Oberfläche selbst aus demselben Ergebnisobjekt.

## Statuscodes

| Code | Anlass |
|---|---|
| 400 | kein gültiges JSON, ungültige `Content-Length`, fehlerhafte Multipart-Anfrage |
| 401 | `identify` liefert keinen Eigentümer |
| 404 | Vergleich unbekannt oder fremder Eigentümer |
| 413 | Datei oder Anfrage zu groß; `LimitExceededError` beim Lesen |
| 415 | Dateiendung nicht DOCX/DOCM/PDF |
| 422 | Feld-, Zeilen- oder Ergebnisprüfung, `CompareError`/`ParseError` (beschädigte, geschützte, leere Datei) |
| 501 | Ausgabe-Extra fehlt (`DependencyError`) |
