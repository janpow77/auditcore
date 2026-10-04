# Changelog – auditcore_pdf

Alle wesentlichen Änderungen dieses Pakets werden in dieser Datei dokumentiert.

## 0.2.0 (2026-10-04) – Restlücken der Schwärzungsprüfung (noch nicht veröffentlicht)

Behebt die beim Einsatz in regulierung (janpow77/regulierung#32) gefundenen Lücken
aus Issue #239. Alle Prüfungen sind mit synthetischen PDFs abgesichert.

### Neu
- `verify_redaction` prüft zusätzlich Lesezeichen, Formularfelder (Name, Wert,
  Tooltip, Auswahlwerte), Verknüpfungen (URI), benannte Ziele,
  Seitenbeschriftungen, Ebenennamen, Alternativtexte, ActualText und
  Abkürzungsauflösungen (Strukturbaum und Inhaltsströme), JavaScript (auch als
  Strom und in OpenAction) sowie XMP-Ströme an Seiten und Objekten. Text auf
  ausgeblendeten Ebenen und Glyphen unter ActualText werden mitgeprüft.
- `sanitize_structure` und neue Schalter in `SanitizationPolicy`:
  `strip_outline`, `strip_form_fields`, `strip_links`,
  `strip_named_destinations`, `strip_page_labels`, `strip_alt_texts` (Standard
  `False`: nur Einträge mit Treffer), `strip_javascript` (Standard `True`),
  `redact_hidden_layers` (Standard `True`), `remove_xmp` (Standard `True`),
  `image_coverage_threshold`. `RedactionReport.structure_cleaned` nennt die
  bereinigten Bereiche.
- Nicht prüfbare Bereiche: `find_unverifiable_pages` meldet Seiten ohne
  Textebene, mit Bildanteil ab Schwelle (`DEFAULT_IMAGE_COVERAGE_THRESHOLD` = 0,25,
  technische Voreinstellung) oder mit Bild über Textblock;
  `find_unverifiable_attachments` meldet binäre oder komprimierte Anhänge.
  Neue Felder `RedactionReport.unverifiable_pages`/`unverifiable_items` und
  `VerificationResult.unverifiable`/`unverifiable_pages`/`fully_verified`.
  Keine OCR.
- Begriffe werden über Zeilenumbruch und Silbentrennung am Zeilenende gefunden
  (Schwärzung und Nachprüfung). `verify_redaction(whole_word=...)`; Wortgrenzen
  als „kein Wortzeichen davor/danach“ statt `\b` (funktioniert auch für „Dr.“).
- `DEFAULT_PATTERNS`: konservative Musterauswahl (`iban`, `email`, `telefon`,
  `ust_id`, `geburtsdatum`). Neues Muster `datum` für jedes TT.MM.JJJJ.
  Muster mit benannter Gruppe `value` schwärzen nur diese Gruppe.

### Geändert (Verhalten)
- `geburtsdatum` trifft nur noch nach Kontextwort (geb., geboren, Geburtsdatum,
  Geburtstag, Geb.-Datum) und schwärzt nur das Datum; das bisherige Verhalten
  bietet `datum`.
- `telefon` trifft nicht mehr innerhalb längerer Ziffern- oder Wortfolgen;
  PDF-Zeitstempel in den Metadaten lösen das Muster nicht mehr aus.
  `steuer_id`, `kreditkarte`, `ip_adresse`, `iban`, `ust_id` und `aktenzeichen`
  sind enger gefasst (siehe README, „Profile und Konfiguration“).
- `RedactionReport.verified` ist `False`, wenn Seiten oder Anhänge nicht prüfbar
  sind; `verification_error` nennt sie mit „nicht prüfbar: …“.
- Bei Metadatenbereinigung wird XMP immer entfernt (`remove_xmp=True`), nicht
  nur bei Treffer; `remove_xmp=False` stellt das alte Verhalten her. Geprüft und
  bereinigt werden alle schreibbaren Metadatenfelder einschließlich Erstell- und
  Änderungsdatum.
- JavaScript wird standardmäßig geleert (`strip_javascript=True`).
- Ausgeblendete Ebenen werden für Suche und Schwärzung eingeblendet; die
  ursprüngliche Sichtbarkeit bleibt im Ergebnis erhalten.
- Standardmusternamen werden auch in `verify_redaction(patterns=...)` aufgelöst.

### Dokumentation und Verteilung
- README: veröffentlichte Version 0.1.0 mit echtem Wheel-Hash aus Release v0.7.0,
  Pin `auditcore_common==0.2.1`, deutlicher AGPL-Hinweis zu PyMuPDF, APT-Lage
  (Ubuntu 24.04: 1.23.7, Debian 12: 1.21.1 unter der Mindestversion 1.23.8).
- `NOTICE` nennt die AGPL-3.0 des optionalen Extras.
- `packaging/library-extras.json`: Debian-*Suggests* `python3-pymupdf (>= 1.23.8)`
  für das Extra `[pymupdf]` (`library-runtime.json` gilt nur für
  Pflichtabhängigkeiten).

## 0.1.0 (2026-10-01)

### Neu
- Erstveröffentlichung von `auditcore_pdf` als eigenständige Fachbibliothek im auditcore-Monorepo.
- Dokumentenanalyse: `get_document_info`, `PageInfo`, Texterkennung, Erkennung gescannter Seiten ohne Textebene.
- Seiten- und Dokumentenoperationen: `reorder_pages`, `rotate_pages`, `delete_pages`, `extract_pages`, `merge_documents`, `split_document`.
- Visuelle Seitendarstellung: `render_page`, `extract_page_text`.
- Vollständige Schwärzung (Redaction): Koordinaten-Schwärzung, Begriffs-Schwärzung, zeilenübergreifende Phrasenschwärzung, Standard-RegEx-Muster (`STANDARD_PATTERNS` für IBAN, E-Mail, Telefon, Steuer-ID, USt-ID, Kreditkarte, Geburtsdatum, IP-Adresse, Aktenzeichen).
- Mehrschichtige Bereinigung (Sanitization): Metadatenbereinigung (Standard- und XMP-Metadaten), Anhangsbereinigung (EmbeddedFiles) und Anmerkungsbereinigung (Sticky Notes, Kommentare, Hervorhebungen).
- Nachprüfung (Verification): Unabhängige Extraktionsprüfung `verify_redaction` zur Sicherstellung der vollständigen Entfernung vertraulicher Angaben.
