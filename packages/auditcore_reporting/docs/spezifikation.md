# Spezifikation auditcore_reporting

Stand: 27.09.2026 (Profil `flowlib-v2`, Befunde B1/B2 behoben), Paketversion 0.3.0. Charakterisierung: 34 Formatfälle
aus flowlib@`aca2dc6` (`tests/test_formats.py`, Fixtures in `tests/fixtures`),
Original-Arbeitsmappen, Wert- und Stil-Rundläufe (`tests/test_excel.py`,
`docs/excel-validation.md`), Profilversionierung in `docs/profiles.md`.
Eigenschaftstests: `tests/test_spezifikation.py`, für die Berichtsvorlagen
`tests/test_spezifikation_vorlagen.py` (I14–I18); Beispiel- und Sicherheitsfälle
der Vorlagen in `tests/test_templates_*.py`.

## Zweck

Zahlenformate für tabellarische Berichte (Spaltenname → Excel-Zahlenformat)
nach benannten, versionierten Formatprofilen und ein abgesicherter
XLSX-Export übergebener Tabellen. Das Paket dient Anwendungen, die
Prüfergebnisse, Verzeichnisse oder Listen als Excel-Datei ausgeben (etwa
`auditcore_dataprotection`). Dazu kommen versionierte Berichtsvorlagen
(`auditcore_reporting.templates`): Datenvertrag als JSON-Schema, bedingte
Textbausteine, Abschnitte und Tabellen, deterministische Ausgabe als DOCX, PDF
und HTML sowie das Befüllen von Word-Vorlagen der Anwendung (Prüfberichte,
Vermerke, Schreiben). Die Gestaltung ist ein austauschbares Profil; das Paket
enthält nur die neutrale Gestaltung `neutral-v1` und die neutralen Vorlagen
`vermerk` und `pruefbericht`.

## Verträge

| Funktion/Klasse | Eingabe | Ausgabe | Nebenwirkungen |
|---|---|---|---|
| `get_number_format(col_name, value=None)` | Spaltenname (Text); `value` wird nicht ausgewertet | eines von `#,##0.00 "EUR"`, `0.00%`, `DD.MM.YYYY`, `#,##0`, `#,##0.00`, `General` | keine |
| `get_profile_format(profile, column, value=None)` | `flowlib-legacy-v1` (Flowlib-Heuristik, `value` unbeachtet), `flowlib-v2` (Wörter statt Teilzeichenketten, Kennungen ohne Zahlenformat, Werttyp vor Spaltenname) oder `plain-v1` (immer `General`) | Formatzeichenkette | keine |
| `PROFILE_IDS` | – | `("flowlib-legacy-v1", "flowlib-v2", "plain-v1")` | – |
| `get_profile_metadata(profile)` | Profilkennung | frische Kopie des Registereintrags (`profile-registry.json`) nach Prüfung von Inhalts- und Implementierungshash | liest Paketdaten |
| `ReportTable(name, columns, rows, start_row=1, profile="flowlib-legacy-v1", formats={})` | Blattname 1–31 Zeichen, eindeutige Spaltennamen, Zeilen als Folge gleicher Breite oder Mapping mit genau den Spaltenschlüsseln; Werte `str`, `int` (≤ 15 Stellen), `float`, `bool`, `date`, `datetime` ohne Zeitzone, `None` | – | Zeilen werden einmal gelesen |
| `render_workbook(tables, options=None)` (Extra `excel`) | eine oder mehrere `ReportTable`, `ExcelOptions` mit `WorkbookLimits` | vollständige XLSX-Datei als Bytes | keine Datei-, Netz- oder Anwendungszugriffe |
| REST `auditcore_reporting.web` (`reporting_ui/1`, Extras `web`/`fastapi`) | JSON-Tabellen, Profilwahl; Vorlagenkennung, Daten, Format, Gestaltung | Katalog, Vorschau, XLSX-Export; Vorlagenliste, Datenvertrag, Vorlagenvorschau, Dokument; Fehler `{"error": {"code", "message"}}` | keine; Vertrag `docs/ui/reporting-rest.md` |
| `templates.define_template(definition, *, docx=None)` | JSON-Definition (`id`, `version` MAJOR.MINOR.PATCH, `title`, `schema`, `conditions`, `text_blocks`, `blocks` oder Word-Datei, `sample`, `status`, `formats`) | unveränderliche `ReportTemplate` mit SHA-256-Fingerabdruck über Definition und Word-Datei | keine; alle Platzhalter, Bedingungen und Schleifen werden gegen das Schema geprüft |
| `templates.render(template, data, output="docx", design=NEUTRAL_DESIGN, limits=None)` | Daten gemäß Datenvertrag; `docx`, `pdf` (Extra `pdf`) oder `html`; `DesignProfile` | `RenderResult`: Bytes, Medientyp, Vorlagenkennung, -version, -fingerabdruck, Datenhash, Gestaltung, verwendete Textbausteine | keine; deterministisch (feste ZIP-Zeitstempel, reportlab `invariant`) |
| `templates.TemplateRegistry`, `builtin_registry()` | Vorlagen | Abruf je Kennung und Version, neueste nicht archivierte Version | eine registrierte Version ist unveränderlich |
| `templates.design_from_dict(data)` / `DesignProfile` | Schriften, Farben (RRGGBB), Ränder, Kopf-/Fußzeilentext | geprüftes Gestaltungsprofil | keine; keine Logos, keine Dateien |

Formatwahl im Profil `flowlib-legacy-v1`: Die erste passende Gruppe gewinnt
(Groß-/Kleinschreibung egal, Teilwortsuche): Betrag (`betrag`, `summe`,
`kosten`, `ausgabe`, `einnahme`, `foerder`, `bewillig`, `auszahl`, `gesamt`,
`netto`, `brutto`, `saldo`) vor Prozent (`quote`, `anteil`, `prozent`, `rate`,
`satz`, `percent`) vor Datum (`datum`, `date`, `von`, `bis`, `beginn`, `ende`,
`stichtag`, `zeitpunkt`) vor Anzahl (`anzahl`, `count`, `nummer`, `nr`, `pos`,
`lfd`) vor Dauer (`stunden`, `tage`, `hours`, `days`); sonst `General`.
Eine Überschreibung in `ReportTable.formats` hat Vorrang vor dem Profil.

Formatwahl im Profil `flowlib-v2` (`auditcore_reporting.formats_v2`, Version
2.0.0, Vorgänger `flowlib-legacy-v1`): Der Spaltenname wird in Wörter aus
Buchstaben zerlegt (Groß-/Kleinschreibung egal, ä/ö/ü/ß gleich ae/oe/ue/ss,
`%` ist ein Wort). Ein Wort trifft einen Begriff, wenn es der Begriff *ist*
oder – bei Kompositumsbegriffen – *auf ihn endet* (der Kopf des Kompositums
trägt die Bedeutung: `Förderbetrag` → Betrag, `Förderquote` → Prozent); der
längste passende Begriff gewinnt (`Stundensatz` → Betrag vor `satz` →
Prozent; `Datensatz`, `Ersatz`, `Montage` → neutral). Kurze Begriffe (`nr`,
`id`, `von`, `bis`, `ende`, `pos`, `lfd`, `netto`, `gesamt` …) zählen nur als
ganzes Wort. Über alle Wörter entscheidet der Rang Kennung vor Datum vor
Prozent vor Betrag vor Anzahl vor Dauer. Kennungen (Postleitzahl, IBAN, BIC,
Konto-, Steuer-, Register-, Beleg- und Hausnummer, Steuer-/USt-ID, Telefon,
Aktenzeichen, `Nr.`, `ID` …) erhalten `@`, bei Zahlenwerten `0` (ohne
Tausendertrenner). Ein übergebener Wert geht dem Namen vor: Datumswerte
erhalten `DD.MM.YYYY`, Text `General` (Kennungen `@`), Wahrheitswerte
`General`, Zahlen nie das Datumsformat. Die REST-Vorschau zeigt das Format für
einen typischen Wert des deklarierten Spaltentyps.

## Invarianten

| Nr. | Invariante | Test |
|---|---|---|
| I1 | Die Formatwahl ist total und deterministisch: jeder Spaltenname ergibt genau eines der sechs Formate; `value` hat keinen Einfluss. | `test_i1_formatwahl_total_und_deterministisch` |
| I2 | Enthält ein Name Stichwörter mehrerer Gruppen, entscheidet die Gruppe mit dem höchsten Rang, unabhängig von der Stellung im Namen. | `test_i2_rangfolge_betrag_prozent_datum_anzahl_dauer` |
| I3 | ASCII-Groß- und Kleinschreibung ändern die Formatwahl nicht. | `test_i3_gross_und_kleinschreibung_ohne_einfluss` |
| I4 | Profile sind ausdrücklich: `plain-v1` liefert immer `General`, `flowlib-legacy-v1` genau die Heuristik, unbekannte Profile werden abgewiesen. | `test_i4_profile_ausdruecklich` |
| I5 | Profilmetadaten gibt es nur bei gültigem Inhalts- und Implementierungshash; jeder Aufruf liefert eine frische, gleiche Kopie. | `test_i5_profilmetadaten_durch_hashes_gebunden` |
| I6 | Übergebene Werte kommen aus der XLSX-Datei unverändert zurück, Gleitkommazahlen im ganzen endlichen Bereich bitgleich (Befund B2 behoben); Texte, auch mit führendem `=`, `+`, `@`, bleiben Text und werden nie Formel. | `test_i6_werte_verlustfrei_texte_nie_als_formel`, `test_i6_groesste_gleitkommazahl_verlustfrei` |
| I7 | Ressourcengrenzen gelten hart: mehr Zeilen als erlaubt ergeben `WorkbookLimitError` und keine Teildatei; bis zur Grenze entsteht eine vollständige Datei. | `test_i7_grenzen_ohne_teilartefakt` |
| I8 | Zeilen, deren Breite oder Schlüssel nicht zu den Spalten passen, werden abgewiesen. | `test_i8_zeilenform_muss_zu_den_spalten_passen` |
| I9 | Das Zellformat ist die ausdrückliche Überschreibung, sonst das Profilformat für Spaltenname und Wert (nur `flowlib-v2` wertet den Wert aus). | `test_i9_zahlenformat_folgt_profil_und_ueberschreibung` |
| I10 | `flowlib-v2`: Spalten mit Kennungen erhalten nie Tausendertrenner, Prozent oder Währung – `@`, bei Zahlen `0`, bei Datumswerten das Datumsformat. | `test_i10_kennungen_nie_mit_zahlenformat` |
| I11 | `flowlib-v2`: Der Werttyp geht dem Spaltennamen vor – Datumswerte erhalten das Datumsformat, Text und Wahrheitswerte kein Zahlenformat, Zahlen nie das Datumsformat. | `test_i11_werttyp_vor_spaltenname` |
| I12 | `flowlib-v2`: In zusammengesetzten Wörtern entscheidet der Kopf (Wortende); kurze Begriffe wirken nur als ganzes Wort. | `test_i12_kopf_des_kompositums_entscheidet`, `test_i12_kurzwoerter_nur_als_ganzes_wort` |
| I13 | `flowlib-v2`: Groß-/Kleinschreibung und Umlautschreibweise (ä/ae, ö/oe, ü/ue, ß/ss) ändern die Formatwahl nicht. | `test_i13_schreibweise_ohne_einfluss` |
| I14 | Vorlagen: gleiche Vorlage, Daten und Gestaltung ergeben bytegleiche DOCX-, HTML- und PDF-Dateien; Datenhash und Fingerabdruck sind stabil. | `test_i14_ausgabe_deterministisch` |
| I15 | Vorlagen: Datenwerte erscheinen wörtlich (HTML maskiert) und werden nie als Platzhalter, Steuer-Tag oder Markup ausgewertet. | `test_i15_daten_bleiben_text` |
| I16 | Vorlagen: Daten, die den Datenvertrag verletzen, ergeben `TemplateDataError` mit allen Pfaden und keine Datei; gültige Daten ergeben immer eine Datei. | `test_i16_datenvertrag_vor_ausgabe` |
| I17 | Vorlagen: Ein Textbaustein erscheint genau dann, wenn seine Bedingung gilt, und wird dann im Ergebnis als verwendet genannt. | `test_i17_textbaustein_genau_bei_bedingung` |
| I18 | Vorlagen: Jede Änderung der Definition ändert den Fingerabdruck; dieselbe Version mit anderem Inhalt wird nicht registriert. | `test_i18_version_unveraenderlich` |

## Fehlerfälle

- `get_profile_format`, `get_profile_metadata`: `ValueError` bei unbekanntem
  Profil oder veränderten Profil-/Implementierungshashes; `TypeError`, wenn
  der Spaltenname kein Text ist (Profile `flowlib-legacy-v1`, `flowlib-v2`).
- `render_workbook`: `ExcelDependencyError` ohne Extra `excel`;
  `WorkbookLimitError` bei Überschreiten von Zeilen-, Spalten-, Blatt-,
  Zellen-, Text- oder Ausgabegrenzen und bei XLSX-Formatgrenzen (Zelltext
  > 32 767 Zeichen, Startzeile außerhalb 1..1 048 576); `ValueError` bei
  ungültigem oder doppeltem Blattnamen, leeren oder doppelten Spaltennamen,
  falscher Zeilenform, unbekanntem Profil, Überschreibung für unbekannte
  Spalte, XML-1.0-fremden Zeichen, ganzen Zahlen über 15 Stellen,
  unendlichen Zahlen, Zeitstempeln mit Zeitzone, ungültigen Optionen, ohne
  Tabelle; `TypeError` bei nicht unterstützten Werttypen oder Optionen.
- NaN wird als leere Zelle geschrieben.
- Vorlagen: `TemplateError` bei ungültiger Definition (unbekannte Felder oder
  Schlüsselwörter des Schemas, nicht deklarierte Datenpfade, unbekannte Filter,
  Operatoren oder Textbausteine, nicht verwendeter Pflichtbaustein, zyklische
  Bedingungen, ungültige Steuer-Tags, Beispieldaten außerhalb des Vertrags);
  `TemplateDataError` (mit `issues`) bei Daten außerhalb des Vertrags;
  `UnsafeDocumentError` bei Word-Dateien mit Makros, ActiveX, OLE-Objekten,
  `altChunk`, externen Quellen außer Hyperlinks, nachladenden Feldern
  (`INCLUDETEXT`, `DDE` …), DTDs, unsicheren Eintragsnamen oder ZIP-Bomben;
  `RenderLimitError` bei Überschreiten von Knoten-, Zeichen- oder
  Schleifengrenzen; `RenderDependencyError` ohne Extra `pdf` bzw. `docx`.

## Abgrenzung

- Keine Diagramme und Bilder in Vorlagen; Logos und Briefköpfe stehen in der
  Word-Vorlage der Anwendung, nicht im Paket.
- Keine behördenspezifische Gestaltung: nur das neutrale Profil `neutral-v1`;
  Hausgestaltungen sind Profile oder Word-Vorlagen der Anwendung.
- Keine Umwandlung DOCX → PDF (kein LibreOffice); PDF entsteht aus derselben
  aufgelösten Struktur wie DOCX und HTML, Word-Vorlagen liefern nur DOCX.
- Keine Ausdruckssprache: Platzhalter sind Datenpfade mit festen Filtern,
  Bedingungen JSON-Operatoren; kein Jinja, kein `eval`.
- Kein Lesen vorhandener Arbeitsmappen, keine Formeln, keine Hyperlinks.
- Keine Umrechnung von Werten (Währung, Zeitzone, Rundung); der Aufrufer
  übergibt fertige Werte und wählt das Profil.
- Keine Speicherung von Exportnachweisen; Profilreferenz, Ein- und
  Ausgabehash legt die Anwendung in ihrem Laufnachweis ab (`docs/profiles.md`).
- Authentisierung und Berechtigung auf exportierte Daten liegen bei der
  Anwendung (REST-Schicht).

## Bewusste Abweichungen vom Altverhalten

Das Profil `flowlib-legacy-v1` ist die Legacy-Variante: Es führt die
Flowlib-Heuristik unverändert weiter (34 charakterisierte Fälle), einschließlich
ihrer Schwächen. Neue Aufrufer wählen `flowlib-v2` (Nachfolger mit
korrigierter Formatwahl) oder `plain-v1` und setzen Formate je Spalte
ausdrücklich über `ReportTable.formats`. Die Voreinstellung von
`ReportTable.profile` bleibt `flowlib-legacy-v1`, damit bestehende Aufrufer
unverändert exportieren.

| Altverhalten (bleibt in `flowlib-legacy-v1`) | Gewolltes Verhalten | Legacy-Variante | Nachweis |
|---|---|---|---|
| Teilwortsuche ohne Wortgrenzen: `Postleitzahl`, `Kontonummer`, `Personalnummer` → `#,##0` (Tausendertrenner in Kennungen); `Stundensatz`, `Grundsatz` → `0.00%`; `Kalenderwoche` → Datum; `Ausgabedatum`, `Gesamtstunden` → Euro | `flowlib-v2`: Kennungen `@`/`0`, Kopf des Kompositums entscheidet (`Stundensatz` → Euro, `Ausgabedatum` → Datum, `Gesamtstunden` → Dauer) | `flowlib-legacy-v1` | I2, I4, I10, I12 |
| Das Format folgt dem Spaltennamen, nicht dem Wert (Befund B1): ein Datum in einer Spalte „Betrag“ erscheint als Zahl mit „EUR“, eine Zahl in einer Spalte „Datum“ als Datum | `flowlib-v2`: Werttyp vor Spaltenname; mit `plain-v1` behalten Datumswerte ihr Datumsformat | `flowlib-legacy-v1` | I9, I11 |
| `value` wird übergeben, aber nicht ausgewertet | unverändert (Kompatibilitätsparameter) | `flowlib-legacy-v1` | I1 |
| Flowlib übernahm formelähnliche Texte (führendes `=`) als ausführbare Formel (`docs/excel-validation.md`) | Texte immer als Text, XML-fremde Zeichen abgewiesen, harte Ressourcengrenzen | – | I6, I7 |

Befund B2 (behoben, alle Profile): openpyxl 3.1 schreibt Gleitkommazahlen mit
16 signifikanten Stellen (`%.16g`). Die letzte Stelle konnte abweichen
(`0.1 + 0.2` → `0.3`, 1,3510798882109862e16 → 1,351079888210986e16), und die
größte endliche Zahl 1,7976931348623157e308 kam als unendlich zurück. Der
Export schreibt jetzt für jede Zahl, die `%.16g` verändern würde, die kürzeste
exakte Darstellung (`repr`, höchstens 17 Stellen) in die Zelle; alle übrigen
Zellen und damit die charakterisierten Arbeitsmappen bleiben bytegleich. Das
ist nicht profilgebunden, weil es keine Formatregel, sondern die Treue der
übergebenen Werte betrifft. Ganze Zahlen über 15 Stellen werden weiterhin mit
`ValueError` abgewiesen (Excel-Genauigkeit); Aufrufer übergeben sie als Text.
