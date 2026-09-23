# auditcore_documents 0.1.0

Dokumentvergleich und Gesetzessynopse ohne Web-, Datenbank-, Celery- oder
KI-Abhängigkeit. Extrahiert und charakterisiert aus
`janpow77/audit_designer@030a71e0` (`backend/app/modules/document_compare`).
Ein Vergleich ist eine Arbeitshilfe: Er stellt Unterschiede fest und
bereitet sie auf, er trifft keine Prüfungsentscheidung.

```bash
python -m pip install 'auditcore_documents[docx,pdf-text,fuzzy,docx-render]==0.1.0'
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
| `docx-render` | python-docx ≥ 1.1 | Synopse als DOCX |

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

columns, rows = ad.synopsis_records(result)  # z. B. für auditcore_reporting.ReportTable
```

Kommandozeile: `auditcore-documents read DATEI`, `auditcore-documents compare
ALT NEU -o synopse.docx --json ergebnis.json [--comparison-type article_law]
[--profile auditcore.document_compare]`, `auditcore-documents create-config PFAD`.

## Vertrag

- **Profile** (`PROFILES`, versioniert, mit Fingerprint):
  `audit_designer.document_compare` 1.1.0 (`LEGACY`, Produktionsverhalten),
  `…difflib` (`LEGACY_DIFFLIB`, Rückfall des Originals ohne rapidfuzz),
  `auditcore.document_compare` 2026.09.1 (`CORRECTED`, siehe DC-C04; Übernahme
  ist eine fachliche Entscheidung).
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

`auditcore_reporting` 0.2.0 kennt nur XLSX; der DOCX-Renderer bleibt deshalb
als Extra hier. Für XLSX liefert `synopsis_records` passende Datensätze.

Nachweise, Abweichungen und offene Entscheidungen: `docs/behavior-changes.md`,
`docs/consumer-integration.md`, `provenance.json`, `NOTICE`.
