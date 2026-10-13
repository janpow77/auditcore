# Changelog @auditcore/sampling-templates-vue

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
