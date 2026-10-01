# Changelog – auditcore_pdf

Alle wesentlichen Änderungen dieses Pakets werden in dieser Datei dokumentiert.

## 0.1.0 (2026-10-01)

### Neu
- Erstveröffentlichung von `auditcore_pdf` als eigenständige Fachbibliothek im auditcore-Monorepo.
- Dokumentenanalyse: `get_document_info`, `PageInfo`, Texterkennung, Erkennung gescannter Seiten ohne Textebene.
- Seiten- und Dokumentenoperationen: `reorder_pages`, `rotate_pages`, `delete_pages`, `extract_pages`, `merge_documents`, `split_document`.
- Visuelle Seitendarstellung: `render_page`, `extract_page_text`.
- Vollständige Schwärzung (Redaction): Koordinaten-Schwärzung, Begriffs-Schwärzung, zeilenübergreifende Phrasenschwärzung, Standard-RegEx-Muster (`STANDARD_PATTERNS` für IBAN, E-Mail, Telefon, Steuer-ID, USt-ID, Kreditkarte, Geburtsdatum, IP-Adresse, Aktenzeichen).
- Mehrschichtige Bereinigung (Sanitization): Metadatenbereinigung (Standard- und XMP-Metadaten), Anhangsbereinigung (EmbeddedFiles) und Anmerkungsbereinigung (Sticky Notes, Kommentare, Hervorhebungen).
- Nachprüfung (Verification): Unabhängige Extraktionsprüfung `verify_redaction` zur Sicherstellung der vollständigen Entfernung vertraulicher Angaben.
