# Spezifikation auditcore_reporting

Stand: 26.09.2026, Paketversion 0.3.0. Charakterisierung: 34 Formatfälle
aus flowlib@`aca2dc6` (`tests/test_formats.py`, Fixtures in `tests/fixtures`),
Original-Arbeitsmappen, Wert- und Stil-Rundläufe (`tests/test_excel.py`,
`docs/excel-validation.md`), Profilversionierung in `docs/profiles.md`.
Eigenschaftstests: `tests/test_spezifikation.py`.

## Zweck

Zahlenformate für tabellarische Berichte (Spaltenname → Excel-Zahlenformat)
nach benannten, versionierten Formatprofilen und ein abgesicherter
XLSX-Export übergebener Tabellen. Das Paket dient Anwendungen, die
Prüfergebnisse, Verzeichnisse oder Listen als Excel-Datei ausgeben (etwa
`auditcore_dataprotection`). Es enthält keine Berichtsvorlagen, Textbausteine
oder PDF-Ausgabe.

## Verträge

| Funktion/Klasse | Eingabe | Ausgabe | Nebenwirkungen |
|---|---|---|---|
| `get_number_format(col_name, value=None)` | Spaltenname (Text); `value` wird nicht ausgewertet | eines von `#,##0.00 "EUR"`, `0.00%`, `DD.MM.YYYY`, `#,##0`, `#,##0.00`, `General` | keine |
| `get_profile_format(profile, column, value=None)` | `flowlib-legacy-v1` (Flowlib-Heuristik) oder `plain-v1` (immer `General`) | Formatzeichenkette | keine |
| `PROFILE_IDS` | – | `("flowlib-legacy-v1", "plain-v1")` | – |
| `get_profile_metadata(profile)` | Profilkennung | frische Kopie des Registereintrags (`profile-registry.json`) nach Prüfung von Inhalts- und Implementierungshash | liest Paketdaten |
| `ReportTable(name, columns, rows, start_row=1, profile="flowlib-legacy-v1", formats={})` | Blattname 1–31 Zeichen, eindeutige Spaltennamen, Zeilen als Folge gleicher Breite oder Mapping mit genau den Spaltenschlüsseln; Werte `str`, `int` (≤ 15 Stellen), `float`, `bool`, `date`, `datetime` ohne Zeitzone, `None` | – | Zeilen werden einmal gelesen |
| `render_workbook(tables, options=None)` (Extra `excel`) | eine oder mehrere `ReportTable`, `ExcelOptions` mit `WorkbookLimits` | vollständige XLSX-Datei als Bytes | keine Datei-, Netz- oder Anwendungszugriffe |
| REST `auditcore_reporting.web` (`reporting_ui/1`, Extras `web`/`fastapi`) | JSON-Tabellen, Profilwahl | Katalog, Vorschau, XLSX-Export; Fehler `{"error": {"code", "message"}}` | keine; Vertrag `docs/ui/reporting-rest.md` |

Formatwahl im Profil `flowlib-legacy-v1`: Die erste passende Gruppe gewinnt
(Groß-/Kleinschreibung egal, Teilwortsuche): Betrag (`betrag`, `summe`,
`kosten`, `ausgabe`, `einnahme`, `foerder`, `bewillig`, `auszahl`, `gesamt`,
`netto`, `brutto`, `saldo`) vor Prozent (`quote`, `anteil`, `prozent`, `rate`,
`satz`, `percent`) vor Datum (`datum`, `date`, `von`, `bis`, `beginn`, `ende`,
`stichtag`, `zeitpunkt`) vor Anzahl (`anzahl`, `count`, `nummer`, `nr`, `pos`,
`lfd`) vor Dauer (`stunden`, `tage`, `hours`, `days`); sonst `General`.
Eine Überschreibung in `ReportTable.formats` hat Vorrang vor dem Profil.

## Invarianten

| Nr. | Invariante | Test |
|---|---|---|
| I1 | Die Formatwahl ist total und deterministisch: jeder Spaltenname ergibt genau eines der sechs Formate; `value` hat keinen Einfluss. | `test_i1_formatwahl_total_und_deterministisch` |
| I2 | Enthält ein Name Stichwörter mehrerer Gruppen, entscheidet die Gruppe mit dem höchsten Rang, unabhängig von der Stellung im Namen. | `test_i2_rangfolge_betrag_prozent_datum_anzahl_dauer` |
| I3 | ASCII-Groß- und Kleinschreibung ändern die Formatwahl nicht. | `test_i3_gross_und_kleinschreibung_ohne_einfluss` |
| I4 | Profile sind ausdrücklich: `plain-v1` liefert immer `General`, `flowlib-legacy-v1` genau die Heuristik, unbekannte Profile werden abgewiesen. | `test_i4_profile_ausdruecklich` |
| I5 | Profilmetadaten gibt es nur bei gültigem Inhalts- und Implementierungshash; jeder Aufruf liefert eine frische, gleiche Kopie. | `test_i5_profilmetadaten_durch_hashes_gebunden` |
| I6 | Übergebene Werte kommen aus der XLSX-Datei unverändert zurück (Gleitkommazahlen bis ±1e308 relativ ≤ 1e-15, Befund B2); Texte, auch mit führendem `=`, `+`, `@`, bleiben Text und werden nie Formel. | `test_i6_werte_verlustfrei_texte_nie_als_formel` |
| I7 | Ressourcengrenzen gelten hart: mehr Zeilen als erlaubt ergeben `WorkbookLimitError` und keine Teildatei; bis zur Grenze entsteht eine vollständige Datei. | `test_i7_grenzen_ohne_teilartefakt` |
| I8 | Zeilen, deren Breite oder Schlüssel nicht zu den Spalten passen, werden abgewiesen. | `test_i8_zeilenform_muss_zu_den_spalten_passen` |
| I9 | Das Zellformat ist die ausdrückliche Überschreibung, sonst das Profilformat des Spaltennamens (nicht des Werts). | `test_i9_zahlenformat_folgt_profil_und_ueberschreibung` |

## Fehlerfälle

- `get_profile_format`, `get_profile_metadata`: `ValueError` bei unbekanntem
  Profil oder veränderten Profil-/Implementierungshashes; `TypeError`, wenn
  der Spaltenname kein Text ist (Flowlib-Profil).
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

## Abgrenzung

- Keine Berichtsvorlagen, keine Textbausteine, keine Diagramme, kein PDF.
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
ihrer Schwächen. Neue Aufrufer wählen `plain-v1` und setzen Formate je Spalte
ausdrücklich über `ReportTable.formats`.

| Altverhalten (bleibt in `flowlib-legacy-v1`) | Gewolltes Verhalten | Legacy-Variante | Nachweis |
|---|---|---|---|
| Teilwortsuche ohne Wortgrenzen: `Postleitzahl`, `Kontonummer`, `Personalnummer` → `#,##0` (Tausendertrenner in Kennungen); `Stundensatz`, `Grundsatz` → `0.00%`; `Kalenderwoche` → Datum; `Ausgabedatum`, `Gesamtstunden` → Euro | `plain-v1` plus ausdrückliche Formate je Spalte | `flowlib-legacy-v1` | I2, I4 |
| Das Format folgt dem Spaltennamen, nicht dem Wert (Befund B1): ein Datum in einer Spalte „Betrag“ erscheint als Zahl mit „EUR“, eine Zahl in einer Spalte „Datum“ als Datum | wie Altverhalten im Legacy-Profil; mit `plain-v1` behalten Datumswerte ihr Datumsformat | `flowlib-legacy-v1` | I9 |
| `value` wird übergeben, aber nicht ausgewertet | unverändert (Kompatibilitätsparameter) | `flowlib-legacy-v1` | I1 |
| Flowlib übernahm formelähnliche Texte (führendes `=`) als ausführbare Formel (`docs/excel-validation.md`) | Texte immer als Text, XML-fremde Zeichen abgewiesen, harte Ressourcengrenzen | – | I6, I7 |

Befund B2: Gleitkommazahlen kommen nicht immer bitgleich zurück. Der Adapter
(openpyxl 3.1) schreibt 16 signifikante Stellen; die letzte Stelle kann
abweichen (beobachtet: 1,3510798882109862e16 → 1,351079888210986e16, relativ
≤ 1e-15). An der Obergrenze läuft die Darstellung über: die größte endliche
Zahl 1,7976931348623157e308 wird als 1,797693134862316e+308 geschrieben und
als unendlich gelesen, obwohl unendliche Werte als Eingabe abgewiesen werden
(`test_i6_befund_b2_groesste_gleitkommazahl`, erwarteter Fehlschlag). Ganze
Zahlen über 15 Stellen werden dagegen mit `ValueError` abgewiesen. Das ist
dokumentiert und nicht geändert; Aufrufer mit exakten langen Dezimalzahlen
übergeben Text.
