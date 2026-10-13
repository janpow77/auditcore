/**
 * Formeln und Hilfen, die die Blätter mit mehreren Stichprobenzeiträumen teilen
 * (MUS 05–07 und einfache Zufallsstichprobe 10–12): Ansatz der Neuberechnung,
 * gewichtete Standardabweichung, globale Neuberechnung, Aufteilung des Umfangs,
 * anzuwendender Umfang eines neu berechneten Zeitraums. Die Größen (Buchwerte
 * bei MUS, Anzahl der Einheiten bei der Zufallsstichprobe) kommen als Argumente.
 *
 * Dazu `computeTwice`: Die Blätter verzweigen an Stellen, an denen die Vorlage
 * einen leeren Zwischenwert übergeht (`MAX` über einen Bezug, `ISNUMBER`, `SUM`).
 * Dort muss der Rechenkern wissen, ob ein Zwischenwert leer ist, weil auch die
 * Vorlage keinen zeigt, oder weil eine Angabe fehlt.
 */
import { divide, guard, isBlank, isNumber, left, minus, required, roundUp, sameText, squareRoot } from '../../excel/index'
import type { CellAddress, CellValue, Cells } from '../../model/types'

type Value = CellValue | undefined

/** Erläuterung zum Hinweis „Auslegung der Vorlage“ an den Zellen der Erhöhung bei begrenztem Umfang (Blatt 00 der Vorlage, Zeile 52). */
export const INCREASE_INTERPRETATION =
  'Die DelVO legt die Rechenweise der Erhöhung nach Art. 5 Abs. 7 UAbs. 4 Buchst. a nicht fest; die Vorlage rechnet mit einer proportionalen Erhöhung als Vorschlag.'

/** Text der Vorlage bei nicht positivem Nenner der Standardneuberechnung (Blatt 05 und 10 ergänzen ihn). */
export const NOT_APPLICABLE = '✖ nicht anwendbar (Nenner ≤ 0)'

/** `true`: Die Zelle ist offen, weil eine Angabe fehlt – die Vorlage zeigte dort einen Wert. */
export type Pending = (cell: CellAddress) => boolean

/**
 * Rechnet ein Blatt zweimal. Zuerst wie die Vorlage: Die genannten Eingaben
 * zählen leer als 0. Dann mit den Eingaben, wie sie sind; fehlt dabei ein Wert,
 * den der erste Lauf hat, ist die Zelle offen („Angabe fehlt“) und `pending`
 * meldet das den Formeln, die einen leeren Wert sonst übergingen. Ergebnis ist
 * der zweite Lauf. Ist keine der genannten Eingaben leer, genügt ein Lauf.
 */
export function computeTwice(inputs: Cells, requiredInputs: readonly CellAddress[], evaluate: (c: Cells, pending: Pending) => void): Cells {
  const cells: Cells = { ...inputs }
  const missing = requiredInputs.filter((cell) => isBlank(inputs[cell]))
  if (!missing.length) {
    evaluate(cells, () => false)
    return cells
  }
  const template: Cells = { ...inputs }
  for (const cell of missing) template[cell] = 0
  evaluate(template, () => false)
  evaluate(cells, (cell) => isBlank(cells[cell]) && !isBlank(template[cell]))
  return cells
}

/** Gewählter Ansatz der Neuberechnung (Auswahl aus Blatt 01, verglichen wie in der Vorlage über `LEFT`). */
export type Recalculation = 'standard' | 'global' | 'increase' | 'none'

/** `LEFT(x;8)="Standard"`, `LEFT(x;6)="Global"`, `LEFT(x;8)="Erhöhung"`; alles andere (auch leer) ist „keine Neuberechnung“. */
export function recalculationOf(choice: Value): Recalculation {
  if (sameText(left(choice, 8), 'Standard')) return 'standard'
  if (sameText(left(choice, 6), 'Global')) return 'global'
  return sameText(left(choice, 8), 'Erhöhung') ? 'increase' : 'none'
}

/** Anteil am Umfang: `ROUNDUP(teil/gesamt·umfang;0)`; ein Fehlerwert bricht die umgebende Formel ab. */
export function allocate(part: Value, whole: Value, size: Value): number {
  return roundUp(divide(required(part), required(whole)) * required(size))
}

/** Anteil am Umfang als Zellwert: `IFERROR(ROUNDUP(teil/gesamt·umfang;0);"")`. */
export function share(part: Value, whole: Value, size: Value): CellValue {
  return guard(() => allocate(part, whole, size))
}

/**
 * Gewichtete Standardabweichung `SQRT(Σ g_t/g·σ²_t)`; je Zeitraum das Gewicht
 * (Buchwert bzw. Anzahl der Einheiten) und die Standardabweichung.
 */
export function weightedDeviation(periods: readonly (readonly [weight: Value, deviation: Value])[], whole: Value): CellValue {
  return guard(() => squareRoot(periods.reduce((value, [weight, deviation]) => value + divide(required(weight), required(whole)) * required(deviation) ** 2, 0)))
}

/**
 * Globale Neuberechnung: `ROUNDUP((z·G·σ_w/(TE-AE))^2;0)` mit G = BV bzw. N.
 * Anders als beim ersten Zeitraum prüft die Vorlage hier nicht auf TE ≤ AE.
 */
export function globalComputedSize(z: Value, size: Value, deviation: Value, tolerable: Value, anticipated: Value): CellValue {
  return guard(() => roundUp(divide(required(z) * required(size) * required(deviation), minus(required(tolerable), required(anticipated))) ** 2))
}

/**
 * Anzuwendender Umfang eines neu berechneten Zeitraums:
 * `MAX(gewählter Umfang;3[;Auffüllung auf 30])`. Der gewählte Umfang ist in der
 * Vorlage ein Bezug; steht dort ein Text („✖ nicht anwendbar …“) oder `""`,
 * übergeht `MAX` ihn und es bleiben die Untergrenzen. `open`: Der gewählte
 * Umfang fehlt nur, weil eine Angabe fehlt.
 */
export function appliedPeriodSize(chosen: Value, open: boolean, shortfall?: () => number): CellValue {
  if (open) return null
  return guard(() => Math.max(...(isNumber(chosen) ? [chosen] : []), 3, ...(shortfall ? [shortfall()] : [])))
}
