/**
 * Begründete Abweichungen des Blatts 14 bei leeren Eingaben, geführt über alle
 * Schichtspalten der Webfassung (D–J und AA–AM). Zwei Fallarten der Richtlinie
 * (`model/policy.ts`):
 *
 * - Wert ohne Grundlage (`kind: 'withoutBasis'`): die Summe 0 über eine
 *   Schichtzeile, in der keine Schicht einen Wert trägt, und alles, was auf
 *   dieser 0 aufbaut (BV, N, Zulässigkeit, Mindesterfassung, Gesamtstichprobe,
 *   Hochrechnung).
 * - Pflichteingabe fehlt (ohne `kind`): Umfang der Zufallsstichprobe, Buchwert
 *   einer belegten Schicht, Wesentlichkeitsschwelle. Eine Zeile mit der ganzen
 *   Schichtzeile 12 unter `whenEmpty` greift, wenn der Buchwert einer belegten
 *   Schicht fehlt.
 */
import { STRATA_COLUMNS, stratumCell } from '../../model/strata'
import type { Deviation } from '../../model/types'

function entries(cells: readonly string[], whenEmpty: readonly string[], template: string, reason: string): Deviation[] {
  return cells.map((cell) => ({ cell, whenEmpty, template, reason }))
}

/** Zellen einer Schichtzeile in allen Schichtspalten. */
const row = (number: number): string[] => STRATA_COLUMNS.map((column) => stratumCell(column, number))

/** Summe einer Schichtzeile, in der keine (belegte) Schicht einen Wert trägt: Die Vorlage zeigt 0. */
function emptyTotal(cell: string, rows: readonly number[]): Deviation {
  return {
    cell,
    whenEmpty: rows.flatMap(row),
    template: '0 (Summe über Schichten ohne Wert)',
    reason: 'Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus.',
    kind: 'withoutBasis',
  }
}

/** Summenzellen mit den Schichtzeilen, deren Werte sie summieren (C27: nur belegte Schichten, Zeile 11). */
const TOTALS: readonly (readonly [cell: string, rows: readonly number[]])[] = [
  ['C11', [11]], ['C12', [12]], ['C18', [18]], ['C24', [24]], ['C25', [25]], ['C27', [11, 27]],
]

/** Zellen, die auf einer Summe ohne Summanden aufbauen: Die Vorlage rechnet mit deren 0 weiter. */
function withoutTotal(cells: readonly string[], totals: readonly string[], template: string): Deviation[] {
  return cells.map((cell) => ({
    cell,
    whenEmpty: totals,
    template,
    reason: 'Der Wert baut auf einer Summe auf, zu der keine Schicht beiträgt; ohne sie ist er nicht bestimmt.',
    kind: 'withoutBasis',
  }))
}

const SIZE = 'Ohne Umfang der Zufallsstichprobe ist die Aufteilung auf die Schichten nicht bestimmt.'
const BOOK_VALUE = 'Fehlt der Buchwert einer belegten Schicht, ist ihr extrapolierter Fehler nicht bestimmt; Summe und Fehlerquoten bleiben offen.'

export const deviations: readonly Deviation[] = [
  ...TOTALS.map(([cell, rows]) => emptyTotal(cell, rows)),
  ...withoutTotal(['C13', 'N4'], ['C12'], 'nur der Buchwert der umfassenden Schicht bzw. 0 € (Summe der Buchwerte ohne belegte Schicht)'),
  ...withoutTotal(['C14'], ['C11'], 'nur die Einheiten der umfassenden Schicht bzw. 0 (Summe der Einheiten ohne belegte Schicht)'),
  ...withoutTotal(['C15'], ['C11'], '„✔ N < 300: zulässig …“ (0 Einheiten liegen unter 300)'),
  ...withoutTotal(['C20'], ['C11'], '10 % der Einheiten der umfassenden Schicht bzw. 0'),
  ...withoutTotal(['C19', 'N10'], ['C18'], 'nur die Einheiten der umfassenden Schicht bzw. 0 (Summe der Schichtumfänge ohne belegte Schicht)'),
  ...withoutTotal(['C21'], ['C19', 'C20'], 'Prüfhinweis auf der Grundlage einer Gesamtstichprobe bzw. einer Mindesterfassung, zu der keine Schicht beiträgt'),
  ...withoutTotal(['C29', 'C32', 'C33', 'C35', 'N5', 'N11'], ['C27'], 'Hochrechnung und Würdigung auf Grundlage eines extrapolierten Fehlers der Zufallsschichten von 0 €, obwohl keine belegte Schicht hochgerechnet werden kann'),
  ...entries(row(18), ['C16'], '1 je belegter Schicht (Mindestwert der Formel bei n = 0)', SIZE),
  ...entries(['C18', 'C19', 'N10'], ['C16'], 'Anzahl der belegten Schichten (je Schicht 1), zuzüglich der umfassenden Schicht', SIZE),
  ...entries(['C21'], ['C16'], 'Prüfhinweis auf der Grundlage von einer Einheit je belegter Schicht', 'Die Prüfung der Mindesterfassung setzt den Umfang der Zufallsstichprobe voraus.'),
  ...STRATA_COLUMNS.flatMap((column) => entries([stratumCell(column, 27)], [stratumCell(column, 12)], '0,00 € (leerer Buchwert der Schicht zählt als 0)', BOOK_VALUE)),
  ...entries(['C27', 'C29', 'N5'], row(12), 'Summe, in die die Schicht ohne Buchwert mit 0 € eingeht', BOOK_VALUE),
  ...entries(['C32', 'C33', 'N11'], row(12), 'Fehlerquote, in die die Schicht ohne Buchwert mit 0 € eingeht, bzw. bezogen nur auf die umfassende Schicht', BOOK_VALUE),
  ...entries(['C35'], ['C34', ...row(12)], 'Würdigung gegen eine Schwelle von 0 % bzw. auf Grundlage der mit 0 € gerechneten Schicht', 'Die Würdigung setzt die Wesentlichkeitsschwelle und den Buchwert jeder belegten Schicht voraus.'),
]
