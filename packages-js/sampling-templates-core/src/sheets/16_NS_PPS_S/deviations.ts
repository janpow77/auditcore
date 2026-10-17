/**
 * Begründete Abweichungen des Blatts 16 bei leeren Eingaben, geführt über alle
 * Schichtspalten der Webfassung (D–J und AA–AM). Zwei Fallarten der Richtlinie
 * (`model/policy.ts`):
 *
 * - Wert ohne Grundlage (`kind: 'withoutBasis'`): die Summe 0 über eine
 *   Schichtzeile, in der keine Schicht einen Wert trägt, und alles, was auf
 *   dieser 0 aufbaut (BV, N, Zulässigkeit, Mindesterfassung, Fehler der
 *   umfassenden Schichten, Hochrechnung). Die Webfassung lässt ihn offen,
 *   solange eine Pflichteingabe fehlt; bei vollständigen Eingaben zeigt sie ihn
 *   wie die Vorlage mit Hinweis.
 * - Pflichteingabe fehlt (ohne `kind`): Stichprobenumfang und
 *   Signifikanzschwelle.
 */
import { STRATA_COLUMNS, stratumCell } from '../../model/strata'
import type { Deviation } from '../../model/types'

function entries(cells: readonly string[], whenEmpty: readonly string[], template: string, reason: string): Deviation[] {
  return cells.map((cell) => ({ cell, whenEmpty, template, reason }))
}

/** Geltende Regel für Werte ohne Grundlage: offen nur, solange eine Pflichteingabe fehlt. */
const WITHOUT_BASIS = 'Die Webfassung lässt ihn offen, solange eine Pflichteingabe fehlt; bei vollständigen Eingaben zeigt sie ihn wie die Vorlage mit Hinweis in Warnfarbe.'

/** Zellen einer Schichtzeile in allen Schichtspalten. */
const row = (number: number): string[] => STRATA_COLUMNS.map((column) => stratumCell(column, number))

/** Summe einer Schichtzeile, in der keine (belegte) Schicht einen Wert trägt: Die Vorlage zeigt 0. */
function emptyTotal(cell: string, rows: readonly number[]): Deviation {
  return {
    cell,
    whenEmpty: rows.flatMap(row),
    template: '0 (Summe über Schichten ohne Wert)',
    reason: `Trägt keine Schicht einen Wert, gibt es nichts zu summieren; eine Summe von 0 sähe wie ein Ergebnis aus. ${WITHOUT_BASIS}`,
    kind: 'withoutBasis',
  }
}

/* Hochwertige Einheiten und Iteration sind freiwillig (Entscheidung des Inhabers vom 17.10.2026): Ihre Summe ist wie in der Vorlage 0, keine Abweichung. */
/** Summenzellen mit den Schichtzeilen, deren Werte sie summieren (C28: nur belegte Schichten, Zeile 9). */
const TOTALS: readonly (readonly [cell: string, rows: readonly number[]])[] = [
  ['C9', [9]], ['C10', [10]], ['C15', [15]], ['C21', [21]], ['C22', [22]], ['C26', [26]], ['C28', [9, 28]],
]

/** Zellen, die auf einer Summe ohne Summanden aufbauen: Die Vorlage rechnet mit deren 0 weiter. */
function withoutTotal(cells: readonly string[], totals: readonly string[], template: string): Deviation[] {
  return cells.map((cell) => ({
    cell,
    whenEmpty: totals,
    template,
    reason: `Der Wert baut auf einer Summe auf, zu der keine Schicht beiträgt; ohne sie ist er nicht bestimmt. ${WITHOUT_BASIS}`,
    kind: 'withoutBasis',
  }))
}

const SIZE = 'Ohne Stichprobenumfang sind die Aufteilung auf die Schichten, die Zufallsschichten und die Auswahlintervalle nicht bestimmt; alle Folgegrößen bleiben offen.'
const SIZE_TEMPLATE = 'Wert auf Grundlage von einer Einheit je belegter Schicht (Mindestwert der Formel bei n = 0)'

export const deviations: readonly Deviation[] = [
  ...TOTALS.map(([cell, rows]) => emptyTotal(cell, rows)),
  ...withoutTotal(['N4'], ['C9'], '0 € (Summe der Buchwerte ohne belegte Schicht)'),
  ...withoutTotal(['C11'], ['C10'], '0 (Summe der Einheiten ohne Angabe in einer Schicht)'),
  ...withoutTotal(['C12'], ['C10'], '„✔ N < 300: zulässig …“ (0 Einheiten liegen unter 300)'),
  ...withoutTotal(['C16'], ['C10'], '0 (10 % von 0 Einheiten)'),
  ...withoutTotal(['C17'], ['C15', 'C16'], 'Prüfhinweis auf der Grundlage einer Summe der Schichtumfänge bzw. einer Mindesterfassung, zu der keine Schicht beiträgt'),
  ...withoutTotal(['N10'], ['C15'], '0 (Summe der Schichtumfänge ohne belegte Schicht)'),
  ...withoutTotal(['C30', 'C33', 'C34', 'C36', 'N5', 'N11'], ['C28'], 'Hochrechnung und Würdigung auf Grundlage eines extrapolierten Fehlers von 0 €, obwohl keine belegte Schicht hochgerechnet werden kann'),
  ...entries([...row(15), ...row(18), ...row(22), ...row(23), ...row(28), 'C15', 'C22', 'C28', 'C30', 'C33', 'C34', 'N5', 'N10', 'N11'], ['C13'], SIZE_TEMPLATE, SIZE),
  ...entries(['C17'], ['C13'], 'Prüfhinweis auf der Grundlage von einer Einheit je belegter Schicht', 'Die Prüfung der Mindesterfassung setzt den Stichprobenumfang voraus.'),
  ...entries(['C36'], ['C13', 'C35'], 'Würdigung gegen eine Schwelle von 0 % bzw. auf Grundlage von einer Einheit je belegter Schicht', 'Die Würdigung setzt die Signifikanzschwelle und den Stichprobenumfang voraus.'),
]
