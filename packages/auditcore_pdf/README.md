# auditcore_pdf

## Zweck

Vollständige PDF-Verarbeitung, Seitenoperationen, visuelle Anzeige und nachprüfbare Schwärzung für Prüf- und Kontrollprozesse.

Die Bibliothek stellt Fachanwendungen der Prüfbehörde robuste Funktionen für Dokumentenanalyse, Seitenmanipulationen (Umsortieren, Drehen, Extrahieren, Zusammenführen, Aufteilen) und mehrschichtige Schwärzungen bereit. Nicht enthalten sind Web-Endpunkte, Benutzeroberflächen oder Datenbankbindungen.

> **Lizenzhinweis PyMuPDF (AGPL-3.0):** Das Paket selbst steht unter MIT und
> enthält keinen PyMuPDF-Code. Alle PDF-Funktionen benötigen aber das Extra
> `[pymupdf]`. PyMuPDF steht unter der **GNU AGPL-3.0** oder einer kommerziellen
> Lizenz von Artifex. Wer eine Anwendung mit diesem Extra weitergibt oder über ein
> Netzwerk anbietet, muss die AGPL-3.0 erfüllen oder eine kommerzielle Lizenz
> erwerben. Ohne das Extra lassen sich nur Modelle und Muster importieren.

## Installation

Zuletzt veröffentlicht ist **0.1.0** (Releases v0.6.0 und v0.7.0, Wheel bytegleich).
Die hier beschriebene Version **0.2.0 ist noch nicht veröffentlicht**; sie erscheint
erst mit einem künftigen Release im Paketindex.

Aus dem Paketindex von auditcore (PEP 503, jede Datei mit SHA-256 verlinkt):

```bash
python -m pip install 'auditcore_pdf==0.1.0' \
  --index-url https://janpow77.github.io/auditcore/simple/
```

Hashgebunden in einer `requirements.txt` (Wheel aus Release v0.7.0; weitere
Versionen und Hashes unter `https://janpow77.github.io/auditcore/simple/auditcore-pdf/`):

```text
auditcore_pdf @ https://github.com/janpow77/auditcore/releases/download/v0.7.0/auditcore_pdf-0.1.0-py3-none-any.whl#sha256=e0d100bd6bd90ceac45dcb60b5e7927ece034c25c3ce918eaa56c0d676e37760
```

Der Paketindex und die Release-Datei `requirements-auditcore_pdf.txt` liefern nur
auditcore-Pakete (`--no-index`). PyMuPDF für das Extra `[pymupdf]` kommt aus PyPI,
also vorher oder getrennt installieren:

```bash
python -m pip install 'pymupdf>=1.23.8'
```

Debian/Ubuntu über die signierte APT-Quelle des Releases
([Einrichtung](../../docs/deployment/package-feed.md)):

```bash
sudo apt-get install python3-auditcore-pdf
```

Das Debian-Paket nennt `python3-pymupdf (>= 1.23.8)` nur als *Suggests*. Die
Distributionspakete erfüllen die Mindestversion nicht überall: Ubuntu 24.04 liefert
PyMuPDF 1.23.7 (Paket `python3-fitz`), Debian 12 liefert 1.21.1 (`python3-fitz`);
Debian 13 (`python3-pymupdf` 1.25.4) und Ubuntu 26.04 (1.26.7) genügen. Auf
Ubuntu 24.04 und Debian 12 PyMuPDF daher per pip in eine virtuelle Umgebung
installieren.

Extras: `[pymupdf]` – PDF-Engine über PyMuPDF (AGPL-3.0, siehe oben); `[pillow]` – Bildverarbeitung; `[dev]` – Test- und Prüfwerkzeuge.

## Schnellstart

```python
from auditcore_pdf import (
    DEFAULT_PATTERNS,
    STANDARD_PATTERNS,
    SanitizationPolicy,
)

# Konservative Musterauswahl; breite Muster wie "datum" nur ausdrücklich wählen.
assert set(DEFAULT_PATTERNS) <= set(STANDARD_PATTERNS)
assert "datum" not in DEFAULT_PATTERNS
policy = SanitizationPolicy(scrub_metadata=True, strip_attachments=True)
assert policy.remove_xmp is True and policy.strip_javascript is True
```

Mit installiertem Extra `[pymupdf]`:

```text
redacted, report = redact_document(pdf_bytes, terms=["Mustermann"],
                                   patterns=list(DEFAULT_PATTERNS))
if not report.verified:
    print(report.verification_error)      # Fundstellen und nicht prüfbare Bereiche
print(report.unverifiable_pages)          # Seiten mit Bildinhalt (keine OCR)
```

## API-Überblick

<!-- api-overview:start (generiert: python scripts/docs/api_overview.py --write) -->
Öffentliche Namen aus `auditcore_pdf.__all__` (34):

| Name | Art | Kurzbeschreibung (erste Docstring-Zeile) | Modul |
|---|---|---|---|
| `DEFAULT_IMAGE_COVERAGE_THRESHOLD` | Konstante | Technische Voreinstellung: Ab diesem Bildanteil an der Seitenfläche gilt eine Seite als nicht prüfbar, weil Bildinhalte ohne OCR weder geschwärzt noch nachgeprüft werden. | `models` |
| `DEFAULT_PATTERNS` | Konstante | Konservative Standardauswahl: nur Muster mit eigener Struktur (Ländercode, @-Zeichen, Vorwahl, Kontextwort). | `models` |
| `MAX_PAGES` | Konstante | Maximale Seitenzahl zur Verhinderung von Ressourcen-Überlastung | `engine` |
| `STANDARD_PATTERNS` | Konstante | Vordefinierte Erkennungsmuster für sensible Daten (technische Voreinstellungen, keine Fachregeln). | `models` |
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
| `find_unverifiable_attachments` | Funktion | Namen der Anhänge, deren Inhalt binär oder komprimiert ist (nicht textlich prüfbar). | `sanitize` |
| `find_unverifiable_pages` | Funktion | 1-basierte Seitennummern mit Grund für alle Seiten mit nicht prüfbarem Bildinhalt. | `imagecheck` |
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
| `sanitize_structure` | Funktion | Bereinigt Lesezeichen, Formularfelder, Verknüpfungen, benannte Ziele, Seitenbeschriftungen, Ebenennamen, JavaScript und Alternativtexte. | `structure_clean` |
| `split_document` | Funktion | Teilt ein Dokument in Abschnitte von jeweils höchstens chunk_size Seiten auf. | `operations` |
| `verify_redaction` | Funktion | Prüft ein PDF unabhängig auf das Vorhandensein verbotener Begriffe und Muster. | `verification` |

Öffentliche Module:

| Modul | Kurzbeschreibung |
|---|---|
| `auditcore_pdf.engine` | Sicherer Zugriffspunkt auf das PDF-Backend. |
| `auditcore_pdf.imagecheck` | Erkennung von Seiten, deren Bildinhalt ohne OCR nicht prüfbar ist. |
| `auditcore_pdf.layers` | Optionale Inhalte (Ebenen, OCG): ausgeblendete Ebenen für Suche und Prüfung einblenden. |
| `auditcore_pdf.matching` | Gemeinsame Begriffs- und Mustererkennung für Schwärzung, Bereinigung und Nachprüfung. |
| `auditcore_pdf.models` | Datenmodelle für PDF-Verarbeitung, Seitenoperationen und Schwärzung. |
| `auditcore_pdf.operations` | Seiten- und Dokumentenoperationen für PDF-Dateien. |
| `auditcore_pdf.pdfstrings` | Lesen, Dekodieren und Ersetzen von PDF-Zeichenketten in Objekt- und Inhaltsdaten. |
| `auditcore_pdf.redact` | Vollständige Schwärzungslogik mit Koordinaten-, Begriffs- und Mustererkennung. |
| `auditcore_pdf.sanitize` | Metadaten-, Anhangs- und Anmerkungsbereinigung zur Verhinderung von Datenabflüssen. |
| `auditcore_pdf.structure` | Text außerhalb der Seiteninhalte: Lesezeichen, Formulare, Ziele, Skripte, Alt-Texte. |
| `auditcore_pdf.structure_clean` | Bereinigung der Strukturbereiche: Lesezeichen, Formulare, Ziele, Skripte, Alt-Texte. |
| `auditcore_pdf.verification` | Unabhängige Nachprüfung und Verifikation von Schwärzungsergebnissen. |
| `auditcore_pdf.viewer` | Anzeige-, Lese- und Analysefunktionen für PDF-Dokumente. |
<!-- api-overview:end -->


## Profile und Konfiguration

**Muster.** `STANDARD_PATTERNS` enthält technische Voreinstellungen, keine
Fachregeln. Die konservative Standardauswahl `DEFAULT_PATTERNS` umfasst nur Muster
mit eigener Struktur: `iban`, `email`, `telefon`, `ust_id`, `geburtsdatum`.
Ausdrücklich zu wählen sind die breiten Muster `datum` (jedes TT.MM.JJJJ),
`steuer_id` (jede 11-stellige Zahl ohne führende 0), `kreditkarte` (16 Ziffern),
`ip_adresse` und `aktenzeichen`. Auswahlgründe:

| Muster | Abgrenzung |
|---|---|
| `telefon` | 0 oder +49, Vorwahl, mindestens dreistellige Rufnummer; nicht nach Wortzeichen, Ziffer oder `+` und nicht vor Wortzeichen oder Bindestrich. PDF-Zeitstempel (`D:20261004120000+02'00'`), ISO-Daten, UUIDs, fünfstellige Postleitzahlen und Datumsangaben treffen nicht. |
| `geburtsdatum` | Datum nur nach Kontextwort (geb., geboren, Geburtsdatum, Geburtstag, Geb.-Datum); geschwärzt wird nur das Datum (benannte Gruppe `value`). |
| `datum` | Jedes Datum TT.MM.JJJJ – das frühere Verhalten von `geburtsdatum`. |
| `iban`, `ust_id`, `aktenzeichen` | Großbuchstaben bleiben auch bei unscharfer Suche Pflicht (`(?-i:…)`). |
| `kreditkarte` | Vier Vierergruppen mit einheitlichem Trenner, keine Prüfziffernprüfung. |

Eigene Muster sind `RedactionPattern`-Objekte; eine benannte Gruppe `value`
begrenzt die Schwärzung auf diesen Teil.

**Begriffe.** Begriffe werden über Zeilenumbruch und Silbentrennung am
Zeilenende hinweg gefunden. `whole_word=False` (Standard) schwärzt jedes Wort, das
den Begriff enthält. Das ist bewusst gewählt: Gebeugte Formen und
Zusammensetzungen („Müllers“, „Müllerstraße“) werden erfasst, und es bleiben keine
Wortreste stehen. `whole_word=True` schwärzt nur ganze Wörter; die Nachprüfung in
`redact_document` sucht weiterhin als Teilzeichenfolge und meldet stehen gebliebene
Wortbestandteile. `verify_redaction(whole_word=True)` prüft auf Wortgrenzen.

**Bereinigung (`SanitizationPolicy`).** Sichere Standards: `remove_xmp=True`
entfernt XMP bei jeder Metadatenbereinigung (auch XMP an Seiten und Bildern),
`strip_javascript=True` leert alle Skripte, `redact_hidden_layers=True` blendet
ausgeblendete Ebenen für Suche und Schwärzung ein und danach wieder aus. Die
Schalter `strip_outline`, `strip_form_fields`, `strip_links`,
`strip_named_destinations`, `strip_page_labels` und `strip_alt_texts` entfernen
die jeweilige Struktur vollständig; ohne Schalter werden nur Einträge mit Treffer
entfernt bzw. ersetzt. `redact_document` meldet das in `structure_cleaned`.

**Nicht prüfbare Bereiche.** Eine OCR findet nicht statt. Seiten ohne Textebene,
Seiten mit einem Bildanteil ab `image_coverage_threshold` (technische
Voreinstellung `DEFAULT_IMAGE_COVERAGE_THRESHOLD` = 0,25 der Seitenfläche) und
Seiten, auf denen ein Bild einen Textblock überdeckt, stehen in
`unverifiable_pages`. Binäre oder komprimierte Anhänge, die bei
`strip_attachments=False` erhalten bleiben, stehen in `unverifiable_items`. In
beiden Fällen ist `RedactionReport.verified` `False`; `VerificationResult.clean`
meldet nur Fundstellen, `fully_verified` verlangt zusätzlich, dass alles prüfbar war.

Die Sicherheitsgrenze `MAX_PAGES` (5.000 Seiten) schützt vor Ressourcenerschöpfung
durch überdimensionierte Dokumente.

## Herkunft und Charakterisierung

Hervorgegangen aus den Anforderungen und Untersuchungen in `audit_designer/pdf-editor-app` sowie der Voruntersuchung `docs/reports/pdf-editor-characterization-20260929.json`. Die Tests sichern die Schwachstellen früherer Werkzeuge ab (Klartextreste in Titeln, Anhängen und Kommentaren, fehlende Treffer bei Zeilenumbrüchen) und seit 0.2.0 die beim Einsatz in regulierung gefundenen Restlücken aus Issue #239 mit synthetischen PDFs: Lesezeichen, Formularfelder, Verknüpfungen, benannte Ziele, Seitenbeschriftungen, ausgeblendete Ebenen, Alt-/ActualText, JavaScript, gemischte Seiten, binäre Anhänge und die Präzision der Standardmuster.

## Bewusste Verhaltensabweichungen

Keine Verhaltensabweichungen gegenüber einem Vorgängerpaket, da es sich um eine Neukonzeption als saubere Fachbibliothek handelt. Gegenüber einfachen visuellen Schwärzungswerkzeugen werden zugrundeliegende Textströme, Metadaten und Anhänge unwiderruflich physisch entfernt und vor der Rückgabe unabhängig verifiziert. Änderungen gegenüber 0.1.0 (u. a. `geburtsdatum` nur mit Kontextwort, `verified=False` bei nicht prüfbaren Bereichen, XMP-Entfernung bei jeder Metadatenbereinigung) stehen im [Changelog](CHANGELOG.md).

## Abhängigkeiten

- Pflicht: `auditcore_common==0.2.1`, Python `>=3.11`
- Optional: `pymupdf>=1.23.8` (Ausführung der PDF-Engine; **AGPL-3.0** oder kommerziell), `Pillow>=10.0` (Bildoperationen)
- Ab PyMuPDF mit `TEXT_IGNORE_ACTUALTEXT` werden auch Glyphen unter ActualText geprüft; ältere Versionen melden das in `details["glyphs_under_actualtext_checked"]`.
- Bewusst keine Abhängigkeit: kein Web-Framework (kein FastAPI, Starlette), kein ORM, keine Datenbank-Treiber.

## Sicherheit und Datenschutz

Die Bibliothek dient dem Schutz personenbezogener und vertraulicher Daten in Prüfunterlagen. Schwärzungen entfernen Zeichen und Vektoren physisch aus den Seitenobjekten; Metadaten und XMP-Datenströme werden aktiv bereinigt. Die unabhängige Nachprüfung (`verify_redaction`) durchsucht Seitentext (auch ausgeblendete Ebenen), Anmerkungen, Metadaten, XMP, Anhänge, Lesezeichen, Formularfelder, Verknüpfungen, benannte Ziele, Seitenbeschriftungen, Ebenennamen, Alternativtexte und JavaScript. Grenzen: Text in Bildern und in binären Anhängen wird nur als nicht prüfbar gemeldet; als Vektorgrafik gezeichneter Text, Sichtbarkeitsausdrücke (OCMD) und alternative Ebenenkonfigurationen werden nicht ausgewertet. Es erfolgen keinerlei Netzwerkzugriffe.

## Lizenz und Herkunftsnachweis

Veröffentlicht unter der MIT-Lizenz gemäß [`LICENSE`](LICENSE) und [`NOTICE`](NOTICE).
Das optionale Extra `[pymupdf]` bindet PyMuPDF unter der AGPL-3.0 ein (siehe
Lizenzhinweis unter „Zweck“ und `NOTICE`); es wird nicht mitgeliefert.
Dokumentation der Herkunft und Charakterisierung in [`provenance.json`](src/auditcore_pdf/provenance.json).

## Änderungen

Alle Änderungen sind im [Changelog](CHANGELOG.md) verzeichnet.
