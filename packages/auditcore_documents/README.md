# auditcore_documents 0.2.0

Dokumentvergleich und Gesetzessynopse ohne Web-, Datenbank-, Celery- oder
KI-Abhängigkeit. Extrahiert und charakterisiert aus
`janpow77/audit_designer@030a71e0` (`backend/app/modules/document_compare`).
Ein Vergleich ist eine Arbeitshilfe: Er stellt Unterschiede fest und
bereitet sie auf, er trifft keine Prüfungsentscheidung.

```bash
python -m pip install 'auditcore_documents[docx,pdf-text,fuzzy,docx-render]==0.2.0'
# Debian: python3-auditcore-documents (Kern); Extras über pip, pdftotext über
# poppler-utils (optional, sonst pypdf). python3-lxml 4.9.2 (bookworm) ist
# technisch lauffähig (gehärteter Parser), erfüllt aber nicht die Extra-Untergrenze.
```

| Extra | Pakete | Zweck |
|---|---|---|
| – | nur Standardbibliothek | Modell, Normalisierung, Zuordnung, Befehle, Einstellungen, Begründungsport, Synopse-Datensätze |
| `docx` | lxml ≥ 6.1.0 | DOCX/DOCM lesen (gehärteter Parser; 6.1.0 behebt CVE-2026-41066) |
| `pdf-text` | pypdf ≥ 4 | PDF-Text ohne pdftotext |
| `fuzzy` | rapidfuzz ≥ 3.10 | Ähnlichkeitsmaß der Produktion (`token_set_ratio`) |
| `docx-render` | python-docx ≥ 1.1 | Synopse als DOCX (Vermerk/Text wie im Designer) |
| `pdf-render` | reportlab ≥ 4.0.8 | Synopse als PDF (wie ECOHESION `comparison.pdf`) |
| `mime` | python-magic ≥ 0.4.27 | MIME-Erkennung der Pipeline wie im Original (libmagic) |
| `ocr-raster` | pypdfium2, Pillow | Seitenrasterung vor Gateway-OCR |
| `donut` | transformers, torch ≥ 2.7, sentencepiece, Pillow | `LocalDonut`: Offline-Inferenz eines eigenen Donut-Modells (nur lokales Verzeichnis, SHA-256-Prüfung); CPU/CUDA-Build über den Paketindex der Anwendung |

## Nutzung

```python
from pathlib import Path
import auditcore_documents as ad

result = ad.compare_files(
    Path("alt.docx"),
    Path("neu.docx"),
    profile=ad.LEGACY,  # charakterisiertes Original
    options=ad.CompareOptions(mode="auto", threshold=85),
)
print(result.changed_count, result.removed_count, result.added_count, result.moved_count)

synopse = ad.compare_files(
    Path("KassenSichV.docx"),
    Path("BGBl-Art15.docx"),
    profile=ad.CORRECTED,  # liest auch „§ … wird aufgehoben“
    options=ad.CompareOptions(comparison_type="article_law"),
)
print(synopse.metadata["open_commands"])  # nicht anwendbare Befehle bleiben sichtbar

from auditcore_documents.render_docx import render_docx

render_docx(result, Path("Vergleich.docx"), user="Prüfer", profile="memo")

from auditcore_documents.render_pdf import render_synopsis_pdf, synopsis_report

Path("Vergleich.pdf").write_bytes(render_synopsis_pdf("Vergleich", synopsis_report(result)))

columns, rows = ad.synopsis_records(result)  # z. B. für auditcore_reporting.ReportTable
```

Kommandozeile: `auditcore-documents read DATEI`, `auditcore-documents compare
ALT NEU -o synopse.docx --pdf synopse.pdf --json ergebnis.json [--comparison-type article_law]
[--profile auditcore.document_compare]`, `auditcore-documents create-config PFAD`.

## Vertrag

- **Profile** (`PROFILES`, versioniert, mit Fingerprint):
  `audit_designer.document_compare` 1.1.0 (`LEGACY`, Produktionsverhalten),
  `…difflib` (`LEGACY_DIFFLIB`, Rückfall des Originals ohne rapidfuzz),
  `auditcore.document_compare` 2026.09.2 (`CORRECTED` = `RECOMMENDED`,
  entschieden am 2026-09-23: DC-C04 und Absatznummerierung nach Einfügung).
- **Standardvergleich**: Checklisten (Tabellenzeilen; stabile Kennung aus
  Inhaltssteuerelementen, dann wortgleich, dann Ähnlichkeit ≥ Schwelle) oder
  Fließtext (reihenfolgetreu, unscharfe Ersetzungsblöcke); wortgleich
  verschobene Stellen sind „moved“. Nachverfolgte Änderungen werden im Speicher
  angenommen; verborgener/kursiver Text gilt als Hinweis. PDF ist immer Fließtext.
- **Gesetzessynopse**: Ersetzen, Aufheben, Neufassen, Einfügen auf
  Absatzebene; offene Befehle mit Grund; konsolidierte Arbeitsfassung.
- **Ports**: `ReadContext(ocr_callback, page_source, limits, now)`,
  `ReasonProvider` für KI-Begründungen (`mcp_tool_provider` für den
  FlowAgent-Aufruf), `apply_reasons_worker`/`apply_reasons_cli`.
- **Fehler**: `CompareError` ⊃ `ParseError` ⊃ `LimitExceededError`;
  `DependencyError` für fehlende Extras. Texte wie im Original.
- **Sicherheit**: keine DTD/Entitäten, begrenzte Größen (`ReadLimits`),
  pdftotext ohne Shell mit Zeitlimit, Eingabedateien werden nie verändert.
  Die Bibliothek protokolliert nicht und schreibt nur ausdrücklich benannte
  Ausgaben.
- `auditcore_documents.legacy.DocumentCompareService` ist die
  Kompatibilitätsfassade für audit_designer (gleiche Namen, Signaturen,
  Fehlertexte).

**Ausgabeformate wie im Designer:** JSON (`to_dict`), DOCX-Synopse
(`render_docx`, Vermerk- oder Textprofil, byte-gleich zum Original geprüft) und
PDF-Synopse (`render_synopsis_pdf`, Seitentext, Titel und Autor gleich dem
Original). `auditcore_reporting` 0.2.0 kennt nur XLSX; beide Renderer bleiben
deshalb Extras hier. Für XLSX liefert `synopsis_records` passende Datensätze.

## Dokumentpipeline (`auditcore_documents.pipeline`)

Frameworkunabhängiger Kern der flowinvoice-Pipeline (fb2d185): Stufenvertrag,
Orchestrierung mit Wiederherstellung, Kontext und Modelle, SHA-256-Hashing mit
Stufen-Hashes, Audit-Ereignisse (Port `AuditSink`, Referenz `InMemoryAuditLog`),
Aufbewahrungsregeln (`RetentionSweeper`) und versionierte Profile
(`LEGACY_PIPELINE`, `CORRECTED_PIPELINE`). OCR-Engines (Gateway, Chandra,
Tesseract), Rasterung, Persistenz, Betrugsprüfung und Webhooks sind Ports;
kein torch/transformers/GPU im Kern.

```python
import asyncio
from auditcore_documents import pipeline as pl

audit = pl.InMemoryAuditLog()
ocr = pl.OcrStage(routing=pl.OcrRouting(mode="router"), router=mein_gateway)  # Port
orchestrator = pl.build_pipeline(profile=pl.LEGACY_PIPELINE, audit=audit, ocr=ocr)
context = asyncio.run(
    orchestrator.run(pl.PipelineContext(document_id="d", input_uri="/pfad/beleg.pdf"))
)
print(context.status, context.validation_flags, context.hash_chain)
```

Details, Korrekturen PL-C01…PL-C08 und Befunde: `docs/pipeline.md`.

Nachweise, Abweichungen und Entscheidungen: `docs/behavior-changes.md`,
`docs/consumer-integration.md`, `provenance.json`, `NOTICE`.

## Donut-Belegerkennung (0.2.0, experimentell)

Plan: `docs/architecture/DONUT_OCR_PLAN.md` (Entscheidungen E1–E9 vom
24.09.2026). Nur über das ausdrücklich gewählte Profil `DONUT_PIPELINE`
(`auditcore.pipeline.donut` 2026.09.24, Status `EXPERIMENTAL`) erreichbar;
`LEGACY_PIPELINE` und `CORRECTED_PIPELINE` sind unverändert (Fingerabdrücke
geprüft).

```python
from auditcore_documents import pipeline as pl

donut = pl.HttpDonut(post, "http://100.102.132.11:8015")          # vision-service
# oder pl.flowagent_donut(post, "https://agent.flowaudit.de")      # FlowAgent (E7)
# oder pl.LocalDonut(Path("/opt/models/donut-invoice-de-1.0.0"), expected_sha256)
ocr = pl.OcrStage(donut=donut, tesseract=my_tesseract_port)
orchestrator = pl.build_pipeline(profile=pl.DONUT_PIPELINE, ocr=ocr)
```

- `DonutPort` (`available`, `parse(page_png) → DonutResult`), `HttpDonut`
  (Transport als Port, ohne Port `DONUT_NOT_CONFIGURED`), `FakeDonut`,
  `LocalDonut` (Extra `donut`; `DONUT_MODEL_HASH_MISMATCH` vor dem Laden).
- `OcrBackend.DONUT`: PDF seitenweise über den `Rasterizer`, Bilder direkt;
  Tesseract läuft zum Zwei-Motoren-Abgleich mit (`ocr_text` = Tesseract-Text,
  sonst Donut-Darstellung); `ocr_raw_json.engine = "donut"` mit Modellkennung,
  SHA-256 und Seitenergebnissen.
- `DonutFieldMergeStage` nach `PostprocessStage`: Übernahme nur nach
  Pflicht-Plausibilität (netto + USt = brutto, Steuerzeile = Basis × Satz,
  IBAN mod 97, USt-IdNr.-/UID-Prüfziffer, zulässige Sätze DE 19/7/0 und
  AT 20/13/10/0, Rechnungsnummer, Datum, Fälligkeit) **und** Feldkonfidenz ≥
  0,90 oder Bestätigung im Tesseract-Text; Beträge ohne rechenbare Summe nur
  mit Textbestätigung. Sonst bleibt der Regex-Wert, und `VAL_DONUT_PLAUSIBILITY`
  bzw. `VAL_DONUT_DISAGREEMENT` setzen `REVIEW_NEEDED`. Bericht:
  `normalized_json["donut_merge"]`.
- Ohne Feldkonfidenzen (z. B. heutiger vision-service) gilt OCR-Konfidenz 0,80:
  ein Donut-Lauf endet dann nie automatisch mit `OK`.
- Das Modell ist nicht Teil des Pakets (Entscheidung E2: Release-Asset).
