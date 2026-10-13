# Changelog @auditcore/sampling-templates-core

## 0.1.0 – 2026-10-13

Erste Fassung (noch nicht veröffentlicht).

- Excel-Semantik (`excel`): Vergleiche `eq`/`ne`/`lt`/`le`/`gt`/`ge`,
  `minus`/`plus` und `roundUp` nach dem an LibreOffice 24.2 gemessenen
  Verhalten (Messwerte als Testdaten), `guard`, `ifError`, `required`, `n`,
  Bereichs- und Textfunktionen. Rohe Vergleiche sind in `src/sheets` per
  Lint-Regel gesperrt.
- Rechenkerne und handgeprüfte Methodendefinitionen für die Blätter
  `02_Grundgesamtheit`, `03_MUS_1Z`, `04_MUS_1Z_S` und `17_Unterstichprobe`;
  Blatt 01 als Daten; alle übrigen Blätter als geplant im Register.
- Kontextfluss: Verknüpfungen aus Blatt 02 als vorbelegte, überschreibbare
  Werte; `computeWorkspace` rechnet die Blätter in Registerreihenfolge.
- Schichtzeilen (Spalten D–J der Vorlage, 8. bis 20. Schicht als Erweiterung
  der Webfassung) und Listenblatt mit Übernahme der Summen in das
  Methodenblatt.
- Fehlende Angaben: „Angabe fehlt“ mit Nennung der fehlenden Eingabe; bei
  fehlender Standardabweichung der Stichprobe Rechnung mit 0 wie in der
  Vorlage und Kennzeichnung der betroffenen Werte (`zeroAssumed`).
- Katalog der Verfahrensfamilien nach Blatt 00, Wegweiser mit dem Wortlaut
  der Vorlage.
- Arbeitsstand `flowaudit-stichprobe` Fassung 1: speichern, öffnen, Prüfsumme
  SHA-256, Migrationsgerüst, strenge Prüfung, JSON-Schema, Hinweise der
  Webfassung als eigenes Feld.
- Excel-Austausch als getrennter Einstieg `./xlsx`: Export mit `_Arbeitsstand`,
  Import des Exports und der ausgefüllten Vorlage mit Rückmeldung jedes nicht
  oder umgedeutet übernommenen Werts und Vergleich mit den Rechenwerten der
  Datei; Leser mit Größen-, Zellen- und Zeitgrenzen.
- Sprache: Texte der Oberfläche deutsch und englisch; englische
  Arbeitsübersetzung der Vorlagentexte für die Blätter 01–03.
- Hinweis des Fachrahmens und Stand der Vorlage (`disclaimer`,
  `templateStatus`) in Oberfläche und Export; Dateinamen mit wählbarem Vorsatz.
- Golden-Abgleich: 262 Fälle, 11.313 Zellen, 0 unbegründete Abweichungen
  (Blatt 02: 21 Fälle, 03: 198, 04: 27, 17: 16).
