# Changelog @auditcore/sampling-templates-vue

## 0.1.4 – 2026-10-17

- Kernpaket 0.1.4 (freiwillige Eingaben nach Entscheidung des Inhabers).

## 0.1.3 – 2026-10-17

- Eine nicht lesbare Eingabe („abc“) meldet auch in den abhängigen Werten und
  in der Ergebnisspalte „Eingabe ungültig“ statt „Angabe fehlt“.
## 0.1.4 – 2026-10-14

Hinweise der Abnahme des Einbaus (noch nicht veröffentlicht); keine Änderung
am Rechenkern.

- Prop `workspaceMenu` (Standard `true`): Die Anwendung kann das Menü
  „Arbeitsstand“ selbst führen; dafür neue Methoden `runAction(aktion)` und
  `openFile(datei)` mit derselben Rückfrage bei ungesicherten Änderungen.
- Kompakte, klebende Kennzahlenleiste in schmalen Behältern (Hauptgröße,
  Gesamtfehlerquote, obere Fehlergrenze, Ampel); Abstand über
  `--fa-st-sticky-top`. Im Druck ausgeblendet.
- Beispielwerte: Das Feld „Stand“ des Berichts (Blatt 20) trägt das heutige
  Datum statt des festen Datums der Beispielwerte.

## 0.1.3 – 2026-10-14

Oberfläche als Arbeitsassistent statt Blattansicht (noch nicht veröffentlicht);
keine Änderung am Rechenkern.

- Verfahrensauswahl als Filter: Methode, Zahl der Zeiträume und Schichtung
  führen auf genau ein Verfahren, das mit „Verfahren verwenden“ übernommen
  wird. Die Blattkacheln und die Tabelle Zeiträume × Schichtung entfallen; nur
  die Altvorlagen erscheinen weiter als Liste.
- Kurzerklärungen zu MUS, PPS, einfacher Zufallsstichprobe und Startwert.
- Nummerierte Schrittleiste mit Teilschritt „Verfahren wählen › Parameter und
  Ergebnis“; Blattnummern stehen nicht mehr in Kopfzeile und Kapsel.
- Kennzahlenspalte: Hauptgröße, hervorgehobene Kennzahlen als Karten, Skala mit
  Ampel gegen die Wesentlichkeitsschwelle, übrige Kennzahlen kompakt.
- Menü „Arbeitsstand“: „Als JSON sichern“, „Datei einlesen …“, „Zurücksetzen“.
- Tests auf die neue Auswahl umgestellt (Hilfen `pickVariant` bzw. `e2e/pick.ts`).

## 0.1.2 – 2026-10-14

Befunde der Abnahme des Einbaus (noch nicht veröffentlicht).

- Bericht: Tabellen in eigenem Rollrahmen (`role="region"`, per Tastatur
  erreichbar); Druck auf einer A4-Seite für leeres Formular und Beispielwerte,
  auch in Google Chrome (Browsertest mit `page.pdf()` und Seitenzahl).
- Nach der Wahl eines Blatts liegt der Fokus auf dem Blatt.
- Die bloße Wahl eines anderen Blatts gilt nicht als Änderung, solange der
  Arbeitsstand nicht aus einer Datei stammt.
- Der Excel-Export zählt als Sicherung: Er trägt den vollständigen
  Arbeitsstand und lässt sich wieder öffnen; der Stand ist danach „gespeichert“.

## 0.1.1 – 2026-10-13

Auflagen der unabhängigen Gesamtabnahme (noch nicht veröffentlicht).

- Ungesicherte Änderungen für den Routenwächter der Anwendung: Ereignis
  `dirty`, Methode `isDirty()` und der reaktive Wert `dirty` (über `ref`).
- Bericht mit Vorlage, Rechtsstand, Fassung des Rechenkerns und Prüfsumme der
  Eingaben, am Bildschirm und im Druck; der Druck verwendet die benannte Seite
  `fa-st-report`.
- Hinweise in Warnfarbe aus dem Verfahren stehen auch in Blatt 18 und im
  Bericht; eine bestandene Würdigung ist dann nicht uneingeschränkt grün.
- Importvorschau: Hinweise zur Mappe, echte Unterschiede getrennt von
  begründet offenen Zellen, „leer“ für Zellen ohne Wert in der Mappe.
- „Letzte Schicht entfernen“ fragt nach, wenn die Schicht Eingaben trägt.
- Zwischenstand in drei Stufen (`draft`: `off`, `session`, `device`), Slot und
  Ereignis `draft`.
- Fußzeile nennt die Prüfgrundlage (LibreOffice 24.2; Gegenprobe mit Microsoft
  Excel steht aus).

## 0.1.0 – 2026-10-13

Erste Fassung (noch nicht veröffentlicht).

- `SamplingCalculator`: Verfahrensauswahl (Familienliste und Variantentabelle,
  per Tastatur bedienbar, Wegweiser mit dem Wortlaut der Vorlage),
  Arbeitsschritte Grundgesamtheit, Verfahren, Unterstichproben,
  Gesamtfehlerquote und Bericht, Rechenblatt aus der Methodendefinition,
  mitlaufende Ergebnisspalte mit Prüfhinweisen als Text und Farbe, Menü
  „Arbeitsstand“ (Öffnen, Speichern, Neu, Beispielwerte), Excel-Export, Status
  geändert/gespeichert, Schutz beim Verlassen der Seite, Ziehen und Ablegen.
- Alle Verfahren der Vorlage sind wählbar; die Nachschlagetabelle X1a öffnet
  sich als Datentabelle aus der Auswahl und aus dem Verfahren X1.
- Schichttabelle mit eigenem Rollbereich (bis 20 Schichten, Schichtspalten je
  Blatt), Liste der Unterstichproben mit Einfügen aus der Zwischenablage und
  Übernahme der Summen je Schicht und Zeitraum, Vorschau vor der Übernahme
  einer ausgefüllten Vorlage.
- Bericht (Blatt 20) als A4-Seite mit „Drucken / als PDF sichern“; im Druck
  nur die Berichtsseite, einschließlich der Hinweise „Keine Angabe, daher mit
  0 berechnet“ und der Einordnung der Webfassung.
- Verknüpfungen aus Blatt 02 als vorbelegte, überschreibbare Werte;
  überschriebene Werte sind markiert.
- Fehlende Angaben werden benannt; mit 0 berechnete Werte sind als Hinweis der
  Webfassung gekennzeichnet; das leere Formular zeigt „noch keine Angaben“.
  Dateiaktionen melden Fehler sichtbar.
- Einbindung: Props `locale` (de, en), `draft` (`off`, `session`, `device`;
  Standard `off`) mit Slot und Ereignis `draft`, `filePrefix`, `dataMark` und
  Slot `mark`; Methode `loadSample(blatt?)`; Hinweis des Fachrahmens und Stand
  der Vorlage in der Fußzeile.
- Bausteine und Composables einzeln exportiert.
