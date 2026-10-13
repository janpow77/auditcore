# Changelog @auditcore/sampling-templates-vue

## 0.1.0 – 2026-10-13

Erste Fassung (noch nicht veröffentlicht).

- `SamplingCalculator`: Verfahrensauswahl (Familienliste und Variantentabelle,
  per Tastatur bedienbar, Wegweiser mit dem Wortlaut der Vorlage),
  Arbeitsschritte Grundgesamtheit, Verfahren und Unterstichproben, Rechenblatt
  aus der Methodendefinition, mitlaufende Ergebnisspalte mit Prüfhinweisen als
  Text und Farbe, Menü „Arbeitsstand“ (Öffnen, Speichern, Neu, Beispielwerte),
  Excel-Export, Status geändert/gespeichert, Schutz beim Verlassen der Seite,
  Ziehen und Ablegen.
- Schichttabelle mit eigenem Rollbereich (bis 20 Schichten), Liste der
  Unterstichproben mit Einfügen aus der Zwischenablage und Übernahme der
  Summen, Vorschau vor der Übernahme einer ausgefüllten Vorlage.
- Verknüpfungen aus Blatt 02 als vorbelegte, überschreibbare Werte;
  überschriebene Werte sind markiert.
- Fehlende Angaben werden benannt; mit 0 berechnete Werte sind als Hinweis der
  Webfassung gekennzeichnet. Dateiaktionen melden Fehler sichtbar.
- Einbindung: Props `locale` (de, en), `localDraft` (Standard aus),
  `filePrefix`, `dataMark` und Slot `mark`; Hinweis des Fachrahmens und Stand
  der Vorlage in der Fußzeile.
- Rechenbar sind die Blätter 02, 03, 04 und 17; die übrigen Varianten sind als
  „noch nicht verfügbar“, die Arbeitsschritte Gesamtfehlerquote und Bericht
  als „folgt“ gekennzeichnet.
- Bausteine und Composables einzeln exportiert.
