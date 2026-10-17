# Abweichungen vom Verhalten der Vorlage

Die Rechenkerne bilden die Formeln der Excel-Vorlage Zelle für Zelle nach.
Rundung, Schwellen und Rechenreihenfolge sind unverändert; für vollständig
ausgefüllte Blätter stimmen alle Formelzellen mit der Vorlage überein
([abgleich.md](abgleich.md)). Abweichungen gibt es nur an den hier genannten
Stellen. Es gilt durchgehend:

> Die Webfassung zeigt nie einen anderen Wert als die Vorlage. Sind alle
> Pflichteingaben vorhanden, zeigt sie **immer**, was die Vorlage zeigt. Nur
> solange eine Eingabe fehlt, zeigt sie an manchen Stellen **keinen** Wert, wo
> die Vorlage einen zeigt.

**Ausnahme nach Entscheidung des Inhabers vom 17.10.2026:** An zwei Stellen, an
denen die Vorlage von der DelVO (EU) 2023/67 abweicht, rechnet die Webfassung
nach der DelVO – Genauigkeit bei Ersetzung in Tabelle 2 (Blatt 18) und globale
Neuberechnung bei AE ≥ TE (Blätter 05–07, 10–12). Dort zeigt sie bewusst einen
anderen Wert bzw. keinen (Nr. 16).

Ausnahmen in der Darstellung: Kopf- und Fußzeile des Berichts (Nr. 12), der
Wahrheitswert FALSCH der Altvorlagen (gezeigt als 0, mit dem die Vorlage
rechnet) und der Fehlerwert `#DIV/0!` in Blatt 20 (kein Wert mit Hinweis;
beides Nr. 3) sowie der amtliche Begriff „Signifikanzschwelle“ statt
„Wesentlichkeitsschwelle“ (Nr. 16). Fragwürdige
Ergebnisse der Vorlage unterdrückt die Webfassung nicht; sie zeigt sie mit
einem Hinweis in Warnfarbe, und eine bestandene Würdigung steht dann nicht
uneingeschränkt grün da (Nr. 13).

## 1. Fehlende Angaben: die Richtlinie und ihre zwei Varianten

Excel behandelt eine leere Zelle in einer Rechnung als 0. Die Vorlage zeigt
deshalb bei unvollständig ausgefüllten Blättern Werte, die wie Ergebnisse
aussehen – einen Stichprobenumfang von 30, solange die voraussichtliche
Standardabweichung fehlt, oder die Würdigung „✔ GFQ und obere Fehlergrenze
unter der Schwelle“ bei „TE ≤ AE“, obwohl es keine Stichprobe gibt.

Was die Webfassung in diesen Fällen zeigt, steht an **einer** Stelle:
`src/model/policy.ts`, Konstante `MISSING_POLICY`. Die Blätter kennen nur die
Fallart; die Anzeige entscheidet `evaluateSheet` (`src/model/evaluate.ts`)
anhand dieser Tabelle. Zum Umstellen wird dort ein Wert geändert, kein Blatt.

| Fallart | Bedeutung | geltend (vorläufige Vorgabe) | Alternative |
|---|---|---|---|
| `requiredInput` | Eine Pflichteingabe fehlt, die Vorlage rechnet mit 0 weiter (Buchwert, Anzahl, Signifikanzschwelle, voraussichtliche Fehlerquote und Standardabweichung, Umfänge, Angaben der Planung und der Neuberechnung). | `missing`: „Angabe fehlt“, die fehlende Eingabe wird genannt | `zero`: wie die Vorlage mit 0 gerechnet, an jedem betroffenen Wert „Keine Angabe, daher mit 0 berechnet.“ |
| `sampleDeviation` | Die Standardabweichung der Stichprobe (s_r, s_q, s der Differenzen) fehlt in der Auswertung; ohne sie ist nur die Genauigkeit 0. | `zero` (vom Auftraggeber entschieden) | `missing` |
| `partialErrorSum` | Die Fehlersumme bzw. Summe der Fehlerquoten einer von mehreren belegten Schichten oder eines von mehreren Zeiträumen fehlt, eine andere ist eingetragen; die Vorlage zeigt ein Ergebnis. | `zero`, ausgewiesen wie oben | `missing` |
| `withoutBasis` | Die Vorlage zeigt einen Wert ohne Grundlage: einen bestandenen Prüfhinweis („✔“), obwohl die geprüfte Größe fehlt, die Summe 0 über Schichten ohne Wert samt allem, was darauf aufbaut, oder die Untergrenze 3 als Umfang, wenn die Standardneuberechnung nicht anwendbar ist. | `open`, **aber nur, solange eine Pflichteingabe fehlt**; sind alle Pflichteingaben vorhanden, wie die Vorlage mit Hinweis in Warnfarbe | `template`: immer wie die Vorlage |

**Verbindliche Regel zu `withoutBasis`** (Entscheidung des Auftraggebers nach
der Gesamtabnahme): Sind alle Pflichteingaben vorhanden, zeigt die Webfassung
immer, was die Vorlage zeigt – einheitlich in allen Blättern, auch in 05, 06,
07, 10, 11 und 12 bei nicht anwendbarer Standardneuberechnung und in den
geschichteten Blättern bei „TE ≤ AE“. Die so gezeigten Zellen führt
`evaluateSheet` in `withoutBasis`; die Ergebnisspalte nennt sie im Hinweis
„Wie in der Vorlage gezeigt, obwohl die Grundlage fehlt: … Das Ergebnis ist
nicht belastbar“, und die Würdigung trägt den Zusatz „Nicht uneingeschränkt:
siehe Hinweise der Webfassung“. Offen bleibt ein Wert ohne Grundlage
ausschließlich, solange eine Pflichteingabe fehlt. Pflichteingaben sind die
Eingaben, die das Blatt in der Tabelle unten als Auslöser einer Abweichung
der Fallart `requiredInput` nennt (bei Schichtzeilen nur für belegte
Schichten); der Abgleich mit einem leeren Blatt 02 zählt nicht dazu. Geprüft
ist die Regel als Eigenschaft über alle Blätter (`test/properties.spec.ts`):
In keiner vollständigen Zufallsbelegung ist eine Zelle offen, die in der
Vorlage einen Wert hat.

Nicht ausgewiesen wird, was fachlich „keine“ bedeutet: abgegrenzte
systembedingte und nicht berichtigte anomale Fehler sowie die Angaben der
hochwertigen Einheiten bzw. der umfassenden Schicht, solange dort gar nichts
eingetragen ist. Sie zählen wie in der Vorlage 0. Ist die Schicht dagegen
erklärt (Anzahl oder Buchwert eingetragen) und fehlt ihre Fehlersumme, weist
die Webfassung das aus (Nr. 13).

**Folgen der beiden Grundsatzvarianten** für fehlende Pflichteingaben:

- *Geltend („Angabe fehlt“):* Ein unvollständiges Blatt zeigt keine
  Scheinergebnisse; die Ergebnisspalte nennt, welche Eingabe fehlt. Dafür
  weicht die Anzeige bei Teilbelegungen von einer daneben geöffneten Vorlage
  ab (dort stehen Zahlen). Der Abgleich weist diese Zellen als „begründet“ aus.
- *Variante „mit 0 berechnet“* (`TEMPLATE_POLICY`: alle vier Fallarten wie die
  Vorlage): Die Webfassung zeigt in jeder Zelle genau den Wert der Vorlage,
  auch den Stichprobenumfang 30 ohne Standardabweichung und die grüne
  Würdigung ohne Stichprobe; jeder so entstandene Wert trägt den Hinweis
  „Keine Angabe, daher mit 0 berechnet: …“ in Warnfarbe, ebenso Ergebnisspalte,
  Export, Arbeitsstand und Bericht. Diese Variante ist für jedes Blatt und
  jeden Fall des Abgleichs geprüft (`test/policy.spec.ts`; Spalte „wie die
  Vorlage“ in [abgleich.md](abgleich.md): 0 Abweichungen).
- Mischformen sind möglich (z. B. nur `withoutBasis: 'template'`).

Was die Blätter dafür tun:

- Pflichteingabe: Der Rechenkern verlangt sie (`required`) und liefert sonst
  `null`; die Zelle steht in `src/sheets/<Blatt>/deviations.ts` mit den
  auslösenden Eingaben. Der Abgleich lässt die Abweichung nur zu, wenn die
  Gegenprobe stimmt: Mit 0 statt der leeren Eingaben liefert der Rechenkern
  den Wert der Vorlage.
- Mit 0 gerechnete Eingabe: Der Rechenkern rechnet wie die Vorlage; das Blatt
  meldet Eingabe und betroffene Zellen über `zeroAssumed`.
- Wert ohne Grundlage: Der Rechenkern gibt den Wert der Vorlage über
  `unfounded(context, wert)` bzw. `totalRow(…)` zurück; die Zelle steht mit
  `kind: 'withoutBasis'` in den Abweichungen. `evaluateSheet` rechnet bei
  vollständigen Pflichteingaben mit dem Wert der Vorlage und kennzeichnet ihn,
  sonst bleibt er offen. Gegenprobe: Unter `TEMPLATE_POLICY` liefert der
  Rechenkern den Wert der Vorlage.

Jede Zeile der folgenden Tabelle ist durch mindestens einen Golden-Fall belegt
(`test/deviations.spec.ts`): entweder bleibt die Zelle in einem Fall begründet
offen, oder – bei Werten ohne Grundlage – ein Fall zeigt sie bei vollständigen
Pflichteingaben wie die Vorlage. Bei Schichtzeilen genügt der Beleg in einer
Schichtspalte, die Abweichung gilt für alle bis zu 20 Schichten. In der
Spalte „Webfassung zeigt“ steht, was gilt, solange eine Eingabe fehlt.

Wo die Vorlage bei fehlenden Angaben `""` zeigt, liefert die Webfassung
ebenfalls `null`; das ist keine Abweichung.

<!-- abweichungen:start – erzeugt mit `npm run docs:write`, nicht von Hand ändern -->

### 02_Grundgesamtheit

| Zellen | leer ist eine von | Vorlage zeigt | Webfassung zeigt | Begründung |
|---|---|---|---|---|
| C17 | C15, C16 | Differenz gegen 0 (leere Zelle zählt als 0) | Angabe fehlt | Ohne den Betrag laut SFC2021 bzw. laut Datenbestand gibt es nichts abzustimmen; eine Differenz gegen 0 wäre irreführend. |
| C22, C30 | C16 | Betrag bzw. Differenz auf Grundlage von 0 € | Angabe fehlt | Ohne den Betrag laut SFC2021 bzw. laut Datenbestand gibt es nichts abzustimmen; eine Differenz gegen 0 wäre irreführend. |
| C37, C39, C51 | C25 | 0 € bzw. nur die TH-Pauschale | Angabe fehlt | Ohne die Datensätze mit positivem Wert ist die Grundgesamtheit unbekannt, nicht null. |
| C38, C52 | C24 | 0 Einheiten | Angabe fehlt | Ohne die Datensätze mit positivem Wert ist die Grundgesamtheit unbekannt, nicht null. |
| C53, C54 | C24 | Prüfhinweis und Mindestumfang auf Grundlage von 0 Einheiten abzüglich der Abzüge (bei vorhandenen Abzügen eine negative Anzahl, z. B. „✔ weniger als 300 Einheiten“ und Mindestumfang −1) | Angabe fehlt | Ohne die Datensätze mit positivem Wert ist die Grundgesamtheit unbekannt, nicht null. |

### 03_MUS_1Z

| Zellen | leer ist eine von | Vorlage zeigt | Webfassung zeigt | Begründung |
|---|---|---|---|---|
| C7, N4 | C7 | 0 (Verknüpfung auf das leere Blatt 02) | Angabe fehlt | Ohne Buchwert der Grundgesamtheit gibt es keine Bezugsgröße; ein Ergebnis von 0 € wäre irreführend. |
| C8 | C8 | 0 (Verknüpfung auf das leere Blatt 02) | Angabe fehlt | Ohne Angabe ist der Umfang der Grundgesamtheit unbekannt, nicht null. |
| C16 | C7, C14 | 0,00 € (leere Zelle zählt als 0) | Angabe fehlt | Der zulässige Fehler setzt Buchwert und Signifikanzschwelle voraus. |
| C18 | C7, C17 | 0,00 € (leere Zelle zählt als 0) | Angabe fehlt | Der voraussichtliche Fehler setzt Buchwert und voraussichtliche Fehlerquote voraus. |
| C31 | C7 | 0 € abzüglich des Buchwerts der hochwertigen Einheiten | Angabe fehlt | Ohne Buchwert der Grundgesamtheit gibt es keine Bezugsgröße; ein Ergebnis von 0 € wäre irreführend. |
| C21 | C17, C20 | Umfang mit AE = 0 bzw. σ_r = 0 (z. B. 0 oder 39) | Angabe fehlt | Ohne voraussichtliche Fehlerquote und Standardabweichung ist der Stichprobenumfang nicht bestimmt; alle Folgegrößen bleiben offen. |
| C27, N10 | C17, C20 | Mindestumfang 30 bzw. der mit AE = 0 berechnete Umfang | Angabe fehlt | Ohne voraussichtliche Fehlerquote und Standardabweichung ist der Stichprobenumfang nicht bestimmt; alle Folgegrößen bleiben offen. |
| C28, C34, C41, C42, C43, C46, C47, N5, N7 | C7, C17, C20 | Wert auf Grundlage des mit 0 gerechneten Buchwerts bzw. Umfangs (bei leerem Buchwert auch negative Beträge) | Angabe fehlt | Ohne voraussichtliche Fehlerquote und Standardabweichung ist der Stichprobenumfang nicht bestimmt; alle Folgegrößen bleiben offen. |
| C32, C33, C48, C49, C50, C51, C52, N11 | C17, C20 | Wert auf Grundlage des mit AE = 0 bzw. σ_r = 0 berechneten Umfangs | Angabe fehlt | Ohne voraussichtliche Fehlerquote und Standardabweichung ist der Stichprobenumfang nicht bestimmt; alle Folgegrößen bleiben offen. |
| C41 | C38 | 0,00 € (die Fehlersumme der Stichprobe fehlt; N(…) zählt sie als 0) | kein Wert | Ohne Fehlersumme der Stichprobe gibt es nichts hochzurechnen; ein extrapolierter Fehler von 0 € sähe wie ein Prüfergebnis aus. |

### 04_MUS_1Z_S

| Zellen | leer ist eine von | Vorlage zeigt | Webfassung zeigt | Begründung |
|---|---|---|---|---|
| C9, C25, C52, N4 | D9–J9, AA9–AM9 | 0 (Summe über Schichten ohne Wert) | kein Wert | Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus. |
| C10 | D10–J10, AA10–AM10 | 0 (Summe über Schichten ohne Wert) | kein Wert | Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus. |
| C35, N10 | D35–J35, AA35–AM35 | 0 (Summe über Schichten ohne Wert) | kein Wert | Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus. |
| C39 | D39–J39, AA39–AM39 | 0 (Summe über Schichten ohne Wert) | kein Wert | Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus. |
| C40 | D40–J40, AA40–AM40 | 0 (Summe über Schichten ohne Wert) | kein Wert | Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus. |
| C46 | D46–J46, AA46–AM46 | 0 (Summe über Schichten ohne Wert) | kein Wert | Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus. |
| C49 | D49–J49, AA49–AM49 | 0 (Summe über Schichten ohne Wert) | kein Wert | Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus. |
| C50 | D50–J50, AA50–AM50 | 0 (Summe über Schichten ohne Wert) | kein Wert | Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus. |
| C51 | D51–J51, AA51–AM51 | 0 (Summe über Schichten ohne Wert) | kein Wert | Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus. |
| C11, C19, C21 | C9 | 0 € (Summe der Buchwerte ohne belegte Schicht) | kein Wert | Der Wert baut auf einer Summe auf, zu der keine Schicht beiträgt; ohne sie ist er nicht bestimmt. |
| N6 | C49 | 0 € (Summe ohne belegte Schicht) | kein Wert | Der Wert baut auf einer Summe auf, zu der keine Schicht beiträgt; ohne sie ist er nicht bestimmt. |
| C53, C57, C58, C60, C61, C62, C63, N5, N11 | C51 | Hochrechnung und Würdigung auf Grundlage eines extrapolierten Fehlers von 0 €, obwohl keine Schicht einen Stichprobenumfang hat (z. B. bei „TE ≤ AE“) | kein Wert | Der Wert baut auf einer Summe auf, zu der keine Schicht beiträgt; ohne sie ist er nicht bestimmt. |
| C11 | 02_Grundgesamtheit!C51 | Summe der Schichten abzüglich 0 € (leeres Blatt 02) | Angabe fehlt | Ohne angepasste Grundgesamtheit in Blatt 02 gibt es nichts abzugleichen. |
| C19 | C17 | 0,00 € (leere Zelle zählt als 0) | Angabe fehlt | Der zulässige Fehler setzt die Signifikanzschwelle voraus. |
| C21 | C20 | 0,00 € (leere Zelle zählt als 0) | Angabe fehlt | Der voraussichtliche Fehler setzt die voraussichtliche Fehlerquote voraus. |
| D25–J25, AA25–AM25 | D24–J24, AA24–AM24 | 0 (σ_rh einer belegten Schicht zählt als 0) | Angabe fehlt | Fehlt die Standardabweichung einer belegten Schicht, ist die gewichtete Standardabweichung nicht bestimmt. |
| C25, C26 | D24–J24, AA24–AM24 | Wert ohne den Beitrag der Schicht mit fehlender Standardabweichung | Angabe fehlt | Fehlt die Standardabweichung einer belegten Schicht, ist die gewichtete Standardabweichung nicht bestimmt. |
| D41–J41, AA41–AM41 | D40–J40, AA40–AM40 | „✔ ≥ 3“ (Excel wertet die leere Textzelle im Vergleich größer als jede Zahl) | kein Wert | Ohne Einheiten der Zufallsschicht gibt es nichts zu prüfen; ein bestandener Prüfhinweis wäre irreführend. |
| C27, C33, C35, C40, C50, C51, C52, C53, C54, C57, C58, C59, C60, C61, C62, C63, N5, N7, N10, N11 | C20, D24–J24, AA24–AM24 | Wert auf Grundlage des mit AE = 0 bzw. σ_rh = 0 berechneten Umfangs (mindestens 30) | Angabe fehlt | Ohne voraussichtliche Fehlerquote und Standardabweichung jeder belegten Schicht ist der Stichprobenumfang nicht bestimmt; alle Folgegrößen bleiben offen. |
| D35–J35, AA35–AM35, D36–J36, AA36–AM36, D40–J40, AA40–AM40, D41–J41, AA41–AM41, D42–J42, AA42–AM42, D50–J50, AA50–AM50, D51–J51, AA51–AM51, D52–J52, AA52–AM52 | C20, D24–J24, AA24–AM24 | Wert auf Grundlage des mit AE = 0 bzw. σ_rh = 0 berechneten Umfangs (mindestens 30) | Angabe fehlt | Ohne voraussichtliche Fehlerquote und Standardabweichung jeder belegten Schicht ist der Stichprobenumfang nicht bestimmt; alle Folgegrößen bleiben offen. |

### 05_MUS_2Z

| Zellen | leer ist eine von | Vorlage zeigt | Webfassung zeigt | Begründung |
|---|---|---|---|---|
| C11 | C7, C8 | 0,00 € bzw. der Wert mit 0 an Stelle der leeren Zelle | Angabe fehlt | Ohne die Buchwerte der Zeiträume gibt es keine Bezugsgröße; ein Betrag auf Grundlage von 0 € wäre irreführend. |
| C19 | C7, C8, C17 | 0,00 € bzw. der Wert mit 0 an Stelle der leeren Zelle | Angabe fehlt | Der zulässige Fehler setzt beide Buchwerte und die Signifikanzschwelle voraus. |
| C21 | C7, C8, C20 | 0,00 € bzw. der Wert mit 0 an Stelle der leeren Zelle | Angabe fehlt | Der voraussichtliche Fehler setzt beide Buchwerte und die voraussichtliche Fehlerquote voraus. |
| C22 | C7, C8 | Prüfhinweis auf Grundlage nur eines Buchwerts | Angabe fehlt | Ohne die Buchwerte der Zeiträume gibt es keine Bezugsgröße; ein Betrag auf Grundlage von 0 € wäre irreführend. |
| C25 | C7, C8, C23, C24 | gewichtete Standardabweichung mit 0 an Stelle der leeren Zelle | Angabe fehlt | Die gewichtete Standardabweichung setzt Buchwert und Standardabweichung beider Zeiträume voraus. |
| C27, C33, C34, C35, C40, C41, C42 | C7, C8, C20, C23, C24 | Wert auf Grundlage des mit 0 gerechneten Buchwerts, AE = 0 bzw. σ_r = 0 (Gesamtumfang mindestens 30) | Angabe fehlt | Ohne Buchwerte, voraussichtliche Fehlerquote und Standardabweichungen beider Zeiträume ist der Gesamtumfang nicht bestimmt; alle Folgegrößen bleiben offen. |
| C36 | C8, C20, C23, C24 | Wert auf Grundlage des mit 0 gerechneten Buchwerts, AE = 0 bzw. σ_r = 0 (Gesamtumfang mindestens 30) | Angabe fehlt | Ohne Buchwerte, voraussichtliche Fehlerquote und Standardabweichungen beider Zeiträume ist der Gesamtumfang nicht bestimmt; alle Folgegrößen bleiben offen. |
| C39 | C7 | 0 € abzüglich des Buchwerts der hochwertigen Einheiten | Angabe fehlt | Ohne die Buchwerte der Zeiträume gibt es keine Bezugsgröße; ein Betrag auf Grundlage von 0 € wäre irreführend. |
| C52, N4 | C7, C48 | 0,00 € bzw. der Wert mit 0 an Stelle der leeren Zelle | Angabe fehlt | Ohne die Buchwerte der Zeiträume gibt es keine Bezugsgröße; ein Betrag auf Grundlage von 0 € wäre irreführend. |
| C53 | C7, C17, C48 | 0,00 € bzw. der Wert mit 0 an Stelle der leeren Zelle | Angabe fehlt | Der aktualisierte zulässige Fehler setzt beide Ist-Buchwerte und die Signifikanzschwelle voraus. |
| C54 | C7, C20, C48 | 0,00 € bzw. der Wert mit 0 an Stelle der leeren Zelle | Angabe fehlt | Der aktualisierte voraussichtliche Fehler setzt beide Ist-Buchwerte und eine voraussichtliche Fehlerquote voraus. |
| C55 | C23 | 0,0000 (leere Zelle zählt als 0) | Angabe fehlt | Ohne Standardabweichung der Stichprobe und ohne voraussichtliche Standardabweichung gibt es keinen Wert für Zeitraum 1. |
| C56 | C8, C20, C23, C24, C48 | Nenner auf Grundlage des mit 0 gerechneten Werts | Angabe fehlt | Ohne Ist-Buchwert und aktualisierte Standardabweichung des zweiten Zeitraums ist die Neuberechnung nicht bestimmt; die Folgegrößen bleiben offen. |
| C57 | C8, C20, C23, C24, C48, C50 | Wert auf Grundlage von BV₂ = 0 bzw. σ_r2 = 0 (z. B. Umfang 0, 3 oder Auffüllung auf 30) | Angabe fehlt | Ohne Ist-Buchwert und aktualisierte Standardabweichung des zweiten Zeitraums ist die Neuberechnung nicht bestimmt; die Folgegrößen bleiben offen. |
| C58 | C7, C23, C48, C50 | gewichtete Standardabweichung mit 0 an Stelle der leeren Zelle | Angabe fehlt | Ohne Ist-Buchwert und aktualisierte Standardabweichung des zweiten Zeitraums ist die Neuberechnung nicht bestimmt; die Folgegrößen bleiben offen. |
| C59, C60, C61, C63 | C7, C17, C20, C23, C48, C50 | Umfang auf Grundlage des mit 0 gerechneten Werts (mindestens 30) | Angabe fehlt | Ohne Ist-Buchwert und aktualisierte Standardabweichung des zweiten Zeitraums ist die Neuberechnung nicht bestimmt; die Folgegrößen bleiben offen. |
| C64 | C8, C48 | Faktor 1 bzw. der Faktor allein aus dem Verhältnis der Anzahlen (ein leerer Buchwert zählt als 0) | Angabe fehlt | Der Faktor der Unterschätzung vergleicht den Ist-Buchwert des zweiten Zeitraums mit seiner Prognose; ohne beide ist die Erhöhung nicht bestimmt. |
| C65 | C7, C8, C20, C23, C24, C48 | geplanter Umfang mal Faktor 1 bzw. mal dem Faktor allein aus dem Verhältnis der Anzahlen | Angabe fehlt | Der Faktor der Unterschätzung vergleicht den Ist-Buchwert des zweiten Zeitraums mit seiner Prognose; ohne beide ist die Erhöhung nicht bestimmt. |
| C73 | C48 | 0 € abzüglich des Buchwerts der hochwertigen Einheiten | Angabe fehlt | Ohne die Buchwerte der Zeiträume gibt es keine Bezugsgröße; ein Betrag auf Grundlage von 0 € wäre irreführend. |
| C62, C66, C67, C68, C69, C70, C74, C75, C76, C79, C84, C85, C86, C89, C90, C91, C92, C93, C94, C95, N5, N7, N10, N11 | C7, C8, C20, C23, C24, C48, C50 | Wert auf Grundlage von BV₂ = 0 bzw. σ_r2 = 0 (z. B. Umfang 0, 3 oder Auffüllung auf 30) | Angabe fehlt | Ohne die Angaben zum Gesamtumfang und zur Neuberechnung für Zeitraum 2 sind die endgültigen Umfänge nicht bestimmt; Auswahl, Hochrechnung und Würdigung bleiben offen. |
| C33 | C27 | begrenzter Umfang (50 bzw. 30 Einheiten), obwohl die Zelle des rechnerischen Umfangs leer ist | kein Wert | Ohne rechnerischen Umfang gibt es nichts zu begrenzen; der begrenzte Umfang allein sähe wie ein Ergebnis aus. |
| C60 | C59 | begrenzter Umfang (50 bzw. 30 Einheiten), obwohl die Zelle des rechnerischen Umfangs leer ist | kein Wert | Ohne rechnerischen Umfang gibt es nichts zu begrenzen; der begrenzte Umfang allein sähe wie ein Ergebnis aus. |
| C34, C35, C36, C40, C41, C42, C56, C57, C61, C62, C63, C65, C66, C67, C79, C68, C69, C70, C74, C75, C76, C84, C85, C86, C89, C90, C91, C92, C93, C94, C95, N5, N7, N10, N11 | C27, C59 | Wert auf Grundlage eines begrenzten Umfangs, den kein rechnerischer Umfang trägt | kein Wert | Der Wert baut auf dem begrenzten Umfang auf; ohne rechnerischen Umfang ist er nicht bestimmt. |
| C67 | C67 | Untergrenze 3 bzw. Auffüllung auf 30 (MAX übergeht den Text bzw. die leere Zelle des gewählten Umfangs) | kein Wert | Liefert der gewählte Ansatz keinen Umfang für Zeitraum 2, gibt es nichts, was die Untergrenzen sichern könnten; ein Umfang von 3 bzw. die Auffüllung auf 30 sähe wie ein Ergebnis der Neuberechnung aus. |
| C68, C69, C70, C74, C75, C76, C84, C85, C86, C89, C90, C91, C92, C93, C94, C95, N5, N7, N10, N11 | C67 | Wert auf Grundlage eines Umfangs für Zeitraum 2, der nur aus den Untergrenzen besteht | kein Wert | Der Wert baut auf einem Umfang für Zeitraum 2 auf, den keine Neuberechnung ergeben hat; ohne ihn ist er nicht bestimmt. |
| C84 | C46, C81 | 0,00 € (die Fehlersumme der Stichprobe fehlt; N(…) zählt sie als 0) | kein Wert | Ohne Fehlersumme der Stichprobe gibt es nichts hochzurechnen; ein extrapolierter Fehler von 0 € sähe wie ein Prüfergebnis aus. |

### 06_MUS_2Z_S

| Zellen | leer ist eine von | Vorlage zeigt | Webfassung zeigt | Begründung |
|---|---|---|---|---|
| C19, C56 | C17 | 0,00 € (leere Zelle zählt als 0) | Angabe fehlt | Der zulässige Fehler setzt die Signifikanzschwelle voraus. |
| C21, C57 | C20 | 0,00 € (leere Zelle zählt als 0) | Angabe fehlt | Der voraussichtliche Fehler setzt die voraussichtliche Fehlerquote voraus. |
| D26–J26, AA26–AM26 | D24–J24, AA24–AM24, D25–J25, AA25–AM25 | Hilfswert ohne den Beitrag der fehlenden Standardabweichung (σ zählt als 0) | Angabe fehlt | Fehlt die Standardabweichung einer belegten Schicht, ist die gewichtete Standardabweichung nicht bestimmt. |
| C26, C27 | D24–J24, AA24–AM24, D25–J25, AA25–AM25 | Wert ohne den Beitrag der Schicht mit fehlender Standardabweichung | Angabe fehlt | Fehlt die Standardabweichung einer belegten Schicht, ist die gewichtete Standardabweichung nicht bestimmt. |
| C29, C35, C37, C38, C44, C60 | C20, D24–J24, AA24–AM24, D25–J25, AA25–AM25 | Wert auf Grundlage des mit AE = 0 bzw. σ_rh = 0 berechneten Umfangs (mindestens 30) | Angabe fehlt | Ohne voraussichtliche Fehlerquote und Standardabweichung jeder belegten Schicht ist der Gesamtumfang nicht bestimmt; alle Folgegrößen bleiben offen. |
| D37–J37, AA37–AM37, D38–J38, AA38–AM38, D40–J40, AA40–AM40, D44–J44, AA44–AM44, D45–J45, AA45–AM45, D46–J46, AA46–AM46, D60–J60, AA60–AM60 | C20, D24–J24, AA24–AM24, D25–J25, AA25–AM25 | Wert auf Grundlage des mit AE = 0 bzw. σ_rh = 0 berechneten Umfangs (mindestens 30) | Angabe fehlt | Ohne voraussichtliche Fehlerquote und Standardabweichung jeder belegten Schicht ist der Gesamtumfang nicht bestimmt; alle Folgegrößen bleiben offen. |
| D59–J59, AA59–AM59 | D24–J24, AA24–AM24 | 0,0000 (leere Zelle zählt als 0) | Angabe fehlt | Ohne Standardabweichung der Stichprobe und ohne voraussichtliche Standardabweichung gibt es keinen Wert für die Schicht. |
| D61–J61, AA61–AM61 | D53–J53, AA53–AM53 | Hilfswert ohne den Beitrag der fehlenden Standardabweichung (σ zählt als 0) | Angabe fehlt | Ohne aktualisierte Standardabweichung jeder im zweiten Zeitraum belegten Schicht ist die Neuberechnung nicht bestimmt; die Folgegrößen bleiben offen. |
| C61 | D53–J53, AA53–AM53 | Hilfswert ohne den Beitrag der fehlenden Standardabweichung (σ zählt als 0) | Angabe fehlt | Ohne aktualisierte Standardabweichung jeder im zweiten Zeitraum belegten Schicht ist die Neuberechnung nicht bestimmt; die Folgegrößen bleiben offen. |
| C62 | C17, C20, D24–J24, AA24–AM24, D25–J25, AA25–AM25 | Nenner auf Grundlage des mit 0 gerechneten Werts | Angabe fehlt | Ohne voraussichtliche Fehlerquote und Standardabweichung jeder belegten Schicht ist der Gesamtumfang nicht bestimmt; alle Folgegrößen bleiben offen. |
| D64–J64, AA64–AM64 | D24–J24, AA24–AM24, D53–J53, AA53–AM53 | Hilfswert ohne den Beitrag der fehlenden Standardabweichung (σ zählt als 0) | Angabe fehlt | Ohne aktualisierte Standardabweichung jeder im zweiten Zeitraum belegten Schicht ist die Neuberechnung nicht bestimmt; die Folgegrößen bleiben offen. |
| C64 | D24–J24, AA24–AM24, D53–J53, AA53–AM53 | Hilfswert ohne den Beitrag der fehlenden Standardabweichung (σ zählt als 0) | Angabe fehlt | Ohne aktualisierte Standardabweichung jeder im zweiten Zeitraum belegten Schicht ist die Neuberechnung nicht bestimmt; die Folgegrößen bleiben offen. |
| C65, C66 | C17, C20, D24–J24, AA24–AM24, D53–J53, AA53–AM53 | Umfang auf Grundlage des mit 0 gerechneten Werts (mindestens 30) | Angabe fehlt | Ohne aktualisierte Standardabweichung jeder im zweiten Zeitraum belegten Schicht ist die Neuberechnung nicht bestimmt; die Folgegrößen bleiben offen. |
| C63, C69, C72, C78, N10 | C17, C20, D24–J24, AA24–AM24, D25–J25, AA25–AM25, D53–J53, AA53–AM53 | Wert auf Grundlage von σ_rh = 0 bzw. AE = 0 (z. B. Umfang 0 oder 3 je Schicht) | Angabe fehlt | Ohne aktualisierte Standardabweichung jeder im zweiten Zeitraum belegten Schicht ist die Neuberechnung nicht bestimmt; die Folgegrößen bleiben offen. |
| D69–J69, AA69–AM69, D74–J74, AA74–AM74, D78–J78, AA78–AM78, D79–J79, AA79–AM79, D80–J80, AA80–AM80 | C17, C20, D24–J24, AA24–AM24, D25–J25, AA25–AM25, D53–J53, AA53–AM53 | Wert auf Grundlage von σ_rh = 0 bzw. AE = 0 (z. B. Umfang 0 oder 3 je Schicht) | Angabe fehlt | Ohne aktualisierte Standardabweichung jeder im zweiten Zeitraum belegten Schicht ist die Neuberechnung nicht bestimmt; die Folgegrößen bleiben offen. |
| C68, C70, C71, C84 | C20, D24–J24, AA24–AM24, D25–J25, AA25–AM25, D53–J53, AA53–AM53 | Wert auf Grundlage von σ_rh = 0 bzw. AE = 0 (z. B. Umfang 0 oder 3 je Schicht) | Angabe fehlt | Ohne die Angaben zum Gesamtumfang und zur Neuberechnung sind die endgültigen Umfänge nicht bestimmt; Hochrechnung und Würdigung bleiben offen. |
| D68–J68, AA68–AM68, D70–J70, AA70–AM70, D84–J84, AA84–AM84, D87–J87, AA87–AM87, D88–J88, AA88–AM88 | C20, D24–J24, AA24–AM24, D25–J25, AA25–AM25, D53–J53, AA53–AM53 | Wert auf Grundlage von σ_rh = 0 bzw. AE = 0 (z. B. Umfang 0 oder 3 je Schicht) | Angabe fehlt | Ohne die Angaben zum Gesamtumfang und zur Neuberechnung sind die endgültigen Umfänge nicht bestimmt; Hochrechnung und Würdigung bleiben offen. |
| C87, C88, C89, C90, C93, C94, C95, C96, C97, C98, C99, N5, N7, N11 | C17, C20, D24–J24, AA24–AM24, D25–J25, AA25–AM25, D53–J53, AA53–AM53 | Wert auf Grundlage von σ_rh = 0 bzw. AE = 0 (z. B. Umfang 0 oder 3 je Schicht) | Angabe fehlt | Ohne die Angaben zum Gesamtumfang und zur Neuberechnung sind die endgültigen Umfänge nicht bestimmt; Hochrechnung und Würdigung bleiben offen. |
| C11, C19, C21, C22, C27, C29, C35, C37, C38, C44, C55, C56, C57, C60, N4, C62, C63, C69, C72, C78, N10, C65, C66, C68, C70, C71, C84, C87, C88, C89, C90, C93, C94, C95, C96, C97, C98, C99, N5, N7, N11 | C8, C9 | Wert auf Grundlage einer Summe der Buchwerte bzw. der Prognose von 0 €, weil keine Schicht einen Buchwert für Zeitraum 1 bzw. eine Prognose für Zeitraum 2 trägt | kein Wert | Der Wert baut auf einer Summe auf, zu der keine Schicht beiträgt; ohne sie ist er nicht bestimmt. |
| D37–J37, AA37–AM37, D38–J38, AA38–AM38, D40–J40, AA40–AM40, D44–J44, AA44–AM44, D45–J45, AA45–AM45, D46–J46, AA46–AM46, D60–J60, AA60–AM60, D69–J69, AA69–AM69, D74–J74, AA74–AM74, D78–J78, AA78–AM78, D79–J79, AA79–AM79, D80–J80, AA80–AM80, D68–J68, AA68–AM68, D70–J70, AA70–AM70, D84–J84, AA84–AM84, D87–J87, AA87–AM87, D88–J88, AA88–AM88 | C8, C9 | Wert auf Grundlage einer Summe der Buchwerte bzw. der Prognose von 0 €, weil keine Schicht einen Buchwert für Zeitraum 1 bzw. eine Prognose für Zeitraum 2 trägt | kein Wert | Der Wert baut auf einer Summe auf, zu der keine Schicht beiträgt; ohne sie ist er nicht bestimmt. |
| C55, C56, C57, C62, C63, N4, N10, C65, C66, C68, C70, C71, C84, C87, C88, C89, C90, C93, C94, C95, C96, C97, C98, C99, N5, N7, N11 | C51 | Wert allein aus dem ersten Zeitraum, weil die Summe der Ist-Buchwerte des zweiten Zeitraums 0 € ist | kein Wert | Der Wert baut auf einer Summe auf, zu der keine Schicht beiträgt; ohne sie ist er nicht bestimmt. |
| D68–J68, AA68–AM68, D70–J70, AA70–AM70, D84–J84, AA84–AM84, D87–J87, AA87–AM87, D88–J88, AA88–AM88 | C51 | Wert allein aus dem ersten Zeitraum, weil die Summe der Ist-Buchwerte des zweiten Zeitraums 0 € ist | kein Wert | Der Wert baut auf einer Summe auf, zu der keine Schicht beiträgt; ohne sie ist er nicht bestimmt. |
| C35 | C29 | begrenzter Umfang (50 bzw. 30 Einheiten), obwohl die Zelle des rechnerischen Umfangs leer ist | kein Wert | Ohne rechnerischen Umfang gibt es nichts zu begrenzen; der begrenzte Umfang allein sähe wie ein Ergebnis aus. |
| C66 | C65 | begrenzter Umfang (50 bzw. 30 Einheiten), obwohl die Zelle des rechnerischen Umfangs leer ist | kein Wert | Ohne rechnerischen Umfang gibt es nichts zu begrenzen; der begrenzte Umfang allein sähe wie ein Ergebnis aus. |
| C37, C38, C44, C60, C62, C63, C69, C72, C78, N10, C68, C70, C71, C84, C87, C88, C89, C90, C93, C94, C95, C96, C97, C98, C99, N5, N7, N11 | C29, C65 | Wert auf Grundlage eines begrenzten Umfangs, den kein rechnerischer Umfang trägt | kein Wert | Der Wert baut auf dem begrenzten Umfang auf; ohne rechnerischen Umfang ist er nicht bestimmt. |
| D37–J37, AA37–AM37, D38–J38, AA38–AM38, D40–J40, AA40–AM40, D44–J44, AA44–AM44, D45–J45, AA45–AM45, D46–J46, AA46–AM46, D60–J60, AA60–AM60, D69–J69, AA69–AM69, D74–J74, AA74–AM74, D78–J78, AA78–AM78, D79–J79, AA79–AM79, D80–J80, AA80–AM80, D68–J68, AA68–AM68, D70–J70, AA70–AM70, D84–J84, AA84–AM84, D87–J87, AA87–AM87, D88–J88, AA88–AM88 | C29, C65 | Wert auf Grundlage eines begrenzten Umfangs, den kein rechnerischer Umfang trägt | kein Wert | Der Wert baut auf dem begrenzten Umfang auf; ohne rechnerischen Umfang ist er nicht bestimmt. |
| C62, C63, C69, C72, C78, N10, C87, C88, C89, C90, C93, C94, C95, C96, C97, C98, C99, N5, N7, N11 | C37, C60 | Wert auf Grundlage einer Hilfssumme von 0, obwohl keine Schicht einen Umfang für Zeitraum 1 hat (z. B. bei „TE ≤ AE“) | kein Wert | Der Wert baut auf einer Summe auf, zu der keine Schicht beiträgt; ohne sie ist er nicht bestimmt. |
| D69–J69, AA69–AM69, D74–J74, AA74–AM74, D78–J78, AA78–AM78, D79–J79, AA79–AM79, D80–J80, AA80–AM80 | C37, C60 | Wert auf Grundlage einer Hilfssumme von 0, obwohl keine Schicht einen Umfang für Zeitraum 1 hat (z. B. bei „TE ≤ AE“) | kein Wert | Der Wert baut auf einer Summe auf, zu der keine Schicht beiträgt; ohne sie ist er nicht bestimmt. |
| D45–J45, AA45–AM45 | D44–J44, AA44–AM44 | „✔ ≥ 3“ (Excel wertet die leere Textzelle im Vergleich größer als jede Zahl) | kein Wert | Ohne Einheiten der Zufallsschicht gibt es nichts zu prüfen; ein bestandener Prüfhinweis wäre irreführend. |
| D79–J79, AA79–AM79 | D78–J78, AA78–AM78 | „✔ ≥ 3“ (Excel wertet die leere Textzelle im Vergleich größer als jede Zahl) | kein Wert | Ohne Einheiten der Zufallsschicht gibt es nichts zu prüfen; ein bestandener Prüfhinweis wäre irreführend. |
| D69–J69, AA69–AM69 | D38–J38, AA38–AM38 | Untergrenze 3 (MAX übergeht den leeren Planumfang der Schicht) | kein Wert | Ohne Planumfang der Schicht gibt es nichts, was die Untergrenze sichern könnte; ein Umfang von 3 sähe wie ein Ergebnis aus. |
| D74–J74, AA74–AM74, D78–J78, AA78–AM78, D80–J80, AA80–AM80, D87–J87, AA87–AM87, D88–J88, AA88–AM88 | D69–J69, AA69–AM69 | Wert auf Grundlage der Untergrenze 3 als Umfang der Schicht für Zeitraum 2 | kein Wert | Ohne Planumfang der Schicht gibt es nichts, was die Untergrenze sichern könnte; ein Umfang von 3 sähe wie ein Ergebnis aus. |
| C71, C72, N10, C87, C88, C89, C90, C93, C94, C95, C96, C97, C98, C99, N5, N7, N11 | C69, C78 | Wert auf Grundlage eines Umfangs für Zeitraum 2, den keine Neuberechnung ergeben hat (0 bei nicht anwendbarer Standardneuberechnung, Untergrenze 3 ohne Planumfang) | kein Wert | Der Wert baut auf einer Summe auf, zu der keine Schicht beiträgt; ohne sie ist er nicht bestimmt. |
| C8 | D8–J8, AA8–AM8 | 0 (Summe über Schichten ohne Wert) | kein Wert | Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus. |
| C9 | D9–J9, AA9–AM9 | 0 (Summe über Schichten ohne Wert) | kein Wert | Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus. |
| C10 | D10–J10, AA10–AM10 | 0 (Summe über Schichten ohne Wert) | kein Wert | Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus. |
| C26 | D8–J8, AA8–AM8, D9–J9, AA9–AM9 | 0 (Summe über Schichten ohne Wert) | kein Wert | Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus. |
| C37 | D37–J37, AA37–AM37 | 0 (Summe über Schichten ohne Wert) | kein Wert | Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus. |
| C38 | D38–J38, AA38–AM38 | 0 (Summe über Schichten ohne Wert) | kein Wert | Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus. |
| C43 | D43–J43, AA43–AM43 | 0 (Summe über Schichten ohne Wert) | kein Wert | Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus. |
| C44 | D44–J44, AA44–AM44 | 0 (Summe über Schichten ohne Wert) | kein Wert | Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus. |
| C48 | D48–J48, AA48–AM48 | 0 (Summe über Schichten ohne Wert) | kein Wert | Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus. |
| C51 | D51–J51, AA51–AM51 | 0 (Summe über Schichten ohne Wert) | kein Wert | Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus. |
| C52 | D52–J52, AA52–AM52 | 0 (Summe über Schichten ohne Wert) | kein Wert | Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus. |
| C60 | D8–J8, AA8–AM8, D60–J60, AA60–AM60 | 0 (Summe über Schichten ohne Wert) | kein Wert | Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus. |
| C61 | D51–J51, AA51–AM51, D61–J61, AA61–AM61 | 0 (Summe über Schichten ohne Wert) | kein Wert | Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus. |
| C64 | D8–J8, AA8–AM8, D51–J51, AA51–AM51 | 0 (Summe über Schichten ohne Wert) | kein Wert | Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus. |
| C68 | D68–J68, AA68–AM68 | 0 (Summe über Schichten ohne Wert) | kein Wert | Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus. |
| C69 | D69–J69, AA69–AM69 | 0 (Summe über Schichten ohne Wert) bzw. Summe mit der Untergrenze 3 einer Schicht ohne Planumfang | kein Wert | Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus. |
| C70 | D70–J70, AA70–AM70 | 0 (Summe über Schichten ohne Wert) | kein Wert | Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus. |
| C77 | D77–J77, AA77–AM77 | 0 (Summe über Schichten ohne Wert) | kein Wert | Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus. |
| C78 | D78–J78, AA78–AM78 | 0 (Summe über Schichten ohne Wert) bzw. Summe mit der Untergrenze 3 einer Schicht ohne Planumfang | kein Wert | Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus. |
| C82 | D82–J82, AA82–AM82 | 0 (Summe über Schichten ohne Wert) | kein Wert | Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus. |
| C84 | D84–J84, AA84–AM84 | 0 (Summe über Schichten ohne Wert) | kein Wert | Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus. |
| C86, N6 | D8–J8, AA8–AM8, D47–J47, AA47–AM47, D51–J51, AA51–AM51, D81–J81, AA81–AM81 | 0 (Summe über Schichten ohne Wert) | kein Wert | Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus. |

### 07_MUS_3Z

| Zellen | leer ist eine von | Vorlage zeigt | Webfassung zeigt | Begründung |
|---|---|---|---|---|
| C12, C23 | C7, C8, C9 | 0,00 € bzw. der Wert mit 0 an Stelle der leeren Zelle | Angabe fehlt | Ohne die Buchwerte der Zeiträume gibt es keine Bezugsgröße; ein Betrag auf Grundlage von 0 € wäre irreführend. |
| C20 | C7, C8, C9, C18 | 0,00 € bzw. der Wert mit 0 an Stelle der leeren Zelle | Angabe fehlt | Der zulässige Fehler setzt die Buchwerte und die Signifikanzschwelle voraus. |
| C22 | C7, C8, C9, C21 | 0,00 € bzw. der Wert mit 0 an Stelle der leeren Zelle | Angabe fehlt | Der voraussichtliche Fehler setzt die Buchwerte und die voraussichtliche Fehlerquote voraus. |
| C27 | C7, C8, C9, C24, C25, C26 | Standardabweichung mit 0 an Stelle der leeren Zelle | Angabe fehlt | Die gewichtete Standardabweichung setzt Buchwert und Standardabweichung aller Zeiträume voraus. |
| C29, C35, C36, C37, C38, C43, C44, C45 | C7, C8, C9, C21, C24, C25, C26 | Wert auf Grundlage des mit 0 gerechneten Buchwerts, AE = 0 bzw. σ_r = 0 (Gesamtumfang mindestens 30) | Angabe fehlt | Ohne Buchwerte, voraussichtliche Fehlerquote und Standardabweichungen aller Zeiträume ist der Gesamtumfang nicht bestimmt; alle Folgegrößen bleiben offen. |
| C74 | C7, C8, C9, C21, C24, C25, C26, C51 | Planumfang mal Faktor 1 bzw. mal dem Faktor allein aus dem Verhältnis der Anzahlen (ein leerer Buchwert zählt als 0) | Angabe fehlt | Der Faktor der Unterschätzung vergleicht den Ist-Buchwert des Zeitraums mit seiner Prognose; ohne beide ist die Erhöhung nicht bestimmt. |
| C39 | C8, C9, C21, C24, C25, C26 | Wert auf Grundlage des mit 0 gerechneten Buchwerts, AE = 0 bzw. σ_r = 0 (Gesamtumfang mindestens 30) | Angabe fehlt | Ohne Buchwerte, voraussichtliche Fehlerquote und Standardabweichungen aller Zeiträume ist der Gesamtumfang nicht bestimmt; alle Folgegrößen bleiben offen. |
| C42 | C7 | 0 € abzüglich des Buchwerts der hochwertigen Einheiten | Angabe fehlt | Ohne die Buchwerte der Zeiträume gibt es keine Bezugsgröße; ein Betrag auf Grundlage von 0 € wäre irreführend. |
| C58 | C7, C51, C53 | 0,00 € bzw. der Wert mit 0 an Stelle der leeren Zelle | Angabe fehlt | Ohne die Buchwerte der Zeiträume gibt es keine Bezugsgröße; ein Betrag auf Grundlage von 0 € wäre irreführend. |
| C59 | C7, C18, C51, C53 | 0,00 € bzw. der Wert mit 0 an Stelle der leeren Zelle | Angabe fehlt | Der aktualisierte zulässige Fehler setzt die Buchwerte und die Signifikanzschwelle voraus. |
| C60 | C7, C21, C51, C53 | 0,00 € bzw. der Wert mit 0 an Stelle der leeren Zelle | Angabe fehlt | Der aktualisierte voraussichtliche Fehler setzt die Buchwerte und eine voraussichtliche Fehlerquote voraus. |
| C61 | C24 | 0,0000 (leere Zelle zählt als 0) | Angabe fehlt | Ohne Standardabweichung der Stichprobe und ohne voraussichtliche Standardabweichung gibt es keinen Wert für Zeitraum 1. |
| C62 | C51, C53 | 0,00 € bzw. der Wert mit 0 an Stelle der leeren Zelle | Angabe fehlt | Ohne die Buchwerte der Zeiträume gibt es keine Bezugsgröße; ein Betrag auf Grundlage von 0 € wäre irreführend. |
| C63 | C51, C53, C55, C56 | Standardabweichung mit 0 an Stelle der leeren Zelle | Angabe fehlt | Ohne Ist-Buchwert des zweiten Zeitraums, aktualisierte Prognose für den dritten und die aktualisierten Standardabweichungen ist die Neuberechnung nach Zeitraum 1 nicht bestimmt. |
| C64 | C8, C9, C21, C24, C25, C26, C51, C53 | Nenner auf Grundlage des mit 0 gerechneten Werts | Angabe fehlt | Ohne Ist-Buchwert des zweiten Zeitraums, aktualisierte Prognose für den dritten und die aktualisierten Standardabweichungen ist die Neuberechnung nach Zeitraum 1 nicht bestimmt. |
| C65, C66, C67 | C8, C9, C21, C24, C25, C26, C51, C53, C55, C56 | Wert auf Grundlage von BV = 0 bzw. σ_r = 0 für die Zeiträume 2 und 3 (z. B. Umfang 0 oder 3) | Angabe fehlt | Ohne Ist-Buchwert des zweiten Zeitraums, aktualisierte Prognose für den dritten und die aktualisierten Standardabweichungen ist die Neuberechnung nach Zeitraum 1 nicht bestimmt. |
| C68 | C7, C24, C51, C53, C55, C56 | Standardabweichung mit 0 an Stelle der leeren Zelle | Angabe fehlt | Ohne Ist-Buchwert des zweiten Zeitraums, aktualisierte Prognose für den dritten und die aktualisierten Standardabweichungen ist die Neuberechnung nach Zeitraum 1 nicht bestimmt. |
| C69, C70, C72, C73 | C7, C18, C21, C24, C51, C53, C55, C56 | Umfang auf Grundlage des mit 0 gerechneten Werts (mindestens 30) | Angabe fehlt | Ohne Ist-Buchwert des zweiten Zeitraums, aktualisierte Prognose für den dritten und die aktualisierten Standardabweichungen ist die Neuberechnung nach Zeitraum 1 nicht bestimmt. |
| C71, C75, C76, C77, C78, C82, C83, C84 | C7, C8, C9, C21, C24, C25, C26, C18, C51, C53, C55, C56 | Wert auf Grundlage von BV = 0 bzw. σ_r = 0 für die Zeiträume 2 und 3 (z. B. Umfang 0 oder 3) | Angabe fehlt | Ohne Ist-Buchwert des zweiten Zeitraums, aktualisierte Prognose für den dritten und die aktualisierten Standardabweichungen ist die Neuberechnung nach Zeitraum 1 nicht bestimmt. |
| C106 | C7, C8, C9, C21, C24, C25, C26, C18, C51, C53, C55, C56, C90 | Planumfang mal Faktor 1 bzw. mal dem Faktor allein aus dem Verhältnis der Anzahlen (ein leerer Buchwert zählt als 0) | Angabe fehlt | Der Faktor der Unterschätzung vergleicht den Ist-Buchwert des Zeitraums mit seiner Prognose; ohne beide ist die Erhöhung nicht bestimmt. |
| C81 | C51 | 0 € abzüglich des Buchwerts der hochwertigen Einheiten | Angabe fehlt | Ohne die Buchwerte der Zeiträume gibt es keine Bezugsgröße; ein Betrag auf Grundlage von 0 € wäre irreführend. |
| C94, N4 | C7, C51, C90 | 0,00 € bzw. der Wert mit 0 an Stelle der leeren Zelle | Angabe fehlt | Ohne die Buchwerte der Zeiträume gibt es keine Bezugsgröße; ein Betrag auf Grundlage von 0 € wäre irreführend. |
| C95 | C7, C18, C51, C90 | 0,00 € bzw. der Wert mit 0 an Stelle der leeren Zelle | Angabe fehlt | Der zulässige Fehler des Geschäftsjahres setzt die Ist-Buchwerte und die Signifikanzschwelle voraus. |
| C96 | C7, C21, C51, C90 | 0,00 € bzw. der Wert mit 0 an Stelle der leeren Zelle | Angabe fehlt | Der voraussichtliche Fehler des Geschäftsjahres setzt die Ist-Buchwerte und eine voraussichtliche Fehlerquote voraus. |
| C97 | C55 | 0,0000 (leere Zelle zählt als 0) | Angabe fehlt | Ohne Standardabweichung der Stichprobe und ohne aktualisierte Standardabweichung gibt es keinen Wert für Zeitraum 2. |
| C98 | C8, C9, C21, C24, C25, C26, C51, C53, C55, C56, C90 | Nenner auf Grundlage des mit 0 gerechneten Werts | Angabe fehlt | Ohne Ist-Buchwert und aktualisierte Standardabweichung des dritten Zeitraums ist die Neuberechnung nach Zeitraum 2 nicht bestimmt; endgültige Umfänge, Hochrechnung und Würdigung bleiben offen. |
| C99 | C8, C9, C21, C24, C25, C26, C51, C53, C55, C56, C90, C92 | Wert auf Grundlage von BV₃ = 0 bzw. σ_r3 = 0 (z. B. Umfang 0, 3 oder Auffüllung auf 30) | Angabe fehlt | Ohne Ist-Buchwert und aktualisierte Standardabweichung des dritten Zeitraums ist die Neuberechnung nach Zeitraum 2 nicht bestimmt; endgültige Umfänge, Hochrechnung und Würdigung bleiben offen. |
| C100 | C7, C24, C51, C55, C90, C92 | Standardabweichung mit 0 an Stelle der leeren Zelle | Angabe fehlt | Ohne Ist-Buchwert und aktualisierte Standardabweichung des dritten Zeitraums ist die Neuberechnung nach Zeitraum 2 nicht bestimmt; endgültige Umfänge, Hochrechnung und Würdigung bleiben offen. |
| C101, C102, C105 | C7, C18, C21, C24, C51, C55, C90, C92 | Umfang auf Grundlage des mit 0 gerechneten Werts (mindestens 30) | Angabe fehlt | Ohne Ist-Buchwert und aktualisierte Standardabweichung des dritten Zeitraums ist die Neuberechnung nach Zeitraum 2 nicht bestimmt; endgültige Umfänge, Hochrechnung und Würdigung bleiben offen. |
| C104, C103, C107, C108, C109, C110, C111, C112, C116, C117, C118, C124, C125, C127, C128, C129, C132, C133, C134, C135, C136, C137, C138, N5, N7, N10, N11 | C7, C8, C9, C21, C24, C25, C26, C18, C51, C53, C55, C56, C90, C92 | Wert auf Grundlage von BV₃ = 0 bzw. σ_r3 = 0 (z. B. Umfang 0, 3 oder Auffüllung auf 30) | Angabe fehlt | Ohne Ist-Buchwert und aktualisierte Standardabweichung des dritten Zeitraums ist die Neuberechnung nach Zeitraum 2 nicht bestimmt; endgültige Umfänge, Hochrechnung und Würdigung bleiben offen. |
| C115 | C90 | 0 € abzüglich des Buchwerts der hochwertigen Einheiten | Angabe fehlt | Ohne die Buchwerte der Zeiträume gibt es keine Bezugsgröße; ein Betrag auf Grundlage von 0 € wäre irreführend. |
| C35 | C29 | begrenzter Umfang (50 bzw. 30 Einheiten), obwohl die Zelle des rechnerischen Umfangs leer ist | kein Wert | Ohne rechnerischen Umfang gibt es nichts zu begrenzen; der begrenzte Umfang allein sähe wie ein Ergebnis aus. |
| C70 | C69 | begrenzter Umfang (50 bzw. 30 Einheiten), obwohl die Zelle des rechnerischen Umfangs leer ist | kein Wert | Ohne rechnerischen Umfang gibt es nichts zu begrenzen; der begrenzte Umfang allein sähe wie ein Ergebnis aus. |
| C102 | C101 | begrenzter Umfang (50 bzw. 30 Einheiten), obwohl die Zelle des rechnerischen Umfangs leer ist | kein Wert | Ohne rechnerischen Umfang gibt es nichts zu begrenzen; der begrenzte Umfang allein sähe wie ein Ergebnis aus. |
| C36, C37, C38, C39, C43, C44, C45, C64, C65, C66, C67, C71, C72, C73, C74, C75, C76, C77, C103, C105, C106, C107, C109, C124, C78, C82, C83, C84, C98, C99, C104, C108, C125, C110, C111, C112, C116, C117, C118, C127, C128, C129, C132, C133, C134, C135, C136, C137, C138, N5, N7, N10, N11 | C29, C69, C101 | Wert auf Grundlage eines begrenzten Umfangs, den kein rechnerischer Umfang trägt | kein Wert | Der Wert baut auf dem begrenzten Umfang auf; ohne rechnerischen Umfang ist er nicht bestimmt. |
| C75 | C75 | Untergrenze 3 bzw. Auffüllung auf 30 (MAX übergeht den Text bzw. die leere Zelle des gewählten Umfangs) | kein Wert | Liefert der gewählte Ansatz keinen Umfang für den Zeitraum, gibt es nichts, was die Untergrenzen sichern könnten; ein Umfang von 3 bzw. die Auffüllung auf 30 sähe wie ein Ergebnis der Neuberechnung aus. |
| C109 | C75, C109 | Untergrenze 3 bzw. Auffüllung auf 30 (MAX übergeht den Text bzw. die leere Zelle des gewählten Umfangs) | kein Wert | Liefert der gewählte Ansatz keinen Umfang für den Zeitraum, gibt es nichts, was die Untergrenzen sichern könnten; ein Umfang von 3 bzw. die Auffüllung auf 30 sähe wie ein Ergebnis der Neuberechnung aus. |
| C78, C82, C83, C84, C98, C99, C104, C108, C125 | C75 | Wert auf Grundlage eines Umfangs für Zeitraum 2 bzw. 3, der nur aus den Untergrenzen besteht | kein Wert | Der Wert baut auf einem Umfang auf, den keine Neuberechnung ergeben hat; ohne ihn ist er nicht bestimmt. |
| C110, C111, C112, C116, C117, C118, C127, C128, C129, C132, C133, C134, C135, C136, C137, C138, N5, N7, N10, N11 | C75, C109 | Wert auf Grundlage eines Umfangs für Zeitraum 2 bzw. 3, der nur aus den Untergrenzen besteht | kein Wert | Der Wert baut auf einem Umfang auf, den keine Neuberechnung ergeben hat; ohne ihn ist er nicht bestimmt. |
| C127 | C49, C88, C122 | 0,00 € (die Fehlersumme der Stichprobe fehlt; N(…) zählt sie als 0) | kein Wert | Ohne Fehlersumme der Stichprobe gibt es nichts hochzurechnen; ein extrapolierter Fehler von 0 € sähe wie ein Prüfergebnis aus. |

### 08_SRS_1Z

| Zellen | leer ist eine von | Vorlage zeigt | Webfassung zeigt | Begründung |
|---|---|---|---|---|
| C7, N4 | C7 | 0 (Verknüpfung auf das leere Blatt 02) | Angabe fehlt | Ohne Buchwert der Grundgesamtheit gibt es keine Bezugsgröße; ein Ergebnis auf Grundlage von 0 € wäre irreführend. |
| C8 | C8 | 0 (Verknüpfung auf das leere Blatt 02) | Angabe fehlt | Ohne Angabe ist die Anzahl der Einheiten der Grundgesamtheit unbekannt, nicht null. |
| C12 | C7 | 0 € abzüglich des Buchwerts der umfassenden Schicht | Angabe fehlt | Ohne Buchwert der Grundgesamtheit gibt es keine Bezugsgröße; ein Ergebnis auf Grundlage von 0 € wäre irreführend. |
| C13 | C8 | 0 abzüglich der Einheiten der umfassenden Schicht | Angabe fehlt | Ohne Angabe ist die Anzahl der Einheiten der Grundgesamtheit unbekannt, nicht null. |
| C21 | C7, C19 | 0,00 € (leere Zelle zählt als 0) | Angabe fehlt | Der zulässige Fehler setzt Buchwert und Signifikanzschwelle voraus. |
| C23 | C7, C22 | 0,00 € (leere Zelle zählt als 0) | Angabe fehlt | Der voraussichtliche Fehler setzt Buchwert und voraussichtliche Fehlerquote voraus. |
| C26 | C8, C22, C25 | Umfang mit N_s ≤ 0, AE = 0 bzw. σ_e = 0 (z. B. 0, 1 oder 16) | Angabe fehlt | Ohne Anzahl der Einheiten, voraussichtliche Fehlerquote und Standardabweichung ist der Stichprobenumfang nicht bestimmt; alle Folgegrößen bleiben offen. |
| C34, C35, N10 | C8, C22, C25 | Mindestumfang bzw. der mit 0 berechnete Umfang, gegebenenfalls begrenzt | Angabe fehlt | Ohne Anzahl der Einheiten, voraussichtliche Fehlerquote und Standardabweichung ist der Stichprobenumfang nicht bestimmt; alle Folgegrößen bleiben offen. |
| C42, C43, N5 | C7 | Hochrechnung auf Grundlage von 0 € abzüglich des Buchwerts der umfassenden Schicht (negativer Betrag) | Angabe fehlt | Ohne Buchwert der Grundgesamtheit gibt es keine Bezugsgröße; ein Ergebnis auf Grundlage von 0 € wäre irreführend. |
| C44, N7, C49, C52, C53 | C8, C22, C25 | Wert auf Grundlage des mit 0 gerechneten Umfangs bzw. einer Zufallsschicht mit N_s ≤ 0 | Angabe fehlt | Ohne Anzahl der Einheiten, voraussichtliche Fehlerquote und Standardabweichung ist der Stichprobenumfang nicht bestimmt; alle Folgegrößen bleiben offen. |
| C47, C48 | C7, C8, C22, C25 | Wert auf Grundlage des mit 0 gerechneten Buchwerts bzw. Umfangs | Angabe fehlt | Ohne Anzahl der Einheiten, voraussichtliche Fehlerquote und Standardabweichung ist der Stichprobenumfang nicht bestimmt; alle Folgegrößen bleiben offen. |
| C42 | C37 | 0,00 € (die Fehlersumme der Stichprobe fehlt; N(…) zählt sie als 0) | kein Wert | Ohne Fehlersumme der Stichprobe gibt es nichts hochzurechnen; ein extrapolierter Fehler von 0 € sähe wie ein Prüfergebnis aus. |

### 09_SRS_1Z_S

| Zellen | leer ist eine von | Vorlage zeigt | Webfassung zeigt | Begründung |
|---|---|---|---|---|
| C15 | 02_Grundgesamtheit!C51 | Buchwert der Grundgesamtheit abzüglich 0 € (leeres Blatt 02) | Angabe fehlt | Ohne angepasste Grundgesamtheit in Blatt 02 gibt es nichts abzugleichen. |
| C23 | C21 | 0,00 € (leere Zelle zählt als 0) | Angabe fehlt | Der zulässige Fehler setzt die Signifikanzschwelle voraus. |
| C25 | C24 | 0,00 € (leere Zelle zählt als 0) | Angabe fehlt | Der voraussichtliche Fehler setzt die voraussichtliche Fehlerquote voraus. |
| D29–J29, AA29–AM29 | D28–J28, AA28–AM28 | 0 (σ_eh einer belegten Schicht zählt als 0) | Angabe fehlt | Fehlt die Standardabweichung einer belegten Schicht, ist die gewichtete Standardabweichung nicht bestimmt. |
| C29, C30 | D28–J28, AA28–AM28 | Wert ohne den Beitrag der Schicht mit fehlender Standardabweichung | Angabe fehlt | Fehlt die Standardabweichung einer belegten Schicht, ist die gewichtete Standardabweichung nicht bestimmt. |
| C31, C39, C41, N10, C53, N7, C58 | C24, D28–J28, AA28–AM28 | Wert auf Grundlage des mit AE = 0 bzw. σ_eh = 0 berechneten Umfangs (mindestens der Mindestumfang) | Angabe fehlt | Ohne voraussichtliche Fehlerquote und Standardabweichung jeder belegten Schicht ist der Stichprobenumfang nicht bestimmt; alle Folgegrößen bleiben offen. |
| D41–J41, AA41–AM41, D42–J42, AA42–AM42 | C24, D28–J28, AA28–AM28 | Wert auf Grundlage des mit AE = 0 bzw. σ_eh = 0 berechneten Umfangs (mindestens der Mindestumfang) | Angabe fehlt | Ohne voraussichtliche Fehlerquote und Standardabweichung jeder belegten Schicht ist der Stichprobenumfang nicht bestimmt; alle Folgegrößen bleiben offen. |
| D49–J49, AA49–AM49 | D13–J13, AA13–AM13 | 0 € (Buchwert einer belegten Schicht zählt als 0) | Angabe fehlt | Fehlt der Buchwert einer belegten Schicht, lässt sich ihr Fehler nicht hochrechnen; die Vorlage rechnet für diese Schicht mit 0 €. |
| C49, C52, N5, C59, C60, N11 | D13–J13, AA13–AM13 | Wert ohne den Beitrag der Schicht mit fehlendem Buchwert | Angabe fehlt | Fehlt der Buchwert einer belegten Schicht, lässt sich ihr Fehler nicht hochrechnen; die Vorlage rechnet für diese Schicht mit 0 €. |
| C56, C57, C61, C62 | C24, D28–J28, AA28–AM28, D13–J13, AA13–AM13 | Wert auf Grundlage des mit 0 berechneten Umfangs bzw. ohne den Beitrag der Schicht mit fehlendem Buchwert | Angabe fehlt | Ohne voraussichtliche Fehlerquote und Standardabweichung jeder belegten Schicht ist der Stichprobenumfang nicht bestimmt; alle Folgegrößen bleiben offen. |
| C12, C29, C50 | D12–J12, AA12–AM12 | 0 (Summe über Schichten ohne Wert) | kein Wert | Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus. |
| C13 | D13–J13, AA13–AM13 | 0 (Summe über Schichten ohne Wert) | kein Wert | Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus. |
| C41 | D41–J41, AA41–AM41 | 0 (Summe über Schichten ohne Wert) | kein Wert | Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus. |
| C45 | D45–J45, AA45–AM45 | 0 (Summe über Schichten ohne Wert) | kein Wert | Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus. |
| C46 | D46–J46, AA46–AM46 | 0 (Summe über Schichten ohne Wert) | kein Wert | Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus. |
| C14, N4, C15, C23, C25 | C13 | Wert auf Grundlage einer Summe der Buchwerte von 0 € (nur die umfassende Schicht) | kein Wert | Der Wert baut auf einer Summe auf, zu der keine Schicht beiträgt; ohne sie ist er nicht bestimmt. |
| C26, C31, C39, C53, N7, C58 | C13 | Stichprobenumfang und Genauigkeit auf Grundlage eines zulässigen Fehlers ohne die Buchwerte der Zufallsschichten | kein Wert | Der Wert baut auf einer Summe auf, zu der keine Schicht beiträgt; ohne sie ist er nicht bestimmt. |
| D41–J41, AA41–AM41 | C13 | Stichprobenumfang und Genauigkeit auf Grundlage eines zulässigen Fehlers ohne die Buchwerte der Zufallsschichten | kein Wert | Der Wert baut auf einer Summe auf, zu der keine Schicht beiträgt; ohne sie ist er nicht bestimmt. |
| N10 | C41 | Einheiten der umfassenden Schicht bzw. 0 (Summe der Schichtumfänge ohne Umfang je Schicht) | kein Wert | Der Wert baut auf einer Summe auf, zu der keine Schicht beiträgt; ohne sie ist er nicht bestimmt. |
| D42–J42, AA42–AM42 | D41–J41, AA41–AM41 | „✔ ≥ 3“ (Excel wertet die leere Textzelle im Vergleich größer als jede Zahl) | kein Wert | Ohne Stichprobenumfang der Schicht gibt es nichts zu prüfen; ein bestandener Prüfhinweis wäre irreführend. |
| C49 | C46 | 0,00 € (keine Schicht trägt eine Fehlersumme) | kein Wert | Solange keine Schicht eine Fehlersumme trägt, gibt es nichts hochzurechnen; ein extrapolierter Fehler von 0 € sähe wie ein Prüfergebnis aus. |
| D49–J49, AA49–AM49 | C46 | 0,00 € (keine Schicht trägt eine Fehlersumme) | kein Wert | Solange keine Schicht eine Fehlersumme trägt, gibt es nichts hochzurechnen; ein extrapolierter Fehler von 0 € sähe wie ein Prüfergebnis aus. |

### 10_SRS_2Z

| Zellen | leer ist eine von | Vorlage zeigt | Webfassung zeigt | Begründung |
|---|---|---|---|---|
| C12 | C7 | 0 € abzüglich des Buchwerts der umfassenden Schicht | Angabe fehlt | Ohne die Buchwerte der Zeiträume gibt es keine Bezugsgröße; ein Betrag auf Grundlage von 0 € wäre irreführend. |
| C13 | C8 | 0 abzüglich der Einheiten der umfassenden Schicht | Angabe fehlt | Ohne Angabe ist die Anzahl der Einheiten eines Zeitraums unbekannt, nicht null. |
| C16 | C7, C14 | 0 bzw. der Wert mit 0 an Stelle der leeren Zelle | Angabe fehlt | Ohne die Buchwerte der Zeiträume gibt es keine Bezugsgröße; ein Betrag auf Grundlage von 0 € wäre irreführend. |
| C17 | C8, C15 | 0 bzw. der Wert mit 0 an Stelle der leeren Zelle | Angabe fehlt | Ohne Angabe ist die Anzahl der Einheiten eines Zeitraums unbekannt, nicht null. |
| C25 | C7, C14, C23 | 0 bzw. der Wert mit 0 an Stelle der leeren Zelle | Angabe fehlt | Der zulässige Fehler setzt beide Buchwerte und die Signifikanzschwelle voraus. |
| C27 | C7, C14, C26 | 0 bzw. der Wert mit 0 an Stelle der leeren Zelle | Angabe fehlt | Der voraussichtliche Fehler setzt beide Buchwerte und die voraussichtliche Fehlerquote voraus. |
| C28 | C7, C14 | Prüfhinweis auf Grundlage nur eines Buchwerts | Angabe fehlt | Ohne die Buchwerte der Zeiträume gibt es keine Bezugsgröße; ein Betrag auf Grundlage von 0 € wäre irreführend. |
| C31 | C8, C15, C29, C30 | gewichtete Standardabweichung mit 0 an Stelle der leeren Zelle | Angabe fehlt | Die gewichtete Standardabweichung setzt Anzahl der Einheiten und Standardabweichung beider Zeiträume voraus. |
| C33, C41, C42, C43, C71 | C7, C8, C14, C15, C26, C29, C30 | Wert auf Grundlage von BV = 0, N = 0, AE = 0 bzw. σ_e = 0 (z. B. Mindestumfang oder begrenzter Umfang) | Angabe fehlt | Ohne Buchwerte, Anzahl der Einheiten, voraussichtliche Fehlerquote und Standardabweichungen beider Zeiträume ist der Gesamtumfang nicht bestimmt; alle Folgegrößen bleiben offen. |
| C54 | C49 | 0 € abzüglich des Buchwerts der umfassenden Schicht | Angabe fehlt | Ohne die Buchwerte der Zeiträume gibt es keine Bezugsgröße; ein Betrag auf Grundlage von 0 € wäre irreführend. |
| C55 | C50 | 0 abzüglich der Einheiten der umfassenden Schicht | Angabe fehlt | Ohne Angabe ist die Anzahl der Einheiten eines Zeitraums unbekannt, nicht null. |
| C58, N4 | C7, C49 | 0 bzw. der Wert mit 0 an Stelle der leeren Zelle | Angabe fehlt | Ohne die Buchwerte der Zeiträume gibt es keine Bezugsgröße; ein Betrag auf Grundlage von 0 € wäre irreführend. |
| C59 | C7, C23, C49 | 0 bzw. der Wert mit 0 an Stelle der leeren Zelle | Angabe fehlt | Der aktualisierte zulässige Fehler setzt beide Ist-Buchwerte und die Signifikanzschwelle voraus. |
| C60 | C7, C26, C49 | 0 bzw. der Wert mit 0 an Stelle der leeren Zelle | Angabe fehlt | Der aktualisierte voraussichtliche Fehler setzt beide Ist-Buchwerte und eine voraussichtliche Fehlerquote voraus. |
| C61 | C29 | 0,00 € (leere Zelle zählt als 0) | Angabe fehlt | Ohne Standardabweichung der Stichprobe und ohne voraussichtliche Standardabweichung gibt es keinen Wert für Zeitraum 1. |
| C62 | C7, C8, C14, C15, C23, C26, C29, C30, C49 | Nenner auf Grundlage des mit 0 gerechneten Werts | Angabe fehlt | Ohne Ist-Werte und aktualisierte Standardabweichung des zweiten Zeitraums ist die Neuberechnung nicht bestimmt; die Folgegrößen bleiben offen. |
| C64 | C8, C50 | 0 bzw. der Wert mit 0 an Stelle der leeren Zelle | Angabe fehlt | Ohne Angabe ist die Anzahl der Einheiten eines Zeitraums unbekannt, nicht null. |
| C65 | C8, C29, C50, C56 | gewichtete Standardabweichung mit 0 an Stelle der leeren Zelle | Angabe fehlt | Die gewichtete Standardabweichung setzt Anzahl der Einheiten und Standardabweichung beider Zeiträume voraus. |
| C66, C68, C70 | C7, C8, C23, C26, C29, C49, C50, C56 | Umfang auf Grundlage des mit 0 gerechneten Werts (mindestens der Mindestumfang) | Angabe fehlt | Ohne Ist-Werte und aktualisierte Standardabweichung des zweiten Zeitraums ist die Neuberechnung nicht bestimmt; die Folgegrößen bleiben offen. |
| C63, C69, C72, C73, C74, C75, C76, N10 | C7, C8, C14, C15, C23, C26, C29, C30, C49, C50, C56 | Wert auf Grundlage von BV₂ = 0, N₂ = 0 bzw. σ_e2 = 0 (z. B. Umfang 0, 3 oder Auffüllung auf 30) | Angabe fehlt | Ohne Ist-Werte und aktualisierte Standardabweichung des zweiten Zeitraums ist die Neuberechnung nicht bestimmt; die Folgegrößen bleiben offen. |
| C83, C84, C91, C92, N5, N11 | C7, C49 | Hochrechnung auf Grundlage von 0 € abzüglich des Buchwerts der umfassenden Schicht (negativer Betrag) | Angabe fehlt | Ohne die Buchwerte der Zeiträume gibt es keine Bezugsgröße; ein Betrag auf Grundlage von 0 € wäre irreführend. |
| C85, C88, C89, C90, C93, N7 | C7, C8, C14, C15, C23, C26, C29, C30, C49, C50, C56 | Wert auf Grundlage der mit 0 gerechneten Umfänge bzw. einer Zufallsschicht mit N ≤ 0 | Angabe fehlt | Ohne die Angaben zum Gesamtumfang und zur Neuberechnung für Zeitraum 2 sind die endgültigen Umfänge nicht bestimmt; Genauigkeit, Fehlergrenzen und Würdigung bleiben offen. |
| C94 | C7, C8, C14, C15, C26, C29, C30, C49, C50, C56 | Würdigung auf Grundlage der mit 0 gerechneten Genauigkeit | Angabe fehlt | Ohne die Angaben zum Gesamtumfang und zur Neuberechnung für Zeitraum 2 sind die endgültigen Umfänge nicht bestimmt; Genauigkeit, Fehlergrenzen und Würdigung bleiben offen. |
| C73, C74, C75, C76, N10 | C63 | Untergrenzen (mindestens 3, Auffüllung auf 30) bzw. die darauf aufbauende Gesamtstichprobe und ihre Prüfhinweise, obwohl die Standardneuberechnung keinen Umfang ergibt (z. B. ohne Konfidenzniveau oder ohne Einheiten der Zufallsschicht in Zeitraum 1) | kein Wert | Ergibt die Standardneuberechnung keinen Umfang, ohne dass ihr Nenner als nicht positiv ausgewiesen ist, bleiben in der Vorlage nur die Untergrenzen (MAX übergeht den leeren Bezug); als anzuwendender Umfang hätten sie keine Grundlage. |
| C83 | C45, C78 | 0,00 € (kein Zeitraum trägt eine Fehlersumme) | kein Wert | Solange kein Zeitraum eine Fehlersumme trägt, gibt es nichts hochzurechnen; ein extrapolierter Fehler von 0 € sähe wie ein Prüfergebnis aus. |

### 11_SRS_2Z_S

| Zellen | leer ist eine von | Vorlage zeigt | Webfassung zeigt | Begründung |
|---|---|---|---|---|
| C24, C62 | C22 | 0,00 € (leere Zelle zählt als 0) | Angabe fehlt | Der zulässige Fehler setzt die Signifikanzschwelle voraus. |
| C26, C63 | C25 | 0,00 € (leere Zelle zählt als 0) | Angabe fehlt | Der voraussichtliche Fehler setzt die voraussichtliche Fehlerquote voraus. |
| D31–J31, AA31–AM31 | D29–J29, AA29–AM29, D30–J30, AA30–AM30 | 0 bzw. nur der Beitrag des anderen Zeitraums (σ_eh einer belegten Schicht zählt als 0) | Angabe fehlt | Fehlt die Standardabweichung einer für den Zeitraum belegten Schicht, ist die Streuung nicht bestimmt; 0 wäre eine Annahme zugunsten eines kleineren Umfangs. |
| C31, C32 | D29–J29, AA29–AM29, D30–J30, AA30–AM30 | Wert mit σ = 0 für die Schicht mit fehlender Standardabweichung | Angabe fehlt | Fehlt die Standardabweichung einer für den Zeitraum belegten Schicht, ist die Streuung nicht bestimmt; 0 wäre eine Annahme zugunsten eines kleineren Umfangs. |
| C34, C42, C44, C45, C66 | C25, D29–J29, AA29–AM29, D30–J30, AA30–AM30 | Wert auf Grundlage des mit AE = 0 bzw. σ_eh = 0 berechneten Gesamtumfangs (mindestens der Mindestumfang) | Angabe fehlt | Ohne voraussichtliche Fehlerquote und Standardabweichung jeder belegten Schicht ist der Gesamtumfang nicht bestimmt; seine Aufteilung und alle Folgegrößen bleiben offen. |
| D44–J44, AA44–AM44, D45–J45, AA45–AM45, D46–J46, AA46–AM46, D66–J66, AA66–AM66 | C25, D29–J29, AA29–AM29, D30–J30, AA30–AM30 | Wert auf Grundlage des mit AE = 0 bzw. σ_eh = 0 berechneten Gesamtumfangs (mindestens der Mindestumfang) | Angabe fehlt | Ohne voraussichtliche Fehlerquote und Standardabweichung jeder belegten Schicht ist der Gesamtumfang nicht bestimmt; seine Aufteilung und alle Folgegrößen bleiben offen. |
| D65–J65, AA65–AM65 | D29–J29, AA29–AM29 | 0 (weder s_eh noch σ_eh1 angegeben; die leere Zelle zählt als 0) | Angabe fehlt | Fehlt die Standardabweichung einer für den Zeitraum belegten Schicht, ist die Streuung nicht bestimmt; 0 wäre eine Annahme zugunsten eines kleineren Umfangs. |
| D67–J67, AA67–AM67 | D59–J59, AA59–AM59 | 0 (σ_eh2 einer belegten Schicht zählt als 0) | Angabe fehlt | Fehlt die Standardabweichung einer für den Zeitraum belegten Schicht, ist die Streuung nicht bestimmt; 0 wäre eine Annahme zugunsten eines kleineren Umfangs. |
| C67 | D59–J59, AA59–AM59 | Wert mit σ = 0 für die Schicht mit fehlender Standardabweichung | Angabe fehlt | Fehlt die Standardabweichung einer für den Zeitraum belegten Schicht, ist die Streuung nicht bestimmt; 0 wäre eine Annahme zugunsten eines kleineren Umfangs. |
| C68 | C22, C25, D29–J29, AA29–AM29, D30–J30, AA30–AM30 | Nenner auf Grundlage von TE = 0, AE = 0 bzw. des mit 0 berechneten Umfangs für Zeitraum 1 | Angabe fehlt | Ohne Signifikanzschwelle, voraussichtliche Fehlerquote und Standardabweichung jeder belegten Schicht ist die Neuberechnung für Zeitraum 2 nicht bestimmt; die endgültigen Umfänge und die Genauigkeit bleiben offen. |
| C69, C76, C77, C78, C80, C81, N10 | C22, C25, D29–J29, AA29–AM29, D30–J30, AA30–AM30, D59–J59, AA59–AM59 | Wert auf Grundlage von TE = 0, AE = 0 bzw. σ_eh = 0 (z. B. Umfang 3 je Schicht oder der Mindestumfang) | Angabe fehlt | Ohne Signifikanzschwelle, voraussichtliche Fehlerquote und Standardabweichung jeder belegten Schicht ist die Neuberechnung für Zeitraum 2 nicht bestimmt; die endgültigen Umfänge und die Genauigkeit bleiben offen. |
| D70–J70, AA70–AM70 | D29–J29, AA29–AM29, D59–J59, AA59–AM59 | 0 bzw. nur der Beitrag des anderen Zeitraums (Standardabweichung einer belegten Schicht zählt als 0) | Angabe fehlt | Fehlt die Standardabweichung einer für den Zeitraum belegten Schicht, ist die Streuung nicht bestimmt; 0 wäre eine Annahme zugunsten eines kleineren Umfangs. |
| C70 | D29–J29, AA29–AM29, D59–J59, AA59–AM59 | Wert mit σ = 0 für die Schicht mit fehlender Standardabweichung | Angabe fehlt | Fehlt die Standardabweichung einer für den Zeitraum belegten Schicht, ist die Streuung nicht bestimmt; 0 wäre eine Annahme zugunsten eines kleineren Umfangs. |
| C72, C74 | C22, C25, D29–J29, AA29–AM29, D59–J59, AA59–AM59 | Wert auf Grundlage von TE = 0, AE = 0 bzw. σ_eh = 0 (z. B. Umfang 3 je Schicht oder der Mindestumfang) | Angabe fehlt | Ohne Signifikanzschwelle, voraussichtliche Fehlerquote und Standardabweichung jeder belegten Schicht ist die Neuberechnung für Zeitraum 2 nicht bestimmt; die endgültigen Umfänge und die Genauigkeit bleiben offen. |
| D76–J76, AA76–AM76, D77–J77, AA77–AM77, D78–J78, AA78–AM78, D79–J79, AA79–AM79 | C22, C25, D29–J29, AA29–AM29, D30–J30, AA30–AM30, D59–J59, AA59–AM59 | Wert auf Grundlage von TE = 0, AE = 0 bzw. σ_eh = 0 (z. B. Umfang 3 je Schicht oder der Mindestumfang) | Angabe fehlt | Ohne Signifikanzschwelle, voraussichtliche Fehlerquote und Standardabweichung jeder belegten Schicht ist die Neuberechnung für Zeitraum 2 nicht bestimmt; die endgültigen Umfänge und die Genauigkeit bleiben offen. |
| D89–J89, AA89–AM89 | D12–J12, AA12–AM12, D58–J58, AA58–AM58 | 0 € bzw. nur der Beitrag des anderen Zeitraums (Buchwert einer belegten Schicht zählt als 0) | Angabe fehlt | Fehlt der Buchwert einer belegten Schicht, lässt sich ihr Fehler nicht hochrechnen; die Vorlage rechnet für diese Schicht mit 0 €. |
| C89, C92, N5, C99, C100, N11 | D12–J12, AA12–AM12, D58–J58, AA58–AM58 | Wert ohne den Beitrag der Schicht mit fehlendem Buchwert | Angabe fehlt | Fehlt der Buchwert einer belegten Schicht, lässt sich ihr Fehler nicht hochrechnen; die Vorlage rechnet für diese Schicht mit 0 €. |
| C90, C93, N7, C98 | C22, C25, D29–J29, AA29–AM29, D30–J30, AA30–AM30, D59–J59, AA59–AM59 | Wert auf Grundlage der mit 0 berechneten Umfänge je Schicht | Angabe fehlt | Ohne Signifikanzschwelle, voraussichtliche Fehlerquote und Standardabweichung jeder belegten Schicht ist die Neuberechnung für Zeitraum 2 nicht bestimmt; die endgültigen Umfänge und die Genauigkeit bleiben offen. |
| D90–J90, AA90–AM90 | C22, C25, D29–J29, AA29–AM29, D30–J30, AA30–AM30, D59–J59, AA59–AM59 | Wert auf Grundlage der mit 0 berechneten Umfänge je Schicht | Angabe fehlt | Ohne Signifikanzschwelle, voraussichtliche Fehlerquote und Standardabweichung jeder belegten Schicht ist die Neuberechnung für Zeitraum 2 nicht bestimmt; die endgültigen Umfänge und die Genauigkeit bleiben offen. |
| C96, C97, C101, C102 | C22, C25, D29–J29, AA29–AM29, D30–J30, AA30–AM30, D59–J59, AA59–AM59, D12–J12, AA12–AM12, D58–J58, AA58–AM58 | Wert auf Grundlage der mit 0 berechneten Umfänge bzw. ohne den Beitrag der Schicht mit fehlendem Buchwert | Angabe fehlt | Ohne Signifikanzschwelle, voraussichtliche Fehlerquote und Standardabweichung jeder belegten Schicht ist die Neuberechnung für Zeitraum 2 nicht bestimmt; die endgültigen Umfänge und die Genauigkeit bleiben offen. |
| C11 | D11–J11, AA11–AM11 | 0 (Summe über Schichten ohne Wert) | kein Wert | Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus. |
| C12 | D12–J12, AA12–AM12 | 0 (Summe über Schichten ohne Wert) | kein Wert | Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus. |
| C13 | D13–J13, AA13–AM13 | 0 (Summe über Schichten ohne Wert) | kein Wert | Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus. |
| C14 | D14–J14, AA14–AM14 | 0 (Summe über Schichten ohne Wert) | kein Wert | Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus. |
| C31 | D31–J31, AA31–AM31, D11–J11, AA11–AM11, D13–J13, AA13–AM13 | 0 (Summe über Schichten ohne Wert) | kein Wert | Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus. |
| C44 | D44–J44, AA44–AM44 | 0 (Summe über Schichten ohne Wert) | kein Wert | Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus. |
| C45 | D45–J45, AA45–AM45 | 0 (Summe über Schichten ohne Wert) | kein Wert | Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus. |
| C49 | D49–J49, AA49–AM49 | 0 (Summe über Schichten ohne Wert) | kein Wert | Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus. |
| C50 | D50–J50, AA50–AM50 | 0 (Summe über Schichten ohne Wert) | kein Wert | Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus. |
| C57 | D57–J57, AA57–AM57 | 0 (Summe über Schichten ohne Wert) | kein Wert | Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus. |
| C58 | D58–J58, AA58–AM58 | 0 (Summe über Schichten ohne Wert) | kein Wert | Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus. |
| C66 | D66–J66, AA66–AM66, D11–J11, AA11–AM11 | 0 (Summe über Schichten ohne Wert) | kein Wert | Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus. |
| C67 | D67–J67, AA67–AM67, D57–J57, AA57–AM57 | 0 (Summe über Schichten ohne Wert) | kein Wert | Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus. |
| C70 | D70–J70, AA70–AM70, D11–J11, AA11–AM11, D57–J57, AA57–AM57 | 0 (Summe über Schichten ohne Wert) | kein Wert | Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus. |
| C76 | D76–J76, AA76–AM76 | 0 (Summe über Schichten ohne Wert) | kein Wert | Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus. |
| C77 | D77–J77, AA77–AM77 | 0 (Summe über Schichten ohne Wert) | kein Wert | Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus. |
| C78 | D78–J78, AA78–AM78 | 0 (Summe über Schichten ohne Wert) | kein Wert | Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus. |
| C84 | D84–J84, AA84–AM84 | 0 (Summe über Schichten ohne Wert) | kein Wert | Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus. |
| C85 | D85–J85, AA85–AM85 | 0 (Summe über Schichten ohne Wert) | kein Wert | Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus. |
| C15, C16, C24, C26, C27, C32, C34, C42 | C11, C12, C13, C14 | Wert auf Grundlage einer Summe von 0 über Schichten ohne Wert | kein Wert | Der Wert baut auf einer Summe auf, zu der keine Schicht beiträgt; ohne sie ist er nicht bestimmt. |
| D44–J44, AA44–AM44, D45–J45, AA45–AM45, D66–J66, AA66–AM66 | C11, C12, C13, C14 | Wert auf Grundlage einer Summe von 0 über Schichten ohne Wert | kein Wert | Der Wert baut auf einer Summe auf, zu der keine Schicht beiträgt; ohne sie ist er nicht bestimmt. |
| C61, N4, C62, C63, C71, C72, C74 | C11, C12, C13, C14, C57, C58 | Wert auf Grundlage einer Summe von 0 über Schichten ohne Wert | kein Wert | Der Wert baut auf einer Summe auf, zu der keine Schicht beiträgt; ohne sie ist er nicht bestimmt. |
| D76–J76, AA76–AM76 | C11, C12, C13, C14, C57, C58 | Wert auf Grundlage einer Summe von 0 über Schichten ohne Wert | kein Wert | Der Wert baut auf einer Summe auf, zu der keine Schicht beiträgt; ohne sie ist er nicht bestimmt. |
| C68, C69 | C11, C12, C13, C14, C57, C58, C66, C67 | Nenner bzw. Umfang des Standardansatzes auf Grundlage einer Summe von 0 (z. B. ohne Umfang je Schicht für Zeitraum 1 bei „TE ≤ AE“) | kein Wert | Der Wert baut auf einer Summe auf, zu der keine Schicht beiträgt; ohne sie ist er nicht bestimmt. |
| D46–J46, AA46–AM46 | D44–J44, AA44–AM44 | „✔ ≥ 3“ (Excel wertet die leere Textzelle im Vergleich größer als jede Zahl) | kein Wert | Ohne Stichprobenumfang der Schicht gibt es nichts zu prüfen; ein bestandener Prüfhinweis wäre irreführend. |
| D79–J79, AA79–AM79 | D77–J77, AA77–AM77 | „✔ ≥ 3“ (Excel wertet die leere Textzelle im Vergleich größer als jede Zahl) | kein Wert | Ohne Stichprobenumfang der Schicht gibt es nichts zu prüfen; ein bestandener Prüfhinweis wäre irreführend. |
| D77–J77, AA77–AM77 | C69, C74, D45–J45, AA45–AM45 | 3 (Untergrenze je Schicht, obwohl es keinen Gesamtumfang gibt, z. B. bei „TE ≤ AE“) bzw. Umfang auf Grundlage einer Summe von 0 | kein Wert | Ohne Gesamtumfang gibt es für Zeitraum 2 nichts aufzuteilen; die Untergrenze von 3 Einheiten je Schicht hätte als anzuwendender Umfang keine Grundlage. |
| D78–J78, AA78–AM78 | D44–J44, AA44–AM44, D76–J76, AA76–AM76 | Wert auf Grundlage einer Summe von 0 über Schichten ohne Wert | kein Wert | Der Wert baut auf einer Summe auf, zu der keine Schicht beiträgt; ohne sie ist er nicht bestimmt. |
| C80, C81, N10 | C77, C78 | Gesamtstichprobe bzw. ihr Prüfhinweis auf Grundlage einer Summe der Schichtumfänge von 0 | kein Wert | Der Wert baut auf einer Summe auf, zu der keine Schicht beiträgt; ohne sie ist er nicht bestimmt. |
| D89–J89, AA89–AM89 | C50, C85 | 0,00 € (keine Schicht trägt eine Fehlersumme) | kein Wert | Solange keine Schicht eine Fehlersumme trägt, gibt es nichts hochzurechnen; ein extrapolierter Fehler von 0 € sähe wie ein Prüfergebnis aus. |
| D90–J90, AA90–AM90 | D77–J77, AA77–AM77, D78–J78, AA78–AM78 | Beitrag zur Genauigkeit auf Grundlage eines Umfangs je Schicht, der auf einer Summe von 0 aufbaut | kein Wert | Der Wert baut auf einer Summe auf, zu der keine Schicht beiträgt; ohne sie ist er nicht bestimmt. |
| C89 | C11, C57, D89–J89, AA89–AM89 | Hochrechnung bzw. Genauigkeit allein aus einem Zeitraum oder aus einer Summe von 0 (z. B. Genauigkeit 0 € ohne Umfang je Schicht bei „TE ≤ AE“) | kein Wert | Hochrechnung und Genauigkeit gelten für das Geschäftsjahr; ist für einen der beiden Zeiträume keine Schicht belegt oder trägt keine belegte Schicht einen Wert, entstünden sie allein aus dem anderen Zeitraum bzw. aus einer Summe von 0. |
| C90 | C11, C57, D90–J90, AA90–AM90 | Hochrechnung bzw. Genauigkeit allein aus einem Zeitraum oder aus einer Summe von 0 (z. B. Genauigkeit 0 € ohne Umfang je Schicht bei „TE ≤ AE“) | kein Wert | Hochrechnung und Genauigkeit gelten für das Geschäftsjahr; ist für einen der beiden Zeiträume keine Schicht belegt oder trägt keine belegte Schicht einen Wert, entstünden sie allein aus dem anderen Zeitraum bzw. aus einer Summe von 0. |
| C92, N5 | C89 | Hochrechnung bzw. Genauigkeit allein aus einem Zeitraum oder aus einer Summe von 0 (z. B. Genauigkeit 0 € ohne Umfang je Schicht bei „TE ≤ AE“) | kein Wert | Hochrechnung und Genauigkeit gelten für das Geschäftsjahr; ist für einen der beiden Zeiträume keine Schicht belegt oder trägt keine belegte Schicht einen Wert, entstünden sie allein aus dem anderen Zeitraum bzw. aus einer Summe von 0. |
| C93, N7, C96, C97 | C89, C90 | Hochrechnung bzw. Genauigkeit allein aus einem Zeitraum oder aus einer Summe von 0 (z. B. Genauigkeit 0 € ohne Umfang je Schicht bei „TE ≤ AE“) | kein Wert | Hochrechnung und Genauigkeit gelten für das Geschäftsjahr; ist für einen der beiden Zeiträume keine Schicht belegt oder trägt keine belegte Schicht einen Wert, entstünden sie allein aus dem anderen Zeitraum bzw. aus einer Summe von 0. |
| C98, C99, C100, N11, C101, C102 | C11, C12, C13, C14, C57, C58, C89, C90 | Quote bzw. Würdigung auf Grundlage einer Summe von 0 über Schichten ohne Wert | kein Wert | Der Wert baut auf einer Summe auf, zu der keine Schicht beiträgt; ohne sie ist er nicht bestimmt. |

### 12_SRS_3Z

| Zellen | leer ist eine von | Vorlage zeigt | Webfassung zeigt | Begründung |
|---|---|---|---|---|
| C12 | C7 | 0 € abzüglich des Buchwerts der umfassenden Schicht | Angabe fehlt | Ohne die Buchwerte der Zeiträume gibt es keine Bezugsgröße; ein Betrag auf Grundlage von 0 € wäre irreführend. |
| C13 | C8 | 0 abzüglich der Einheiten der umfassenden Schicht | Angabe fehlt | Ohne Angabe ist die Anzahl der Einheiten unbekannt, nicht null. |
| C18 | C7, C14, C16 | Wert mit 0 an Stelle der leeren Zelle | Angabe fehlt | Ohne die Buchwerte der Zeiträume gibt es keine Bezugsgröße; ein Betrag auf Grundlage von 0 € wäre irreführend. |
| C19 | C8, C15, C17 | Wert mit 0 an Stelle der leeren Zelle | Angabe fehlt | Ohne Angabe ist die Anzahl der Einheiten unbekannt, nicht null. |
| C27 | C7, C14, C16, C25 | Wert mit 0 an Stelle der leeren Zelle | Angabe fehlt | Der zulässige Fehler setzt die Buchwerte aller Zeiträume und die Signifikanzschwelle voraus. |
| C29 | C7, C14, C16, C28 | Wert mit 0 an Stelle der leeren Zelle | Angabe fehlt | Der voraussichtliche Fehler setzt die Buchwerte aller Zeiträume und die voraussichtliche Fehlerquote voraus. |
| C30 | C7, C14, C16 | Prüfhinweis auf Grundlage der vorhandenen Buchwerte | Angabe fehlt | Ohne die Buchwerte der Zeiträume gibt es keine Bezugsgröße; ein Betrag auf Grundlage von 0 € wäre irreführend. |
| C34 | C8, C15, C17, C31, C32, C33 | gewichtete Standardabweichung mit 0 an Stelle der leeren Zelle | Angabe fehlt | Fehlt die Standardabweichung eines Zeitraums oder seine Anzahl der Einheiten, ist die gewichtete Standardabweichung nicht bestimmt. |
| C36, C44, C45, C46, C47, C83 | C7, C14, C16, C8, C15, C17, C28, C31, C32, C33 | Wert auf Grundlage des mit 0 gerechneten Buchwerts, N = 0, AE = 0 bzw. σ_e = 0 (Gesamtumfang mindestens der Mindestumfang) | Angabe fehlt | Ohne Buchwerte, Anzahl der Einheiten, voraussichtliche Fehlerquote und Standardabweichungen aller drei Zeiträume ist der Gesamtumfang nicht bestimmt; alle Folgegrößen bleiben offen. |
| C58 | C53 | 0 € abzüglich des Buchwerts der umfassenden Schicht | Angabe fehlt | Ohne die Buchwerte der Zeiträume gibt es keine Bezugsgröße; ein Betrag auf Grundlage von 0 € wäre irreführend. |
| C59 | C54 | 0 abzüglich der Einheiten der umfassenden Schicht | Angabe fehlt | Ohne Angabe ist die Anzahl der Einheiten unbekannt, nicht null. |
| C65 | C7, C53, C60 | Wert mit 0 an Stelle der leeren Zelle | Angabe fehlt | Ohne die Buchwerte der Zeiträume gibt es keine Bezugsgröße; ein Betrag auf Grundlage von 0 € wäre irreführend. |
| C66 | C7, C53, C60, C25 | Wert mit 0 an Stelle der leeren Zelle | Angabe fehlt | Der aktualisierte zulässige Fehler setzt die Buchwerte aller Zeiträume und die Signifikanzschwelle voraus. |
| C67 | C7, C53, C60, C28 | Wert mit 0 an Stelle der leeren Zelle | Angabe fehlt | Der aktualisierte voraussichtliche Fehler setzt die Buchwerte aller Zeiträume und eine voraussichtliche Fehlerquote voraus. |
| C68 | C31 | 0,00 € (leere Zelle zählt als 0) | Angabe fehlt | Ohne Standardabweichung der Stichprobe und ohne voraussichtliche Standardabweichung gibt es keinen Wert für Zeitraum 1. |
| C69 | C54, C61 | Wert mit 0 an Stelle der leeren Zelle | Angabe fehlt | Ohne Angabe ist die Anzahl der Einheiten unbekannt, nicht null. |
| C70 | C54, C61, C62, C63 | gewichtete Standardabweichung mit 0 an Stelle der leeren Zelle | Angabe fehlt | Fehlt die Standardabweichung eines Zeitraums oder seine Anzahl der Einheiten, ist die gewichtete Standardabweichung nicht bestimmt. |
| C71 | C7, C14, C16, C8, C15, C17, C28, C31, C32, C33, C25, C53, C60 | Nenner auf Grundlage der mit 0 gerechneten Angabe | Angabe fehlt | Ohne die Ist-Werte des Zeitraums 2 und die aktualisierten Prognosen und Standardabweichungen ist die Neuberechnung nach Zeitraum 1 nicht bestimmt; die Folgegrößen bleiben offen. |
| C72, C73, C74, C80, C84, C85, C86, C115 | C7, C14, C16, C8, C15, C17, C28, C31, C32, C33, C25, C53, C60, C54, C61, C62, C63 | Wert auf Grundlage der mit 0 gerechneten Angabe (z. B. Umfang 0 oder 3, „✖ nicht anwendbar (Nenner ≤ 0)“) | Angabe fehlt | Ohne die Ist-Werte des Zeitraums 2 und die aktualisierten Prognosen und Standardabweichungen ist die Neuberechnung nach Zeitraum 1 nicht bestimmt; die Folgegrößen bleiben offen. |
| C75 | C8, C54, C61 | Wert mit 0 an Stelle der leeren Zelle | Angabe fehlt | Ohne Angabe ist die Anzahl der Einheiten unbekannt, nicht null. |
| C76 | C8, C31, C54, C61, C62, C63 | gewichtete Standardabweichung mit 0 an Stelle der leeren Zelle | Angabe fehlt | Fehlt die Standardabweichung eines Zeitraums oder seine Anzahl der Einheiten, ist die gewichtete Standardabweichung nicht bestimmt. |
| C77, C79, C81, C82 | C7, C53, C60, C25, C28, C8, C31, C54, C61, C62, C63 | Umfang auf Grundlage der mit 0 gerechneten Angabe (mindestens der Mindestumfang, gegebenenfalls begrenzt) | Angabe fehlt | Ohne die Ist-Werte des Zeitraums 2 und die aktualisierten Prognosen und Standardabweichungen ist die Neuberechnung nach Zeitraum 1 nicht bestimmt; die Folgegrößen bleiben offen. |
| C97 | C92 | 0 € abzüglich des Buchwerts der umfassenden Schicht | Angabe fehlt | Ohne die Buchwerte der Zeiträume gibt es keine Bezugsgröße; ein Betrag auf Grundlage von 0 € wäre irreführend. |
| C98 | C93 | 0 abzüglich der Einheiten der umfassenden Schicht | Angabe fehlt | Ohne Angabe ist die Anzahl der Einheiten unbekannt, nicht null. |
| C101, N4 | C7, C53, C92 | Wert mit 0 an Stelle der leeren Zelle | Angabe fehlt | Ohne die Buchwerte der Zeiträume gibt es keine Bezugsgröße; ein Betrag auf Grundlage von 0 € wäre irreführend. |
| C102 | C7, C53, C92, C25 | Wert mit 0 an Stelle der leeren Zelle | Angabe fehlt | Der endgültige zulässige Fehler setzt die Buchwerte aller Zeiträume und die Signifikanzschwelle voraus. |
| C103 | C7, C53, C92, C28 | Wert mit 0 an Stelle der leeren Zelle | Angabe fehlt | Der endgültige voraussichtliche Fehler setzt die Buchwerte aller Zeiträume und eine voraussichtliche Fehlerquote voraus. |
| C104 | C62 | 0,00 € (leere Zelle zählt als 0) | Angabe fehlt | Ohne Standardabweichung der Stichprobe und ohne aktualisierte Standardabweichung gibt es keinen Wert für Zeitraum 2. |
| C105 | C7, C14, C16, C8, C15, C17, C28, C31, C32, C33, C25, C53, C60, C54, C61, C62, C63, C92 | Nenner auf Grundlage der mit 0 gerechneten Angabe | Angabe fehlt | Ohne die Ist-Werte des Zeitraums 3 und die aktualisierte Standardabweichung ist die Neuberechnung nach Zeitraum 2 nicht bestimmt; endgültige Umfänge, Genauigkeit und Würdigung bleiben offen. |
| C107 | C8, C54, C93 | Wert mit 0 an Stelle der leeren Zelle | Angabe fehlt | Ohne Angabe ist die Anzahl der Einheiten unbekannt, nicht null. |
| C108 | C8, C31, C54, C62, C93, C99 | gewichtete Standardabweichung mit 0 an Stelle der leeren Zelle | Angabe fehlt | Fehlt die Standardabweichung eines Zeitraums oder seine Anzahl der Einheiten, ist die gewichtete Standardabweichung nicht bestimmt. |
| C109, C111, C114 | C7, C53, C92, C25, C28, C8, C31, C54, C62, C93, C99 | Umfang auf Grundlage der mit 0 gerechneten Angabe (mindestens der Mindestumfang, gegebenenfalls begrenzt) | Angabe fehlt | Ohne die Ist-Werte des Zeitraums 3 und die aktualisierte Standardabweichung ist die Neuberechnung nach Zeitraum 2 nicht bestimmt; endgültige Umfänge, Genauigkeit und Würdigung bleiben offen. |
| C106, C112, C113, C116, C117, C118, C119, C120, N10, C129, C132, C133, C134, C137, C138, N7 | C7, C14, C16, C8, C15, C17, C28, C31, C32, C33, C25, C53, C60, C54, C61, C62, C63, C92, C93, C99 | Wert auf Grundlage der mit 0 gerechneten Angabe (z. B. Umfang 3, Auffüllung auf 30, Genauigkeit ohne den Beitrag des Zeitraums) | Angabe fehlt | Ohne die Ist-Werte des Zeitraums 3 und die aktualisierte Standardabweichung ist die Neuberechnung nach Zeitraum 2 nicht bestimmt; endgültige Umfänge, Genauigkeit und Würdigung bleiben offen. |
| C127, C128, C135, C136, N5, N11 | C7, C53, C92 | Hochrechnung auf Grundlage eines mit 0 € gerechneten Buchwerts (bei umfassender Schicht ein negativer Betrag) | Angabe fehlt | Ohne die Buchwerte der Zeiträume gibt es keine Bezugsgröße; ein Betrag auf Grundlage von 0 € wäre irreführend. |
| C84 | C73, C81, C83, C46 | 3 (Untergrenze, obwohl für Zeitraum 2 kein Umfang bestimmt ist, z. B. beim leeren Formular oder bei „TE ≤ AE“) | kein Wert | Ohne gewählten Umfang für Zeitraum 2 bleibt in der Vorlage nur die Untergrenze von 3 Einheiten (MAX übergeht den leeren Bezug); als anzuwendender Umfang hätte sie keine Grundlage. |
| C113, C117 | C84 | Wert auf Grundlage eines Umfangs von 3 Einheiten für Zeitraum 2, der nur die Untergrenze ist | kein Wert | Ohne gewählten Umfang für Zeitraum 2 bleibt in der Vorlage nur die Untergrenze von 3 Einheiten (MAX übergeht den leeren Bezug); als anzuwendender Umfang hätte sie keine Grundlage. |
| C127 | C49, C88, C122 | 0,00 € (kein Zeitraum trägt eine Fehlersumme) | kein Wert | Solange kein Zeitraum eine Fehlersumme trägt, gibt es nichts hochzurechnen; ein extrapolierter Fehler von 0 € sähe wie ein Prüfergebnis aus. |

### 13_NS_GW

| Zellen | leer ist eine von | Vorlage zeigt | Webfassung zeigt | Begründung |
|---|---|---|---|---|
| C7, N4 | C7 | 0 (Verknüpfung auf das leere Blatt 02) | Angabe fehlt | Ohne Buchwert der Grundgesamtheit gibt es keine Bezugsgröße; ein Ergebnis auf der Grundlage von 0 € wäre irreführend. |
| C8 | C8 | 0 (Verknüpfung auf das leere Blatt 02) | Angabe fehlt | Ohne Angabe ist die Anzahl der Stichprobeneinheiten unbekannt, nicht null. |
| C9 | C8 | „✔ N < 300: zulässig …“ (0 Einheiten liegen unter 300) | Angabe fehlt | Ohne Angabe ist die Anzahl der Stichprobeneinheiten unbekannt, nicht null. |
| C12 | C7 | 0 € abzüglich des Buchwerts der umfassenden Schicht | Angabe fehlt | Ohne Buchwert der Grundgesamtheit gibt es keine Bezugsgröße; ein Ergebnis auf der Grundlage von 0 € wäre irreführend. |
| C14, N10 | C13 | nur die Einheiten der umfassenden Schicht bzw. 0 (leere Zelle zählt als 0) | Angabe fehlt | Ohne Umfang der Zufallsstichprobe ist die Gesamtstichprobe nicht bestimmt. |
| C15 | C8 | 0 (10 % von 0 Einheiten) | Angabe fehlt | Ohne Angabe ist die Anzahl der Stichprobeneinheiten unbekannt, nicht null. |
| C16 | C8, C13 | Prüfhinweis auf der Grundlage von 0 Einheiten der Grundgesamtheit bzw. der Zufallsstichprobe | Angabe fehlt | Die Prüfung der Mindesterfassung setzt die Anzahl der Stichprobeneinheiten und den Umfang der Zufallsstichprobe voraus. |
| C21, C22, N5 | C7 | Hochrechnung mit dem negativen Buchwert der Zufallsschicht (0 € abzüglich umfassende Schicht) bzw. 0 € | Angabe fehlt | Ohne Buchwert der Grundgesamtheit gibt es keine Bezugsgröße; ein Ergebnis auf der Grundlage von 0 € wäre irreführend. |
| C28 | C27 | Würdigung gegen eine Schwelle von 0 % | Angabe fehlt | Die Würdigung setzt die Signifikanzschwelle voraus. |
| C21 | C18 | 0,00 € (die Fehlersumme der Stichprobe fehlt; N(…) zählt sie als 0) | kein Wert | Ohne Fehlersumme der Stichprobe gibt es nichts hochzurechnen; ein extrapolierter Fehler von 0 € sähe wie ein Prüfergebnis aus. |

### 14_NS_GW_S

| Zellen | leer ist eine von | Vorlage zeigt | Webfassung zeigt | Begründung |
|---|---|---|---|---|
| C11 | D11–J11, AA11–AM11 | 0 (Summe über Schichten ohne Wert) | kein Wert | Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus. Die Webfassung lässt ihn offen, solange eine Pflichteingabe fehlt; bei vollständigen Eingaben zeigt sie ihn wie die Vorlage mit Hinweis in Warnfarbe. |
| C12 | D12–J12, AA12–AM12 | 0 (Summe über Schichten ohne Wert) | kein Wert | Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus. Die Webfassung lässt ihn offen, solange eine Pflichteingabe fehlt; bei vollständigen Eingaben zeigt sie ihn wie die Vorlage mit Hinweis in Warnfarbe. |
| C18 | D18–J18, AA18–AM18 | 0 (Summe über Schichten ohne Wert) | kein Wert | Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus. Die Webfassung lässt ihn offen, solange eine Pflichteingabe fehlt; bei vollständigen Eingaben zeigt sie ihn wie die Vorlage mit Hinweis in Warnfarbe. |
| C24 | D24–J24, AA24–AM24 | 0 (Summe über Schichten ohne Wert) | kein Wert | Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus. Die Webfassung lässt ihn offen, solange eine Pflichteingabe fehlt; bei vollständigen Eingaben zeigt sie ihn wie die Vorlage mit Hinweis in Warnfarbe. |
| C25 | D25–J25, AA25–AM25 | 0 (Summe über Schichten ohne Wert) | kein Wert | Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus. Die Webfassung lässt ihn offen, solange eine Pflichteingabe fehlt; bei vollständigen Eingaben zeigt sie ihn wie die Vorlage mit Hinweis in Warnfarbe. |
| C27 | D11–J11, AA11–AM11, D27–J27, AA27–AM27 | 0 (Summe über Schichten ohne Wert) | kein Wert | Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus. Die Webfassung lässt ihn offen, solange eine Pflichteingabe fehlt; bei vollständigen Eingaben zeigt sie ihn wie die Vorlage mit Hinweis in Warnfarbe. |
| C13, N4 | C12 | nur der Buchwert der umfassenden Schicht bzw. 0 € (Summe der Buchwerte ohne belegte Schicht) | kein Wert | Der Wert baut auf einer Summe auf, zu der keine Schicht beiträgt; ohne sie ist er nicht bestimmt. Die Webfassung lässt ihn offen, solange eine Pflichteingabe fehlt; bei vollständigen Eingaben zeigt sie ihn wie die Vorlage mit Hinweis in Warnfarbe. |
| C14 | C11 | nur die Einheiten der umfassenden Schicht bzw. 0 (Summe der Einheiten ohne belegte Schicht) | kein Wert | Der Wert baut auf einer Summe auf, zu der keine Schicht beiträgt; ohne sie ist er nicht bestimmt. Die Webfassung lässt ihn offen, solange eine Pflichteingabe fehlt; bei vollständigen Eingaben zeigt sie ihn wie die Vorlage mit Hinweis in Warnfarbe. |
| C15 | C11 | „✔ N < 300: zulässig …“ (0 Einheiten liegen unter 300) | kein Wert | Der Wert baut auf einer Summe auf, zu der keine Schicht beiträgt; ohne sie ist er nicht bestimmt. Die Webfassung lässt ihn offen, solange eine Pflichteingabe fehlt; bei vollständigen Eingaben zeigt sie ihn wie die Vorlage mit Hinweis in Warnfarbe. |
| C20 | C11 | 10 % der Einheiten der umfassenden Schicht bzw. 0 | kein Wert | Der Wert baut auf einer Summe auf, zu der keine Schicht beiträgt; ohne sie ist er nicht bestimmt. Die Webfassung lässt ihn offen, solange eine Pflichteingabe fehlt; bei vollständigen Eingaben zeigt sie ihn wie die Vorlage mit Hinweis in Warnfarbe. |
| C19, N10 | C18 | nur die Einheiten der umfassenden Schicht bzw. 0 (Summe der Schichtumfänge ohne belegte Schicht) | kein Wert | Der Wert baut auf einer Summe auf, zu der keine Schicht beiträgt; ohne sie ist er nicht bestimmt. Die Webfassung lässt ihn offen, solange eine Pflichteingabe fehlt; bei vollständigen Eingaben zeigt sie ihn wie die Vorlage mit Hinweis in Warnfarbe. |
| C21 | C19, C20 | Prüfhinweis auf der Grundlage einer Gesamtstichprobe bzw. einer Mindesterfassung, zu der keine Schicht beiträgt | kein Wert | Der Wert baut auf einer Summe auf, zu der keine Schicht beiträgt; ohne sie ist er nicht bestimmt. Die Webfassung lässt ihn offen, solange eine Pflichteingabe fehlt; bei vollständigen Eingaben zeigt sie ihn wie die Vorlage mit Hinweis in Warnfarbe. |
| C29, C32, C33, C35, N5, N11 | C27 | Hochrechnung und Würdigung auf Grundlage eines extrapolierten Fehlers der Zufallsschichten von 0 €, obwohl keine belegte Schicht hochgerechnet werden kann | kein Wert | Der Wert baut auf einer Summe auf, zu der keine Schicht beiträgt; ohne sie ist er nicht bestimmt. Die Webfassung lässt ihn offen, solange eine Pflichteingabe fehlt; bei vollständigen Eingaben zeigt sie ihn wie die Vorlage mit Hinweis in Warnfarbe. |
| D18–J18, AA18–AM18 | C16 | 1 je belegter Schicht (Mindestwert der Formel bei n = 0) | Angabe fehlt | Ohne Umfang der Zufallsstichprobe ist die Aufteilung auf die Schichten nicht bestimmt. |
| C18, C19, N10 | C16 | Anzahl der belegten Schichten (je Schicht 1), zuzüglich der umfassenden Schicht | Angabe fehlt | Ohne Umfang der Zufallsstichprobe ist die Aufteilung auf die Schichten nicht bestimmt. |
| C21 | C16 | Prüfhinweis auf der Grundlage von einer Einheit je belegter Schicht | Angabe fehlt | Die Prüfung der Mindesterfassung setzt den Umfang der Zufallsstichprobe voraus. |
| D27–J27, AA27–AM27 | D12–J12, AA12–AM12 | 0,00 € (leerer Buchwert der Schicht zählt als 0) | Angabe fehlt | Fehlt der Buchwert einer belegten Schicht, ist ihr extrapolierter Fehler nicht bestimmt; Summe und Fehlerquoten bleiben offen. |
| C27, C29, N5 | D12–J12, AA12–AM12 | Summe, in die die Schicht ohne Buchwert mit 0 € eingeht | Angabe fehlt | Fehlt der Buchwert einer belegten Schicht, ist ihr extrapolierter Fehler nicht bestimmt; Summe und Fehlerquoten bleiben offen. |
| C32, C33, N11 | D12–J12, AA12–AM12 | Fehlerquote, in die die Schicht ohne Buchwert mit 0 € eingeht, bzw. bezogen nur auf die umfassende Schicht | Angabe fehlt | Fehlt der Buchwert einer belegten Schicht, ist ihr extrapolierter Fehler nicht bestimmt; Summe und Fehlerquoten bleiben offen. |
| C35 | C34, D12–J12, AA12–AM12 | Würdigung gegen eine Schwelle von 0 % bzw. auf Grundlage der mit 0 € gerechneten Schicht | Angabe fehlt | Die Würdigung setzt die Signifikanzschwelle und den Buchwert jeder belegten Schicht voraus. |

### 15_NS_PPS

| Zellen | leer ist eine von | Vorlage zeigt | Webfassung zeigt | Begründung |
|---|---|---|---|---|
| C7, N4 | C7 | 0 (Verknüpfung auf das leere Blatt 02) | Angabe fehlt | Ohne Buchwert der Grundgesamtheit gibt es keine Bezugsgröße; ein Ergebnis auf der Grundlage von 0 € wäre irreführend. |
| C8 | C8 | 0 (Verknüpfung auf das leere Blatt 02) | Angabe fehlt | Ohne Angabe ist die Anzahl der Stichprobeneinheiten unbekannt, nicht null. |
| C9 | C8 | „✔ N < 300: zulässig …“ (0 Einheiten liegen unter 300) | Angabe fehlt | Ohne Angabe ist die Anzahl der Stichprobeneinheiten unbekannt, nicht null. |
| C11 | C8 | 0 (10 % von 0 Einheiten) | Angabe fehlt | Ohne Angabe ist die Anzahl der Stichprobeneinheiten unbekannt, nicht null. |
| C12 | C8 | „✔ Mindesterfassung erreicht“ (gegen 0 Einheiten) | Angabe fehlt | Ohne Angabe ist die Anzahl der Stichprobeneinheiten unbekannt, nicht null. |
| N10 | C10 | 0 (leere Zelle zählt als 0) | Angabe fehlt | Ohne Stichprobenumfang sind Zufallsschicht und Auswahlintervall nicht bestimmt; alle Folgegrößen bleiben offen. |
| C13 | C7 | 0,00 € (0 € geteilt durch den Stichprobenumfang) | Angabe fehlt | Ohne Buchwert der Grundgesamtheit gibt es keine Bezugsgröße; ein Ergebnis auf der Grundlage von 0 € wäre irreführend. |
| C16 | C7 | 0 € abzüglich des Buchwerts der hochwertigen Einheiten | Angabe fehlt | Ohne Buchwert der Grundgesamtheit gibt es keine Bezugsgröße; ein Ergebnis auf der Grundlage von 0 € wäre irreführend. |
| C17 | C10 | 0 abzüglich der Anzahl hochwertiger Einheiten | Angabe fehlt | Ohne Stichprobenumfang sind Zufallsschicht und Auswahlintervall nicht bestimmt; alle Folgegrößen bleiben offen. |
| C18 | C10 | „✖ < 3 Einheiten (Art. 5 Abs. 5)“ (gegen 0 bzw. eine negative Anzahl) | Angabe fehlt | Ohne Stichprobenumfang sind Zufallsschicht und Auswahlintervall nicht bestimmt; alle Folgegrößen bleiben offen. |
| C19, C25, C26, N5 | C7, C10 | Wert auf Grundlage des mit 0 gerechneten Buchwerts bzw. Stichprobenumfangs (auch negative Beträge) | Angabe fehlt | Auswahlintervall und Hochrechnung setzen Buchwert der Grundgesamtheit und Stichprobenumfang voraus. |
| C29, C30, N11 | C10 | Fehlerquote auf Grundlage des mit n = 0 gerechneten (negativen) Auswahlintervalls | Angabe fehlt | Ohne Stichprobenumfang sind Zufallsschicht und Auswahlintervall nicht bestimmt; alle Folgegrößen bleiben offen. |
| C32 | C10, C31 | Würdigung gegen eine Schwelle von 0 % bzw. auf Grundlage des mit n = 0 gerechneten Auswahlintervalls | Angabe fehlt | Die Würdigung setzt die Signifikanzschwelle und den Stichprobenumfang voraus. |
| C25 | C23 | 0,00 € (die Fehlersumme der Stichprobe fehlt; N(…) zählt sie als 0) | kein Wert | Ohne Fehlersumme der Stichprobe gibt es nichts hochzurechnen; ein extrapolierter Fehler von 0 € sähe wie ein Prüfergebnis aus. |

### 16_NS_PPS_S

| Zellen | leer ist eine von | Vorlage zeigt | Webfassung zeigt | Begründung |
|---|---|---|---|---|
| C9 | D9–J9, AA9–AM9 | 0 (Summe über Schichten ohne Wert) | kein Wert | Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus. Die Webfassung lässt ihn offen, solange eine Pflichteingabe fehlt; bei vollständigen Eingaben zeigt sie ihn wie die Vorlage mit Hinweis in Warnfarbe. |
| C10 | D10–J10, AA10–AM10 | 0 (Summe über Schichten ohne Wert) | kein Wert | Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus. Die Webfassung lässt ihn offen, solange eine Pflichteingabe fehlt; bei vollständigen Eingaben zeigt sie ihn wie die Vorlage mit Hinweis in Warnfarbe. |
| C15 | D15–J15, AA15–AM15 | 0 (Summe über Schichten ohne Wert) | kein Wert | Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus. Die Webfassung lässt ihn offen, solange eine Pflichteingabe fehlt; bei vollständigen Eingaben zeigt sie ihn wie die Vorlage mit Hinweis in Warnfarbe. |
| C21 | D21–J21, AA21–AM21 | 0 (Summe über Schichten ohne Wert) | kein Wert | Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus. Die Webfassung lässt ihn offen, solange eine Pflichteingabe fehlt; bei vollständigen Eingaben zeigt sie ihn wie die Vorlage mit Hinweis in Warnfarbe. |
| C22 | D22–J22, AA22–AM22 | 0 (Summe über Schichten ohne Wert) | kein Wert | Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus. Die Webfassung lässt ihn offen, solange eine Pflichteingabe fehlt; bei vollständigen Eingaben zeigt sie ihn wie die Vorlage mit Hinweis in Warnfarbe. |
| C26 | D26–J26, AA26–AM26 | 0 (Summe über Schichten ohne Wert) | kein Wert | Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus. Die Webfassung lässt ihn offen, solange eine Pflichteingabe fehlt; bei vollständigen Eingaben zeigt sie ihn wie die Vorlage mit Hinweis in Warnfarbe. |
| C28 | D9–J9, AA9–AM9, D28–J28, AA28–AM28 | 0 (Summe über Schichten ohne Wert) | kein Wert | Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus. Die Webfassung lässt ihn offen, solange eine Pflichteingabe fehlt; bei vollständigen Eingaben zeigt sie ihn wie die Vorlage mit Hinweis in Warnfarbe. |
| N4 | C9 | 0 € (Summe der Buchwerte ohne belegte Schicht) | kein Wert | Der Wert baut auf einer Summe auf, zu der keine Schicht beiträgt; ohne sie ist er nicht bestimmt. Die Webfassung lässt ihn offen, solange eine Pflichteingabe fehlt; bei vollständigen Eingaben zeigt sie ihn wie die Vorlage mit Hinweis in Warnfarbe. |
| C11 | C10 | 0 (Summe der Einheiten ohne Angabe in einer Schicht) | kein Wert | Der Wert baut auf einer Summe auf, zu der keine Schicht beiträgt; ohne sie ist er nicht bestimmt. Die Webfassung lässt ihn offen, solange eine Pflichteingabe fehlt; bei vollständigen Eingaben zeigt sie ihn wie die Vorlage mit Hinweis in Warnfarbe. |
| C12 | C10 | „✔ N < 300: zulässig …“ (0 Einheiten liegen unter 300) | kein Wert | Der Wert baut auf einer Summe auf, zu der keine Schicht beiträgt; ohne sie ist er nicht bestimmt. Die Webfassung lässt ihn offen, solange eine Pflichteingabe fehlt; bei vollständigen Eingaben zeigt sie ihn wie die Vorlage mit Hinweis in Warnfarbe. |
| C16 | C10 | 0 (10 % von 0 Einheiten) | kein Wert | Der Wert baut auf einer Summe auf, zu der keine Schicht beiträgt; ohne sie ist er nicht bestimmt. Die Webfassung lässt ihn offen, solange eine Pflichteingabe fehlt; bei vollständigen Eingaben zeigt sie ihn wie die Vorlage mit Hinweis in Warnfarbe. |
| C17 | C15, C16 | Prüfhinweis auf der Grundlage einer Summe der Schichtumfänge bzw. einer Mindesterfassung, zu der keine Schicht beiträgt | kein Wert | Der Wert baut auf einer Summe auf, zu der keine Schicht beiträgt; ohne sie ist er nicht bestimmt. Die Webfassung lässt ihn offen, solange eine Pflichteingabe fehlt; bei vollständigen Eingaben zeigt sie ihn wie die Vorlage mit Hinweis in Warnfarbe. |
| N10 | C15 | 0 (Summe der Schichtumfänge ohne belegte Schicht) | kein Wert | Der Wert baut auf einer Summe auf, zu der keine Schicht beiträgt; ohne sie ist er nicht bestimmt. Die Webfassung lässt ihn offen, solange eine Pflichteingabe fehlt; bei vollständigen Eingaben zeigt sie ihn wie die Vorlage mit Hinweis in Warnfarbe. |
| C30, C33, C34, C36, N5, N11 | C28 | Hochrechnung und Würdigung auf Grundlage eines extrapolierten Fehlers von 0 €, obwohl keine belegte Schicht hochgerechnet werden kann | kein Wert | Der Wert baut auf einer Summe auf, zu der keine Schicht beiträgt; ohne sie ist er nicht bestimmt. Die Webfassung lässt ihn offen, solange eine Pflichteingabe fehlt; bei vollständigen Eingaben zeigt sie ihn wie die Vorlage mit Hinweis in Warnfarbe. |
| D15–J15, AA15–AM15, D18–J18, AA18–AM18, D22–J22, AA22–AM22, D23–J23, AA23–AM23, D28–J28, AA28–AM28 | C13 | Wert auf Grundlage von einer Einheit je belegter Schicht (Mindestwert der Formel bei n = 0) | Angabe fehlt | Ohne Stichprobenumfang sind die Aufteilung auf die Schichten, die Zufallsschichten und die Auswahlintervalle nicht bestimmt; alle Folgegrößen bleiben offen. |
| C15, C22, C28, C30, C33, C34, N5, N10, N11 | C13 | Wert auf Grundlage von einer Einheit je belegter Schicht (Mindestwert der Formel bei n = 0) | Angabe fehlt | Ohne Stichprobenumfang sind die Aufteilung auf die Schichten, die Zufallsschichten und die Auswahlintervalle nicht bestimmt; alle Folgegrößen bleiben offen. |
| C17 | C13 | Prüfhinweis auf der Grundlage von einer Einheit je belegter Schicht | Angabe fehlt | Die Prüfung der Mindesterfassung setzt den Stichprobenumfang voraus. |
| C36 | C13, C35 | Würdigung gegen eine Schwelle von 0 % bzw. auf Grundlage von einer Einheit je belegter Schicht | Angabe fehlt | Die Würdigung setzt die Signifikanzschwelle und den Stichprobenumfang voraus. |

### 17_Unterstichprobe

| Zellen | leer ist eine von | Vorlage zeigt | Webfassung zeigt | Begründung |
|---|---|---|---|---|
| C13, C16, C20, C22 | C6 | Wert auf Grundlage eines Buchwerts von 0 € | Angabe fehlt | Ohne Buchwert der Stichprobeneinheit lässt sich nichts hochrechnen; die Vorlage rechnet mit 0 € weiter. |
| C20, C22, C23 | C15 | Wert auf Grundlage eines Umfangs von 0 (bei vorhandenen hochwertigen Einheiten negativ) | Angabe fehlt | Ohne Umfang der Unterstichprobe gibt es kein Auswahlintervall; mit 0 abzüglich der hochwertigen Einheiten entstünden ein negatives Intervall und ein negativer Fehler. |

### 18_GFQ_AnhIII

| Zellen | leer ist eine von | Vorlage zeigt | Webfassung zeigt | Begründung |
|---|---|---|---|---|
| C5 | C5 | Wert auf Grundlage der in Blatt 02 bzw. im Methodenblatt mit 0 gerechneten leeren Eingaben; ohne Genauigkeit „n. a.“ | kein Wert | Blatt 02 bzw. das Methodenblatt zeigen für die zugrunde liegende Größe „Angabe fehlt“; ein darauf aufbauender Wert hätte keine Grundlage. |
| C6 | C6 | Wert auf Grundlage der in Blatt 02 bzw. im Methodenblatt mit 0 gerechneten leeren Eingaben; ohne Genauigkeit „n. a.“ | kein Wert | Blatt 02 bzw. das Methodenblatt zeigen für die zugrunde liegende Größe „Angabe fehlt“; ein darauf aufbauender Wert hätte keine Grundlage. |
| C7, C23 | C7 | Wert auf Grundlage der in Blatt 02 bzw. im Methodenblatt mit 0 gerechneten leeren Eingaben; ohne Genauigkeit „n. a.“ | kein Wert | Blatt 02 bzw. das Methodenblatt zeigen für die zugrunde liegende Größe „Angabe fehlt“; ein darauf aufbauender Wert hätte keine Grundlage. |
| C8 | C8 | Wert auf Grundlage der in Blatt 02 bzw. im Methodenblatt mit 0 gerechneten leeren Eingaben; ohne Genauigkeit „n. a.“ | kein Wert | Blatt 02 bzw. das Methodenblatt zeigen für die zugrunde liegende Größe „Angabe fehlt“; ein darauf aufbauender Wert hätte keine Grundlage. |
| C12 | 02_Grundgesamtheit!C39 | Wert auf Grundlage der in Blatt 02 bzw. im Methodenblatt mit 0 gerechneten leeren Eingaben; ohne Genauigkeit „n. a.“ | kein Wert | Blatt 02 bzw. das Methodenblatt zeigen für die zugrunde liegende Größe „Angabe fehlt“; ein darauf aufbauender Wert hätte keine Grundlage. |
| C14 | C12 | Wert auf Grundlage der in Blatt 02 bzw. im Methodenblatt mit 0 gerechneten leeren Eingaben; ohne Genauigkeit „n. a.“ | kein Wert | Blatt 02 bzw. das Methodenblatt zeigen für die zugrunde liegende Größe „Angabe fehlt“; ein darauf aufbauender Wert hätte keine Grundlage. |
| C17 | C14 | Wert auf Grundlage der in Blatt 02 bzw. im Methodenblatt mit 0 gerechneten leeren Eingaben; ohne Genauigkeit „n. a.“ | kein Wert | Blatt 02 bzw. das Methodenblatt zeigen für die zugrunde liegende Größe „Angabe fehlt“; ein darauf aufbauender Wert hätte keine Grundlage. |
| C18 | C14, C17 | Wert auf Grundlage der in Blatt 02 bzw. im Methodenblatt mit 0 gerechneten leeren Eingaben; ohne Genauigkeit „n. a.“ | kein Wert | Blatt 02 bzw. das Methodenblatt zeigen für die zugrunde liegende Größe „Angabe fehlt“; ein darauf aufbauender Wert hätte keine Grundlage. |
| C19 | C5, C14, C17 | Wert auf Grundlage der in Blatt 02 bzw. im Methodenblatt mit 0 gerechneten leeren Eingaben; ohne Genauigkeit „n. a.“ | kein Wert | Blatt 02 bzw. das Methodenblatt zeigen für die zugrunde liegende Größe „Angabe fehlt“; ein darauf aufbauender Wert hätte keine Grundlage. |
| C24 | C6, C7, C18, C23 | Wert auf Grundlage der in Blatt 02 bzw. im Methodenblatt mit 0 gerechneten leeren Eingaben; ohne Genauigkeit „n. a.“ | kein Wert | Blatt 02 bzw. das Methodenblatt zeigen für die zugrunde liegende Größe „Angabe fehlt“; ein darauf aufbauender Wert hätte keine Grundlage. |
| C25 | C8, C18, 02_Grundgesamtheit!C52 | Wert auf Grundlage der in Blatt 02 bzw. im Methodenblatt mit 0 gerechneten leeren Eingaben; ohne Genauigkeit „n. a.“ | kein Wert | Blatt 02 bzw. das Methodenblatt zeigen für die zugrunde liegende Größe „Angabe fehlt“; ein darauf aufbauender Wert hätte keine Grundlage. |
| C26 | C14, C24 | Wert auf Grundlage der in Blatt 02 bzw. im Methodenblatt mit 0 gerechneten leeren Eingaben; ohne Genauigkeit „n. a.“ | kein Wert | Blatt 02 bzw. das Methodenblatt zeigen für die zugrunde liegende Größe „Angabe fehlt“; ein darauf aufbauender Wert hätte keine Grundlage. |
| C27 | C12, C26 | Wert auf Grundlage der in Blatt 02 bzw. im Methodenblatt mit 0 gerechneten leeren Eingaben; ohne Genauigkeit „n. a.“ | kein Wert | Blatt 02 bzw. das Methodenblatt zeigen für die zugrunde liegende Größe „Angabe fehlt“; ein darauf aufbauender Wert hätte keine Grundlage. |
| C28 | C14, C24, C25 | Wert auf Grundlage der in Blatt 02 bzw. im Methodenblatt mit 0 gerechneten leeren Eingaben; ohne Genauigkeit „n. a.“ | kein Wert | Blatt 02 bzw. das Methodenblatt zeigen für die zugrunde liegende Größe „Angabe fehlt“; ein darauf aufbauender Wert hätte keine Grundlage. |
| C30 | C26, C28 | Wert auf Grundlage der in Blatt 02 bzw. im Methodenblatt mit 0 gerechneten leeren Eingaben; ohne Genauigkeit „n. a.“ | kein Wert | Blatt 02 bzw. das Methodenblatt zeigen für die zugrunde liegende Größe „Angabe fehlt“; ein darauf aufbauender Wert hätte keine Grundlage. |
| C15 | 02_Grundgesamtheit!C49 | 0 (Bezug auf die leere Auswahlzelle in Blatt 02) | Angabe fehlt | Ohne Auswahl in Blatt 02 ist die Behandlung der nicht prüfbaren Einheiten unbekannt, nicht 0. |
| C30 | C29 | Würdigung gegen eine Schwelle von 0 % | Angabe fehlt | Ohne Signifikanzschwelle gibt es nichts zu würdigen. |
| C23 | C21 | 0,00 € (leere Zelle zählt als 0) | Angabe fehlt | Die Anpassung der hochwertigen Schicht setzt den Buchwert der ursprünglichen hochwertigen Schicht voraus; mit 0 entfiele der Fehler der umfassenden Schicht. |
| C24, C26, C27, C28, C30 | C21 | Wert ohne den Fehler der umfassenden Schicht (EE_e = 0), wenn die Anpassung mit „Ja“ gewählt ist | Angabe fehlt | Die Anpassung der hochwertigen Schicht setzt den Buchwert der ursprünglichen hochwertigen Schicht voraus; mit 0 entfiele der Fehler der umfassenden Schicht. |

### 20_Druck_KOM

| Zellen | leer ist eine von | Vorlage zeigt | Webfassung zeigt | Begründung |
|---|---|---|---|---|
| F11 | 02_Grundgesamtheit!C23 | 0 (leere Zelle zählt als 0) | Angabe fehlt | Ohne Anzahl der Datensätze in Blatt 02 ist sie unbekannt, nicht 0. |
| G11 | 02_Grundgesamtheit!C16 | 0,00 € (leere Zelle zählt als 0) | Angabe fehlt | Ohne Betrag laut SFC2021 in Blatt 02 ist er unbekannt, nicht 0 €. |
| A37 | 18_GFQ_AnhIII!C29 | Satz zur Würdigung gegen eine Schwelle von 0 % | Angabe fehlt | Ohne Signifikanzschwelle in Blatt 18 gibt es nichts zu würdigen. |
| F12 | 02_Grundgesamtheit!C52 | Wert auf Grundlage der in Blatt 02, im Methodenblatt bzw. in Blatt 18 mit 0 gerechneten leeren Eingaben; ohne Zahl in Blatt 18 „nicht berechnet“ | kein Wert | Das liefernde Blatt zeigt für die Größe „Angabe fehlt“; der Bericht übernimmt keinen Wert, der dort keine Grundlage hat. |
| G12 | 02_Grundgesamtheit!C51 | Wert auf Grundlage der in Blatt 02, im Methodenblatt bzw. in Blatt 18 mit 0 gerechneten leeren Eingaben; ohne Zahl in Blatt 18 „nicht berechnet“ | kein Wert | Das liefernde Blatt zeigt für die Größe „Angabe fehlt“; der Bericht übernimmt keinen Wert, der dort keine Grundlage hat. |
| F14 | F14 | Wert auf Grundlage der in Blatt 02, im Methodenblatt bzw. in Blatt 18 mit 0 gerechneten leeren Eingaben; ohne Zahl in Blatt 18 „nicht berechnet“ | kein Wert | Das liefernde Blatt zeigt für die Größe „Angabe fehlt“; der Bericht übernimmt keinen Wert, der dort keine Grundlage hat. |
| G32, A37 | 18_GFQ_AnhIII!C26 | Wert auf Grundlage der in Blatt 02, im Methodenblatt bzw. in Blatt 18 mit 0 gerechneten leeren Eingaben; ohne Zahl in Blatt 18 „nicht berechnet“ | kein Wert | Das liefernde Blatt zeigt für die Größe „Angabe fehlt“; der Bericht übernimmt keinen Wert, der dort keine Grundlage hat. |
| G33 | 18_GFQ_AnhIII!C24 | Wert auf Grundlage der in Blatt 02, im Methodenblatt bzw. in Blatt 18 mit 0 gerechneten leeren Eingaben; ohne Zahl in Blatt 18 „nicht berechnet“ | kein Wert | Das liefernde Blatt zeigt für die Größe „Angabe fehlt“; der Bericht übernimmt keinen Wert, der dort keine Grundlage hat. |
| G34 | 18_GFQ_AnhIII!C25 | Wert auf Grundlage der in Blatt 02, im Methodenblatt bzw. in Blatt 18 mit 0 gerechneten leeren Eingaben; ohne Zahl in Blatt 18 „nicht berechnet“ | kein Wert | Das liefernde Blatt zeigt für die Größe „Angabe fehlt“; der Bericht übernimmt keinen Wert, der dort keine Grundlage hat. |
| G35 | 18_GFQ_AnhIII!C28 | Wert auf Grundlage der in Blatt 02, im Methodenblatt bzw. in Blatt 18 mit 0 gerechneten leeren Eingaben; ohne Zahl in Blatt 18 „nicht berechnet“ | kein Wert | Das liefernde Blatt zeigt für die Größe „Angabe fehlt“; der Bericht übernimmt keinen Wert, der dort keine Grundlage hat. |
| G36 | 18_GFQ_AnhIII!C27 | Wert auf Grundlage der in Blatt 02, im Methodenblatt bzw. in Blatt 18 mit 0 gerechneten leeren Eingaben; ohne Zahl in Blatt 18 „nicht berechnet“ | kein Wert | Das liefernde Blatt zeigt für die Größe „Angabe fehlt“; der Bericht übernimmt keinen Wert, der dort keine Grundlage hat. |
| G42 | 18_GFQ_AnhIII!C26, 18_GFQ_AnhIII!C14 | Wert auf Grundlage der in Blatt 02, im Methodenblatt bzw. in Blatt 18 mit 0 gerechneten leeren Eingaben; ohne Zahl in Blatt 18 „nicht berechnet“ | kein Wert | Das liefernde Blatt zeigt für die Größe „Angabe fehlt“; der Bericht übernimmt keinen Wert, der dort keine Grundlage hat. |
| G43 | G42 | Betrag der Korrektur, obwohl die Restfehlerquote fehlt (Excel wertet die leere Textzelle im Vergleich größer als 0,02) | kein Wert | Ohne Restfehlerquote steht nicht fest, ob eine Korrektur erforderlich ist; ein Betrag hätte keine Grundlage. |

### X1_KonsMUS_2017

| Zellen | leer ist eine von | Vorlage zeigt | Webfassung zeigt | Begründung |
|---|---|---|---|---|
| C5, C6 | C4 | FALSCH (keine Stufe des Konfidenzniveaus trifft zu; zählt in der Rechnung als 0) | Angabe fehlt | Ohne Konfidenzniveau gibt es keinen Zuverlässigkeits- und keinen Erweiterungsfaktor. |
| C8 | C1, C7 | 0 € (leere Zelle zählt als 0) | Angabe fehlt | Der voraussichtliche Fehler setzt Buchwert und erwartete Fehlerquote voraus. |
| C10 | C1 | 0 € (leere Zelle zählt als 0) | Angabe fehlt | Der zulässige Fehler setzt den Buchwert voraus. |
| C11, C12, C15 | C4, C7 | Wert auf Grundlage des mit RF = 0 bzw. AE = 0 berechneten Umfangs (z. B. Mindestumfang 30) | Angabe fehlt | Ohne Konfidenzniveau und erwartete Fehlerquote ist der Stichprobenumfang nicht bestimmt; alle Folgegrößen bleiben offen. |
| C17, C18 | C4, C7, C16 | Genauigkeit mit Incremental Allowance = 0 bzw. auf Grundlage des mit 0 berechneten Umfangs | Angabe fehlt | Die Genauigkeit setzt den Stichprobenumfang und die Incremental Allowance voraus. |
| C19, C21 | C4, C7, C13, C14 | Hochrechnung mit Fehlern = 0 bzw. auf Grundlage des mit 0 berechneten Umfangs | Angabe fehlt | Die Hochrechnung setzt den Stichprobenumfang und die Fehler der Stichprobe voraus. |
| C20, C22 | C4, C7, C13, C14, C16 | Obere Fehlergrenze mit Fehlern bzw. Incremental Allowance = 0 oder auf Grundlage des mit 0 berechneten Umfangs | Angabe fehlt | Die Hochrechnung setzt den Stichprobenumfang und die Fehler der Stichprobe voraus. |

### X2_DiffSch_2017

| Zellen | leer ist eine von | Vorlage zeigt | Webfassung zeigt | Begründung |
|---|---|---|---|---|
| C6 | C5 | FALSCH (keine Stufe des Konfidenzniveaus trifft zu; zählt in der Rechnung als 0) | Angabe fehlt | Ohne Konfidenzniveau gibt es keinen Koeffizienten z. |
| C8 | C1, C7 | 0 € (leere Zelle zählt als 0) | Angabe fehlt | Der voraussichtliche Fehler setzt Buchwert und erwartete Fehlerquote voraus. |
| C10, C23 | C1 | 0 € (leere Zelle zählt als 0) | Angabe fehlt | Der zulässige Fehler setzt den Buchwert voraus. |
| C11, C19, C20 | C3, C4, C5, C7 | Wert auf Grundlage des mit 0 berechneten Umfangs (Mindestumfang 30) | Angabe fehlt | Ohne Umfang der Grundgesamtheit, Standardabweichung, Konfidenzniveau und erwartete Fehlerquote ist der Stichprobenumfang nicht bestimmt; alle Folgegrößen bleiben offen. |
| C14, C16, C17, C18, C21, C22 | C3, C4, C5, C7, C13 | Hochrechnung mit einem Stichprobenfehler von 0 € bzw. auf Grundlage des mit 0 berechneten Umfangs | Angabe fehlt | Die Hochrechnung setzt den Stichprobenumfang und den Fehler der Stichprobe voraus. |

### X3_DiffSch_S_2017

| Zellen | leer ist eine von | Vorlage zeigt | Webfassung zeigt | Begründung |
|---|---|---|---|---|
| D1, D14, D30 | E6–K6, AA6–AM6 | Wert ohne den Buchwert der Schicht mit fehlender Angabe | Angabe fehlt | Zu einer belegten Schicht gehören Buchwert, Umfang und Standardabweichung; fehlt eine Angabe, sind die Summen des Blatts nicht bestimmt. |
| D3 | E7–K7, AA7–AM7 | Summe ohne den Umfang der Schicht mit fehlender Angabe | Angabe fehlt | Zu einer belegten Schicht gehören Buchwert, Umfang und Standardabweichung; fehlt eine Angabe, sind die Summen des Blatts nicht bestimmt. |
| D4 | E7–K7, AA7–AM7, E8–K8, AA8–AM8 | Wert ohne den Beitrag der Schicht mit fehlender Angabe | Angabe fehlt | Zu einer belegten Schicht gehören Buchwert, Umfang und Standardabweichung; fehlt eine Angabe, sind die Summen des Blatts nicht bestimmt. |
| D10 | D9 | FALSCH (keine Stufe des Konfidenzniveaus trifft zu; zählt in der Rechnung als 0) | Angabe fehlt | Ohne Konfidenzniveau gibt es keinen Koeffizienten z. |
| D12 | D11, E6–K6, AA6–AM6 | 0 € bzw. Wert ohne den Buchwert der Schicht mit fehlender Angabe | Angabe fehlt | Der voraussichtliche Fehler setzt die erwartete Fehlerquote und den Buchwert jeder belegten Schicht voraus. |
| D15, D26, D27, E17–K17, AA17–AM17 | D9, D11, E6–K6, AA6–AM6, E7–K7, AA7–AM7, E8–K8, AA8–AM8 | Wert auf Grundlage des mit 0 berechneten Umfangs (mindestens 30) | Angabe fehlt | Ohne Konfidenzniveau, erwartete Fehlerquote und die Angaben jeder belegten Schicht ist der Stichprobenumfang nicht bestimmt; alle Folgegrößen bleiben offen. |
| D23, D24, D25, D28, D29, E20–K20, AA20–AM20, E22–K22, AA22–AM22 | D9, D11, E6–K6, AA6–AM6, E7–K7, AA7–AM7, E8–K8, AA8–AM8, E19–K19, AA19–AM19 | Hochrechnung mit einem Stichprobenfehler von 0 € bzw. auf Grundlage des mit 0 berechneten Umfangs | Angabe fehlt | Die Hochrechnung setzt den Stichprobenumfang und den Fehler der Stichprobe mindestens einer belegten Schicht voraus. |
| D23 | E22–K22, AA22–AM22 | 0 € (Summe über Schichten ohne hochgerechneten Fehler) | kein Wert | Trägt keine Schicht einen hochgerechneten Fehler, gibt es nichts zu summieren; eine Summe von 0 € sähe wie ein Ergebnis aus. Die Webfassung lässt ihn offen, solange eine Pflichteingabe fehlt; bei vollständigen Eingaben zeigt sie ihn wie die Vorlage mit Hinweis in Warnfarbe. |
| D24, D25 | D23 | Fehlerquote 0 % bzw. berichtigter Buchwert in Höhe des Buchwerts, gerechnet mit einem hochgerechneten Fehler von 0 € | kein Wert | Der Wert baut auf einer Summe auf, zu der keine Schicht beiträgt; ohne sie ist er nicht bestimmt. Die Webfassung lässt ihn offen, solange eine Pflichteingabe fehlt; bei vollständigen Eingaben zeigt sie ihn wie die Vorlage mit Hinweis in Warnfarbe. |

### X4_DiffSch_2Z_2017

| Zellen | leer ist eine von | Vorlage zeigt | Webfassung zeigt | Begründung |
|---|---|---|---|---|
| C1, C15 | C3, C4 | Wert auf Grundlage nur eines Buchwerts bzw. 0 € | Angabe fehlt | Der Buchwert der Grundgesamtheit setzt die Buchwerte beider Zeiträume voraus. |
| C9 | C5, C6, C7, C8 | Wert ohne den Beitrag des Zeitraums mit fehlender Angabe | Angabe fehlt | Das gewichtete Mittel der Varianzen setzt Umfang und Standardabweichung beider Zeiträume voraus. |
| C11 | C10 | FALSCH (keine Stufe des Konfidenzniveaus trifft zu; zählt in der Rechnung als 0) | Angabe fehlt | Ohne Konfidenzniveau gibt es keinen Koeffizienten z. |
| C13 | C3, C4, C12 | 0 € bzw. Wert auf Grundlage nur eines Buchwerts | Angabe fehlt | Der voraussichtliche Fehler setzt die Buchwerte beider Zeiträume und die erwartete Fehlerquote voraus. |
| C16, C17, C18 | C3, C4, C5, C6, C7, C8, C10, C12 | Umfang auf Grundlage der mit 0 gerechneten Angabe (z. B. 0) | Angabe fehlt | Ohne die Angaben zur Planung des ersten Zeitraums ist der Stichprobenumfang nicht bestimmt. |
| C24, C30, C43 | C3, C25 | Wert auf Grundlage nur eines Buchwerts bzw. 0 € | Angabe fehlt | Der Buchwert der Grundgesamtheit setzt die Buchwerte beider Zeiträume voraus. |
| C28 | C3, C25, C27 | 0 € bzw. Wert auf Grundlage nur eines Buchwerts | Angabe fehlt | Der voraussichtliche Fehler setzt die Buchwerte beider Zeiträume und die erwartete Fehlerquote voraus. |
| C31 | C3, C4, C6, C7, C8, C12, C22, C25, C27, C23, C26 | Umfang auf Grundlage der mit 0 gerechneten Angabe (z. B. 0) | Angabe fehlt | Ohne die Angaben beider Zeiträume ist der neu berechnete Stichprobenumfang nicht bestimmt; alle Folgegrößen bleiben offen. |
| C39, C40 | C3, C4, C6, C7, C8, C12, C22, C25, C27 | Genauigkeit auf Grundlage der mit 0 gerechneten Angabe | Angabe fehlt | Ohne die Angaben beider Zeiträume ist der neu berechnete Stichprobenumfang nicht bestimmt; alle Folgegrößen bleiben offen. |
| C36, C37, C38, C41, C42 | C3, C4, C6, C7, C8, C12, C22, C25, C27, C21, C34 | Hochrechnung mit einem Stichprobenfehler von 0 € bzw. auf Grundlage der mit 0 gerechneten Angabe | Angabe fehlt | Die Hochrechnung setzt die Stichprobenumfänge und die Fehler der Stichproben beider Zeiträume voraus. |

<!-- abweichungen:end -->

## 2. Verknüpfungen zu Blatt 02

Die grünen Verknüpfungen (z. B. `03_MUS_1Z!C7 = 02_Grundgesamtheit!C51`) zeigen
in der Vorlage 0, solange Blatt 02 leer ist. In der Webfassung liefert ein
leeres Blatt 02 keinen Buchwert 0, sondern keinen Wert (Blatt 02: C37, C38,
C51, C52); die Verknüpfung im Methodenblatt ist dann leer. Leert die
Prüfbehörde eine überschriebene Verknüpfung, gilt wieder der Wert aus Blatt
02; in Excel bliebe die Zelle leer, weil die Formel überschrieben ist.
Überschriebene Verknüpfungen sind in der Oberfläche markiert.

Eine nicht lesbare Eingabe in einem vorbelegten Feld (etwa „abc“ im Buchwert
von Blatt 03) fällt nicht still auf den Wert aus Blatt 02 zurück: Das Feld
zählt als ungültig, Ergebnisspalte und Kennzahlenleiste melden „Eingabe
ungültig“, abhängige Größen zeigen „—“. Erst ein geleertes Feld übernimmt
wieder die Vorbelegung (`UNREADABLE_INPUT` in `src/model/sheet.ts`). Hängt
kein Ergebnis an dem Feld (N in Blatt 03 geht in den MUS-Umfang nicht ein),
ist nur das Feld selbst als ungültig markiert.

Seit 0.1.11 gilt das für **jedes** Eingabefeld, nicht nur für vorbelegte: Eine
nicht lesbare Eingabe („abc“, zu viele Nachkommastellen, Punkt als
Dezimaltrenner) fällt auf keine Leer-Regel zurück – weder auf „leer = 0“
(Standardabweichungen der Stichprobe s_e/s_q/s_r je Zeitraum und Schicht) noch
auf „keine“ (freiwillige Felder und Gruppen). `evaluateSheet` ermittelt die
abhängigen Zellen durch Nachrechnen mit Probewerten (`dependentCells` in
`src/model/dependence.ts`) und lässt jede offen; sie zeigt „Eingabe ungültig“,
der Hinweis „mit 0 berechnet“ entfällt, und Werte ohne Grundlage bleiben offen.
Ergebnisspalte, Kennzahlenleiste und Ansage nennen die ungültige Eingabe
(`SummaryView.invalidNote`, seit 0.1.12); was nicht von ihr abhängt, bleibt
sichtbar.
Ist die obere Fehlergrenze offen, zeigen Skala und Kennzahlenleiste keine Ampel
(vorher grün aus der Gesamtfehlerquote allein). Ein wirklich leeres Feld folgt
weiter seiner Leer-Regel. Eigenschaftstest über alle Zahlenfelder der Blätter
02–20 und X1–X4: `test/unreadable.spec.ts`.

## 3. Rechensemantik von Excel: Vergleiche, Differenzen, Aufrunden, Summen

Referenz ist die Excel-Vorlage, also gilt das Rechenverhalten von **Microsoft
Excel** (Microsoft 365, Version 16.0.20326, 64 Bit, de-de). Es ist in einer
Versuchsmappe gemessen (Excel-Gegenprobe vom 17.10.2026; 451 Vergleiche mit
eingegebenen und 363 mit berechneten Zahlen, 193 Rundungen, 10 Summen in
`test/fixtures/excel-semantik.json`) und in `test/excel.spec.ts` Probe für
Probe nachgeprüft. LibreOffice ist nur noch Hilfsmittel; seine Messung
(`test/fixtures/libreoffice-semantik.json`, `scripts/measure_semantics.py`)
bleibt zum Vergleich erhalten.

- **Vergleiche** (`=`, `<>`, `<`, `<=`, `>`, `>=`): Excel rundet beide Seiten
  auf 15 geltende Dezimalstellen und vergleicht dann genau (`excel.eq`, `ne`,
  `lt`, `le`, `gt`, `ge`; rohe Vergleiche sind in `src/sheets` per
  Lint-Regel gesperrt). Das Fenster, in dem zwei Zahlen gleich sind, hängt
  deshalb von der Lage der Dezimalstellen ab: 1 und 1,0000000000000036 sind
  gleich, 0,9999999999999993 ist kleiner als 1. LibreOffice verglich mit
  einer festen relativen Toleranz von 2⁻⁴⁸; an Schwellen (Prüfsonden „GFQ =
  Schwelle ± 3e-15“) würdigt Excel deshalb in 89 Zellen anders.
- **Differenzen und Summen als letzte Rechenoperation** (`excel.minus`,
  `excel.plus`): Liegt das Ergebnis der letzten Addition oder Subtraktion
  einer Formel um mindestens 50 Binärstellen unter dem kleineren Summanden,
  setzt Excel es auf genau 0 (1 − 1,0000000000000013 ergibt 0,
  1 − 1,0000000000000018 ergibt 1,8 · 10⁻¹⁵). Innerhalb einer Formel gilt die
  Regel nicht (`=WENN(B−A=0;…)` sieht den Rest). Die Rechenkerne wenden sie an
  den Stellen an, an denen sie `minus`/`plus` verwenden, auch wo die
  Operation in der Vorlage innerhalb einer Formel steht; der Abgleich zeigt
  dort keine Abweichung.
- **`AUFRUNDEN`** (`excel.roundUp`): Excel rundet den Wert zuerst auf
  15 geltende Stellen und rundet dann von null weg auf. 100 · (1 + 10⁻¹⁴)
  ergibt 101, 100 · (1 + 16 · 2⁻⁵²) bleibt 100. LibreOffice kürzte auf zwölf
  Stellen; ein Rohumfang mit Rechenrauschen ab etwa 10⁻¹⁴ relativ über einer
  ganzen Zahl ergibt deshalb in Excel (und jetzt in der Webfassung) **einen
  Stichprobenumfang mehr** (Prüfsonden „R-off“, „G… n = … + 2e-12“, „K TE−AE
  relativ …“; Blätter 03, 08, X2).
- **`VERGLEICH(…;0)`** (`excel.matchExact`, z-Wert in Blatt 01) sucht Zahlen
  genau, ohne die 15-Stellen-Regel von `=`: Ein Konfidenzniveau
  0,7000000000000001 steht nicht in der Tabelle, z und alle Folgezellen
  bleiben leer (Blatt 03, Prüfsonde T06). LibreOffice fand 0,7.
- **`SUMME`** (`excel.sum`) addiert der Reihe nach ohne Fehlerausgleich; nur die
  letzte Addition folgt der Regel für Differenzen: `SUMME(0,1;0,7;0,2;−1)`
  ergibt 0, `SUMME(0,1;0,2;−0,3;0)` 5,55 · 10⁻¹⁷. LibreOffice summierte mit
  Fehlerausgleich (Kahan-Neumaier). In der Vorlage wirkt das nur auf
  Rundungsrauschen, zum Beispiel Blatt 02 C30, wo Excel einen Rest bis
  4,8 · 10⁻⁷ € zeigt; die Abstimmungsprüfung C31 entscheidet gleich.

Wie die Regeln für eine Formel genau greifen, die nicht gemessen ist (etwa
`SUMME` über Bereiche mit Lücken), ist aus den Messungen abgeleitet, nicht
einzeln belegt; der Abgleich über alle 728.895 Formelzellen ist der Nachweis
für die Vorlage.

**Sollwerte und Toleranz.** Seit Fassung 0.1.6 stammen alle Sollwerte des
Golden-Abgleichs aus der Neuberechnung der Vorlage in Excel (10.531 Fälle,
eingetragen über COM, `CalculateFull`; Werkzeugkette der Excel-Gegenprobe).
Die früheren Sollwerte aus LibreOffice 24.2 liegen in der Versionsgeschichte
(Fassung 0.1.5, `test/golden/`); sie weichen in 937 Zellen von Excel ab
(Vergleich an Schwellen 89, `AUFRUNDEN` 723, `VERGLEICH` 21, Wahrheitswert 82,
`#DIV/0!` 22). Der Abgleich vergleicht Zellen mit Ganzzahlformat genau, die
übrigen auf 1e-9 relativ: Die Toleranz deckt nur die Reihenfolge der
Gleitkommaoperationen, die in JavaScript und Excel nicht in jeder Formel
gleich ist (Unterschiede bis etwa 10⁻¹⁵ relativ), nicht eine abweichende
Semantik. Bei Eurobeträgen gilt zusätzlich ein Unterschied bis 10⁻⁶ € als
gleich (Auslöschung in Abstimmungszellen, Blatt 02 C30). Zwei Nebenbefunde der
Gegenprobe erklären, warum die Toleranz trotzdem nötig ist: LibreOffice
schrieb Formelergebnisse nur mit 15 geltenden Stellen in die Mappe, die alten
Sollwerte waren also auf 15 Stellen gerundet; Excel liefert über COM die volle
Gleitkommazahl. In der Versuchsmappe speicherte Excel Zahlkonstanten nur mit
16 geltenden Stellen (1,0000000000000002 wurde 1). In der Gegenprobe selbst
kamen die über COM gesetzten Eingaben dagegen bitgenau an: Mit den
unveränderten 17-stelligen Prüfeingaben stimmt jede Zelle, mit auf 16 Stellen
gerundeten Eingaben wichen 24 Zellen ab (Prüfsonden „K TE−AE relativ 1e-4“).

**Toleranzkanten** gibt es gegen Excel keine mehr. Die beiden Würdigungen, die
gegen LibreOffice als „Toleranzkante“ geführt waren (Blatt 06 C99, Blatt 12
C138, je eine Prüfsonde der Abnahme), zeigt die Webfassung mit der
Vergleichsregel von Excel genau wie Excel; die Sonderregel des Abgleichs für
verschobene Eingaben ist entfallen.

**Wahrheitswert und Fehlerwert: bewusst anders dargestellt.** Zwei Fälle zeigt
die Webfassung bewusst anders als Excel; der Abgleich führt sie als „bewusst
anders dargestellt“ (`adapted`) und prüft je Zelle, dass die Webfassung genau
den Wert zeigt, der sich nach der Regel aus dem Wert von Excel ergibt:

- Altvorlagen X1 C5/C6, X2 C6, X3 D10, X4 C11: Bei einem Konfidenzniveau
  außerhalb der fünf Stufen fehlt der innersten `WENN` der Sonst-Zweig; Excel
  zeigt den Wahrheitswert FALSCH und rechnet damit wie mit 0. Ein
  Wahrheitswert ist als Faktor nicht lesbar; die Webfassung zeigt die Zahl, mit
  der die Vorlage rechnet (0), und den Hinweis „Konfidenzniveau ist keine Stufe
  der Altvorlage …“ in Warnfarbe. Alle Folgewerte sind gleich.
- Blatt 20 E20–E27: Bei Buchwert 0 zeigt die Vorlage für die Fehlerquote des
  Falls `#DIV/0!` (die Formel `=WENN(ODER(C21="";D21="");"";D21/C21)` fängt
  den Fehler nicht ab). Die Webfassung zeigt keinen Wert und den Hinweis
  „Fehlerfall …: Buchwert 0 – die Quote ist nicht bestimmbar“. Der alte
  Sollwert aus LibreOffice war hier leer und entsprach nicht der Vorlage; auch
  eine frische Neuberechnung mit LibreOffice ergibt `#DIV/0!`.

**Grenze des geprüften Zahlenbereichs:** Stichprobenumfänge ab 10¹⁵ Einheiten
entstehen nur, wenn TE und AE bis auf Rundungsrauschen gleich sind. Dort
streuen Vorlage und Webfassung um bis zu einige 10⁻⁵ relativ (gegen Excel
gemessen: höchstens 5,4 · 10⁻⁵). Die Webfassung zeigt den Wert und weist ihn
mit „… außerhalb des geprüften Zahlenbereichs … nicht belastbar“ in Warnfarbe
aus; der Abgleich vergleicht dort nur die Größenordnung (relativ 10⁻³).

**Nicht geprüft** sind Eingaben von Hand über die Oberfläche von Excel (Excel
schneidet getippte Ziffern ab der 16. Stelle ab), Datenüberprüfung,
bedingte Formate und das Druckbild der Vorlage.

## 4. Blatt 03: begrenzter Stichprobenumfang ohne rechnerischen Umfang

Ist der begrenzte Stichprobenumfang gewählt und fehlt die voraussichtliche
Fehlerquote oder Standardabweichung, zeigt die Vorlage `MIN(MAX(n;30);n_lim)`
mit dem aus 0 berechneten n. Der Referenz-Rechenkern `engine.js` des
Ausgangsmaterials zeigte hier den begrenzten Umfang (50 bzw. 30). Die
Webfassung zeigt „Angabe fehlt“, damit die Regel oben ohne Ausnahme gilt. Für
`TE ≤ AE` und für ein fehlendes Konfidenzniveau zeigt die Vorlage selbst den
begrenzten Umfang; die Webfassung folgt ihr.

## 5. Schichtzeilen

Die Summe über eine Schichtzeile, in der keine Schicht einen Wert trägt, ist
in der Vorlage 0. Solange eine Pflichteingabe fehlt, zeigt die Webfassung
dort keinen Wert (`withoutBasis`) – auch nicht in den Zellen, die auf dieser 0
aufbauen (Abgleich mit Blatt 02, zulässiger Fehler, Hochrechnung, Würdigung,
Ergebnisübersicht). Summen, die vom Stichprobenumfang abhängen, bleiben offen,
solange der Umfang wegen einer fehlenden Angabe offen ist.

Der Prüfhinweis „mindestens drei Einheiten je (Zufalls-)Schicht“ lautet in
der Vorlage „✔ ≥ 3“, wenn es keinen Umfang je Schicht gibt (leere Textzelle,
im Vergleich größer als jede Zahl). Fehlt eine Pflichteingabe, zeigt die
Webfassung ihn in allen geschichteten Blättern einheitlich nicht
(`checkStratumUnits`); sind alle Pflichteingaben vorhanden (etwa bei „TE ≤
AE“), zeigt sie ihn wie die Vorlage und weist ihn als Wert ohne Grundlage aus.

Die 8. bis 20. Schicht (Spalten AA–AM) gibt es in der Vorlage nicht; siehe
[schichten-und-listen.md](schichten-und-listen.md). Die Altvorlage X3 führt
ihre Schichten in E–K; die Webfassung liest die Schichtspalten je Blatt aus
der Definition (`strataColumnsOf`).

## 6. Blatt 17 als Liste

Die Vorlage wird je Stichprobeneinheit kopiert, die Webfassung führt eine
Liste. Die Zuordnung der Einheiten zum Methodenblatt (Zellen W5–W10:
Zufallsschicht oder hochwertige Einheit, maßgebliche Variante, Nummer der
Schicht, Stichprobenzeitraum) und die Summenbildung sind Hinweise der
Webfassung; der Rechenkern je Einheit folgt der Vorlage. Die Summen werden
per Schaltfläche in die Eingaben des gewählten Verfahrens übernommen. Die
Übernahme gibt es für die Blätter 03, 04, 08, 13 und 15 – in Blatt 04 je
Schicht; Einheiten ohne die dafür nötige Schichtnummer werden nicht
übernommen und genannt. Die übrigen Blätter (05–07, 09–12, 14, 16) nehmen
keine Summen auf; dort sind sie von Hand einzutragen. Die Hinweise an den
Feldern W9 und W10 und die Meldung der Oberfläche sagen genau das.

## 7. Darstellung

Prozentwerte erscheinen mit drei Nachkommastellen (0,652 %), die Vorlage
formatiert mit zwei. Gerechnet wird mit dem vollen Wert; der Excel-Export
verwendet die Zahlenformate der Vorlage.

## 8. Mit 0 gerechnet und ausgewiesen

Entscheidung des Auftraggebers: Fehlt die Standardabweichung der Stichprobe
(z. B. Blatt 03: C39; Blatt 04: Zeile 47 einer belegten Schicht), rechnet die
Webfassung wie die Vorlage mit 0 und zeigt die Werte. An den betroffenen
Werten (Genauigkeit, Fehlergrenzen, Würdigung) steht der Hinweis der
Webfassung „Keine Angabe, daher mit 0 berechnet.“ (englisch „Not provided,
therefore calculated with 0.“). Die Würdigung erscheint mit dem Wortlaut der
Vorlage, daneben in Warnfarbe der Hinweis; sie ist nicht uneingeschränkt grün.
Derselbe Hinweis steht in der Ergebnisspalte, im Excel-Export, im Arbeitsstand
(`hinweise`), in Blatt 18 und im Bericht (Nr. 13). Ebenso behandelt wird die fehlende Fehlersumme
einer von mehreren belegten Schichten bzw. eines von mehreren Zeiträumen
(`partialErrorSum`). Das ist keine Abweichung im Wert, sondern eine
Kennzeichnung; die Fallarten stehen in Abschnitt 1.

## 9. Import der ausgefüllten Vorlage

Die Webfassung liest die Eingabezellen aller Blätter der ausgefüllten Vorlage
und nennt, welche Blätter Werte enthielten. Kopien des Blatts 17 werden zu
weiteren Stichprobeneinheiten – auch unter freiem Namen, erkannt am Titel des
Blatts und in der Vorschau genannt; das in Blatt 18 gewählte Methodenblatt
wird das aktive Verfahren, und Blatt 18 gilt damit als ausgefüllt. Vor der
Übernahme zeigt eine Vorschau:

- **Umgedeutete und nicht übernommene Werte** mit Blatt, Zelle, gefundenem
  Wert und Grund (abweichende Schreibweise einer Auswahl, Zahl als Text,
  überschriebene Verknüpfung, unbekannter Auswahlwert). Ein Datum, das als
  Tageszahl in der Zelle steht (Blatt 20 „Stand“), wird als Datum übernommen.
- **Hinweise zur Mappe:** Zahlen in Schichtzeilen außerhalb der sieben
  Schichtspalten (z. B. eine selbst angelegte Spalte K) werden nicht gelesen
  und genannt; ist in Blatt 18 der Mappe kein Methodenblatt gewählt, sagt die
  Vorschau, welches Verfahren die Webfassung als aktiv annimmt; eine in der
  Mappe gelöschte Vorgabe (z. B. die Signifikanzschwelle) übernimmt die
  Webfassung als leere Zelle, statt die Vorgabe wieder einzusetzen.
- **Gegenprobe gegen die Rechenwerte der Mappe** für alle ausgefüllten Blätter
  und immer auch für Blatt 18 und den Bericht, einschließlich der Summenzellen
  und der Ergebnisübersicht N3–N11, in beide Richtungen: anderer Wert, „Mappe
  mit Wert, Webfassung ohne“ und „Mappe leer, Webfassung mit Wert“.
  Begründete Fälle („Angabe fehlt“, die Vorlage rechnet mit 0) stehen getrennt
  in einer zugeklappten Liste, damit echte Unterschiede auffallen. Verglichen
  werden nur Zellen, die es in der Mappe gibt; eine nie berechnete Datei
  enthält keine Rechenwerte und wird nicht verglichen.

Ein abgeschnittenes oder übergroßes Blatt ist ein Lesefehler; die Datei wird
abgelehnt, nicht teilweise gelesen. Übernommen wird erst nach Bestätigung.

## 10. Prüfsumme des Arbeitsstands

Die Prüfsumme (SHA-256) umfasst Kopf, aktives Verfahren und Eingaben in
kanonischer Reihenfolge. Der Zeitpunkt `gespeichertAm`, die gespeicherten
Ergebnisse und die Hinweise gehören bewusst nicht dazu: Die Prüfsumme
belegt, dass die Eingaben unverändert sind; Ergebnisse und Hinweise werden
beim Öffnen neu gerechnet. Ein nachträglich geänderter Zeitstempel fällt
deshalb nicht auf.

## 11. Wo die Webfassung der Vorlage trotz Auffälligkeit folgt

Die vorläufige Vorgabe betrifft Werte, die nur wegen einer fehlenden Angabe
entstehen, und bestandene Prüfhinweise ohne Grundlage. Folgende Stellen fallen
nicht darunter; die Webfassung zeigt dort denselben Wert wie die Vorlage und,
wo es der Einordnung dient, einen Hinweis der Webfassung in Warnfarbe:

- **Warnung ohne obere Fehlergrenze** (Blätter 03–12): Fehlt die obere
  Fehlergrenze, zeigt die Vorlage „⚠ GFQ unter, obere Fehlergrenze über der
  Schwelle – weitere Würdigung“. Die Warnung ist die vorsichtigere Aussage und
  bleibt; fehlt die Genauigkeit nur wegen einer fehlenden Angabe, bleibt die
  Würdigung offen.
- **Nicht positiver Nenner der Standardneuberechnung** (05–07, 10–12): Der
  Text „✖ nicht anwendbar (Nenner ≤ 0)“ steht wie in der Vorlage; sind alle
  Pflichteingaben vorhanden, zeigen alle sechs Blätter einheitlich die
  Untergrenzen (3 bzw. Auffüllung auf 30) und die Auswertung wie die Vorlage,
  dazu Hinweise in Warnfarbe (Empfehlung: globale Neuberechnung).
- **Negative oder unbegrenzte Umfänge der Altvorlagen** (X1–X4) und der
  **nicht positive Anpassungsfaktor in Blatt 18**: wie die Vorlage, mit Hinweis.
- **Hilfszeilen je Schicht**, die für unbelegte Schichten 0 tragen (z. B.
  Blatt 04 Zeilen 25 und 52, Blatt 14 Zeile 27): wie die Vorlage.
- **Freiwillige Einzelbeträge** aus `N(…)` (systembedingte und anomale
  Fehler, in Blatt 20 die Beträge nach Art. 98 Abs. 6 und die
  Finanzkorrekturen): 0 ohne Ausweis. Für die Fehler der hochwertigen bzw.
  umfassenden Schicht gilt das nur, solange die Schicht gar nicht erklärt ist
  (Nr. 13).
- **Negative Ergebnisse** (mehr hochwertige Einheiten als Stichprobenumfang,
  negative Gesamt- oder Restfehlerquote): wie die Vorlage, mit Hinweis in
  Warnfarbe (Nr. 13).

Eine Zusammenstellung dieser und weiterer Auffälligkeiten der Vorlage für den
Auftraggeber liegt außerhalb des Repositorys.

## 12. Bericht: Programm und Prüfbehörde sind Angaben, kein fester Text

Die Vorlage nennt in Blatt 20 fest ein bestimmtes Programm (Kopfzeile, Zelle
A6) und eine bestimmte Prüfbehörde (Fußzeile der Druckseite). Die Webfassung
wird von Prüfbehörden verschiedener Programme und Mitgliedstaaten benutzt;
ein Bericht mit fremder Behörde im Fuß wäre dort falsch. Sie weicht deshalb
**bewusst im Wert** von der Vorlage ab:

- **Kopfzeile:** „Bezeichnung des Programms · CCI … · Geschäftsjahr … ·
  Status“. Die Bezeichnung gibt die Prüfbehörde bei den Steuerfeldern an (Zelle
  W4, in der Vorlage unbelegt); ohne Angabe gilt „Programm(e) / CCI“ des
  gewählten Verfahrens, sonst beginnt die Zeile mit der CCI-Nummer. Der Teil ab
  „CCI“ ist wie in der Vorlage.
- **Fußzeile:** Prüfbehörde, Organisationseinheit und Ort aus den Angaben W5–W7.
  Ohne Angabe bleibt die Fußzeile im Druck leer.
- Fehlende Angaben zeigt die Bildschirmansicht als Platzhalter in eckigen
  Klammern; er wird nicht gedruckt. Kopf- und Fußzeile folgen der gewählten
  Sprache; die Angaben selbst bleiben, wie sie eingegeben sind.
- Die Angaben stehen im Arbeitsstand und im Excel-Export. Beim Import der
  ausgefüllten Vorlage bleiben sie leer, weil die Vorlage sie nicht kennt.
- Am Bericht steht dazu der Hinweis der Webfassung (`own-header`); im
  Abgleich ist Zelle A6 als bewusst anders gebildet geführt (`adapted` im
  Blattmodul): Verglichen wird der Teil ab „CCI“.

Das ausgelieferte Paket enthält keinen festen Namen einer Behörde oder eines
Programms, auch nicht in den Beispielwerten (`test/neutral.spec.ts`).

Ebenfalls anders als in der Vorlage: Leere Freitextfelder des Berichts werden
nicht mit ihrem Platzhaltertext in eckigen Klammern gedruckt, sondern bleiben
im Druck leer; der Platzhalter steht nur am Bildschirm.

## 13. Einschränkungen eines Ergebnisses: Hinweise in Warnfarbe

An keiner dieser Stellen weicht ein Wert von der Vorlage ab. Die Webfassung
sagt aber dazu, wenn ein gezeigtes Ergebnis nicht belastbar ist
(`src/view/limits.ts`):

| Art | Wann | Hinweis |
|---|---|---|
| mit 0 gerechnet | Standardabweichung der Stichprobe oder Fehlersumme einer von mehreren Schichten fehlt (Nr. 8) | „Keine Angabe, daher mit 0 berechnet: …“ |
| stille Lücke | Eine nicht freiwillige Eingabe ist leer, die Vorlage rechnet ohne sie weiter, und ein gezeigtes Ergebnis hängt von ihr ab – etwa Buchwert, Anzahl oder Summe der Buchwerte der Stichprobe einer belegten Schicht, der Ist-Wert eines Zeitraums, das Konfidenzniveau oder die Fehlersumme einer erklärten hochwertigen bzw. umfassenden Schicht | „Angabe fehlt: Schicht n: … (Zelle). Die Vorlage rechnet ohne sie weiter; das Ergebnis hängt aber von ihr ab und ist so nicht belastbar. Trifft 0 zu, bitte 0 eintragen“ |
| ohne Grundlage | Wert der Vorlage ohne Grundlage bei vollständigen Pflichteingaben (Nr. 1) | „Wie in der Vorlage gezeigt, obwohl die Grundlage fehlt: …“ |
| negatives Ergebnis | Eine berechnete Anzahl, ein Auswahlintervall, der extrapolierte Fehler oder eine Fehlerquote ist negativ | „Mehr hochwertige Einheiten als Stichprobenumfang: Die Zufallsschicht ist negativ …“ und „Negativer Wert wie in der Vorlage: …“ |
| Zahlenbereich | Stichprobenumfang ab 10¹⁵ (Nr. 3) | „… außerhalb des geprüften Zahlenbereichs …“ |
| Hinweis des Blatts | Hinweise der Webfassung in Warnfarbe (`webHints`) | Text des Blatts |
| Abweichung von der DelVO | Die Vorlage weicht an dieser Stelle von der DelVO ab (Nr. 16) | Text mit Fundstelle der DelVO und Wirkung |
| Auslegung, Altvorlage | wie bisher | „Auslegung der Vorlage – …“, Hinweis der Altvorlage |

**Stille Lücken** ermittelt `src/model/dependence.ts` einheitlich für alle
Blätter durch Nachrechnen: Das Blatt wird mit Probewerten an der Stelle der
leeren Eingabe noch einmal gerechnet; ändert sich eine Ergebniszelle
(extrapolierter Fehler, Fehlerquote, obere Fehlergrenze, Stichprobenumfang),
hängt sie davon ab. Bei Schichtzeilen zählen nur belegte Schichten. Die Regel
ist als Eigenschaft geprüft (`test/properties.spec.ts`): Für jede Einzellücke
der Abnahme, die in der Vorlage ein Ergebnis ändert, ist dieses Ergebnis in der
Webfassung offen oder trägt einen Hinweis in Warnfarbe.

**Welche Eingaben freiwillig sind, richtet sich nach der Original-Arbeitsmappe.**
Ausgewertet sind Bezeichnungen, Kommentare, Datenüberprüfungen, bedingte
Formatierungen, die Farblegende (Blatt 00, B5–C8: alle Eingaben gleich „gelb
hinterlegt, blaue Schrift: von der Prüfbehörde auszufüllen“) und die Formeln,
die eine leere Zelle abfangen. Datenüberprüfungen erlauben überall leere Zellen
(Standard der Auswahllisten), bedingte Formatierungen färben nur die
Prüfhinweise (✔/⚠/✖), Kommentare gibt es nur in Blatt 20 („Frei editierbarer
Text“). Was die Vorlage nicht als freiwillig erkennen lässt, ist Pflicht. Wo die Vorlage leere Zellen ohne Kennzeichnung als 0 liest, hat der Inhaber am 17.10.2026 entschieden: freiwillig, leer heißt „keine“, kein Hinweis „Angabe fehlt“. Gruppen (Anzahl, Buchwert und Fehler der hochwertigen Einheiten; Angaben der umfassenden Schicht; Anzahl und Betrag in Blatt 02; Buchwert und Fehler eines Fehlerfalls in Blatt 20) sind nur gemeinsam leer zulässig: Ist ein Teil gefüllt, sind die übrigen Pflicht.

| Eingabe | Kennzeichnung in der Vorlage | Einstufung |
|---|---|---|
| Geschäftsjahr, Programm, CCI, Stichprobeneinheit, Schichtungskriterium, Datenquelle | keine; von keiner Formel verwendet (Blatt 02 C12 nur im Kopf des Berichts) | freiwillig – kein Ergebnis hängt davon ab |
| Freitexte und Fehlerfälle in Blatt 20 | Kommentare A9, A18, A31, A45 „Frei editierbarer Text“; A20 „Fehlerfälle von Hand eintragen“ | freiwillig; Buchwert und Fehler eines Falls nur gemeinsam |
| Aktualisierte bzw. endgültige voraussichtliche Fehlerquote | Bezeichnung „(leer = Wert aus I)“ bzw. „(leer = vorheriger Wert)“ | freiwillig |
| Umfassende Schicht (Buchwert, Anzahl, davon hochwertige, Fehlersumme) | Bezeichnung „(fakultativ)“ am Buchwert | freiwillig als Gruppe |
| Anpassung der hochwertigen Schicht in Blatt 18 (C20–C22) | Abschnittstitel „Anhang III, optional“; Vorgabe „Nein“ | freiwillig; ist „Ja“ gewählt, sind C21 und C22 Pflicht |
| Abgegrenzte systembedingte, nicht berichtigte anomale Fehler | keine Kennzeichnung; leer als 0 gelesen (`N(…)`) | freiwillig, leer = keine (Entscheidung des Inhabers vom 17.10.2026) |
| Hochwertige Einheiten (Anzahl, Buchwert, Fehler) | keine Kennzeichnung; leer als 0 gelesen (`N(…)`) | freiwillig als Gruppe, leer = keine; in 04, 06, 16 sind die Summen n_eh, BV_eh und ΣE_eh ohne Schicht wie in der Vorlage 0 (Entscheidung des Inhabers vom 17.10.2026). Die Summe der Fehlerquoten der Zufallsschicht (Σ E/BV: 04 C46, 06 C48/C82, 16 C26) gehört nicht dazu: Sie ist Ergebnis der Stichprobe, ohne Schicht zeigt die Webfassung „Angabe fehlt“, die Vorlage 0 |
| Blatt 02: TH-Pauschale, negative Datensätze, Ausschlüsse nach Art. 15 Abs. 5, Wiederaufnahmen, Art.-80-Einheiten | keine Kennzeichnung; leer als 0 gelesen | freiwillig, Anzahl und Betrag je als Gruppe (Entscheidung des Inhabers vom 17.10.2026) |
| Blatt 20 J6–J8 (geprüfte Ausgaben, Beträge nach Art. 98 Abs. 6, Finanzkorrekturen) | keine Kennzeichnung; J7, J8 leer als 0 gelesen | freiwillig (Entscheidung des Inhabers vom 17.10.2026) |
| Einheiten der Zufallsschicht mit BV > Auswahlintervall (Iteration; 03 C35, 04 Zeile 43, 05 C43/C77, 07 C46/C85/C119, 15 C20) | keine Kennzeichnung; speist nur den Prüfhinweis „✔ keine weitere Iteration“ | freiwillig (Entscheidung des Inhabers vom 17.10.2026) |
| Konfidenzniveau, Systembewertung, Signifikanzschwelle, voraussichtliche Fehlerquote | keine; unmittelbar in den Formeln | Pflicht |
| Voraussichtliche Standardabweichung (σ_r, σ_e; z. B. 03 C20, 08 C25) | keine; die Vorlage rechnet leer mit 0 und zeigt den Mindestumfang 30 | Pflicht – „Angabe fehlt“ |
| Standardabweichung der Stichprobe in der Auswertung | keine | Pflicht, auf Entscheidung des Auftraggebers mit 0 gerechnet und ausgewiesen |
| Altvorlage X1 C13 (Fehler der hochwertigen Einheiten) | keine; unmittelbar in der Formel | Pflicht (bisher nach dem Feldnamen freiwillig) |

**Die Hinweise reisen mit.** Blatt 18 führt die Einschränkungen des Blatts 02
und des gewählten Verfahrens mit der Blattnummer davor („Blatt 03: …“), der
Bericht zusätzlich die des Blatts 18 – am Bildschirm, im Druck und auf jedem
Blatt des Excel-Exports; im Arbeitsstand stehen sie unter `hinweise`. Ist eine
Altvorlage das gewählte Verfahren, steht der Hinweis in Blatt 18 auch bei
sonst leerem Formular. Schränkt ein Hinweis in Warnfarbe das Ergebnis ein,
erscheint eine bestandene Würdigung („✔“) mit dem Zusatz „Nicht
uneingeschränkt: siehe Hinweise der Webfassung“ und in Warnfarbe statt grün.
Je Hinweisart gibt es einen Durchstich Verfahren → Blatt 18 → Bericht → Export
(`test/limits.spec.ts`).

## 14. Bericht: Zuordnung zum Arbeitsstand

Der Bericht trägt am Bildschirm und im Druck – wie der Kopf des Excel-Exports
– die Vorlage, den Rechtsstand, die Fassung des Rechenkerns und die Prüfsumme
der Eingaben. Damit lässt sich ein Ausdruck einem Arbeitsstand zuordnen. Die
Vorlage kennt diese Zeile nicht.

## 15. Excel-Export: nur bearbeitete Blätter

Exportiert werden das gewählte Verfahren (Blatt „Ergebnis“), Blatt 18 und der
Bericht dazu und jedes weitere Blatt, in dem mindestens eine Eingabe von den
Vorgaben der Vorlage abweicht. Ein Blatt nur mit Vorgaben („✔ ≤ 2 %“) steht
nicht im Export. Ein anderes, früher bearbeitetes Verfahrensblatt trägt im
Kopf den Satz „Nicht das gewählte Verfahren: Dieses Blatt fließt nicht in
Blatt 18 und den Bericht ein.“

## 16. Abgleich mit der DelVO und dem KOM-Leitfaden

Grundlage ist der Abgleich der Vorlage und der Webfassung mit der Delegierten
Verordnung (EU) 2023/67 vom 17.10.2026 (Bericht `DELVO_ABGLEICH_2026-10-17.md`
im Materialordner der Prüfung, nicht im Repository; amtliches PDF ABl. L 7 vom
10.1.2023, S. 1–24). Ergebnis: Jede Formel des Anhangs II, die die Vorlage
abbildet, ist in Vorlage und Webfassung richtig umgesetzt (Stichprobenumfang,
Gewichtung, Aufteilung, Standard- und globale Neuberechnung, Hochrechnung,
Genauigkeit, Fehlergrenzen, Gesamtfehlerquote; z-Werte nach Anhang I Nr. 3).
Abweichungen gibt es nur an den Rändern. **Die Rechenwerte bleiben wie in der
Vorlage**; die Webfassung sagt an jeder Abweichung dazu, was die DelVO verlangt.

**Amtlicher Begriff.** Die Vorlage sagt „Wesentlichkeitsschwelle“ (67 Zellen);
amtlich ist „Signifikanzschwelle“ (Anhang I Nr. 1 DelVO; Anhang XX Nr. 5.9
VO (EU) 2021/1060). Die Webfassung verwendet den amtlichen Begriff in allen
Bezeichnungen, Texten, Hinweisen, im Bericht und im Excel-Export; beim ersten
Vorkommen je Blatt steht „Signifikanzschwelle (Vorlage: Wesentlichkeitsschwelle)“
(`src/model/terms.ts`). Beim Öffnen einer Arbeitsmappe gelten beide Begriffe als
gleich; eine Mappe der Vorlage und ein Export der Webfassung werden gleich
gelesen. Der Golden-Abgleich führt die betroffenen Texte als „amtlicher
Begriff“ (sonst wortgleich). Englisch bleibt „materiality threshold“ wie in der
englischen DelVO. „gering“ (Systembewertung) bleibt: Die DelVO verwendet es
selbst (Anhang I Nr. 2 Satz 1, Erwägungsgrund 11; nur Satz 3 sagt „niedrige
Zuverlässigkeit“).

Weitere Begriffe des Abgleichs, nicht umgestellt:

- „voraussichtliche Fehlerquote“ (Eingabe): Die DelVO nennt die Größe
  „voraussichtlicher Fehler“ (AE), die VO (EU) 2021/1060 Anhang XX Nr. 5.3
  „erwartete Fehlerquote“. Als Bezeichnung der eingegebenen Quote ist
  „voraussichtliche Fehlerquote“ vertretbar und dem amtlichen „voraussichtlichen
  Fehler“ nah; „erwartete Fehlerquote“ wäre in der DelVO-Fassung fremd.
- „prognostizierter Buchwert“ / „prognostizierte Anzahl“ (05–07, 10–12): keine
  Falschbezeichnung (Art. 5 Abs. 7 UAbs. 4 spricht von „Vorhersagen“). Der
  amtliche Begriff „prognostizierter Fehler“ (Art. 2 Nr. 19) ist aber ein
  Synonym des extrapolierten Fehlers; Verwechslungsgefahr besteht, eine
  Umstellung auf „vorhergesagt“ wäre ohne amtlichen Begriff. Bleibt wie in der
  Vorlage.

**Entscheidung des Inhabers vom 17.10.2026: „Es gelten die Vorgaben der KOM“**
(DelVO (EU) 2023/67 und KOM-Leitfaden EGESIF_16-0014-01 zu den
Stichprobenverfahren der Prüfbehörden). Bei den Abweichungen 1 und 2 rechnet die Webfassung nach diesen
Vorgaben, nicht wie die Vorlage. Die Hinweistexte sagen „nach DelVO“ nur, wo
die DelVO es selbst sagt; was aus dem Leitfaden stammt, ist als „nach
KOM-Leitfaden EGESIF_16-0014-01“ gekennzeichnet. Fassung 0.1.8 hatte Nr. 2 nach
einer engeren Lesart der DelVO gesperrt (Umfang bei AE ≥ TE „nicht anwendbar“);
die Gegenprüfung hat das als nicht von der DelVO gedeckt bewertet, Fassung 0.1.9
nimmt es zurück. Ebenso ersetzt 0.1.9 die Gesamt-Näherung von 0.1.8 bei Nr. 1
durch den Bezug auf die Zufallsschicht.

- **Nr. 2, Planung bei AE > TE** (03–12, erster Zeitraum, Standard- und globale
  Neuberechnung). Anhang II DelVO nennt die Formel n = (z·BV·σ / (TE − AE))²,
  aber keine Bedingung TE > AE. Der Leitfaden plant ausdrücklich auch bei
  AE > TE, mit der geplanten Genauigkeit |TE − AE| (Abschnitt 7.1, S. 183 mit
  Fußnote 59); ab AE ≥ 4 % empfiehlt er, mit 4 % zu rechnen (geplante
  Genauigkeit höchstens 2 %), nahe der Schwelle die Grundgesamtheit zu teilen.
  Die Webfassung rechnet daher bei AE > TE den Umfang wie die Formel
  (quadriert, also mit |TE − AE|), mit neutralem Hinweis
  `anticipated-above-tolerable` (globale Neuberechnung `-global`, `-global-3`);
  ab dem Doppelten der Signifikanzschwelle zusätzlich der neutrale Hinweis
  `anticipated-at-least-4` (Auslegung der Webfassung: Der Leitfaden nennt
  4,0 % bei 2 % Schwelle; bei niedrigerer Schwelle löst der Hinweis beim
  Doppelten aus) – der eingegebene Wert wird nicht ersetzt. Die
  Standardneuberechnung trägt denselben Hinweis (`-standard`, `-standard-3`):
  Ihr Nenner (TE − AE)² − … beruht ebenso auf |TE − AE|. Im ersten Zeitraum weicht das von der
  Vorlage ab (sie zeigt „TE ≤ AE“ und keinen Umfang, Prüfhinweis „✖ TE ≤ AE“);
  die Webfassung zeigt den Umfang und als Prüfhinweis „⚠ AE > TE: Umfang mit der
  geplanten Genauigkeit |TE − AE| (KOM-Leitfaden EGESIF_16-0014-01, 7.1)“. In
  der globalen Neuberechnung rechnet die Vorlage bei AE > TE ebenso.
  **AE = TE:** Die Formel teilt durch null. Der Umfang zeigt „✖ nicht anwendbar
  (Division durch null)“, der Prüfhinweis „✖ TE = AE: Stichprobenumfang nicht
  bestimmbar (Division durch null)“. Im ersten Zeitraum gilt ein gewählter
  begrenzter Stichprobenumfang wie in der Vorlage (Art. 5 Abs. 7).
  In der globalen Neuberechnung bleiben anzuwendender Umfang, Zusatzeinheiten,
  Folgezeiträume und – bei gewähltem globalem Ansatz – Hochrechnung,
  Genauigkeit, Fehlergrenzen und Würdigung offen („—“), auch bei begrenztem
  Umfang: Die Neuberechnung kann ihn nicht bestätigen; als andere Maßnahme
  nennt Art. 5 Abs. 7 UAbs. 4 Buchst. a DelVO die Erhöhung des
  Stichprobenumfangs (Warnhinweis `size-not-applicable-global[-3]`, reist mit
  zu Blatt 18, Bericht und Export). Beispiel Blatt 03 (Golden-Fall „TE ≤ AE“):
  z = 0,842, BV = 30 Mio. €, σ = 0,1, TE = 600.000 €, AE = 750.000 € →
  n = ⌈(0,842 · 30.000.000 · 0,1 / 150.000)²⌉ = ⌈283,58⌉ = 284 (Vorlage „TE ≤ AE“).
- **Nr. 1, Blatt 18, Anhang III bei Ausschluss und Ersetzung.** Der Leitfaden
  passt je Schicht an (7.10.2, 7.10.3): der Zufallsteil mit dem Verhältnis der
  Zufallsschicht, die hochwertige bzw. umfassende Schicht über
  EE_e = EE_e,r · BV_e / BV_e,r (Beispiele 7.10.3.1 b, 7.10.3.2, 7.10.3.4).
  Dafür erfasst Blatt 18 freiwillig in Abschnitt F die Lage der berührten
  Einheiten: Anzahl und Buchwert der umfassenden Schicht (C31, C32) und davon
  berührt (C33, C34). Abgeleitet: A_s = A − A_e (C35), BV_s = BV_u − BV_e (C36),
  BV_s,r = BV_s − (BV_A − BV_A,e) (C37), Faktor BV_s / BV_s,r (C38).
  - Ausschluss mit Lage: EE = EE_e · BV_e/BV_e,r + (EE − EE_e) · BV_s/BV_s,r,
    SE = SE · BV_s/BV_s,r (Leitfaden 7.10.3.2, 7.10.3.4; Hinweis
    `exclusion-by-stratum`). Ohne Lage wie die Vorlage mit dem Gesamtfaktor
    BV/BV_r (mit Abschnitt C nur für den Zufallsteil); gibt es eine umfassende
    Schicht, mit Warnhinweis `exclusion-location-missing` (nicht KOM-konform;
    Beispiel 7.10.3.4: nach KOM 1,44 %, wie die Vorlage ohne Abschnitt C
    1,49 %, mit Abschnitt C 1,50 %).
  - Ersetzung bei Tabelle 2 (DelVO Anhang III Tabelle 2: Genauigkeit für die
    reduzierte Grundgesamtheit, dann mal BV(h) ursprünglich / BV(h) reduziert;
    Leitfaden 7.10.2 mit Fußnote 70): mit Lage
    **SE = SE_Methodenblatt · (N_s − A_s)/N_s · BV_s/BV_s,r** mit
    N_s = N − N_e (Blatt 02 C52 − C31) – die Genauigkeit der Zufallsstichprobe
    ist proportional zur Zahl der Einheiten; ohne Lage die Gesamt-Näherung
    SE · (N − A)/N · BV/BV_r, exakt nur ohne umfassende Schicht (Hinweis
    `replacement-precision-reduced`), sonst nicht KOM-konform (Warnhinweis
    `replacement-location-missing`). Hochrechnung bei Ersetzung: Zufallsteil
    unverändert, umfassende Schicht mit Lage über EE_e (Beispiel 7.10.3.1 b).
  - Ob es eine umfassende Schicht gibt, bestimmt Blatt 18 aus n_e bzw. N_e und
    BV_e des Methodenblatts (> 0), nicht aus EE_e: Die Methodenblätter liefern
    EE_e auch ohne Schicht als 0 (Fassung 0.1.10).
  - Plausibilität von Abschnitt F (Prüfzelle C39): A_e ≤ A (Blatt 02 C47),
    BV_A,e ≤ BV_A (C16), A_e ≤ N_e, BV_A,e ≤ BV_e, BV_e ≤ BV_u (C14). Bei einem
    Verstoß „✖ Eingabe unplausibel“, Hinweis `location-implausible` mit den
    verletzten Bedingungen; angepasster Fehler und Genauigkeit bleiben „—“,
    es wird weder nach Lage noch wie die Vorlage weitergerechnet.
  - Alle Einheiten der umfassenden Schicht berührt (BV_e = BV_A,e): BV_e,r = 0,
    EE_e = EE_e,r · BV_e/BV_e,r ist nicht bestimmbar. Der angepasste Fehler
    bleibt „—“, Hinweis `exhaustive-all-affected` nach Leitfaden 7.10.3.1 b
    (berührte Einheiten der hochwertigen Schicht werden durch Einheiten der
    Zufallsschicht ersetzt).
    Die Vorlage übernimmt SE unverändert (`LEFT($C$11;10)="Tabelle 2"` trifft
    nie zu).
  - Ersetzung bei Tabelle 1 (MUS): ohne Anpassung, wie Vorlage und Leitfaden
    (7.10.3.1 a).
  - Mehrere Schichten oder Zeiträume (04–07, 09–12, 14, 16): Abschnitt F nimmt
    die Lage nur für die umfassende Schicht auf; je Zufallsschicht bzw. Zeitraum
    rechnet Blatt 18 mit einem Verhältnis über die ganze Zufallsschicht. Das ist
    eine anteilige Näherung; Warnhinweis `annex-iii-approximation` an den
    Blättern 04–07 und 09–12 sowie in Blatt 18.
  - Belegrechnungen der Leitfadenbeispiele in `test/kom-annex.spec.ts`:
    7.10.3.1 a (EE 52.294.628 € = 1,25 %), 7.10.3.1 b (EE_e = 420 ·
    1.987.446.254 / 1.697.136.654 = 492, EE = 50.020.779 € = 1,19 %), 7.10.3.2
    (42.459.164 → 42.609.012 €, EE = 50.225.817 € = 1,20 %, SE 52.829.067 →
    53.015.513 €), 7.10.3.4 (EE_e = 680.068,95 €, Zufallsschicht 32.426.844,02 →
    32.461.940,01 €, EE = 33.142.008,96 € = 1,44 %, SE-Faktor 1,0011).
    Beispiel 7.10.3.3 (konservatives MUS) hat in der Vorlage kein Verfahren.

| Nr. | Abweichung | Blätter | Hinweis | Fundstelle |
|---|---|---|---|---|
| 1 | Anhang III je Schicht – **nach KOM gerechnet** | 18 | `exclusion-by-stratum`, `exclusion-location-missing`, `replacement-precision-not-scaled`, `replacement-precision-reduced`, `replacement-location-missing`, `location-implausible`, `exhaustive-all-affected` | Anhang III Tabellen 1 und 2; Leitfaden 7.10.2, 7.10.3 |
| 2 | Umfang bei AE > TE mit \|TE − AE\|, bei AE = TE nicht anwendbar – **nach KOM gerechnet** | 03–12 | `anticipated-above-tolerable[-global[-3]\|-standard[-3]]`, `anticipated-at-least-4[…]` (neutral), `size-not-applicable-global[-3]` | Anhang II; Leitfaden 7.1, S. 183; Art. 5 Abs. 7 UAbs. 4 Buchst. a |
| 3 | nicht anwendbare Standardneuberechnung (Nenner ≤ 0): Umfang aus den Untergrenzen | 05, 06, 07, 10, 11, 12 | bestehender Hinweis `negative-denominator…` mit Zusatz „Standardansatz nicht anwendbar … Untergrenze“ | Anhang II, Anmerkungen zu Nr. 1.2 und 2.2 |
| 4 | anteilige Näherung bei mehreren Schichten oder Zeiträumen | 04–07, 09–12; 18 bei 04–07, 09–12, 14, 16 | `annex-iii-approximation` | Anhang III, „BV(h)“; Leitfaden 7.10.2 |
| 5 | Umfangsparameter bei Ausschluss aus der reduzierten Grundgesamtheit (Auslegungsfrage) | 08–12 (nur einfache Zufallsstichprobe; bei MUS kürzt sich BV heraus) | `exclusion-reference-population`, wenn in Blatt 02 der Ausschluss gewählt und eine Einheit betroffen ist | Anhang III Tabellen 1 und 2 |

**Nachweis im Golden-Abgleich:** Die Zellen, an denen die Webfassung nach den
Vorgaben der KOM rechnet, führt `docs/abgleich.md` als eigene Spalte „bewusst
nach KOM“. Die Sollwerte rechnet `scripts/delvo_soll.py` unabhängig vom
Rechenkern nach (`test/golden-delvo/`, Prüfung `--check` in `npm test`): für
Nr. 2 im ersten Zeitraum den Prüfhinweis und alle Zellen, die sich ändern, aus
einer Neuberechnung der Vorlage in LibreOffice, in die `scripts/kom_lo.py` den
in Python nachgerechneten Umfang einsetzt (gegen dieselbe Neuberechnung ohne
Eingriff verglichen, `test/golden-delvo/lo/`); bei AE = TE den Text; in der
globalen Neuberechnung bei AE = TE den Text, jede weitere abweichende Zelle
muss leer sein; für Nr. 1 SE, obere Fehlergrenze und Würdigung (Blatt 18) bzw.
G34 und G35 (Bericht) mit der Gesamt-Näherung (die Golden-Fälle erfassen keine
Lage). Alle übrigen Zellen bleiben beim Abgleich mit Excel.

**Auslegungen, die die Vorlage nicht kennzeichnet**, kennzeichnet die
Webfassung wie die übrigen Auslegungen am Feld („Auslegung der Vorlage – …“,
neutral; `src/sheets/shared/interpretations.ts`):

| Auslegung | Felder |
|---|---|
| Aufrunden aller Stichprobenumfänge | rechnerischer Umfang: 03 C21, 04 C27, 05 C27, 06 C29, 07 C29, 08 C26, 09 C31, 10 C33, 11 C34, 12 C36 |
| Vergleich der oberen Fehlergrenze mit der Schwelle in der Würdigung | 03 C52, 04 C63, 05 C95, 06 C99, 07 C138, 08 C53, 09 C62, 10 C94, 11 C102, 12 C138, 18 C30 |
| n schließt beim MUS-Standardansatz die hochwertigen Einheiten ein (n_s = n − n_e) | 03 C32, 04 D40, 05 C40, 06 D44, 07 C43 |
| Anrechnung der umfassenden Schicht auf den Mindestumfang 30 (einfache Zufallsstichprobe) | 08 C32, 09 C37, 10 C39/C73, 11 C40, 12 C42/C118 |
| Aufteilung von Zeitraum 2 auf die Schichten (N_h2 / N_2) | 11 D77 (zusätzlich zur Erhöhung) |
| proportionale Aufteilung beim nichtstatistischen Verfahren | 14 D18, 16 D15 |
| „mindestens 3 Einheiten“ beim nichtstatistischen PPS-Verfahren (strenger als die DelVO) | 15 C18 |

Die Erhöhung je Schicht in 06 und 11 kennzeichnete die Webfassung schon vorher.
Die allgemeinen Auslegungen (Aufrunden, Würdigung, n_s, Anrechnung auf 30,
Aufteilung in 14/16, „mindestens 3“ in 15) beschreiben eine Rechenregel des
Verfahrens, keine Einschränkung des einzelnen Ergebnisses: Sie stehen am Feld
des Blatts und reisen nicht in Blatt 18, den Bericht und den Export mit
(`Limitation.local`); so bleibt der Bericht auf einer A4-Seite. Die übrigen
Auslegungen (Erhöhung, Aufteilung von Zeitraum 2 in 11, Skalierung in Blatt 18)
reisen wie bisher mit.

**Redaktionsversehen der deutschen Fassung von Anhang II** (am gerenderten
Amtsblatt beobachtet; die Vorlage folgt jeweils der sachlich gemeinten Formel,
soweit sie das Verfahren abbildet; ob die englische Fassung dieselben Versehen
hat, ist nicht geprüft):

- Nr. 1.1 rechts und 1.2/1.3 rechts: Laufindex „i = 1“ statt „h = 1“; Gewicht
  BV_ht/BV ohne Zeitraumindex.
- Nr. 1.3 rechts, EE_s dritter Summand: obere Grenze „n_h1s“ statt „n_h3s“
  (nicht in der Vorlage abgebildet).
- Nr. 2.2 rechts, EE_s: überzählige „1“ am Ende.
- Nr. 2.3 rechts: EE_s dritter Summand „N_h3 · Σ E_i / n_h3“
  (Mittelwertschätzung statt Verhältnisschätzung); „σ_ew3 = Σ (N_h3 · σ²_eh3)“
  ohne Quadrat und ohne Gewicht; EE_e dritter Summand „H2“ statt „H3“ (nicht in
  der Vorlage abgebildet).
- Nr. 2.2/2.3 rechts: σ²_ew mit Gewicht N_ht/N, im zweiten Zeitraum ohne
  Teilung durch N.

Nicht abgebildet ist das geschichtete Verfahren mit drei Zeiträumen (Anhang II
Nr. 1.3 und 2.3, jeweils rechts); die Vorlage sagt das selbst (Blatt 00, B51).
