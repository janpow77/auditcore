# auditcore_pdf

## Zweck

Vollständige PDF-Verarbeitung, Seitenoperationen, visuelle Anzeige und nachprüfbare Schwärzung für Prüf- und Kontrollprozesse.

Die Bibliothek stellt Fachanwendungen der Prüfbehörde robuste Funktionen für Dokumentenanalyse, Seitenmanipulationen (Umsortieren, Drehen, Extrahieren, Zusammenführen, Aufteilen) und mehrschichtige Schwärzungen bereit. Das Unterpaket `auditcore_pdf.redaction` schwärzt in zwei Schritten: `build_plan` sucht Fundstellen (Muster mit Prüfziffer, Begriffe, optional KI-Namenserkennung) und liefert einen Plan zur Vorschau; `apply_plan` schwärzt genau die bestätigte Auswahl, bereinigt versteckte Ablagen und prüft das Ergebnis fail-closed nach. Das Unterpaket `auditcore_pdf.web` (Extras `[web]`, `[fastapi]`) stellt den zustandslosen REST-Vertrag `pdf_redaction/1` für die Oberfläche `<flowaudit-pdf-redaction>` bereit ([Vertrag](../../docs/ui/redaction-rest.md)). Nicht enthalten sind Anmeldung, Ablage und Datenbankbindungen.

## Installation

Aus dem Paketindex von auditcore (PEP 503, jede Datei mit SHA-256 verlinkt):

```bash
python -m pip install 'auditcore_pdf==0.3.0' \
  --index-url https://janpow77.github.io/auditcore/simple/
```

Hashgebunden in einer `requirements.txt` (Direkt-URL und `sha256` stehen im
Index unter `https://janpow77.github.io/auditcore/simple/auditcore-pdf/`):

```text
auditcore_pdf @ https://github.com/janpow77/auditcore/releases/download/v<release>/auditcore_pdf-0.3.0-py3-none-any.whl#sha256=<sha256>
```

Debian/Ubuntu über die signierte APT-Quelle des Releases
([Einrichtung](../../docs/deployment/package-feed.md)):

```bash
sudo apt-get install python3-auditcore-pdf
```

Extras: `[pymupdf]` – PDF-Engine über PyMuPDF; `[pillow]` – Bildverarbeitung; `[ner]` – KI-Namenserkennung über spaCy (das Sprachmodell, etwa `de_core_news_sm`, installiert die Anwendung); `[web]` – REST-Endpunkte über Starlette; `[fastapi]` – zusätzlich als FastAPI-Router; `[dev]` – Test- und Prüfwerkzeuge.

## Schnellstart

```python
from auditcore_pdf import STANDARD_PATTERNS, SanitizationPolicy
from auditcore_pdf.redaction import PATTERNS, Criteria, Selection

assert "email" in STANDARD_PATTERNS
policy = SanitizationPolicy(scrub_metadata=True, strip_attachments=True)
assert policy.scrub_metadata is True

# Zweistufige Schwärzung: Kriterien festlegen, Plan bauen, Auswahl bestätigen.
criteria = Criteria.from_input(patterns=["iban", "email"], terms=["Erika Mustermann"])
assert "iban" in PATTERNS
# plan = build_plan(pdf_bytes, criteria)             # Vorschau: plan.to_dict()
# selection = Selection.from_dict(antwort_der_vorschau)
# out, report = apply_plan(pdf_bytes, selection)     # fail-closed nachgeprüft
```

## API-Überblick

<!-- api-overview:start (generiert: python scripts/docs/api_overview.py --write) -->
Öffentliche Namen aus `auditcore_pdf.__all__` (29):

| Name | Art | Kurzbeschreibung (erste Docstring-Zeile) | Modul |
|---|---|---|---|
| `MAX_PAGES` | Konstante | Maximale Seitenzahl zur Verhinderung von Ressourcen-Überlastung | `engine` |
| `STANDARD_PATTERNS` | Konstante | Vordefinierte Erkennungsmuster für sensible Daten | `models` |
| `DocumentInfo` | Datenklasse | Struktur- und Metadatenübersicht eines PDF-Dokuments. | `models` |
| `PageInfo` | Datenklasse | Metadaten und Eigenschaften einer einzelnen PDF-Seite. | `models` |
| `RedactionBox` | Datenklasse | Expliziter geometrischer Schwärzungsbereich auf einer Seite. | `models` |
| `RedactionFinding` | Datenklasse | Gefundene Stelle, die für eine Schwärzung markiert wurde. | `models` |
| `RedactionPattern` | Datenklasse | Regulärer Ausdruck zur Erkennung sensibler Muster. | `models` |
| `RedactionReport` | Datenklasse | Ergebnisbericht eines Schwärzungslaufs. | `models` |
| `SanitizationPolicy` | Datenklasse | Richtlinie für begleitende Metadaten- und Struktur-Bereinigungen. | `models` |
| `VerificationResult` | Datenklasse | Ergebnis der unabhängigen Nachprüfung einer Schwärzung. | `models` |
| `delete_pages` | Funktion | Löscht die angegebenen 1-basierten Seitennummern aus dem Dokument. | `operations` |
| `extract_all_text` | Funktion | Extrahiert den gesamten Text aller Seiten eines Dokuments. | `viewer` |
| `extract_page_text` | Funktion | Extrahiert den Klartext einer einzelnen Seite. | `viewer` |
| `extract_pages` | Funktion | Extrahiert ausgewählte 1-basierte Seiten in ein neues PDF-Dokument. | `operations` |
| `find_redaction_targets` | Funktion | Durchsucht das Dokument nach Begriffen und Mustern über alle Seiten. | `redact` |
| `get_document_info` | Funktion | Ermittelt Struktur- und Metadaten eines PDF-Dokuments. | `viewer` |
| `get_toc` | Funktion | Liest das Inhaltsverzeichnis (Lesezeichen) des Dokuments aus. | `viewer` |
| `is_pymupdf_available` | Funktion | Gibt zurück, ob PyMuPDF auf dem System zur Verfügung steht. | `engine` |
| `merge_documents` | Funktion | Führt mehrere PDF-Dokumente nahtlos zu einer gemeinsamen PDF zusammen. | `operations` |
| `open_pdf` | Funktion | Öffnet ein PDF-Dokument sicher aus einem Byte-Puffer im Arbeitsspeicher. | `engine` |
| `redact_document` | Funktion | Führt eine vollständige und überprüfbare Schwärzung eines PDF-Dokuments durch. | `redact` |
| `render_page` | Funktion | Rendert eine einzelne PDF-Seite als Rasterbild. | `viewer` |
| `reorder_pages` | Funktion | Sortiert die Seiten eines Dokuments nach einer 1-basierten Reihenfolge um. | `operations` |
| `rotate_pages` | Funktion | Dreht ausgewählte Seiten (1-basierte Seitennummern auf Gradzahl, z. B. 90, 180, 270). | `operations` |
| `sanitize_annotations` | Funktion | Entfernt oder bereinigt Notizen, Kommentare und Hervorhebungen mit vertraulichem Inhalt. | `sanitize` |
| `sanitize_attachments` | Funktion | Entfernt oder bereinigt eingebettete Dateien (EmbeddedFiles). | `sanitize` |
| `sanitize_metadata` | Funktion | Bereinigt Standard- und XMP-Metadaten des Dokuments. | `sanitize` |
| `split_document` | Funktion | Teilt ein Dokument in Abschnitte von jeweils höchstens chunk_size Seiten auf. | `operations` |
| `verify_redaction` | Funktion | Prüft ein PDF unabhängig auf das Vorhandensein verbotener Begriffe und Muster. | `verification` |

Öffentliche Module:

| Modul | Kurzbeschreibung |
|---|---|
| `auditcore_pdf.engine` | Sicherer Zugriffspunkt auf das PDF-Backend. |
| `auditcore_pdf.models` | Datenmodelle für PDF-Verarbeitung, Seitenoperationen und Schwärzung. |
| `auditcore_pdf.operations` | Seiten- und Dokumentenoperationen für PDF-Dateien. |
| `auditcore_pdf.redact` | Vollständige Schwärzungslogik mit Koordinaten-, Begriffs- und Mustererkennung. |
| `auditcore_pdf.redaction` | Schwärzung mit Pflichtvorschau: Plan, Auswahl, Anwendung und Nachprüfung. |
| `auditcore_pdf.sanitize` | Metadaten-, Anhangs- und Anmerkungsbereinigung zur Verhinderung von Datenabflüssen. |
| `auditcore_pdf.verification` | Unabhängige Nachprüfung und Verifikation von Schwärzungsergebnissen. |
| `auditcore_pdf.viewer` | Anzeige-, Lese- und Analysefunktionen für PDF-Dokumente. |
| `auditcore_pdf.web` | REST contract ``pdf_redaction/1`` for "PDF schwärzen" (extras ``web``, ``fastapi``). |
<!-- api-overview:end -->

## Profile und Konfiguration

Die Bibliothek verwendet standardisierte Erkennungsmuster unter `STANDARD_PATTERNS` für IBAN, E-Mail, Telefonnummern, Steuer-IDs, USt-IDs, Kreditkarten, Geburtsdaten, IP-Adressen und Aktenzeichen. Die Sicherheitsgrenze `MAX_PAGES` (5.000 Seiten) schützt vor Ressourcenerschöpfung durch überdimensionierte Dokumente. Über `SanitizationPolicy` lässt sich steuern, ob Metadaten bereinigt, Anhänge entfernt und Anmerkungen gesäubert werden.

## Herkunft und Charakterisierung

Hervorgegangen aus den Anforderungen und Untersuchungen in `audit_designer/pdf-editor-app` sowie der Voruntersuchung `docs/reports/pdf-editor-characterization-20260929.json`. Charakterisiert anhand von 29 automatisierten Tests, die alle Schwachstellen früherer Werkzeuge (wie verbleibende Klartextreste in Titeln, Anhängen, Kommentaren sowie fehlende Treffer bei Zeilenumbrüchen) gezielt absichern und nachweisen.

## Bewusste Verhaltensabweichungen

Die Schwärzung `auditcore_pdf.redaction` übernimmt den Stand von pdf-editor@c5b3e1d ohne fachliche Abweichung; Einzelheiten und die Abgrenzung zu den Funktionen aus 0.1.0 in [`docs/behavior-changes.md`](docs/behavior-changes.md). Gegenüber einfachen visuellen Schwärzungswerkzeugen werden zugrundeliegende Textströme, Metadaten und Anhänge unwiderruflich physisch entfernt und vor der Rückgabe unabhängig verifiziert.

## Abhängigkeiten

- Pflicht: `auditcore_common==0.2.1`, Python `>=3.11`
- Optional: `pymupdf>=1.23.8` (Ausführung der PDF-Engine), `Pillow>=10.0` (Bildoperationen), `spacy>=3.8` (KI-Namenserkennung)
- Optional für `auditcore_pdf.web`: `starlette>=0.47.2,<2` und `python-multipart>=0.0.20` (`[web]`), `fastapi>=0.116.1` (`[fastapi]`)
- Bewusst keine Abhängigkeit: kein ORM, keine Datenbank-Treiber; der Kern importiert kein Web-Framework.

## Sicherheit und Datenschutz

Die Bibliothek dient dem Schutz personenbezogener und vertraulicher Daten in Prüfunterlagen. Schwärzungen entfernen Zeichen und Vektoren physisch aus den Seitenobjekten; Metadaten und XMP-Datenströme werden aktiv bereinigt. Eine unabhängige Nachprüfung (`verify_redaction`) stellt sicher, dass keine vertraulichen Begriffe im Ausgabedokument verbleiben. Es erfolgen keinerlei Netzwerkzugriffe. Ein Schwärzungsplan (`Plan.to_dict()`) enthält die gefundenen Texte im Klartext: Er darf nur zwischen Vorschau und Anwendung übertragen, nie protokolliert oder gespeichert werden. Klartext steht auch in `Selection.criteria.terms`, in den Schlüsseln von `ApplyReport.by_source` und als Zeichenanfang in `RedactionVerificationError`; auch diese nicht protokollieren. Dateigröße und Seitenzahl begrenzt die Anwendung; Einzelheiten in [`docs/behavior-changes.md`](docs/behavior-changes.md#was-die-anwendung-selbst-begrenzen-und-schützen-muss). Die Anwendung prüft über SHA-256, dass Plan und Datei zusammengehören, und lehnt eine veraltete Auswahl ab.

## Lizenz und Herkunftsnachweis

Veröffentlicht unter der MIT-Lizenz gemäß [`LICENSE`](LICENSE) und [`NOTICE`](NOTICE).
Dokumentation der Herkunft und Charakterisierung in [`provenance.json`](src/auditcore_pdf/provenance.json).

## Änderungen

Alle Änderungen sind im [Changelog](CHANGELOG.md) verzeichnet.
