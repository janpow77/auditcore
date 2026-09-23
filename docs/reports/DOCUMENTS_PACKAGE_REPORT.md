# auditcore_documents 0.1.0 — Bericht

Stand: 23. September 2026. Branch `feat/auditcore-documents` (Worktree
`auditcore-wt-documents`, Basis `origin/main`, zuletzt mit `7c063d4`
zusammengeführt). Teil 1 (PR #18, gemergt als `d779a44`) betrifft
Dokumentvergleich, Gesetzessynopse und Synopse-Ausgabe aus audit_designer.
Teil 2 (Branch `feat/auditcore-documents-pipeline`) ergänzt den Kern der
flowinvoice-Dokumentpipeline, siehe Abschnitt „Teil 2“.

## Umfang Teil 1

Eigenständige Distribution `auditcore_documents` (Debian
`python3-auditcore-documents`), Laufzeit nur Standardbibliothek, keine
Abhängigkeit auf `auditcore`. Extras: `docx` (lxml ≥ 6.1.0), `pdf-text`
(pypdf), `fuzzy` (rapidfuzz), `docx-render` (python-docx), `pdf-render`
(reportlab). Konsolenbefehl `auditcore-documents`.

| Fähigkeit | Umsetzung |
|---|---|
| Lesen | DOCX/DOCM (gehärteter lxml-Parser, Nachverfolgung im Speicher angenommen, Inhaltssteuerelemente, Kontrollkästchen, verborgener/kursiver Hinweistext), PDF über injizierbare Seitenquelle (`pdftotext`, `pypdf`, Originalreihenfolge) und ausdrücklichen OCR-Rückruf |
| Standardvergleich | Checklisten- und Fließtextzuordnung, Umstellungserkennung, Wortdifferenz, redaktionelle Änderungen optional |
| Gesetzessynopse | Ersetzen/Aufheben/Neufassen/Einfügen auf Absatzebene, offene Befehle mit Grund, konsolidierte Arbeitsfassung |
| Profile | `audit_designer.document_compare` 1.1.0 (LEGACY), `…difflib`, `auditcore.document_compare` 2026.09.1 (CORRECTED), versioniert mit Fingerprint |
| Ports | `ReadContext` (Uhr, Seitenquelle, OCR, Grenzen), `ReasonProvider` für KI-Begründungen (FlowAgent-Adapter `mcp_tool_provider`) |
| Synopse/Bericht | Alle Formate, die der Designer erzeugt: JSON (`to_dict`/`from_dict`), DOCX-Vermerk/-Text (`render_docx`, Extra `docx-render`, Hauptteil/Kopf/Fuß byte-gleich zum Original) und PDF wie ECOHESION `comparison.pdf` (`render_synopsis_pdf`, Extra `pdf-render`, Seitentext/Titel/Autor gleich); Synopse-Datensätze für `auditcore_reporting` (XLSX) |
| Kompatibilität | `legacy.DocumentCompareService`, `legacy.compare_documents` mit Namen, Signaturen und Fehlertexten des Originals |

`auditcore_reporting` 0.2.0 kennt nur XLSX; DOCX- und PDF-Renderer bleiben deshalb
als Extras in diesem Paket (`RENDERER_OWNERS` unverändert; Extra-Name `pdf-render`
kollidiert nicht mit dem veröffentlichten `pdf` von auditcore_invoicegenerator).
Das OCR-/torch-/transformers-Servicepaket `flowinvoice services/parser.py:PDFParser`
wurde nicht übernommen.

## Quelle, Rechte, Testdaten

`janpow77/audit_designer@030a71e083ef0feddc14545b095a4945bc0bbd7a`, gegen GitHub
geprüft; `main@1254591` ist für alle genutzten Pfade unverändert. Zwölf Blobs
(`types`, `parsing`, `matching`, `article_law`, `service`, `rendering`,
`configuration`, `cli`, `tasks`, ecohesion `worker`, ecohesion
`services/research_pdf`, `core/shared/research/contracts`) in `provenance.json`.
Repository privat ohne Lizenzdatei; USER_AUTHORIZED_MIT vom 22.09.2026 für den
extrahierten Bibliothekscode, keine Umlizenzierung des Quellrepositorys.

Öffentliche Fixtures (§ 5 Abs. 1 UrhG): Kassensicherungsverordnung als amtliche
PDF von gesetze-im-internet.de in den Fassungen 2021 (Archiv 10.06.2023) und
2026 (Archiv 27.08.2026), HTML-/XML-Fassungen 2025/2026 als Quellen der
DOCX-Fixtures sowie Seite 55 aus BGBl. 2025 I Nr. 301 mit Artikel 15
(„In § 11 Absatz 1 Satz 1 wird die Angabe „§ 9 des BSI-Gesetzes“ durch die
Angabe „§ 52 des BSI-Gesetzes“ ersetzt“). Alle übrigen Fixtures sind synthetisch.

## Characterization

`tools/capture_legacy.py` führt die unveränderten Originalmodule in einem
Wegwerf-Container mit den Versionen des laufenden `audit_designer_backend`
aus (Python 3.11.16, lxml 5.1.0, python-docx 1.1.0, pypdf 6.16.2,
rapidfuzz 3.14.5, pdftotext 22.12.0, reportlab 4.0.8, DejaVuSans). Aufgezeichnet:
61 Lesefälle, 29 Moduserkennungen, 62 Standardvergleiche, 7 Gesetzessynopsen,
6 PDF-Extraktionen, Einstellungen, Begründungen, 8 DOCX-Renderings, 3 CLI-,
5 Celery- und 5 ECOHESION-Abläufe, davon 4 mit echter PDF-Synopse. Zwei Läufe mit verschiedenem `PYTHONHASHSEED` sind
byte-gleich; nach Umformatierung des Werkzeugs erneut byte-gleich. Die
9 Originaltests bestehen gegen das Original.

Das Profil LEGACY reproduziert alle Fälle exakt, auch den DOCX-Hauptteil, die
Kopf- und die Fußzeile; die PDF-Synopse stimmt in Seitentext, Titel und Autor
überein (reportlab 4.0.8 im Original, 5.0.1 im Test). Korrekturen DC-C01 bis DC-C11 und beibehaltenes
Originalverhalten DC-L01 bis DC-L09 stehen in
`packages/auditcore_documents/docs/behavior-changes.md`. Unabhängig von der
Aufzeichnung prüfen die Tests die Anwendung von Artikel 15 gegen den Wortlaut
der amtlichen Quelle.

**Sicherheitsbefund:** Der Originalparser (`etree.fromstring` ohne Härtung)
liest mit lxml 4.9.2 (Debian bookworm) eine externe Entität
`file:///etc/hostname` in den Vergleichstext ein (nachgewiesen im
Debian-Container). pip-audit meldet CVE-2026-41066/PYSEC-2026-87 für die
Produktionsfassung lxml 5.1.0 des Consumers. Die Bibliothek parst mit
`resolve_entities=False`, weist DTDs ab und verlangt lxml ≥ 6.1.0.

## Tests und Gates (tatsächlich ausgeführt)

| Prüfung | Ergebnis |
|---|---|
| Paket-pytest (Python 3.12, lxml 6.1.3, reportlab 5.0.1) | 341 passed, 3 skipped (pdftotext 24.02 statt 22.12) |
| Paket-pytest in Referenzumgebung (Python 3.11.16, pdftotext 22.12.0, reportlab 4.0.8) | 343 passed, 1 skipped (`auditcore_reporting` dort nicht installiert) |
| Paket-pytest ohne pdftotext (python:3.12-slim, wie CI) | PASS (pdftotext-Fälle übersprungen) |
| Paket-pytest mit lxml 6.1.3, rapidfuzz 3.10.1, pypdf 6.19.0 | PASS (pypdf-Extraktion identisch zu 6.16.2) |
| Lesen/Modus/Regeln mit Debian python3-lxml 4.9.2 (bookworm) | 178 passed; 1 erwartete Abweichung ohne pypdf |
| Originalsuite (9 Tests) gegen die Bibliothek | PASS |
| ruff, ruff format, mypy strict, bandit | PASS |
| Plattform-pytest / ruff / mypy / CLI-Hilfen | 283 passed; PASS; PASS; quality, consolidate, refactor, deploy PASS |
| auditcore-quality strict | Syntax, Lint, Typen, bandit, pip-audit, Tests, Supply Chain PASS; 35 Hinweise (Docstrings, Komplexität); Gesamt REVIEW_REQUIRED wegen Policy |
| Policy (verwaltung-app-framework@15f5338) | F-04 (T-09), F-07-Nachweisteil (T-14, T-37), F-09 (T-38), F-15 VERIFIED, artefaktgebunden; offen F-05, F-07.ASSESS, T-12 (Schutzbedarf/DSFA-Pflicht UNKNOWN, Consumer-Kontext) |

## Installation

`scripts/verify_domain_packages.py packages/auditcore_documents --apt` mit
Plattform-Wheel: Build, SBOM, hashgebundene Requirements-Installation,
`pip check`, Importherkunft, Smoke aus dem installierten Wheel, selektive
Installation und Entfernung, Debian-Pakete Revision 1 und 2, signierte
APT-Quelle, Installation, Upgrade 1→2 und Entfernung im netzlosen Container:
alle 21 Prüfungen PASS. Wheel-SHA256
`70e83f18e0e265a9d238f65f1a0b847c00ad3e00a5a81f70d532541e396d4005`.
Keine Debian-Zuordnung der Extras: bookworm liefert python3-lxml 4.9.2,
python3-docx 0.8.11, python3-pypdf 3.4.1 und python3-reportlab 3.6.12 unterhalb
der Extra-Untergrenzen, rapidfuzz fehlt.

## Consumer audit_designer

Belegte Consumer: `api/document_comparisons.py`, `document_compare/tasks.py`,
`ecohesion/comparisons/worker.py`, Modul-CLI. Integrationsvariante in einer
Checkout-Kopie (lokale Commits `64675e53`, `ea650452`, `fe6dcb3b`, nicht
gepusht): Fachmodule entfallen, dünne Anbindungen bleiben; der ECOHESION-Worker
erzeugt `comparison.pdf` über `render_synopsis_pdf`. Im Wegwerf-Container aus
`audit_designer-backend` (SQLite im Speicher): vorher 31 passed, nachher
31 passed; Replay von 44 aufgezeichneten Fällen durch den umgestellten Code:
44 identisch, 0 abweichend – mit `--no-deps` und mit echter Auflösung der Extras
bei lxml 6.1.3; nach Umstellung der PDF-Erzeugung erneut 31 passed und 44/0
(reportlab 4.0.8 des Images). Umstellungsanleitung:
`packages/auditcore_documents/docs/consumer-integration.md`.
**MIGRATION_BLOCKED** bis Release v0.3.0 im Paketfeed; Consumer-Requirements
werden erst danach umgestellt.

Weitere Consumer (QChess-DOCM-Import, PDF-/DOCX-Werkzeuge des Designers) sind
**geplant**, nicht belegt.

## auditdatabase docformatter

`auditdatabase/packages/docformatter` (`EFREConverter`, `ExcelFormatter`,
`ExcelAnalyzer`) formatiert Dokumente in Corporate-Vorlagen und hat im
Repository keinen Aufrufer. Keine Überschneidung mit Lesen/Vergleichen; bewusst
getrennt, keine Doppelimplementierung. Späterer Schritt: Abgleich mit
QCHESS_PRINT und Einordnung bei `auditcore_reporting`, Vorlagenrechte
(`EFRE_TEMPLATE.docx`) gesondert klären.

## Offene Entscheidungen (HUMAN_DECISION_REQUIRED)

1. DC-C04: Profil CORRECTED (liest „§ … wird aufgehoben/gefasst“) statt LEGACY
   in audit_designer/ECOHESION übernehmen.
2. DC-L01: Absatzzählung nach „Nach … wird folgender Absatz … eingefügt“.
3. DC-L02: Ersetzen aller Vorkommen und Überlesen von Satz-/Nummernangaben.
4. DC-C01: Vergleich ohne rapidfuzz zulassen (heute stiller difflib-Rückfall).

Weitere Befunde ohne Entscheidungsbedarf: die seit 2024 übliche Befehlsform
„wird durch den folgenden … ersetzt“ und Satz-/Nummernbefehle bleiben offen
(DC-L03, Funktionserweiterung).

## Teil 2: Dokumentpipeline aus flowinvoice

Quelle `janpow77/flowinvoice@fb2d18568d2eaf64574d131ceae51a936b9aac02`
(`main`, gegen GitHub geprüft), 13 Blobs aus `backend/app/pipeline` in
`provenance.json`; Quellbindung in `scripts/prepare_library_release.py`
ergänzt. Unterpaket `auditcore_documents.pipeline`: Stufenvertrag,
Orchestrierung mit Wiederherstellung, Kontext/Modelle ohne pydantic, Hashing
mit bytegleichen Stufen-Hashes, Audit-Port mit unveränderlicher Referenzsenke,
Aufbewahrung, Profile `LEGACY_PIPELINE`/`CORRECTED_PIPELINE`. OCR-Engines
(Gateway, Chandra, Tesseract), Rasterung, libmagic, Persistenz,
Betrugsprüfung und Webhooks sind Ports; neue Extras `mime` (python-magic) und
`ocr-raster` (pypdfium2, Pillow); kein torch/transformers/GPU.
`services/parser.py:PDFParser` und `services/chandra_ocr.py` bleiben in der
Anwendung; `services/extraction_quality_watchdog.py` ist geplant
(HUMAN_DECISION_REQUIRED zu den Meldungstexten ohne Umlaute).

| Prüfung | Ergebnis |
|---|---|
| Originaltests flowinvoice (Pipeline, Watchdog, Profile) gegen Wegwerf-PostgreSQL | 164 passed |
| Charakterisierung (`tools/capture_pipeline.py`) | 30 vollständige Läufe + Einzelfälle; erneuter Lauf identisch bis auf temporäre Pfade |
| Replay durch die Bibliothek | 30/30 Läufe exakt (Kontext inkl. Stufen-Hashes, Audit, Gateway-Aufrufe, Artefakte, Exporte) |
| Paket-pytest gesamt (Python 3.12) | 491 passed, 3 skipped |
| ruff, mypy strict, bandit, pip-audit | PASS |
| auditcore-quality strict | Sicherheits-/Lieferketten-Gates PASS; Gesamt REVIEW_REQUIRED (Policy F-05/F-07 UNKNOWN) |
| Policy | F-04, F-07-Nachweisteil, F-09, F-15 VERIFIED |
| `verify_domain_packages.py --apt` | 21/21 PASS, Wheel-SHA256 `572e85f9a5b06802cd55bddf7ad584617d87a65ea9324b66633fda2c97d6f1da` |
| Installationstest | fand einen Defekt (leeres `InMemoryAuditLog` „falsy“), behoben in `545b354` |

**Befunde** (Details `packages/auditcore_documents/docs/pipeline.md`):
REVIEW_NEEDED geht im Original verloren – Belege mit niedriger OCR-Konfidenz oder
Regelbefund enden als `ok` (PL-C01, korrigiert nur im Profil `CORRECTED_PIPELINE`);
das IBAN-Muster frisst Folgezeilen und lehnt gültige IBAN als CRITICAL ab
(PL-C02); englische Beträge werden als deutsches Format gelesen (PL-L01);
Gateway-Ausfall wird zu REJECTED (PL-L03); nur eine von fünf Aufbewahrungsfristen
wirkt (PL-L05). Beim Consumer: doppelte `run_id`, ungenutzte Profil-Einstellungen,
doppelte Audit-Ereignisse, `NameError` im Export-Task, und die Audit-Tabelle
`pipeline_audit_events` ist nicht durch den WORM-Trigger geschützt
(SECURITY_OR_POLICY_REVIEW_REQUIRED).

**Consumer flowinvoice:** Integrationsvariante in einer Checkout-Kopie (lokaler
Commit `bfe3d78`, nicht gepusht): `app/pipeline/auditcore_runner.py` mit Ports,
Worker ruft `run_document_pipeline`. Im Wegwerf-Container mit den
Produktionsabhängigkeiten und Wegwerf-PostgreSQL: 164 Originaltests plus neuer
Worker-Integrationstest → 165 passed; `pip check` mit
`auditcore_documents[mime,ocr-raster,pdf-text]` ohne Befund.
**MIGRATION_BLOCKED** bis Release v0.3.0.

Weitere offene Entscheidungen: Übernahme von `CORRECTED_PIPELINE`, Gebietsschema
der Feldextraktion (PL-L01), Umgang mit Gateway-Ausfall (PL-L03), Löschkonzept
(PL-L05), Meldungstexte des Watchdogs.
