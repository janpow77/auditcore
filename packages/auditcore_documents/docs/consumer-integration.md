# Consumer-Anbindung audit_designer (Dokumentvergleich)

Belegte Consumer am Quellstand `janpow77/audit_designer@030a71e0`
(unverändert bis `main@1254591`, per `git diff` geprüft):

| Stelle | Symbol | Nutzung |
|---|---|---|
| `backend/app/api/document_comparisons.py` | `DocumentCompareService`, `CompareRow`, `ComparisonResult`, `load/save/merge/sanitise_settings` | Upload, Vorschau, DOCX-Download, Einstellungen |
| `backend/app/modules/document_compare/tasks.py` | `DocumentCompareService.compare/generate_reason` | Celery-Lauf mit OCR-Rückruf und FlowAgent-Begründungen |
| `backend/app/modules/ecohesion/comparisons/worker.py` | `DocumentCompareService.compare/render_docx`, `CompareError` | ECOHESION-Vergleich im begrenzten Prozess |
| `backend/app/modules/document_compare/cli.py`, `__main__.py` | `compare_documents`, `read_document` | Kommandozeile und Jupyter |

Weitere Consumer sind **geplant**, aber nicht belegt (Stand 23.09.2026):
QChess-DOCM-Import (`services/qchess_report/`), PDF-/DOCX-Werkzeuge des
Designers, die flowinvoice-Dokumentpipeline (eigener Schritt).

## Getestete Integrationsvariante

Kopie des Checkouts, Branch `feat/auditcore-documents`, lokale Commits
`64675e53` (Umstellung), `ea650452` (lxml 6.1.3) und `fe6dcb3b` (ECOHESION-PDF
über die Bibliothek), nicht gepusht. Die Fachmodule `matching.py`, `article_law.py`
und `rendering.py` entfallen; `types.py`, `parsing.py`, `configuration.py`
und `service.py` werden zu dünnen Anbindungen, `cli.py` delegiert.
`tasks.py`, `api/document_comparisons.py` und der ECOHESION-Worker bleiben
unverändert, weil die Fassade Namen, Signaturen und Fehlertexte beibehält.

Nachweis in einem Wegwerf-Container aus dem Image `audit_designer-backend`
(Python 3.11.16, lxml 5.1.0, python-docx 1.1.0, pypdf 6.16.2,
rapidfuzz 3.14.5, pdftotext 22.12.0; SQLite im Speicher, keine
Produktionsdatenbank), Wheel `auditcore_documents-0.1.0` per
`pip install --no-deps`:

- vorher (Original): `tests/test_document_compare_service.py`,
  `tests/test_document_compare_tasks.py`,
  `tests/ecohesion/test_document_comparisons.py` → **31 passed**
- nachher (umgestellt, Import nachweislich aus `site-packages`) → **31 passed**
- Replay der Aufzeichnung durch den umgestellten Code: 31 Standardvergleiche,
  7 Gesetzessynopsen, 6 Begründungsantworten → **44 identisch, 0 abweichend**
  (PDF-Fälle hier mit echtem pdftotext 22.12.0 des Images).
- Zweiter Lauf mit echter Abhängigkeitsauflösung
  `auditcore_documents[docx,pdf-text,fuzzy,docx-render]` und lxml 6.1.3:
  wieder 31 passed und 44/0. `pip check` meldet nur den bereits im Image
  vorhandenen Konflikt `wheel 0.46.3` ↔ `packaging 23.2`.
- Dritter Lauf mit PDF über die Bibliothek im ECOHESION-Worker: 31 passed, 44/0.

## Umstellungsanleitung

1. `backend/requirements.txt`: `lxml==5.1.0` → `lxml==6.1.3` (das Extra
   `docx` verlangt ≥ 6.1.0; CVE-2026-41066 betrifft lxml < 6.1.0) und nach
   `rapidfuzz>=3.10` ergänzen:
   `auditcore_documents[docx,pdf-text,fuzzy,docx-render]==0.1.0`
   (erst nach Veröffentlichung von Release v0.3.0 im Paketfeed).
2. `app/modules/document_compare/matching.py`, `article_law.py`,
   `rendering.py` löschen.
3. `types.py`:
   ```python
   from auditcore_documents.model import CompareItem, CompareRow, ComparisonResult
   ```
4. `parsing.py` (Rückwärtsnamen, u. a. für
   `tests/ecohesion/test_document_comparisons.py`):
   ```python
   from auditcore_documents.errors import ParseError
   from auditcore_documents.normalize import (
       normalise_for_match,
       normalise_semantic,
       normalise_verbatim,
       word_diff,
   )
   from auditcore_documents.pdftext import paragraphs_from_pdf_pages as _paragraphs_from_pdf_pages
   from auditcore_documents.pdftext import remove_repeating_margins as _remove_repeating_margins
   from auditcore_documents.reading import detect_mode, read_document
   ```
5. `configuration.py`: Konstanten, `merge_settings`, `sanitise_settings` aus
   `auditcore_documents.settings`; `default_config_path =
   auditcore_documents.legacy.audit_designer_config_path`; `load_settings(path=None)`
   und `save_settings(values, path=None)` rufen die Bibliothek mit
   `path or default_config_path()` auf.
6. `service.py`:
   ```python
   from auditcore_documents.legacy import CompareError
   from auditcore_documents.legacy import DocumentCompareService as _LibraryService
   from auditcore_documents.model import CompareItem, CompareRow, ComparisonResult


   def flowagent_reason(old_text, new_text, model):
       from app.modules.standards import mcp_tools

       return mcp_tools.ausfuehren(
           "document_compare_reason", {"alt": old_text, "neu": new_text, "modell": model}
       )


   class DocumentCompareService(_LibraryService):
       reason_provider = staticmethod(flowagent_reason)
   ```
7. ECOHESION-Worker (optional, getestet): statt `ResearchResult` und
   `research_pdf.render_pdf` erzeugt
   `render_synopsis_pdf(spec["title"], synopsis_report(result), {})` die
   `comparison.pdf`; Requirement dann mit Extra `pdf-render`. `research_pdf`
   bleibt für die übrigen Recherchewerkzeuge in der Anwendung.
8. `cli.py`: `compare_documents` ruft
   `auditcore_documents.legacy.compare_documents(..., config=config or default_config_path(),
   reason_provider=flowagent_reason, **overrides)`; `main` bleibt.

Verhaltensunterschiede für die Anwendung: Dokumente mit DTD werden mit
`CompareError` abgelehnt (DC-C02, ECOHESION prüft das bereits beim Upload);
ohne rapidfuzz kein stiller Rückfall (DC-C01). Das Profil bleibt `LEGACY`;
die Übernahme von `CORRECTED` (DC-C04) ist HUMAN_DECISION_REQUIRED.

## Verhältnis zu auditdatabase `packages/docformatter`

`janpow77/auditdatabase@bba911e` (`main@6988064` unverändert) enthält
`docformatter` 0.1.0 (`word.converter:EFREConverter`,
`excel.formatter:ExcelFormatter`, `excel.analyzer:ExcelAnalyzer`; Laufzeit
python-docx, openpyxl, pydantic; eingebettete Vorlage `EFRE_TEMPLATE.docx`).
Es **formatiert** vorhandene Word-/Excel-Dateien in eine Corporate-Vorlage;
im Repository selbst hat es keinen Aufrufer. `auditcore_documents` **liest
und vergleicht** Dokumente. Es gibt keine gemeinsame Funktion und keine
Doppelimplementierung; beide bleiben bewusst getrennt. Späterer Schritt:
`EFREConverter`/`ExcelFormatter` gegen QCHESS_PRINT abgleichen und – falls ein
Consumer belegt ist – als Renderer bei `auditcore_reporting` einordnen, nicht
hier. Die Vorlagenrechte (`EFRE_TEMPLATE.docx`) sind dafür gesondert zu klären.
