# Changelog auditcore_reporting

Rekonstruiert aus der Git-Historie (0.2.1: Pull Request #68).

## 0.4.0 – unveröffentlicht

Lücken aus Issue #235 (Umstellung der Fachberichte von regulierung). Alle
Erweiterungen sind abschaltbar und standardmäßig aus: die eingebauten
Vorlagen `vermerk` und `pruefbericht` rendern byte-gleich (Golden-Hashes
unverändert, `tests/test_templates_options.py`).

- Tabellen ohne Zeilen: neuer Schlüssel `"header_if_empty": true` am Block
  `table` zeichnet die Kopfzeile auch ohne Zeilen, danach folgt der Text aus
  `empty`. Standard bleibt `false` (bisher: nur der Leertext), damit
  bestehende Vorlagen unverändert bleiben und ein leerer Tabellenkopf nur dort
  erscheint, wo er fachlich gewollt ist.
- Leere Felder: neuer Schlüssel `"empty"` am Block `fields` (z. B. `"—"`).
  Ist er gesetzt, bleiben Zeilen mit leerem Wert samt Bezeichnung stehen und
  zeigen diesen Text (Platzhalter werden wie überall gegen den Datenvertrag
  geprüft); ohne ihn entfallen sie wie bisher.
- Dokumenteigenschaften: `render(..., options=RenderOptions(author=…,
  title=…, created=…))` setzt in DOCX `dc:creator`, `cp:lastModifiedBy`,
  `dc:title`, `dcterms:created`/`modified` (UTC), im PDF Author, Title,
  CreationDate/ModDate und im HTML `<title>`, `meta author` und
  `meta dcterms.created`. Eine Erstellzeit erscheint nur, wenn der Aufrufer
  sie übergibt (Zeitzone Pflicht) – die Ausgabe bleibt deterministisch.
  Word-Vorlagen (`docx=`) behalten die Eigenschaften ihrer Datei und weisen
  Optionen mit `TemplateError` ab.
- Neues Modul `format_de` mit `format_eur` (auch als
  `auditcore_reporting.format_eur`): Python-Umsetzung des Vertrags
  `format-money` (`contracts/common-cases/format-money.json`) – Komma,
  Tausenderpunkt, geschütztes Leerzeichen U+00A0 vor „€“, kaufmännische
  Rundung (half-up) auf dem Dezimalwert, Ersatzwert „—“ bei leer/ungültig;
  alle Vertragsfälle laufen in `tests/test_format_de.py`. Ziel des Katalogs
  bleibt `auditcore_common.format_de`; die Funktion liegt vorerst hier, weil
  eine neue `auditcore_common`-Version die exakten Pins aller Pakete
  nachziehen müsste. Der Filter `eur` der Vorlagen bleibt unverändert
  (normales Leerzeichen, Golden-Hashes).
- Seitenausrichtung: `DesignProfile.orientation` (`portrait`/`landscape`,
  A4) und Schlüssel `"orientation"` in der Vorlage (geht dem Profil vor; nicht
  bei Word-Vorlagen). DOCX `w:pgSz` mit `w:orient="landscape"`, PDF
  `landscape(A4)`, HTML `@page{size:A4 landscape}`. Gilt für das ganze
  Dokument; ein Wechsel innerhalb des Dokuments ist nicht vorgesehen.
- Tabellen: je Spalte `width` (relative Gewichte, 0 = gleicher Anteil),
  `bold` und `fill` (Farbe `RRGGBB` oder Regeln `[{"if", "color", "bold"}]`
  für einzelne Zellen); je Tabelle `borders` (`grid` Standard, `horizontal`,
  `none`), `header_fill`, `stripe` (jede zweite Zeile) und `row_fill`
  (Zeilenfarbe/Hervorhebung per Bedingung). Vorrang: Zellregel vor Zeilenregel
  vor Streifen. Bedingungen werden beim Anlegen gegen den Datenvertrag geprüft.
  Ohne diese Schlüssel bleibt jede Tabelle byte-gleich.
- Unicode-Schriften im PDF: `PdfFont(name, regular, bold=None)` (TrueType als
  bytes) in `DesignProfile.pdf_fonts`, auswählbar über `pdf_font`. reportlab
  bettet eine Teilmenge ein (deterministisch); damit erscheinen z. B. ☐/☒,
  griechische oder osteuropäische Zeichen. Ohne Schriftdatei bleiben die
  Basis-14-Schriften. Das Paket liefert keine Schriftdateien aus (Lizenz liegt
  bei der Anwendung); `to_dict` zeigt nur Name und SHA-256, `design_from_dict`
  nimmt keine Schriftdateien an. DOCX und HTML nennen weiterhin
  `font_family`.
- Bilder: Block `image` mit `image` (Name eines `ReportImage` aus
  `RenderOptions.images` oder `DesignProfile.images`, Optionen gehen vor)
  oder `source` (Datenpfad mit Base64 bzw. `data:image/png|jpeg;base64,`),
  dazu `width_cm`, `align`, `alt`. Nur PNG/JPEG aus bytes; Format und Größe
  werden aus dem Dateikopf gelesen, keine Pfade, kein Netz. Neue Grenze
  `ResolveLimits.max_image_bytes` (30 MiB je Dokument). DOCX als Medienteil
  (je Inhalt einmal) mit DrawingML, PDF `platypus.Image`, HTML als
  `data:`-URI (CSP erhält `img-src data:` nur bei Bildern).
- Sprungmarken und Links: `"anchor"` an `heading` und `section` (bei
  Wiederholung `anker-2`, `anker-3` …), `"link"` am `paragraph`; Ziele werden
  beim Anlegen geprüft (eindeutig, deklariert, `auto-…` reserviert).
  Inhaltsverzeichnis als Block `toc` (`title`, `levels` 1–3) und
  PDF-Lesezeichen mit `"outline": true` in der Vorlage; Überschriften ohne
  eigene Marke erhalten dann `auto-1`, `auto-2` …. PDF: benannte Ziele,
  Verweise und Inhaltsverzeichnis mit Seitenzahlen (`multiBuild`, Aufbau bis
  die Gesamtseitenzahl stabil ist); DOCX: Textmarken und `w:hyperlink`
  (Inhaltsverzeichnis als verlinkte Zeilen ohne Seitenzahlen, Word-Navigation
  über die Überschriftsformate); HTML: `id`, `<a href>` und `<nav>`.
  Dokumente ohne diese Schlüssel werden wie bisher gebaut.
- Paketstand 0.4.0; `auditcore_dataprotection` 0.5.3 pinnt
  `auditcore_reporting[excel]==0.4.0`.

## 0.3.1 – 2026-10-03

- Neues Modul `auditcore_reporting.templates`: versionierte Berichtsvorlagen
  (`define_template`, `TemplateRegistry`, `builtin_registry`, `render`,
  `resolve`, `DesignProfile`/`design_from_dict`). Datenvertrag als
  JSON-Schema-Teilmenge (nicht unterstützte Schlüsselwörter werden abgewiesen),
  benannte Bedingungen als JSON-Operatoren, Textbausteine mit Bedingung,
  Pflichtkennzeichen und Rechtsgrundlage, Blöcke `heading`, `paragraph`,
  `textblock`, `list`, `table`, `fields`, `pagebreak`, `section` (`if`,
  `for`). Platzhalter `{{ pfad | filter }}` mit deutschen Filtern; alle Pfade
  werden beim Anlegen gegen den Datenvertrag geprüft. Ausgabe DOCX
  (Standardbibliothek, feste ZIP-Zeitstempel), HTML (maskiert, ohne Skripte,
  eigene CSP) und PDF (Extra `pdf`: reportlab ≥ 3.6.12, < 6, BSD, `invariant`);
  gleiche Eingaben ergeben gleiche Bytes (Golden-Hashes in
  `tests/test_templates_render.py`). Word-Vorlagen (DOCX/DOTX) der Anwendung
  mit `{{ … }}`, `{%p … %}` und `{%tr … %}` (Extra `docx`: defusedxml),
  vorher Sicherheitsprüfung des Pakets. Neutrale Vorlagen `vermerk` 1.0.0 und
  `pruefbericht` 1.0.0 als Paketdaten, Gestaltung `neutral-v1`.
- REST `reporting_ui/1`: `GET /templates`, `GET /templates/{id}`,
  `POST /templates/{id}/preview`, `POST /templates/{id}/render`
  (Herkunftskopfzeilen `X-Template-*`, `X-Data-SHA256`); `create_app`,
  `routes`, `create_router` nehmen einen `TemplateCatalogue` der Anwendung.
  Bestehende Endpunkte unverändert.
- Spezifikation: Invarianten I14–I18 (Determinismus, Daten bleiben Text,
  Datenvertrag vor Ausgabe, Textbausteine genau bei Bedingung, Versionen
  unveränderlich) als Hypothesis-Tests in `tests/test_spezifikation_vorlagen.py`;
  I1–I13 unverändert. Debian-„Suggests“ für die neuen Extras in
  `packaging/library-extras.json`. Keine Versionsanhebung.

- Neues Formatprofil `flowlib-v2` (2.0.0, Nachfolger von `flowlib-legacy-v1`,
  Modul `formats_v2`) behebt Befund B1: Wörter statt Teilzeichenketten, der
  Kopf des Kompositums entscheidet (`Stundensatz` → Euro statt Prozent),
  Kennungen (Postleitzahl, Kontonummer, IBAN, Steuernummer, Telefon, `Nr.`,
  `ID` …) erhalten `@` bzw. `0` statt Tausendertrennern, der Werttyp geht dem
  Spaltennamen vor (Datum in „Betrag“ bleibt Datum). `flowlib-legacy-v1` und
  die Voreinstellung von `ReportTable.profile` unverändert; wegen der
  geänderten `profiles.py` neue Implementierungs-/Inhaltshashes im
  Profilregister. Der REST-Katalog listet `flowlib-v2`; die Vorschau zeigt das
  Format für einen typischen Wert des deklarierten Spaltentyps.
- Befund B2 behoben (alle Profile): Gleitkommazahlen, die openpyxl mit 16
  Stellen verändert schreiben würde (`0.1 + 0.2`, größte endliche Zahl),
  werden exakt geschrieben und kommen bitgleich zurück; übrige Zellen
  bytegleich. Invarianten I10–I13 neu, der erwartete Fehlschlag zu B2 ist ein
  normaler Test.

Status „spezifiziert“: fachliche Spezifikation `docs/spezifikation.md` (Zweck,
Verträge, Invarianten, Fehlerfälle, Abgrenzung, bewusste Abweichungen vom
Altverhalten), 9 Invarianten als Hypothesis-Eigenschaftstests
(`tests/test_spezifikation.py`, `hypothesis` im Extra `dev`),
`specification`-Block in `provenance.json`. Legacy-Varianten benannt:
Profil `flowlib-legacy-v1`. Befunde B1 (Format folgt dem Spaltennamen, nicht dem Wert) und B2 (Gleitkommazahlen mit 16 Stellen geschrieben; die größte endliche Zahl kommt als unendlich zurück, erwarteter Fehlschlag `test_i6_befund_b2_groesste_gleitkommazahl`) dokumentiert, Code unverändert. Keine Verhaltensänderung.

## 0.3.0 – 2026-09-26 – Paketstand für Release v0.4.2

- Neue Laufzeitabhängigkeit `auditcore_common==0.2.0` (selbst nur
  Standardbibliothek): `web.ContractError` ist Unterklasse von
  `auditcore_common.rest.ContractError`, die JSON-Objekt-Prüfung nutzt
  `rest.json_object`. Meldungen, Statuscodes und Vertrag unverändert.
- Neues Modul `auditcore_reporting.web` (Extras `web`, `fastapi`): REST-Vertrag
  `reporting_ui/1` für Formatprofile, Vorschau und XLSX-Export übergebener
  Tabellen (`docs/ui/reporting-rest.md`). Formatregeln, Profile und
  `render_workbook` unverändert; Fingerabdrücke gültig.

## 0.2.2 – 2026-09-26 – Paketstand für Release v0.4.1

Keine Verhaltensänderung. README-Installationshinweis auf v0.4.0.

## 0.2.1 – 2026-09-25 – Refaktorierung ohne Verhaltensänderung

Keine fachliche Änderung: alle 88 bestehenden Tests (Flowlib-Goldens für
Zahlenformate und Arbeitsmappen, Profil-Fingerprints, Ressourcengrenzen) laufen
unverändert grün. Die Profile `flowlib-legacy-v1` und `plain-v1` sind
bytegleich; `formats.py`, `profiles.py` und `profile-registry.json` wurden
nicht berührt, damit die Implementierungs-Fingerprints gültig bleiben.

- `_excel._table_columns` in Einzelprüfungen zerlegt (Blattname, Spalten,
  Startzeile, Formate); Reihenfolge, Ausnahmetypen und Meldungen bleiben gleich.
- `_excel._body` in Zellformat, Zellschreiben und Blattabschluss
  (Spaltenbreiten, Fixierung, Autofilter) zerlegt.
- Neue Charakterisierungstests `tests/test_validation_messages.py` (19 Fälle)
  halten jeden Prüfzweig mit Typ, Meldung und Vorrang fest; sie liefen vor der
  Zerlegung gegen den unveränderten Code grün.

Messung mit `auditcore-codegate check --package auditcore_reporting`:

| Messung | 0.2.0 | 0.2.1 |
|---|---|---|
| Funktionen mit McCabe > 10 | 2 | 0 |
| Funktionen > 60 Zeilen | 0 | 0 |
| Module > 400 Zeilen | 0 | 0 |
| `Any`-Verwendungen | 4 | 4 |
| mypy --strict | sauber | sauber |

Keine Umbenennungen öffentlicher Namen. Die `Any` stehen ausschließlich
in `formats.py` und `profiles.py`; beide Dateien sind per SHA-256 im
Profilregister verankert. Eine Verengung auf `object` würde die Fingerprints und
damit die Profilmetadaten ändern und ist deshalb bewusst unterblieben.

## 0.2.0 – 2026-09-22

- Optionaler, validierter XLSX-Export (`render_workbook`, `ReportTable`,
  `ExcelOptions`, `WorkbookLimits`) im Extra `[excel]` (openpyxl, defusedxml);
  fünf Workbook-Fälle am Flowlib-Original charakterisiert; Texte als
  XML-String gegen Formel-Injektion; Schriftreihenfolge in `styles.xml` nach
  Open-XML-SDK-Schema (Commit `05c0d24`).
- Benannte Formatprofile `flowlib-legacy-v1` und `plain-v1` mit
  `get_profile_format` und `get_profile_metadata`.
- `get_number_format` und die 34 beobachteten Fälle unverändert.

## 0.1.0 – 2026-09-22

- Eigenständig installierbare MIT-Bibliothek mit den charakterisierten
  Flowlib-Zahlenformaten `get_number_format` (34 Fälle, Commit `c4cc9e7`).
- Anwendbarkeitskontext für die Paketquelle ergänzt (Commit `ae737e2`).
