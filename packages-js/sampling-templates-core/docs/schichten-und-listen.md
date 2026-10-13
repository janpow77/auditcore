# Schichttabellen und Listenblätter

Zwei Bausteine, die mehrere Blätter teilen. Beide liegen im Kern
(`src/model/strata.ts`, `src/model/list.ts`) und in der Vue-Bindung
(`StrataTable`, `UnitList`); Blätter benutzen sie, ändern sie aber nicht.

## Schichttabelle

### Zellen und Schlüssel

Die Vorlage sieht sieben Schichtspalten vor: D–I („Schicht 1–6“) und J
(„Schicht k“). Die Webfassung erlaubt bis zu 20 Schichten:

| Schicht | Spalte | Herkunft |
|---|---|---|
| 1–7 | `D`, `E`, `F`, `G`, `H`, `I`, `J` | Vorlage (`TEMPLATE_STRATA`) |
| 8–20 | `AA` … `AM` | Erweiterung der Webfassung (`EXTRA_STRATA`) |

Die Zelle einer Schicht heißt immer `<Spalte><Zeile>` (`D9`, `AA9`). Die
Spalten AA–AM sind in keinem Blatt der Vorlage belegt (dort enden die Blätter
bei Spalte N), die Schlüssel sind gültige Zelladressen und bleiben im
Arbeitsstand eindeutig. Die Web-Oberfläche nennt Spalte J „Schicht 7“.

**Die 8. bis 20. Schicht ist ein Hinweis der Webfassung, keine Eigenschaft der
Vorlage.** Sie ist dreifach gekennzeichnet: als Text unter der Schichttabelle,
als Hinweis der Webfassung in der Ergebnisspalte (`webHints`, Kennung
`strata-beyond-template`) und als Zeile im Excel-Export. Der Golden-Abgleich
deckt die sieben Spalten der Vorlage ab; für die weiteren gilt dieselbe Formel
je Spalte (`fillRow`), geprüft in `test/strata.spec.ts`.

### Definition

```ts
{ cell: 'D9', alias: 'stratumBookValue', kind: 'input', type: 'amount', columns: STRATA_COLUMNS, total: 'C9', label: 'Buchwert je Schicht (BV_h)' }
```

`cell` ist die Zelle der ersten Schicht, `columns` `STRATA_COLUMNS` (in der
Altvorlage X3 `LEGACY_STRATA`, dort liegen die Schichten in E–K), `total` die
Summenzelle in Spalte C, falls die Vorlage eine hat. Oberfläche, Export und
Import lesen die Schichtspalten eines Blatts aus seiner Definition
(`strataColumnsOf`). Der Generator
erzeugt diese Felder. `cellsOf(field)` liefert alle 20 Zellen, `findField`
findet das Feld auch über eine Schicht- oder Summenzelle.

### Rechenkern

```ts
import { countRow, fillRow, stratumCell as at, sumRow, totalRow } from '../../model/strata'

c.C9 = totalRow(c, 9, context)                       // =SUM(D9:J9), angezeigte Summe
fillRow(c, 39, (column) => (isBlank(c[at(column, 9)]) ? null : guard(() => minus(required(c[at(column, 9)]), n(c[at(column, 38)])))))
c.C53 = eq(countRow(c, 46), 0) ? null : c.C51        // COUNT(D46:J46)
```

- `IF(D9="";"";…)` wird zu „Schicht nicht belegt → `null`“, `IF(D9="";0;…)` zu `0`.
- Summen laufen über alle 20 Spalten; leere Zellen und Texte zählen nicht.
- **Summe ohne Summanden:** Trägt keine Schicht einen Wert, zeigt die Vorlage
  0. `totalRow` gibt dann einen Wert ohne Grundlage zurück, den die Webfassung
  nach der geltenden Richtlinie nicht zeigt ([abweichungen.md](abweichungen.md)
  Nr. 1 und 5); die Zelle steht mit `kind: 'withoutBasis'` in den Abweichungen.
  `sumRow` bleibt für Zwischenrechnungen.
- **Offener Stichprobenumfang:** Fehlt eine Angabe, mit der die Vorlage als 0
  weiterrechnen würde, bleiben auch die Summen der davon abhängigen
  Schichtzeilen offen. Muster in `04_MUS_1Z_S/compute.ts` (`sampleSize` gibt
  `pending` zurück, `total(row)` berücksichtigt es).
- **Mindestens drei Einheiten je Schicht:** `checkStratumUnits(units, open, context)`
  aus `shared/statistical.ts`.
- Prüfhinweise je Schicht (`type: 'check'` mit `columns`) erscheinen in der
  Ergebnisspalte zusammengefasst: ein gemeinsamer Hinweis, wenn alle Schichten
  erfüllt sind, sonst je Schicht mit Befund eine Zeile („Schicht 2: ✖ < 3“).

### Oberfläche

Aufeinanderfolgende Schichtzeilen eines Abschnitts werden zu einer Tabelle
(Zeile = Größe, Spalte = Schicht, davor „Gesamt“) in einem eigenen
waagerechten Rollbereich, der mit der Tastatur erreichbar ist
(`role="region"`, `tabindex="0"`); die Seite selbst rollt nie waagerecht. Jede
Zelle trägt die Beschriftung „<Bezeichnung> – Schicht n“. Hinzufügen und
Entfernen stehen an der ersten Tabelle des Blatts; gezeigt werden mindestens
drei Schichten bzw. so viele, wie belegt sind. Entfernen löscht die Eingaben
der letzten Schicht.

### Arbeitsstand, Export, Import

- **Arbeitsstand:** Schichtzellen stehen wie alle Eingaben unter ihrer
  Zelladresse (`"AA9": 2000000`). Die Zahl der gezeigten Schichten wird nicht
  gespeichert; sie ergibt sich aus den belegten Zellen.
- **Excel-Export:** Schichtzeilen stehen als eine Zeile mit der Summe in der
  Wertspalte und einer Spalte je belegter Schicht („Schicht 1“ …); die Spalte
  „Zelle der Vorlage“ nennt Summenzelle und Bereich (`C9; D9:AA9`). Ab der
  achten Schicht steht der Hinweis der Webfassung im Blatt.
- **Import der ausgefüllten Vorlage:** gelesen werden die Spalten D–J; mehr
  kann die Vorlage nicht enthalten. Ein Arbeitsstand mit mehr als sieben
  Schichten lässt sich nicht in die Vorlage zurückschreiben.

## Listenblatt (Blatt 17)

Die Vorlage sagt zu Blatt 17: „Das Blatt ist je Stichprobeneinheit zu
kopieren.“ Die Webfassung führt stattdessen eine Liste von Einheiten
(`layout: 'list'`): Im Arbeitsstand steht unter `17_Unterstichprobe` eine
Liste, je Einheit ein Satz Zellwerte mit den Zelladressen der Vorlage (höchstens
2.000 Einheiten). Gerechnet wird je Einheit mit demselben Rechenkern;
`computeWorkspace` übergeht Listenblätter.

### Felder der Webfassung (Abschnitt W)

Die Vorlage überlässt die Übernahme des hochgerechneten Fehlers ins
Methodenblatt der Prüfbehörde. Damit die Webfassung summieren kann, braucht
jede Einheit Angaben, die es in der Vorlage nicht gibt. Sie liegen in den
dort unbelegten Zellen W5–W10, tragen `web: true` und sind als „Hinweis der
Webfassung“ gekennzeichnet:

| Zelle | Inhalt |
|---|---|
| `W5` | Schicht der Einheit im Methodenblatt: „Zufallsschicht“ oder „hochwertige Einheit“ |
| `W6` | maßgebliche Variante: „Variante 1“ (gleiche Wahrscheinlichkeit) oder „Variante 2“ (PPS) |
| `W9` | Nummer der Schicht im Methodenblatt (nur geschichtete Verfahren) |
| `W10` | Stichprobenzeitraum im Methodenblatt, 1 bis 3 (nur Verfahren mit mehreren Zeiträumen) |
| `W7`, `W8` | maßgeblicher hochgerechneter Fehler und maßgebliche Fehlerquote (aus C13/C14 bzw. C22/C23) |

### Übernahme ins Methodenblatt

`sheet.totals(rows, context, needs)` summiert über alle Einheiten; ein
Methodenblatt kennzeichnet die Felder, die eine Summe aufnehmen, mit `subsample`:

| Rolle | Summe | in Blatt 03 | in Blatt 04 (je Schicht) |
|---|---|---|---|
| `highValueErrors` | Fehler der Einheiten „hochwertige Einheit“ | C37 (ΣE_e) | Zeile 45 |
| `errorRateSum` | Fehlerquoten der Einheiten „Zufallsschicht“ | C38 (Σ E_i/BV_i) | Zeile 46 |
| `errorSum` | Fehler der Einheiten „Zufallsschicht“ | – (für Verhältnisschätzung) | – |
| `bookValueSum` | Buchwerte der Einheiten „Zufallsschicht“ | – (für Verhältnisschätzung) | – |

Die Schaltfläche „Summen in Blatt nn übernehmen“ schreibt die Summen als
gewöhnliche Eingaben in das gewählte Methodenblatt (`applySubsamples`); danach
besteht keine Verbindung mehr, die Werte bleiben überschreibbar. Einheiten
ohne bestimmbaren Fehler gehen nicht ein und werden gezählt.

**Je Schicht und je Zeitraum.** Trägt das Zielfeld eine Schichtzeile
(`columns`), entstehen die Summen je Schicht aus `W9` und landen in der Spalte
dieser Schicht. Trägt es `period: 2`, gehen nur Einheiten mit `W10 = 2` ein.
`subsampleNeeds(definition)` sagt, wonach ein Methodenblatt unterscheidet;
Einheiten ohne die nötige Angabe werden nicht übernommen und als „nicht
zugeordnet“ gezählt (`totals.unassigned`).

### Einfügen aus Zwischenablage oder CSV

`parsePastedRows(text, definition)`: je Zeile eine Einheit, Trenner Tabulator,
Semikolon oder Komma, Zahlen in deutscher Schreibweise. Ohne Kopfzeile gilt
die Reihenfolge der Eingabezellen der Vorlage (C5, C6, C7, C8, C9, C10, C11,
C12, C15, C17, C18, C19, C21); eine Kopfzeile aus Zelladressen
(`C5;C6;C10;C11;C12;W5`) bestimmt die Spalten. Nicht lesbare Zellen bleiben
leer und werden gezählt.

### Export und Import

Der Export enthält ein Blatt `17_Unterstichprobe` mit einer Zeile je Einheit
und einer Spalte je Feld. Beim Import der ausgefüllten Vorlage ist Blatt 17
eine Einheit; Kopien des Blatts in der Mappe (`17_Unterstichprobe (2)` …)
werden zu weiteren Einheiten.
