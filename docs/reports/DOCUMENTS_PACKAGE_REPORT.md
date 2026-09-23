# auditcore_documents 0.1.0 — Bericht

Stand: 23. September 2026. Branch `feat/auditcore-documents` (Worktree
`auditcore-wt-documents`, Basis `origin/main`, zuletzt mit `7c063d4`
zusammengeführt). Teil 1 dieses Berichts betrifft den Dokumentvergleich und die
Gesetzessynopse aus audit_designer. Die flowinvoice-Dokumentpipeline folgt als
eigener, logisch getrennter Pull Request (Teil 2).

## Umfang Teil 1

Eigenständige Distribution `auditcore_documents` (Debian
`python3-auditcore-documents`), Laufzeit nur Standardbibliothek, keine
Abhängigkeit auf `auditcore`. Extras: `docx` (lxml ≥ 6.1.0), `pdf-text`
(pypdf), `fuzzy` (rapidfuzz), `docx-render` (python-docx). Konsolenbefehl
`auditcore-documents`.

| Fähigkeit | Umsetzung |
|---|---|
| Lesen | DOCX/DOCM (gehärteter lxml-Parser, Nachverfolgung im Speicher angenommen, Inhaltssteuerelemente, Kontrollkästchen, verborgener/kursiver Hinweistext), PDF über injizierbare Seitenquelle (`pdftotext`, `pypdf`, Originalreihenfolge) und ausdrücklichen OCR-Rückruf |
| Standardvergleich | Checklisten- und Fließtextzuordnung, Umstellungserkennung, Wortdifferenz, redaktionelle Änderungen optional |
| Gesetzessynopse | Ersetzen/Aufheben/Neufassen/Einfügen auf Absatzebene, offene Befehle mit Grund, konsolidierte Arbeitsfassung |
| Profile | `audit_designer.document_compare` 1.1.0 (LEGACY), `…difflib`, `auditcore.document_compare` 2026.09.1 (CORRECTED), versioniert mit Fingerprint |
| Ports | `ReadContext` (Uhr, Seitenquelle, OCR, Grenzen), `ReasonProvider` für KI-Begründungen (FlowAgent-Adapter `mcp_tool_provider`) |
| Ausgabe | JSON (`to_dict`/`from_dict`), DOCX-Synopse (Extra), Synopse-Datensätze für `auditcore_reporting` (XLSX) |
| Kompatibilität | `legacy.DocumentCompareService`, `legacy.compare_documents` mit Namen, Signaturen und Fehlertexten des Originals |

`auditcore_reporting` 0.2.0 kennt nur XLSX; der DOCX-Renderer bleibt deshalb als
Extra in diesem Paket (`RENDERER_OWNERS` unverändert, keine neue Renderer-Sperre).
Das OCR-/torch-/transformers-Servicepaket `flowinvoice services/parser.py:PDFParser`
wurde nicht übernommen.

## Quelle, Rechte, Testdaten

`janpow77/audit_designer@030a71e083ef0feddc14545b095a4945bc0bbd7a`, gegen GitHub
geprüft; `main@1254591` ist für alle genutzten Pfade unverändert. Zehn Blobs
(`types`, `parsing`, `matching`, `article_law`, `service`, `rendering`,
`configuration`, `cli`, `tasks`, ecohesion `worker`) in `provenance.json`.
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
rapidfuzz 3.14.5, pdftotext 22.12.0). Aufgezeichnet: 61 Lesefälle,
29 Moduserkennungen, 62 Standardvergleiche, 7 Gesetzessynopsen, 6 PDF-Extraktionen,
Einstellungen, Begründungen, 8 DOCX-Renderings, 3 CLI-, 5 Celery- und
3 ECOHESION-Abläufe. Zwei Läufe mit verschiedenem `PYTHONHASHSEED` sind
byte-gleich; nach Umformatierung des Werkzeugs erneut byte-gleich. Die
9 Originaltests bestehen gegen das Original.

Das Profil LEGACY reproduziert alle Fälle exakt, auch den DOCX-Hauptteil, die
Kopf- und die Fußzeile. Korrekturen DC-C01 bis DC-C10 und beibehaltenes
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
| Paket-pytest (Python 3.12, lxml 6.1.3) | 338 passed, 3 skipped (pdftotext 24.02 statt 22.12) |
| Paket-pytest in Referenzumgebung (Python 3.11.16, pdftotext 22.12.0) | 339 passed, 1 skipped (`auditcore_reporting` dort nicht installiert) |
| Paket-pytest mit lxml 6.1.3, rapidfuzz 3.10.1, pypdf 6.19.0 | PASS (pypdf-Extraktion identisch zu 6.16.2) |
| Lesen/Modus/Regeln mit Debian python3-lxml 4.9.2 (bookworm) | 178 passed; 1 erwartete Abweichung ohne pypdf |
| Originalsuite (9 Tests) gegen die Bibliothek | PASS |
| ruff, ruff format, mypy strict, bandit | PASS |
| Plattform-pytest / ruff / mypy / CLI-Hilfen | 283 passed; PASS; PASS; quality, consolidate, refactor, deploy PASS |
| auditcore-quality strict | Syntax, Lint, Typen, bandit, pip-audit, Tests, Supply Chain PASS; 30 Hinweise (Docstrings, Komplexität); Gesamt REVIEW_REQUIRED wegen Policy |
| Policy (verwaltung-app-framework@15f5338) | F-04 (T-09), F-07-Nachweisteil (T-14, T-37), F-09 (T-38), F-15 VERIFIED, artefaktgebunden; offen F-05, F-07.ASSESS, T-12 (Schutzbedarf/DSFA-Pflicht UNKNOWN, Consumer-Kontext) |

## Installation

`scripts/verify_domain_packages.py packages/auditcore_documents --apt` mit
Plattform-Wheel: Build, SBOM, hashgebundene Requirements-Installation,
`pip check`, Importherkunft, Smoke aus dem installierten Wheel, selektive
Installation und Entfernung, Debian-Pakete Revision 1 und 2, signierte
APT-Quelle, Installation, Upgrade 1→2 und Entfernung im netzlosen Container:
alle 21 Prüfungen PASS. Wheel-SHA256
`55e029ce0f89f6b20a1336ae931e306932098561e6b7772ab62ab2871b1c06ef`.
Keine Debian-Zuordnung der Extras: bookworm liefert python3-lxml 4.9.2,
python3-docx 0.8.11 und python3-pypdf 3.4.1 unterhalb der Extra-Untergrenzen,
rapidfuzz fehlt.

## Consumer audit_designer

Belegte Consumer: `api/document_comparisons.py`, `document_compare/tasks.py`,
`ecohesion/comparisons/worker.py`, Modul-CLI. Integrationsvariante in einer
Checkout-Kopie (lokale Commits `64675e53`, `ea650452`, nicht gepusht):
Fachmodule entfallen, dünne Anbindungen bleiben. Im Wegwerf-Container aus
`audit_designer-backend` (SQLite im Speicher): vorher 31 passed, nachher
31 passed; Replay von 44 aufgezeichneten Fällen durch den umgestellten Code:
44 identisch, 0 abweichend – mit `--no-deps` und mit echter Auflösung der Extras
bei lxml 6.1.3. Umstellungsanleitung:
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
