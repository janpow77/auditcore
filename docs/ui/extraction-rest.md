# REST-Vertrag Belegerkennung (`documents_extraction/1`, `auditcore_documents.web`)

Stand 2026-09-26. Vertrag zwischen `auditcore_documents.web` (Belegerkennung,
nach 0.3.3) und der Oberfläche `<flowaudit-extraction>` aus `@auditcore/ui`
(Vue `FaExtraction`, React `FlowauditExtraction`). Die Oberfläche erkennt
nichts selbst: Sie lädt ein Dokument hoch, zeigt Extraktionsergebnis,
Konfidenzen und Validierungsbefunde. Das Ergebnis ist eine Arbeitshilfe,
keine Prüfungsentscheidung.

## Bestandsaufnahme: was die Bibliothek kann

| Baustein | In `auditcore_documents.pipeline` | Im Vertrag |
|---|---|---|
| Einlesen | Datei, MIME per Signatur (PDF, PNG, JPEG, TIFF, WebP), Seitenzahl (pypdf), Größenprüfung | ja |
| OCR | nur Ports: OCR-Gateway (`RouterOcr` + `OcrRouting`), `ChandraPort`, `TesseractPort`; Rasterung `pdfium_rasterizer` (Extra `ocr-raster`); Qualitätsstufen OK ≥ 0,85, Prüfung ≥ 0,60 | ja, Engines übergibt die Anwendung |
| Donut | `DonutPort`: `HttpDonut`/`flowagent_donut` (Transport-Port, Adresse von der Anwendung), `LocalDonut` (Extra `donut`, nur lokales Verzeichnis nach SHA-256-Prüfung), `FakeDonut`; Profil `DONUT_PIPELINE` (erprobend) mit Feldkonfidenz, Abgleich mit Tesseract und Pflicht-Plausibilität | ja, nur mit angeschlossenem `donut` |
| Nachverarbeitung | Feldmuster (Rechnungsnummer, Datum, Beträge, IBAN, USt-IdNr.), gebietsschemabewusste Beträge (D5) | ja |
| Validierung | Regeln `VAL_IBAN_CHECKSUM`, `VAL_VAT_ID_FORMAT`, `VAL_TOTAL_PLAUSIBILITY`, `VAL_OCR_CONFIDENCE`, `VAL_AMOUNT_FORMAT`, `VAL_FRAUD_DETECTION` (ohne Port nur „zu wenig Daten“), `VAL_DONUT_*` | ja |
| Aufbewahrung | `RetentionSweeper` über den Port `RetentionStore` der Anwendung (Datenbank) | nur Anzeige der Fristen; der Dienst speichert nichts |
| Watchdog C-01…C-13 | Bestandsprüfung über viele Belege | nicht im Vertrag (Einzelbeleg-Oberfläche) |
| Persistenz, Export | Ports `RunRepository`, `ArtifactStore`, Webhook | nicht im Vertrag |

Ohne Engine rechnet der Dienst nichts: `enabled` ist `false`, `POST /runs`
antwortet 404 `extraction_disabled`. Die Bibliothek kennt keinen Host und
kein Modell; Adressen (vision-service, FlowAgent-Plattform, GPU-Knoten)
stehen ausschließlich in den Ports der Anwendung.

## Einbinden

Extras wie die Synopse: `auditcore_documents[web]` (Starlette,
python-multipart), `auditcore_documents[fastapi]`; für Donut-Inferenz im
Prozess zusätzlich `[donut]`, für die PDF-Rasterung `[ocr-raster]`.

```python
from starlette.routing import Mount
from auditcore_documents.pipeline import flowagent_donut
from auditcore_documents.web import (
    ExtractionEngines, ExtractionService, ExtractionSettings,
    create_extraction_app, create_extraction_router, extraction_routes,
)

engines = ExtractionEngines(
    tesseract=meine_tesseract_engine,                  # TesseractPort der Anwendung
    donut=flowagent_donut(mein_post, einstellungen.plattform_url),  # optional
)
service = ExtractionService(engines, ExtractionSettings(max_upload_bytes=20 * 1024 * 1024))
app.mount("/api/extraction", create_extraction_app(service))                 # Starlette
fastapi_app.include_router(create_extraction_router(service, prefix="/api/extraction"))
starlette_app.router.routes.append(Mount("/api/extraction", routes=extraction_routes(service)))
```

`ExtractionSettings`: `max_upload_bytes` (20 MiB), `profiles` (angebotene
Pipeline-Profile, Vorgabe alle drei), `default_profile` (empfohlen:
`auditcore.pipeline`), `retention` (`RetentionPolicyConfig`, nur zur Anzeige),
`thresholds` (`Thresholds(ok=0.85, review=0.60)`). Anmeldung, CORS und
Ratenbegrenzung sind Sache der Anwendung. Ein Lauf blockiert (OCR, Donut)
und läuft im Thread-Pool.

## Endpunkte

| Methode | Pfad | Zweck |
|---|---|---|
| GET | `/profile` | Vertrag, Profile, angeschlossene Engines, Dateitypen, Grenzen, Schwellen, Aufbewahrung |
| POST | `/runs` | Dokument verarbeiten (`multipart/form-data`: `file`, optional `profile`) |

### `GET /profile`

```json
{"contract": "documents_extraction/1", "library": "auditcore_documents 0.4.0",
 "enabled": true,
 "engines": {"router": false, "chandra": false, "tesseract": true, "donut": true},
 "profiles": [{"id": "flowinvoice.pipeline", "version": "1.0.0", "fingerprint": "…",
               "label": "Originalverhalten flowinvoice", "status": "SOURCE_CHARACTERIZED",
               "ocr_backend": null, "recommended": false, "min_field_confidence": null,
               "available": true, "retention_categories": ["processing_logs"]},
              {"id": "auditcore.pipeline", "…": "…", "recommended": true},
              {"id": "auditcore.pipeline.donut", "…": "…", "status": "EXPERIMENTAL",
               "ocr_backend": "donut", "min_field_confidence": 0.9}],
 "default_profile": "auditcore.pipeline",
 "accepted_types": ["application/pdf", "image/jpeg", "image/png", "image/tiff", "image/webp"],
 "limits": {"max_upload_bytes": 20971520},
 "thresholds": {"ok": 0.85, "review": 0.6},
 "retention": {"stored": false, "days": {"original_documents": 2555, "ocr_raw_output": 365,
   "structured_extraction": 2555, "processing_logs": 90, "audit_events": 3650}}}
```

`available` ist `false`, wenn die Engine des Profils fehlt (Donut-Profil ohne
`donut`, übrige ohne Gateway/Chandra/Tesseract); die Oberfläche zeigt solche
Profile gesperrt an.

### `POST /runs`

Felder: `file` (Pflicht, höchstens `max_upload_bytes`), `profile` (Kennung;
fehlt sie, gilt `default_profile`). Die Datei liegt nur während des Laufs in
einem temporären Verzeichnis. Antwort 200 – auch für einen fehlgeschlagenen
Lauf (`run.status = "failed"` mit `error_code`, z. B. `INVALID_MIME_TYPE`,
`OCR_GATEWAY_UNAVAILABLE` mit `retryable: true`):

| Feld | Inhalt |
|---|---|
| `contract`, `library`, `profile` | Vertrag, Bibliothek, Profil mit Version, Fingerabdruck und Status |
| `run` | `run_id`, `status` (`ok`, `review_needed`, `rejected`, `failed`), `needs_review`, `error_code`, `error`, `retryable`, `completed_stages`, `hash_chain` (SHA-256 je Stufe), `duration_ms` |
| `document` | `filename` (nur Name), `sha256`, `size_bytes`, `mime_type`, `page_count` |
| `ocr` | `engine`, `avg_confidence`, `min_confidence`, `max_confidence`, `pages_processed`, `pages_failed`, `duration_ms`, `retries`, `quality` (`ok`/`review`/`rejected` nach `thresholds`); `null` ohne OCR-Lauf |
| `pages[]` | `page`, `confidence` (nur wenn die Engine sie je Seite liefert), `text` |
| `fields[]` | `name`, `value` (normalisiert), `raw` (Rohtreffer), `confidence` (nur Donut: Feldkonfidenz), `decision` (nur Donut: `accepted`, `rejected`, `unconfirmed`, `disagreement`, `not_taken`), `proposal` (Donut-Wert), `text_match`, `checks` |
| `findings[]` | `rule_id`, `rule_name`, `severity` (`INFO`, `WARN`, `CRITICAL`), `outcome` (`PASS`, `FAIL`, `REVIEW`), `message` (Wortlaut des Regelwerks, englisch wie im Original), `evidence` |
| `flags` | Kennzeichen des Laufs (z. B. `LOW_OCR_CONFIDENCE`, `FAIL_VAL_DONUT_PLAUSIBILITY`) |
| `stored` | immer `false` |

Feldkonfidenzen gibt es nur im Donut-Profil; sonst gilt die Konfidenz der
Texterkennung (`ocr`). Donut-Werte sind Vorschläge: Übernommen wird ein Wert
erst nach Plausibilitätsprüfung bzw. Bestätigung im Tesseract-Text
(`decision = accepted`).

## Fehler

`{"error": {"code": "…", "message": "…"}}` mit deutscher Meldung:
400 `bad_request` (fehlerhaftes Multipart, Content-Length), 404
`extraction_disabled`, 413 `too_large`, 422 `missing_file`, `empty_file`,
`unknown_profile`, `profile_unavailable`.

## Oberfläche

`createExtractionRestPort({ baseUrl: '/api/extraction' })` aus
`@auditcore/ui-core` (auch über `@auditcore/ui` und `@auditcore/ui-react`).
Eigenschaften `port`, `result` (vorhandenes Ergebnis anzeigen), `locale`;
Ereignisse `extraction-completed` und `error` (React: `onExtractionCompleted`,
`onError`). Paritätsfälle: `packages-js/ui-core/test/parity/cases-extraction.ts`.
Demo: `packages-js/ui/demo/extraction_demo.py` (Attrappen-Ports, synthetische
Belege aus `auditcore_invoicesynth`).
