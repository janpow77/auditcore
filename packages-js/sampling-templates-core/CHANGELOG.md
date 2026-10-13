# Changelog @auditcore/sampling-templates-core

## 0.1.0 – 2026-10-13

Erste Fassung (noch nicht veröffentlicht).

- Excel-Semantik (`excel`): Vergleiche `eq`/`ne`/`lt`/`le`/`gt`/`ge`,
  `minus`/`plus` und `roundUp` nach dem an LibreOffice 24.2 gemessenen
  Verhalten (Messwerte als Testdaten), `guard`, `ifError`, `required`, `n`,
  Bereichs- und Textfunktionen. Rohe Vergleiche sind in `src/sheets` per
  Lint-Regel gesperrt.
- Rechenkerne und handgeprüfte Methodendefinitionen für alle Blätter der
  Vorlage: 02 (Grundgesamtheit), 03–07 (MUS), 08–12 (einfaches
  Zufallsstichprobenverfahren), 13–16 (nichtstatistisch), 17
  (Unterstichproben), 18 (Gesamtfehlerquote nach Anhang III), 20 (Bericht),
  X1–X4 (Altvorlagen von 2017); X1a als Datentabelle; Blatt 01 als Daten.
- Richtlinie für fehlende Angaben an einer Stelle (`model/policy.ts`,
  `evaluateSheet`): Fallarten Pflichteingabe, Standardabweichung der
  Stichprobe, Teilfehlersumme, Wert ohne Grundlage; geltende Richtlinie und
  die Variante „wie die Vorlage“ sind für jedes Blatt geprüft.
- Kontextfluss: Verknüpfungen aus Blatt 02 als vorbelegte, überschreibbare
  Werte; Blatt 18 und 20 übernehmen die Ergebnisübersicht des gewählten
  Verfahrens (ersetzt `INDIRECT`); `computeWorkspace` rechnet die Blätter in
  Registerreihenfolge.
- Schichtzeilen (Spalten der Vorlage, 8. bis 20. Schicht als Erweiterung der
  Webfassung; Schichtspalten je Blatt aus der Definition, Altvorlage X3 in
  E–K) und Listenblatt mit Übernahme der Summen in das Verfahren – je Schicht
  und je Stichprobenzeitraum.
- Katalog der Verfahrensfamilien nach Blatt 00, Wegweiser mit dem Wortlaut
  der Vorlage.
- Arbeitsstand `flowaudit-stichprobe` Fassung 1: speichern, öffnen, Prüfsumme
  SHA-256, Migrationsgerüst, strenge Prüfung, JSON-Schema, Hinweise der
  Webfassung als eigenes Feld.
- Excel-Austausch als getrennter Einstieg `./xlsx`: Export mit `_Arbeitsstand`,
  Import des Exports und der ausgefüllten Vorlage über alle Blätter (Kopien
  des Blatts 17 als Einheiten, gewähltes Methodenblatt aus Blatt 18) mit
  Rückmeldung jedes nicht oder umgedeutet übernommenen Werts und Vergleich
  mit den Rechenwerten der Datei; Leser mit Größen-, Zellen- und Zeitgrenzen.
- Anzeigemodelle: Formular, Ergebnisspalte (Skala je Blattart, „noch keine
  Angaben“ beim leeren Formular), Liste, Datentabelle, Bericht
  (`buildReport`, Druck-Stylesheet für eine A4-Seite).
- Sprache: Texte der Oberfläche deutsch und englisch; englische
  Arbeitsübersetzung der Vorlagentexte je Blatt.
- Hinweis des Fachrahmens und Stand der Vorlage (`disclaimer`,
  `templateStatus`) in Oberfläche, Export und Bericht; Dateinamen mit
  wählbarem Vorsatz.
- Werkzeuge: `scripts/golden_recalc.py` (Sollwerte durch Neuberechnung der
  Vorlage), `scripts/random-cases.mjs` (Zufallsbelegungen mit festem
  Startwert), `scripts/generate-definition.mjs`, `scripts/measure_semantics.py`.
- Golden-Abgleich aller Blätter: siehe `docs/abgleich.md` (0 unbegründete
  Abweichungen; Variante „wie die Vorlage“ 0 Abweichungen).
