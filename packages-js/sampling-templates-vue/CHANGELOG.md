# Changelog @auditcore/sampling-templates-vue

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
- Einbindung: Props `locale` (de, en), `localDraft` (Standard aus),
  `filePrefix`, `dataMark` und Slot `mark`; Hinweis des Fachrahmens und Stand
  der Vorlage in der Fußzeile.
- Bausteine und Composables einzeln exportiert.
