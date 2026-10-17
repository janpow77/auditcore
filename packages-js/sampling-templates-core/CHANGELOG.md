# Changelog @auditcore/sampling-templates-core

## 0.1.5 – 2026-10-17

Zusammenführung: Stand 0.1.3/0.1.4 vom 14.10.2026 (Arbeitsassistent, Hinweise
der Abnahme) mit den Regeln für freiwillige Eingaben vom 17.10.2026. Die
Zwischenstände 0.1.3 und 0.1.4 dieses Strangs vom 17.10.2026 wurden nicht
ausgeliefert; ihr Inhalt steht hier.

Freiwillige Eingaben nach der Original-Arbeitsmappe (noch nicht veröffentlicht).
Keine Änderung an Rechenwerten; der Abgleich ist unverändert.

- Die Einstufung freiwilliger Eingaben (`optionalOf`, `model/dependence.ts`)
  ist jetzt an der Vorlage begründet: Kennzeichnungen „(leer = …)“ und
  „(fakultativ)“, Abschnitt „optional“ in Blatt 18, Kommentare in Blatt 20;
  Felder, die keine Formel verwendet (z. B. das Geschäftsjahr), lösen nie einen
  Hinweis aus. Tabelle in `docs/abweichungen.md`, Nr. 13.
- `FieldDefinition.optional` kann `false` sein (Pflicht trotz des Feldnamens);
  so in der Altvorlage X1 für C13, die die Vorlage unmittelbar verwendet.
- Nicht lesbare Eingaben („abc“): `buildSections` und `buildSummary` nehmen die
  Menge der ungültigen Eingaben und melden abhängige Werte als „Eingabe
  ungültig“ mit „Ungültige Eingabe: …“ statt „Angabe fehlt“.

Entscheidung des Inhabers vom 17.10.2026 zu freiwilligen Eingaben (noch nicht
veröffentlicht). Kein Wert weicht von der Vorlage ab.

- Freiwillig, leer heißt „keine“ (0), ohne Hinweis „Angabe fehlt“:
  systembedingte und anomale Fehler, hochwertige Einheiten (Gruppe), Einheiten
  der Zufallsschicht mit BV > Auswahlintervall (Iteration), in Blatt 02
  TH-Pauschale, negative Datensätze, Ausschlüsse, Wiederaufnahmen und
  Art.-80-Einheiten, in Blatt 20 J6–J8. Gruppen nur gemeinsam leer.
- Blätter 04, 06 und 16: Die Summen der hochwertigen Einheiten und der
  Iteration ohne Eintrag in einer Schicht zeigen wie in der Vorlage 0 statt
  „kein Wert“; die zugehörigen Abweichungseinträge entfallen.

## 0.1.3 – 2026-10-14

Nur Stile und Texte der Oberfläche (noch nicht veröffentlicht); keine Änderung
am Rechenkern.

- Stile für Filterauswahl, Schrittleiste, Kennzahlenkarten, Ampel und
  Begriffserklärungen; Schrittleiste bricht bei schmaler Breite um.
- Neue Oberflächentexte (deutsch und englisch); Menütexte „Als JSON sichern“,
  „Datei einlesen …“, „Zurücksetzen (leeres Formular)“; Wegweiser nennt
  „Schritt 1“ statt „Blatt 02“.

## 0.1.2 – 2026-10-14

Befunde der Abnahme des Einbaus (noch nicht veröffentlicht). Keine Änderung am
Rechenkern; der Abgleich ist unverändert.

- Berichtsdruck (`styles/report.css`): Kopf- und Summenzeile der Tabellen sind
  im Druck gewöhnliche Zeilengruppen. Als wiederholte Gruppen schob Google
  Chrome die Summenzeile der Tabelle „Ergebnisse der Vorhabenprüfungen“ auf
  eine zweite Seite. Leeres Formular und Beispielwerte ergeben eine A4-Seite;
  Freitexte dürfen umbrechen, Tabellen bleiben je für sich zusammen.
- Mit „Hintergrundgrafiken“ bleibt das Blatt weiß (Seitenhintergrund der
  Anwendung an `html` und `body` wird nicht gedruckt).
- Bericht am Bildschirm: jede Tabelle in einem eigenen, waagerecht rollenden
  Rahmen mit Mindestbreite; Kennzahlentabellen passen ohne Rollen.
- Schmale Breite: Menü „Arbeitsstand“ an der Kopfzeile ausgerichtet, Kopfzeile
  verdichtet und nicht klebend; Schichttabellen mit breiteren Feldern.

## 0.1.1 – 2026-10-13

Auflagen der unabhängigen Gesamtabnahme (noch nicht veröffentlicht).

- **Verbindliche Regel:** Sind alle Pflichteingaben vorhanden, zeigt die
  Webfassung immer, was die Vorlage zeigt – einheitlich in allen Blättern, auch
  bei nicht anwendbarer Standardneuberechnung (05–07, 10–12). Werte ohne
  Grundlage bleiben nur offen, solange eine Eingabe fehlt; sonst tragen sie
  einen Hinweis in Warnfarbe (`SheetEvaluation.withoutBasis`, `complete`).
- **Einschränkungen eines Ergebnisses** (`view/limits.ts`: `limitationsOf`,
  `carriedLimitations`, `isQualified`): mit 0 gerechnete Eingaben, stille
  Lücken, Werte ohne Grundlage, negative Ergebnisse, Zahlenbereich,
  Warnhinweise, Auslegung, Altvorlage. Sie reisen vollständig in Blatt 18, den
  Bericht (Bildschirm und Druck), den Arbeitsstand und jeden Export; eine
  bestandene Würdigung steht dann nicht uneingeschränkt grün da.
- **Stille Lücken** (`model/dependence.ts`, `SheetEvaluation.silent`,
  `FieldDefinition.optional`): Fällt eine Schicht, ein Zeitraum oder eine Größe
  wegen einer leeren, nicht freiwilligen Eingabe aus der Rechnung der Vorlage,
  nennt ein Hinweis in Warnfarbe Schicht und Eingabe.
- **Negative Ergebnisse** (mehr hochwertige Einheiten als Stichprobenumfang,
  negative Fehlerquote) und Stichprobenumfänge ab 10¹⁵ sind ausgewiesen.
- `excel.roundUp` kürzt wie LibreOffice auch oberhalb von zwölf ganzzahligen
  Stellen auf zwölf geltende Stellen; `excel.sum` summiert mit Fehlerausgleich
  (Kahan-Neumaier) wie `SUMME`.
- Bericht: Vorlage, Rechtsstand, Fassung des Rechenkerns und – über
  `workspaceChecksum` – die Prüfsumme der Eingaben (`ReportPage.identity`).
- Import der ausgefüllten Vorlage: Gegenprobe für alle Blätter einschließlich
  18 und 20, Ergebnisübersicht N3–N11, beide Richtungen (`ImportDifference.kind`,
  `explained`); `notes` nennt ungelesene Schichtdaten (Spalte K), ein nicht
  gewähltes Methodenblatt, gelöschte Vorgaben und Kopien des Blatts 17 unter
  freiem Namen; abgeschnittene oder übergroße Blätter sind Lesefehler; ein
  Datum als Tageszahl wird als Datum übernommen.
- Excel-Export nur noch mit bearbeiteten Blättern; ein anderes Verfahrensblatt
  ist im Kopf gekennzeichnet.
- Abweichungstabelle ergänzt: Blatt 02 (C53, C54 ohne C24), Blatt 07 (ohne
  Wesentlichkeitsschwelle bei globaler Neuberechnung), Blatt 17 (ohne Umfang
  der Unterstichprobe).
- Eingabe: eigene Meldungen für zu viele Nachkommastellen; Prozentfelder
  zeigen alle eingegebenen Stellen. Hinweise zur Übernahme aus den
  Unterstichproben sagen genau, welche Blätter sie haben.
- Abgleich: 10.531 Fälle (davon 6.805 der Abnahme), 728.895 Zellen, 0
  unbegründete Abweichungen; Eigenschaftstests über alle Blätter
  (`test/properties.spec.ts`). `scripts/golden_recalc.py` rechnet in Stapeln.
- Einstieg für den Excel-Austausch: `@auditcore/sampling-templates-core/workbook`.

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
- Bericht (Blatt 20): Programm und Prüfbehörde in Kopf- und Fußzeile sind
  Angaben der Prüfbehörde, kein fester Text der Vorlage (bewusste Abweichung);
  Druck als benannte Seite `fa-st-report`.
- Excel-Austausch als getrennter Einstieg `./workbook`: Export mit `_Arbeitsstand`,
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
