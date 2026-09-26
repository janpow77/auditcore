# auditcore_documents

## Zweck

Dokumentvergleich (Checklisten und Fließtext aus DOCX/PDF), Gesetzessynopse für Artikelgesetze und ein frameworkunabhängiger Kern der Dokumentpipeline mit OCR-Ports.

Für audit_designer, ecohesion, regulierung und flowinvoice. Ohne Web-,
Datenbank-, Celery- oder KI-Abhängigkeit im Kern; Lesen, Rendern, OCR und
REST kommen über Extras oder Ports. Ein Vergleich ist eine Arbeitshilfe: Er
stellt Unterschiede fest und bereitet sie auf, er trifft keine
Prüfungsentscheidung.

## Installation

Aus dem Paketindex von auditcore (PEP 503, jede Datei mit SHA-256 verlinkt):

```bash
python -m pip install 'auditcore_documents[docx,pdf-text,fuzzy,docx-render]' \
  --index-url https://janpow77.github.io/auditcore/simple/
```

Hashgebunden in einer `requirements.txt` (zuletzt veröffentlicht: 0.3.3 im
Release v0.4.1; weitere Versionen und Hashes unter
`https://janpow77.github.io/auditcore/simple/auditcore-documents/`):

```text
auditcore_documents @ https://github.com/janpow77/auditcore/releases/download/v0.4.1/auditcore_documents-0.3.3-py3-none-any.whl#sha256=7ad288d593c9ea5f6578d38c9ed94660186c23729ea31bf52e8817ec153305f4
```

Debian/Ubuntu über die signierte APT-Quelle eines Releases
([Einrichtung](../../docs/deployment/package-feed.md)):

```bash
sudo apt-get install python3-auditcore-documents
```

Das Debian-Paket enthält den Kern; Extras über pip, `pdftotext` über
`poppler-utils` (optional, sonst pypdf). `python3-lxml` 4.9.2 (bookworm) ist
technisch lauffähig (gehärteter Parser), erfüllt aber nicht die
Extra-Untergrenze. `python3-starlette`/`python3-fastapi` stehen als
*Suggests*; die Mindestversionen erfüllt erst ein neueres Debian als trixie,
sonst pip.

Extras (`[dev]` – Test- und Prüfwerkzeuge):

| Extra | Pakete | Zweck |
|---|---|---|
| – | Standardbibliothek und `auditcore_common` | Modell, Normalisierung, Zuordnung, Befehle, Einstellungen, Begründungsport, Synopse-Datensätze |
| `[docx]` | lxml ≥ 6.1.0 | DOCX/DOCM lesen (gehärteter Parser; 6.1.0 behebt CVE-2026-41066) |
| `[pdf-text]` | pypdf ≥ 4 | PDF-Text ohne pdftotext |
| `[fuzzy]` | rapidfuzz ≥ 3.10 | Ähnlichkeitsmaß der Produktion (`token_set_ratio`) |
| `[docx-render]` | python-docx ≥ 1.1 | Synopse als DOCX (Vermerk/Text wie im Designer) |
| `[pdf-render]` | reportlab ≥ 4.0.8 | Synopse als PDF (wie ECOHESION `comparison.pdf`) |
| `[mime]` | python-magic ≥ 0.4.27 | MIME-Erkennung der Pipeline wie im Original (libmagic) |
| `[ocr-raster]` | pypdfium2, Pillow | Seitenrasterung vor Gateway-OCR |
| `[web]` | Starlette ≥ 0.47.2, python-multipart ≥ 0.0.20 | REST-Anbindung der Synopse-Oberfläche als ASGI-Anwendung (`auditcore_documents.web.create_app`) |
| `[fastapi]` | FastAPI ≥ 0.116.1 (+ `web`) | dieselben Endpunkte als `APIRouter` (`create_router`) |
| `[donut]` | transformers, torch ≥ 2.7, sentencepiece, Pillow | `LocalDonut`: Offline-Inferenz eines eigenen Donut-Modells (nur lokales Verzeichnis, SHA-256-Prüfung); CPU/CUDA-Build über den Paketindex der Anwendung |

## Schnellstart

Der Kern vergleicht bereits gelesene Einheiten und wendet Änderungsbefehle an
– ohne Extras (das Profil `LEGACY_DIFFLIB` nutzt `difflib`, das empfohlene
Profil verlangt `[fuzzy]`):

```python
import auditcore_documents as ad

alt = [
    ad.CompareItem("a1", text="Der Antrag ist schriftlich zu stellen.", order=0),
    ad.CompareItem("a2", text="Die Frist beträgt vier Wochen.", order=1),
    ad.CompareItem("a3", text="Zuständig ist die Bewilligungsbehörde.", order=2),
]
neu = [
    ad.CompareItem("n1", text="Der Antrag ist elektronisch zu stellen.", order=0),
    ad.CompareItem("n2", text="Zuständig ist die Bewilligungsbehörde.", order=1),
    ad.CompareItem("n3", text="Die Frist beträgt sechs Wochen.", order=2),
]
zeilen, zaehler = ad.compare_items(alt, neu, mode="text", profile=ad.LEGACY_DIFFLIB)
assert [z.status for z in zeilen] == ["changed", "removed", "added", "unchanged"]
assert zaehler["changed_count"] == 1

# Gesetzessynopse: Befehle auf Absatzebene, nicht anwendbare bleiben offen
absaetze = ad.base_paragraphs([
    ad.CompareItem("p1", section="§ 3", text="Die Frist beträgt vier Wochen."),
    ad.CompareItem("p2", section="§ 3", text="Die Anzeige ist schriftlich."),
])
fassung, offen, erkannt = ad.apply_commands(absaetze, [
    "In § 3 Absatz 1 werden die Wörter „vier Wochen“ durch die Wörter „einen Monat“ ersetzt.",
    "§ 3 Absatz 2 wird aufgehoben.",
    "In § 3 Absatz 1 wird Satz 2 gestrichen.",
])
assert fassung[0].new_text == "Die Frist beträgt einen Monat."
assert fassung[1].repealed and erkannt == 2
assert offen == ["In § 3 Absatz 1 wird Satz 2 gestrichen. [Befehlsart nicht unterstützt]"]
assert ad.RECOMMENDED is ad.CORRECTED
```

Dateien vergleichen und ausgeben (Extras `docx`, `fuzzy`, `docx-render`,
`pdf-render`; nicht im automatischen Lauf):

```python no-run
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

Kommandozeile: `auditcore-documents read DATEI`, `auditcore-documents compare
ALT NEU -o synopse.docx --pdf synopse.pdf --json ergebnis.json [--comparison-type article_law]
[--profile auditcore.document_compare]`, `auditcore-documents create-config PFAD`.

## API-Überblick

<!-- api-overview:start (generiert: python scripts/docs/api_overview.py --write) -->
Öffentliche Namen aus `auditcore_documents.__all__` (56):

| Name | Art | Kurzbeschreibung (erste Docstring-Zeile) | Modul |
|---|---|---|---|
| `ALLOWED_EXTENSIONS` | Konstante | – | `reading` |
| `COMMAND_PATTERNS` | Konstante | – | `article_law` |
| `CORRECTED` | Konstante | Korrigiertes, empfohlenes Verhalten (Nutzerentscheidung D1/D2 vom 23.09.2026): Änderungsbefehle, die mit „§“ beginnen, werden gelesen (DC-C04), nach einer Einfügung wird umnummerie … | `profiles` |
| `DEFAULT_LIMITS` | Konstante | – | `limits` |
| `DEFAULT_SETTINGS` | Konstante | – | `settings` |
| `LEGACY` | Konstante | Originalverhalten in der Produktionsumgebung (rapidfuzz installiert). | `profiles` |
| `LEGACY_DIFFLIB` | Konstante | Originalverhalten ohne rapidfuzz (Rückfall auf difflib im Original). | `profiles` |
| `PROFILES` | Konstante | – | `profiles` |
| `RECOMMENDED` | Konstante | Empfohlenes Profil für neue Anwendungen (D1). | `profiles` |
| `CompareError` | Ausnahme | Ein vom Nutzer behebbarer Vergleichsfehler. | `errors` |
| `CompareItem` | Datenklasse | Eine Vergleichseinheit aus einem Quelldokument. | `model` |
| `CompareOptions` | Datenklasse | Fachliche Optionen eines Laufs (Vorgaben wie im Original). | `compare` |
| `CompareProfile` | Datenklasse | Fachliche Schalter eines Vergleichs. | `profiles` |
| `CompareRow` | Datenklasse | Eine Zeile der Vorschau und der abschließenden Synopse. | `model` |
| `ComparisonResult` | Datenklasse | Vollständiges, JSON-serialisierbares Vergleichsergebnis. | `model` |
| `DependencyError` | Ausnahme | Ein optionales Extra (lxml, pypdf, rapidfuzz, python-docx) fehlt. | `errors` |
| `LawParagraph` | Datenklasse | – | `article_law` |
| `LimitExceededError` | Ausnahme | Eine konfigurierte Ressourcengrenze wurde überschritten. | `errors` |
| `ParseError` | Ausnahme | Beschädigte, geschützte, nicht unterstützte oder unlesbare Eingabe. | `errors` |
| `ReadContext` | Datenklasse | Umgebungsabhängige Lesebausteine; alle optional und austauschbar. | `compare` |
| `ReadLimits` | Datenklasse | – | `limits` |
| `ReasonProvider` | Protokoll | Liefert die Rohantwort (JSON-Text oder Mapping) für einen Begründungsvorschlag. | `reasons` |
| `__version__` | Wert | – | `(Paketstamm)` |
| `apply_commands` | Funktion | Befehle der Reihe nach anwenden; nicht anwendbare bleiben offen. | `article_law` |
| `apply_reasons_cli` | Funktion | Begründungen wie ``compare_documents`` (CLI/Jupyter) des Originals. | `reasons` |
| `apply_reasons_worker` | Funktion | Begründungen wie die Celery-Aufgabe des Originals (Vorschau-Workflow). | `reasons` |
| `base_paragraphs` | Funktion | Absätze des Stammgesetzes aus Fließtext-Einheiten unter „§ …“-Überschriften. | `article_law` |
| `compare_article_law_files` | Funktion | Stammgesetz und Änderungsbefehle zur Synopse zusammenführen. | `compare` |
| `compare_files` | Funktion | Zwei Fassungen vergleichen (Vertrag von ``DocumentCompareService.compare``). | `compare` |
| `compare_items` | Funktion | Reiner Kern ohne Dateizugriff: Zuordnung, Umstellungen, Zeilen, Zählwerte. | `compare` |
| `detect_mode` | Funktion | PDF ist immer Fließtext; DOCX nach Tabellenzeilen- und Absatzzahl. | `reading` |
| `difflib_ratio` | Funktion | Rückfall des Originals: ``round(100 * SequenceMatcher.ratio())``. | `scoring` |
| `generate_reason` | Funktion | Vorschlag erzeugen und Fundstellen prüfen (Vertrag des Originals). | `reasons` |
| `get_profile` | Funktion | – | `profiles` |
| `get_scorer` | Funktion | – | `scoring` |
| `legacy_pdf_pages` | Funktion | Originalreihenfolge: zuerst ``pdftotext``, bei Fehlen/Fehler ``pypdf``. | `pdftext` |
| `load_settings` | Funktion | Vorgaben, überlagert von der bereinigten Datei; fehlende Datei → Vorgaben. | `settings` |
| `mcp_tool_provider` | Funktion | Adapter für eine MCP-Werkzeugfunktion mit dem Aufrufvertrag des Originals. | `reasons` |
| `merge_settings` | Funktion | Wirksame Einstellungen und Herkunft je Pfad (department/personal/run). | `settings` |
| `normalise_for_match` | Funktion | Für die Zuordnung normalisieren; führende Nummerierung wird ignoriert. | `normalize` |
| `normalise_semantic` | Funktion | Reine Zeichensetzungs- und Nummerierungsänderungen herausrechnen. | `normalize` |
| `normalise_verbatim` | Funktion | Nur Leerraum und Groß-/Kleinschreibung vereinheitlichen. | `normalize` |
| `paragraphs_from_pdf_pages` | Funktion | Absätze aus Seiten; Satzende oder Leerzeile beendet einen Absatz. | `pdftext` |
| `pdftotext_pages` | Funktion | ``pdftotext -layout`` (poppler-utils) als externer Prozess. | `pdftext` |
| `pypdf_pages` | Funktion | Textextraktion mit ``pypdf`` (Extra ``pdf-text``); Fehlertexte wie im Original. | `pdftext` |
| `rapidfuzz_token_set` | Funktion | Produktionsmaß des Originals: ``round(float(fuzz.token_set_ratio(a, b)))``. | `scoring` |
| `read_document` | Funktion | Dokument lesen; liefert erkannte Dokumentart und Vergleichseinheiten. | `reading` |
| `read_text_paragraphs` | Funktion | Alle sichtbaren Absätze mit Überschriftenkennzeichen (Fließtextsicht). | `reading` |
| `remove_repeating_margins` | Funktion | Seitenzahlen und wiederkehrende Kopf-/Fußzeilen entfernen. | `pdftext` |
| `sanitise_settings` | Funktion | Nur bekannte Schlüssel, Werte begrenzt; ungültige Auswahlwerte → Vorgabe. | `settings` |
| `save_settings` | Funktion | Atomar über eine temporäre Datei schreiben (wie im Original). | `settings` |
| `synopsis_extra` | Funktion | Kopfangaben und Hinweise wie im ecohesion-Worker. | `synopsis` |
| `synopsis_records` | Funktion | (Spalten, Zeilen) aller nicht unveränderten Zeilen in Ergebnisreihenfolge. | `synopsis` |
| `text_items_from_paragraphs` | Funktion | Fließtext-Einheiten; Überschriften gliedern und werden nicht verglichen. | `pdftext` |
| `verify_legal_references` | Funktion | Genannte Fundstellen, die in keiner Fassung stehen (sortiert). | `reasons` |
| `word_diff` | Funktion | ``difflib.ndiff`` über Wörter; leer, wenn beide Texte gleich sind. | `normalize` |

Öffentliche Module:

| Modul | Kurzbeschreibung |
|---|---|
| `auditcore_documents.article_law` | Gesetzessynopse: gängige Änderungsbefehle eines Artikelgesetzes anwenden. |
| `auditcore_documents.cli` | Kommandozeile ``auditcore-documents`` (lesen, vergleichen, Einstellungen anlegen). |
| `auditcore_documents.compare` | Vergleich zweier Fassungen: Standardvergleich und Gesetzessynopse. |
| `auditcore_documents.docx_parts` | Bausteine der DOCX-Synopse: Zellformat, Wortmarkierung, Fassungszellen (python-docx). |
| `auditcore_documents.errors` | Fehlervertrag der Bibliothek. |
| `auditcore_documents.legacy` | Kompatibilitätsfassade für die Umstellung von audit_designer. |
| `auditcore_documents.limits` | Ressourcengrenzen beim Einlesen (im Original nicht vorhanden, DC-C03). |
| `auditcore_documents.matching` | Deterministische Zuordnung und Einstufung der Unterschiede. |
| `auditcore_documents.model` | Web-unabhängige Datenverträge des Dokumentvergleichs (unverändert aus dem Original). |
| `auditcore_documents.normalize` | Normalisierung und Wortdifferenz (unverändert aus ``parsing.py`` des Originals). |
| `auditcore_documents.ooxml` | Lesen von DOCX/DOCM (WordprocessingML) – Extra ``docx`` (lxml). |
| `auditcore_documents.pdftext` | PDF-Text: austauschbare Seitenquelle und reine Absatzbildung. |
| `auditcore_documents.pipeline` | Frameworkunabhängige Dokumentpipeline (aus flowinvoice ``backend/app/pipeline``). |
| `auditcore_documents.profiles` | Versionierte, quellengebundene Vergleichsprofile. |
| `auditcore_documents.reading` | Einheitlicher Einstieg zum Lesen von DOCX/DOCM/PDF in Vergleichseinheiten. |
| `auditcore_documents.reasons` | Optionale maschinelle Begründungsvorschläge über einen injizierbaren Port. |
| `auditcore_documents.render_docx` | DOCX-Synopse (Extra ``docx-render``: python-docx). |
| `auditcore_documents.render_pdf` | PDF-Ausgabe der Synopse (Extra ``pdf-render``: reportlab). |
| `auditcore_documents.scoring` | Ähnlichkeitsmaße für die Zuordnung. |
| `auditcore_documents.settings` | Einstellungsvertrag für Web, CLI und Jupyter (aus ``configuration.py``). |
| `auditcore_documents.synopsis` | Tabellarische Synopse als reine Datensätze (aus dem ecohesion-Worker). |
| `auditcore_documents.web` | REST-Anbindung der Synopse-Oberfläche (``<flowaudit-synopsis>``) und der Belegerkennung. |
<!-- api-overview:end -->

## Profile und Konfiguration

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

### Dokumentpipeline (`auditcore_documents.pipeline`)

Frameworkunabhängiger Kern der flowinvoice-Pipeline (fb2d185): Stufenvertrag,
Orchestrierung mit Wiederherstellung, Kontext und Modelle, SHA-256-Hashing mit
Stufen-Hashes, Audit-Ereignisse (Port `AuditSink`, Referenz `InMemoryAuditLog`),
Aufbewahrungsregeln (`RetentionSweeper`) und versionierte Profile
(`LEGACY_PIPELINE`, `CORRECTED_PIPELINE`). OCR-Engines (Gateway, Chandra,
Tesseract), Rasterung, Persistenz, Betrugsprüfung und Webhooks sind Ports;
kein torch/transformers/GPU im Kern.

```python no-run
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

### Donut-Belegerkennung (seit 0.2.0, experimentell)

Plan: `docs/architecture/DONUT_OCR_PLAN.md` (Entscheidungen E1–E9 vom
24.09.2026). Nur über das ausdrücklich gewählte Profil `DONUT_PIPELINE`
(`auditcore.pipeline.donut` 2026.09.24, Status `EXPERIMENTAL`) erreichbar;
`LEGACY_PIPELINE` und `CORRECTED_PIPELINE` sind unverändert (Fingerabdrücke
geprüft).

```python no-run
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

### REST-Anbindung der Synopse-Oberfläche (seit 0.3.0)

`auditcore_documents.web` verbindet die Oberfläche `<flowaudit-synopsis>` aus
`@auditcore/ui` mit dem Vergleichskern. Dienst, Ablage-Port und Ausgaben
(JSON, Markdown, DOCX, PDF) brauchen nur die Standardbibliothek; Starlette
bzw. FastAPI kommen über die Extras `web` und `fastapi`. Die bestehenden
Module sind unverändert.

```python no-run
from auditcore_documents.web import SynopsisService, create_app

app.mount("/api/synopsis", create_app(SynopsisService(), identify=aktueller_benutzer))
```

Endpunkte, JSON-Formen, Grenzen und Statuscodes: `docs/ui/synopsis-rest.md`
im Repository; Abgleich mit audit_designer, ecohesion und regulierung:
`docs/ui/synopsis-paritaet.md`. Die Bibliothek authentifiziert nicht:
`identify` liefert den Eigentümer je Anfrage, fremde Vergleiche ergeben 404.
Debian: `python3-starlette`/`python3-fastapi` stehen als *Suggests*; die
Mindestversionen erfüllt erst ein neueres Debian als trixie, sonst pip.

### REST-Anbindung der Belegerkennung (Vertrag `documents_extraction/1`)

`ExtractionService` führt ein hochgeladenes Dokument mit einem gewählten
Pipeline-Profil aus und liefert Felder (bei Donut mit Feldkonfidenz und
Übernahmeentscheidung), OCR-Qualität und Validierungsbefunde für
`<flowaudit-extraction>`. OCR und Donut kommen nur über die Ports der
Anwendung (`ExtractionEngines`); ohne Engine ist die Belegerkennung
abgeschaltet (404 `extraction_disabled`). Das Dokument wird nur für den Lauf
zwischengespeichert.

```python no-run
from auditcore_documents.web import ExtractionEngines, ExtractionService, create_extraction_app

service = ExtractionService(ExtractionEngines(tesseract=meine_tesseract_engine))
app.mount("/api/extraction", create_extraction_app(service))
```

Vertrag: `docs/ui/extraction-rest.md` im Repository.

## Herkunft und Charakterisierung

Dokumentvergleich aus `janpow77/audit_designer@030a71e0`
(`backend/app/modules/document_compare`, dazu ecohesion-Worker und
Research-PDF), Pipeline aus `janpow77/flowinvoice@fb2d185`
(`backend/app/pipeline`). Die unveränderten, Blob-geprüften Originalmodule
wurden ausgeführt und aufgezeichnet (`tools/capture_legacy.py`,
`tests/fixtures/legacy_observed.json`; Pipeline `tools/capture_pipeline.py`
mit 30 Szenarien); die 9 Originaltests des Vergleichs und 164 der Pipeline
bestehen. `LEGACY`, `LEGACY_DIFFLIB` und `LEGACY_PIPELINE` reproduzieren das
Original **legacy-exakt** (DOCX-Synopse bytegleich); `CORRECTED` und
`CORRECTED_PIPELINE` setzen die Entscheidungen D1–D8 vom 23.09.2026 um.
Der Donut-Pfad ist eine Neuimplementierung ohne übernommenen Code.
Consumer-Anbindung: [docs/consumer-integration.md](docs/consumer-integration.md).

## Bewusste Verhaltensabweichungen

Vollständig in [docs/behavior-changes.md](docs/behavior-changes.md), für die
Pipeline (PL-C01…PL-C08, D4–D8) in [docs/pipeline.md](docs/pipeline.md).
Wichtigste Korrekturen: kein stiller Wechsel des Ähnlichkeitsmaßes (DC-C01),
gehärteter XML-Parser ohne DTD/Entitäten (DC-C02), Größen- und Seitengrenzen
(DC-C03), mit „§“ beginnende Änderungsbefehle werden gelesen (DC-C04, nur
`CORRECTED`), pdftotext ohne Gebietsschema- und Optionsrisiko (DC-C05),
Konfigurationspfad ist Pflicht (DC-C07), KI-Begründung über einen Port
(DC-C08). Beibehaltene fragwürdige Originalregeln sind als DC-L01…DC-L09
dokumentiert.

## Abhängigkeiten

Python ≥ 3.11, `auditcore_common==0.2.0` (Hashing, Uhr, Kennungen,
eingefrorene Audit-Details; APT `python3-auditcore-common`) und
`auditcore_identifiers==0.2.0` (Prüfziffern der USt-IdNr. für DE und AT; APT
`python3-auditcore-identifiers`); beide nur Standardbibliothek. Die
Extras und ihre Drittpakete stehen in der Tabelle unter „Installation“. Keine
Abhängigkeit von der Plattform `auditcore`; für XLSX liefert
`synopsis_records` Datensätze für `auditcore_reporting`.

## Sicherheit und Datenschutz

Keine DTD/Entitäten, begrenzte Größen (`ReadLimits`), pdftotext ohne Shell
mit Zeitlimit; Eingabedateien werden nie verändert, geschrieben werden nur
ausdrücklich benannte Ausgaben, die Bibliothek protokolliert nicht. Die
Pipeline hasht Dokumente und Stufen (SHA-256) und kennt Aufbewahrungsregeln;
Persistenz und Löschung liegen in den Ports der Anwendung. `LocalDonut` lädt
nur ein lokales Modellverzeichnis nach SHA-256-Prüfung. Die REST-Anbindung
authentifiziert nicht: `identify` liefert den Eigentümer je Anfrage, fremde
Vergleiche ergeben 404. Testdaten: amtliche Gesetzestexte (§ 5 Abs. 1 UrhG)
und synthetische Rechnungen.

## Lizenz und Herkunftsnachweis

MIT (`LICENSE`). Die Quellrepositories sind privat und ohne Lizenzdatei; der
Rechteinhaber hat am 22.09.2026 den extrahierten Bibliothekscode freigegeben
(`USER_AUTHORIZED_MIT`), die Quellen selbst werden nicht umlizenziert.
Quelldateien mit Git-Blobs: `NOTICE` und `provenance.json`.

## Änderungen

Siehe [CHANGELOG.md](CHANGELOG.md).
