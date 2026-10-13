# Abweichungen vom Verhalten der Vorlage

Die Rechenkerne bilden die Formeln der Excel-Vorlage Zelle für Zelle nach.
Rundung, Schwellen und Rechenreihenfolge sind unverändert; für vollständig
ausgefüllte Blätter stimmen alle Formelzellen mit der Vorlage überein
([abgleich.md](abgleich.md)). Abweichungen gibt es nur an den hier genannten
Stellen. Es gilt durchgehend:

> Die Webfassung zeigt nie einen anderen Wert als die Vorlage. Sie zeigt an
> manchen Stellen **keinen** Wert, wo die Vorlage einen zeigt.

## 1. Leere Eingaben: „Angabe fehlt“ statt Rechnen mit 0

Excel behandelt eine leere Zelle in einer Rechnung als 0. Die Vorlage zeigt
deshalb bei unvollständig ausgefüllten Blättern Werte, die wie Ergebnisse
aussehen – zum Beispiel einen Stichprobenumfang von 30, solange die
voraussichtliche Standardabweichung fehlt. Die Webfassung liefert an diesen
Zellen `null` und zeigt „Angabe fehlt“.

Jedes Blatt führt diese Stellen als Daten (`src/sheets/<Blatt>/deviations.ts`):
Zelle, auslösende leere Eingaben, Anzeige der Vorlage, Begründung. Der
Golden-Abgleich lässt eine Abweichung nur zu, wenn sie dort steht, die
Webfassung `null` liefert und eine der genannten Eingaben tatsächlich leer ist;
jede Zeile muss durch mindestens einen Golden-Fall belegt sein
(`test/deviations.spec.ts`).

Wo die Vorlage bei fehlenden Angaben `""` zeigt, liefert die Webfassung
ebenfalls `null`; das ist keine Abweichung. Wo die Vorlage ausdrücklich mit
`N(…)` rechnet (z. B. leere Fehlersumme der hochwertigen Einheiten = 0), rechnet
die Webfassung genauso.

<!-- abweichungen:start – erzeugt mit `npm run docs:write`, nicht von Hand ändern -->

### 02_Grundgesamtheit

| Zellen | leer ist eine von | Vorlage zeigt | Webfassung zeigt | Begründung |
|---|---|---|---|---|
| C17 | C15, C16 | Differenz gegen 0 (leere Zelle zählt als 0) | Angabe fehlt | Ohne den Betrag laut SFC2021 bzw. laut Datenbestand gibt es nichts abzustimmen; eine Differenz gegen 0 wäre irreführend. |
| C22, C30 | C16 | Betrag bzw. Differenz auf Grundlage von 0 € | Angabe fehlt | Ohne den Betrag laut SFC2021 bzw. laut Datenbestand gibt es nichts abzustimmen; eine Differenz gegen 0 wäre irreführend. |
| C37, C39, C51 | C25 | 0 € bzw. nur die TH-Pauschale | Angabe fehlt | Ohne die Datensätze mit positivem Wert ist die Grundgesamtheit unbekannt, nicht null. |
| C38, C52 | C24 | 0 Einheiten | Angabe fehlt | Ohne die Datensätze mit positivem Wert ist die Grundgesamtheit unbekannt, nicht null. |

### 03_MUS_1Z

| Zellen | leer ist eine von | Vorlage zeigt | Webfassung zeigt | Begründung |
|---|---|---|---|---|
| C7, N4 | C7 | 0 (Verknüpfung auf das leere Blatt 02) | Angabe fehlt | Ohne Buchwert der Grundgesamtheit gibt es keine Bezugsgröße; ein Ergebnis von 0 € wäre irreführend. |
| C8 | C8 | 0 (Verknüpfung auf das leere Blatt 02) | Angabe fehlt | Ohne Angabe ist der Umfang der Grundgesamtheit unbekannt, nicht null. |
| C16 | C7, C14 | 0,00 € (leere Zelle zählt als 0) | Angabe fehlt | Der zulässige Fehler setzt Buchwert und Wesentlichkeitsschwelle voraus. |
| C18 | C7, C17 | 0,00 € (leere Zelle zählt als 0) | Angabe fehlt | Der voraussichtliche Fehler setzt Buchwert und voraussichtliche Fehlerquote voraus. |
| C31 | C7 | 0 € abzüglich des Buchwerts der hochwertigen Einheiten | Angabe fehlt | Ohne Buchwert der Grundgesamtheit gibt es keine Bezugsgröße; ein Ergebnis von 0 € wäre irreführend. |
| C21 | C17, C20 | Umfang mit AE = 0 bzw. σ_r = 0 (z. B. 0 oder 39) | Angabe fehlt | Ohne voraussichtliche Fehlerquote und Standardabweichung ist der Stichprobenumfang nicht bestimmt; alle Folgegrößen bleiben offen. |
| C27, N10 | C17, C20 | Mindestumfang 30 bzw. der mit AE = 0 berechnete Umfang | Angabe fehlt | Ohne voraussichtliche Fehlerquote und Standardabweichung ist der Stichprobenumfang nicht bestimmt; alle Folgegrößen bleiben offen. |
| C28, C34, C41, C42, C43, C46, C47, N5, N7 | C7, C17, C20 | Wert auf Grundlage des mit 0 gerechneten Buchwerts bzw. Umfangs (bei leerem Buchwert auch negative Beträge) | Angabe fehlt | Ohne voraussichtliche Fehlerquote und Standardabweichung ist der Stichprobenumfang nicht bestimmt; alle Folgegrößen bleiben offen. |
| C32, C33, C48, C49, C50, C51, C52, N11 | C17, C20 | Wert auf Grundlage des mit AE = 0 bzw. σ_r = 0 berechneten Umfangs | Angabe fehlt | Ohne voraussichtliche Fehlerquote und Standardabweichung ist der Stichprobenumfang nicht bestimmt; alle Folgegrößen bleiben offen. |

### 04_MUS_1Z_S

| Zellen | leer ist eine von | Vorlage zeigt | Webfassung zeigt | Begründung |
|---|---|---|---|---|
| C11 | 02_Grundgesamtheit!C51 | Summe der Schichten abzüglich 0 € (leeres Blatt 02) | Angabe fehlt | Ohne angepasste Grundgesamtheit in Blatt 02 gibt es nichts abzugleichen. |
| C19 | C17 | 0,00 € (leere Zelle zählt als 0) | Angabe fehlt | Der zulässige Fehler setzt die Wesentlichkeitsschwelle voraus. |
| C21 | C20 | 0,00 € (leere Zelle zählt als 0) | Angabe fehlt | Der voraussichtliche Fehler setzt die voraussichtliche Fehlerquote voraus. |
| D25 | D24 | 0 (σ_rh einer belegten Schicht zählt als 0) | Angabe fehlt | Fehlt die Standardabweichung einer belegten Schicht, ist die gewichtete Standardabweichung nicht bestimmt. |
| E25 | E24 | 0 (σ_rh einer belegten Schicht zählt als 0) | Angabe fehlt | Fehlt die Standardabweichung einer belegten Schicht, ist die gewichtete Standardabweichung nicht bestimmt. |
| F25 | F24 | 0 (σ_rh einer belegten Schicht zählt als 0) | Angabe fehlt | Fehlt die Standardabweichung einer belegten Schicht, ist die gewichtete Standardabweichung nicht bestimmt. |
| G25 | G24 | 0 (σ_rh einer belegten Schicht zählt als 0) | Angabe fehlt | Fehlt die Standardabweichung einer belegten Schicht, ist die gewichtete Standardabweichung nicht bestimmt. |
| H25 | H24 | 0 (σ_rh einer belegten Schicht zählt als 0) | Angabe fehlt | Fehlt die Standardabweichung einer belegten Schicht, ist die gewichtete Standardabweichung nicht bestimmt. |
| I25 | I24 | 0 (σ_rh einer belegten Schicht zählt als 0) | Angabe fehlt | Fehlt die Standardabweichung einer belegten Schicht, ist die gewichtete Standardabweichung nicht bestimmt. |
| J25 | J24 | 0 (σ_rh einer belegten Schicht zählt als 0) | Angabe fehlt | Fehlt die Standardabweichung einer belegten Schicht, ist die gewichtete Standardabweichung nicht bestimmt. |
| C25, C26 | D24–J24 | Wert ohne den Beitrag der Schicht mit fehlender Standardabweichung | Angabe fehlt | Fehlt die Standardabweichung einer belegten Schicht, ist die gewichtete Standardabweichung nicht bestimmt. |
| D41–J41 | C33 | „✔ ≥ 3“ (Excel wertet die leere Textzelle im Vergleich größer als jede Zahl) | Angabe fehlt | Ohne Stichprobenumfang gibt es keine Zufallsschicht zu prüfen. |
| C27, C33, C35, C40, C50, C51, C52, C53, C54, C57, C58, C59, C60, C61, C62, C63, N5, N7, N10, N11, D35–J35, D36–J36, D40–J40, D42–J42, D50–J50, D51–J51, D52–J52 | C20, D24–J24 | Wert auf Grundlage des mit AE = 0 bzw. σ_rh = 0 berechneten Umfangs (mindestens 30) | Angabe fehlt | Ohne voraussichtliche Fehlerquote und Standardabweichung jeder belegten Schicht ist der Stichprobenumfang nicht bestimmt; alle Folgegrößen bleiben offen. |

### 17_Unterstichprobe

| Zellen | leer ist eine von | Vorlage zeigt | Webfassung zeigt | Begründung |
|---|---|---|---|---|
| C13, C16, C20, C22 | C6 | Wert auf Grundlage eines Buchwerts von 0 € | Angabe fehlt | Ohne Buchwert der Stichprobeneinheit lässt sich nichts hochrechnen; die Vorlage rechnet mit 0 € weiter. |

<!-- abweichungen:end -->

## 2. Verknüpfungen zu Blatt 02

Die grünen Verknüpfungen (z. B. `03_MUS_1Z!C7 = 02_Grundgesamtheit!C51`) zeigen
in der Vorlage 0, solange Blatt 02 leer ist. In der Webfassung liefert ein
leeres Blatt 02 keinen Buchwert 0, sondern keinen Wert (Blatt 02: C37, C38,
C51, C52); die Verknüpfung im Methodenblatt ist dann leer. Leert die
Prüfbehörde eine überschriebene Verknüpfung, gilt wieder der Wert aus Blatt
02; in Excel bliebe die Zelle leer, weil die Formel überschrieben ist.
Überschriebene Verknüpfungen sind in der Oberfläche markiert.

## 3. Vergleiche, Differenzen und Aufrunden

Die Tabellenkalkulation rechnet nicht mit rohem Gleitkomma. Gemessen an
LibreOffice 24.2 (`scripts/measure_semantics.py`, 451 Vergleiche und 81
Rundungen in `test/fixtures/libreoffice-semantik.json`) gilt:

- **Vergleiche** (`=`, `<>`, `<`, `<=`, `>`, `>=`) behandeln zwei Zahlen als
  gleich, wenn sie sich um weniger als 2⁻⁴⁸ relativ unterscheiden. Die
  Rechenkerne vergleichen deshalb ausschließlich über `excel.eq`, `ne`, `lt`,
  `le`, `gt`, `ge`; rohe Vergleiche sind in `src/sheets` per Lint-Regel
  gesperrt.
- **Differenzen** fast gleicher Werte ergeben 0 (`excel.minus`, `excel.plus`).
- **`ROUNDUP`** kürzt den Wert zuerst auf zwölf signifikante Stellen und
  rundet dann von null weg auf. 100,00000000000004 bleibt 100;
  100,000000001 wird 101. `excel.roundUp` bildet das nach; die frühere
  Schwelle von einem Milliardstel ist entfallen.

Die Messwerte sind Bestandteil der Tests (`test/excel.spec.ts`). Der
Golden-Abgleich vergleicht Zellen mit Ganzzahlformat exakt, die übrigen auf
1e-9 relativ.

**Offen:** Gemessen ist LibreOffice, mit dem auch die Sollwerte entstehen.
Microsoft Excel ist nicht gegengeprüft. Excel rundet bei der Anzeige und in
Vergleichen ebenfalls auf 15 Stellen, die genauen Grenzen können abweichen;
betroffen wären nur Werte, die sich erst jenseits der zwölften Stelle von
einer Schwelle oder ganzen Zahl unterscheiden.

## 4. Blatt 03: begrenzter Stichprobenumfang ohne rechnerischen Umfang

Ist der begrenzte Stichprobenumfang gewählt und fehlt die voraussichtliche
Fehlerquote oder Standardabweichung, zeigt die Vorlage `MIN(MAX(n;30);n_lim)`
mit dem aus 0 berechneten n. Der Referenz-Rechenkern `engine.js` des
Ausgangsmaterials zeigte hier den begrenzten Umfang (50 bzw. 30). Die
Webfassung zeigt „Angabe fehlt“, damit die Regel oben ohne Ausnahme gilt. Für
`TE ≤ AE` und für ein fehlendes Konfidenzniveau zeigt die Vorlage selbst den
begrenzten Umfang; die Webfassung folgt ihr.

## 5. Schichtzeilen

Geschichtete Blätter (Muster: Blatt 04) zeigen „Angabe fehlt“ auch in den
Summen der Schichtzeilen, solange der Stichprobenumfang offen ist – die Summe
über leere Zellen wäre 0, die Vorlage zeigt dort eine Zahl. Der Prüfhinweis
„Mindestens drei Einheiten je Zufallsschicht“ bleibt leer, solange es keinen
Umfang je Schicht gibt; die Vorlage zeigt in diesem Fall „✔ ≥ 3“, weil Excel
eine leere Textzelle im Vergleich größer als jede Zahl wertet.

Die 8. bis 20. Schicht (Spalten AA–AM) gibt es in der Vorlage nicht; siehe
[schichten-und-listen.md](schichten-und-listen.md).

## 6. Blatt 17 als Liste

Die Vorlage wird je Stichprobeneinheit kopiert, die Webfassung führt eine
Liste. Die Zuordnung der Einheiten zum Methodenblatt (Zellen W5–W8) und die
Summenbildung sind Hinweise der Webfassung; der Rechenkern je Einheit folgt
der Vorlage.

## 7. Darstellung

Prozentwerte erscheinen mit drei Nachkommastellen (0,652 %), die Vorlage
formatiert mit zwei. Gerechnet wird mit dem vollen Wert; der Excel-Export
verwendet die Zahlenformate der Vorlage.

## 8. Fehlende Standardabweichung der Stichprobe: mit 0 berechnet

Entscheidung des Auftraggebers: Fehlt die Standardabweichung der Fehlerquoten
in der Stichprobe (Blatt 03: C39; Blatt 04: Zeile 47 einer belegten Schicht),
rechnet die Webfassung wie die Vorlage mit 0 und zeigt die Werte. An den
betroffenen Werten (Genauigkeit, Fehlergrenzen, Würdigung) steht der Hinweis
der Webfassung „Keine Angabe, daher mit 0 berechnet.“ (englisch „Not provided,
therefore calculated with 0.“). Die Würdigung erscheint mit dem Wortlaut der
Vorlage, daneben in Warnfarbe der Hinweis; sie ist nicht uneingeschränkt grün.
Derselbe Hinweis steht in der Ergebnisspalte, im Excel-Export und im
Arbeitsstand (`hinweise`). Das ist keine Abweichung im Wert, sondern eine
Kennzeichnung. Für alle anderen Eingaben bleibt es bei „Angabe fehlt“.

## 9. Import der ausgefüllten Vorlage

Die Webfassung liest die Eingabezellen der ausgefüllten Vorlage. Jeder Wert,
den sie nicht oder umgedeutet übernimmt (abweichende Schreibweise einer
Auswahl, Zahl als Text, Datum, überschriebene Verknüpfung, unbekannter
Auswahlwert), erscheint vor der Übernahme in einer Vorschau mit Blatt, Zelle,
gefundenem Wert und Grund. Enthält die Datei Rechenwerte, werden die
Ergebnisse der Webfassung dagegen verglichen und Abweichungen genannt.
Übernommen wird erst nach Bestätigung.

## 10. Prüfsumme des Arbeitsstands

Die Prüfsumme (SHA-256) umfasst Kopf, aktives Verfahren und Eingaben in
kanonischer Reihenfolge. Der Zeitpunkt `gespeichertAm`, die gespeicherten
Ergebnisse und die Hinweise gehören bewusst nicht dazu: Die Prüfsumme
belegt, dass die Eingaben unverändert sind; Ergebnisse und Hinweise werden
beim Öffnen neu gerechnet. Ein nachträglich geänderter Zeitstempel fällt
deshalb nicht auf.

