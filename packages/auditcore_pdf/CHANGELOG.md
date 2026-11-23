# Changelog – auditcore_pdf

Alle wesentlichen Änderungen dieses Pakets werden in dieser Datei dokumentiert.

## 0.2.0 (2026-11-23)

### Neu
- Unterpaket `auditcore_pdf.redaction`: zweistufige Schwärzung mit Vorschau. `build_plan` liefert einen `Plan` mit Fundstellen (Seite, Rechtecke, Quelle, Fundort) samt Seitengeometrie; `apply_plan` schwärzt genau die bestätigte `Selection` und prüft das Ergebnis fail-closed nach (`RedactionVerificationError`). `redact_all` schwärzt ohne Vorschau.
- Muster mit Prüfziffer (IBAN mod 97, Steuer-ID, Kreditkarte nach Luhn) und Plausibilitätsprüfung (Telefon, Datum, IP-Adresse, Aktenzeichen mit Sperrliste); Begriffe mit Trennstrich, Silbentrennung und unsichtbaren Zeichen.
- Versteckte Ablagen: Metadaten, XMP, Lesezeichen, Kommentare, Verknüpfungen, Formularfelder, Anhänge, Alternativ- und ActualText, XFA; ausgeblendete Ebenen und Inhalte außerhalb der CropBox werden mitgeprüft.
- Bereinigung (`sanitize`): Metadaten, XMP, Anhänge, JavaScript, Anwendungsdaten; nachgeprüft werden davon Metadaten, XMP und Anhänge.
- Nachprüfung der ausgewählten Fundstellen im Seitentext und im Rohinhalt aller entpackten Objekte, wortgenau außerhalb der Inhaltsströme.
- KI-Namenserkennung über eine austauschbare Funktion (`NerFn`) mit Adapter `spacy_ner` für spaCy (Extra `[ner]`); Nachsuche belegter Namen mit Grenze `max(10, 4 × verschiedene direkte Fundtexte)`; ohne Grenze bei Satz, Listenform und vollständiger Bestätigung im Mustersatz, Untergrenze 50 bei Belegen über Zellgrenzen und teilweiser Bestätigung; über der Grenze bleiben Fundstellen mit Anrede oder Titel.
- Veraltete Auswahl wird abgelehnt (`RedactionStaleError`): SHA-256 der Datei und Kennungen der Fundstellen müssen passen.
- `engine.require_engine` als öffentliche Prüfung auf die PDF-Engine.

### Herkunft
- Übernommen aus pdf-editor@c5b3e1d (`backend/app/services/redaction.py`) unter MIT, Freigabe des Rechteinhabers vom 23.11.2026; Verhalten unverändert (lokal nachgewiesen am 23.11.2026), siehe `docs/behavior-changes.md` mit den Grenzen, die die Anwendung selbst setzen muss.

## 0.1.0 (2026-10-01)

### Neu
- Erstveröffentlichung von `auditcore_pdf` als eigenständige Fachbibliothek im auditcore-Monorepo.
- Dokumentenanalyse: `get_document_info`, `PageInfo`, Texterkennung, Erkennung gescannter Seiten ohne Textebene.
- Seiten- und Dokumentenoperationen: `reorder_pages`, `rotate_pages`, `delete_pages`, `extract_pages`, `merge_documents`, `split_document`.
- Visuelle Seitendarstellung: `render_page`, `extract_page_text`.
- Vollständige Schwärzung (Redaction): Koordinaten-Schwärzung, Begriffs-Schwärzung, zeilenübergreifende Phrasenschwärzung, Standard-RegEx-Muster (`STANDARD_PATTERNS` für IBAN, E-Mail, Telefon, Steuer-ID, USt-ID, Kreditkarte, Geburtsdatum, IP-Adresse, Aktenzeichen).
- Mehrschichtige Bereinigung (Sanitization): Metadatenbereinigung (Standard- und XMP-Metadaten), Anhangsbereinigung (EmbeddedFiles) und Anmerkungsbereinigung (Sticky Notes, Kommentare, Hervorhebungen).
- Nachprüfung (Verification): Unabhängige Extraktionsprüfung `verify_redaction` zur Sicherstellung der vollständigen Entfernung vertraulicher Angaben.
