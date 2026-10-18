/**
 * Formeln und Hilfen, die die Blätter mit mehreren Stichprobenzeiträumen teilen
 * (MUS 05–07 und einfache Zufallsstichprobe 10–12): Ansatz der Neuberechnung,
 * gewichtete Standardabweichung, globale Neuberechnung, Aufteilung des Umfangs,
 * anzuwendender Umfang eines neu berechneten Zeitraums. Die Größen (Buchwerte
 * bei MUS, Anzahl der Einheiten bei der Zufallsstichprobe) kommen als Argumente.
 *
 * Dazu `computeBesideTemplate`: Die Blätter verzweigen an Stellen, an denen die Vorlage
 * einen leeren Zwischenwert übergeht (`MAX` über einen Bezug, `ISNUMBER`, `SUM`).
 * Dort muss der Rechenkern wissen, ob ein Zwischenwert leer ist, weil auch die
 * Vorlage keinen zeigt, oder weil eine Angabe fehlt.
 */
import { divide, eq, gt, guard, isBlank, isNumber, left, minus, ne, required, roundUp, sameText, squareRoot } from '../../excel/index'
import { cellsOf, fieldsOf, type MethodDefinition } from '../../model/definition'
import { TEMPLATE_POLICY } from '../../model/policy'
import type { CellAddress, CellValue, Cells, SheetContext } from '../../model/types'

type Value = CellValue | undefined

/** Erläuterung zum Hinweis „Auslegung der Vorlage“ an den Zellen der Erhöhung bei begrenztem Umfang (Blatt 00 der Vorlage, Zeile 52). */
export const INCREASE_INTERPRETATION =
  'Die DelVO legt die Rechenweise der Erhöhung nach Art. 5 Abs. 7 UAbs. 4 Buchst. a nicht fest; die Vorlage rechnet mit einer proportionalen Erhöhung als Vorschlag.'

/** Text der Vorlage bei nicht positivem Nenner der Standardneuberechnung (Blatt 05 und 10 ergänzen ihn). */
export const NOT_APPLICABLE = '✖ nicht anwendbar (Nenner ≤ 0)'

/** `true`: Die Zelle ist offen, weil eine Angabe fehlt – die Vorlage zeigte dort einen Wert. */
export type Pending = ((cell: CellAddress) => boolean) & {
  /** Wert der Zelle im Lauf „wie die Vorlage“ (leere Pflichteingaben als 0); nur im Lauf des Aufrufs gesetzt. */
  readonly likeTemplate?: (cell: CellAddress) => CellValue
}

/**
 * Rechnet ein Blatt mit dem Kontext des Aufrufs und, sobald eine Formel danach
 * fragt, ein zweites Mal vollständig wie die Vorlage: Die genannten
 * Pflichteingaben zählen leer als 0, und Werte ohne Grundlage (`unfounded`,
 * `totalRow`) erscheinen so, wie die Vorlage sie zeigt (`TEMPLATE_POLICY`).
 * Fehlt im Lauf des Aufrufs ein Wert, den der Lauf „wie die Vorlage“ hat, ist
 * die Zelle offen – gleich, ob eine Angabe fehlt oder der Wert keine Grundlage
 * hat – und `pending` meldet das den Formeln, die einen leeren Bezug sonst
 * übergingen (`MAX`, `ISNUMBER`, `SUM`). Sie bleiben dann offen, statt einen
 * anderen Wert zu zeigen als die Vorlage. Bei vollständiger Belegung fragt keine
 * Formel nach einer leeren Zelle; dann bleibt es bei einem Lauf.
 */
export function computeBesideTemplate(inputs: Cells, requiredInputs: readonly CellAddress[], context: SheetContext, evaluate: (c: Cells, pending: Pending, context: SheetContext) => void): Cells {
  let template: Cells | undefined
  const likeTemplate = (): Cells => {
    if (!template) {
      template = { ...inputs }
      for (const cell of requiredInputs) if (isBlank(inputs[cell])) template[cell] = 0
      evaluate(template, () => false, { ...context, policy: TEMPLATE_POLICY })
    }
    return template
  }
  const cells: Cells = { ...inputs }
  const pending: Pending = Object.assign((cell: CellAddress) => isBlank(cells[cell]) && !isBlank(likeTemplate()[cell]), { likeTemplate: (cell: CellAddress) => likeTemplate()[cell] ?? null })
  evaluate(cells, pending, context)
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
 * Stichprobenumfang bei AE = TE: Die Formel des Anhangs II DelVO (EU) 2023/67
 * teilt durch TE − AE und ist dann nicht anwendbar (Division durch null). Bei
 * AE > TE rechnet die Webfassung nach KOM-Leitfaden EGESIF_16-0014-01 (7.1,
 * S. 183, Fußnote 59) mit der geplanten Genauigkeit |TE − AE| – die quadrierte
 * Formel liefert das ohne Änderung (`docs/abweichungen.md` Nr. 16).
 */
export const SIZE_NOT_APPLICABLE = '✖ nicht anwendbar (Division durch null)'

/** Englische Arbeitsübersetzung von `SIZE_NOT_APPLICABLE`. */
export const SIZE_NOT_APPLICABLE_EN = '✖ not applicable (division by zero)'

/**
 * Globale Neuberechnung: Bei AE = TE (und AE ≠ 0) `SIZE_NOT_APPLICABLE`; sonst
 * die Formel `formula` wie in der Vorlage – bei AE > TE mit |TE − AE| nach
 * KOM-Leitfaden. Bei TE = AE = 0 (leere Eingaben, die die Vorlage als 0 liest)
 * ist schon die Formel ein Fehlerwert wie in der Vorlage.
 */
export function globalSize(tolerable: Value, anticipated: Value, formula: () => number): CellValue {
  if (isNumber(tolerable) && isNumber(anticipated) && ne(anticipated, 0) && eq(tolerable, anticipated)) return SIZE_NOT_APPLICABLE
  return guard(formula)
}

/** Globale Neuberechnung: `ROUNDUP((z·G·σ_w/(TE-AE))^2;0)` mit G = BV bzw. N; bei AE = TE nicht anwendbar (`globalSize`). */
export function globalComputedSize(z: Value, size: Value, deviation: Value, tolerable: Value, anticipated: Value): CellValue {
  return globalSize(tolerable, anticipated, () => roundUp(divide(required(z) * required(size) * required(deviation), minus(required(tolerable), required(anticipated))) ** 2))
}

/**
 * Der globale Ansatz liefert keinen Umfang, weil die Formel bei AE = TE nicht
 * anwendbar ist: Der anzuwendende Gesamtumfang und die Umfänge der
 * Folgezeiträume bleiben offen („—“), statt auf den begrenzten Umfang oder die
 * Untergrenzen zu fallen (Erhöhung nach Art. 5 Abs. 7 UAbs. 4 Buchst. a prüfen).
 */
export function globalBlocked(computed: Value): boolean {
  return computed === SIZE_NOT_APPLICABLE
}

/** Folgegrößen der Ergebnisübersicht, die vom Stichprobenumfang abhängen (EE, SE, Umfang, Gesamtfehlerquote). */
const SIZE_DEPENDENT_SUMMARY: readonly CellAddress[] = ['N5', 'N7', 'N10', 'N11']

/**
 * Geschichtete Blätter (06, 11): Ist der gewählte globale Ansatz bei AE = TE
 * nicht anwendbar (Division durch null), sind alle Formelzellen nach der globalen Neuberechnung
 * (`row`) Folgegrößen ohne bestimmbaren Umfang: Sie bleiben offen („—“), auch
 * Summen über Schichten, die sonst wie in der Vorlage 0 zeigten.
 */
export function clearAfterGlobal(c: Cells, definition: MethodDefinition, row: number): void {
  for (const field of fieldsOf(definition)) {
    if (field.kind === 'input') continue
    for (const cell of [...cellsOf(field), ...(field.total ? [field.total] : [])]) if (gt(Number(cell.replace(/^[A-Z]+/, '')), row)) c[cell] = null
  }
  for (const cell of SIZE_DEPENDENT_SUMMARY) c[cell] = null
}

/**
 * Ist der gewählte globale Ansatz bei AE = TE nicht anwendbar – oder offen,
 * weil eine Angabe fehlt –, gibt es keine Würdigung: Sie bliebe sonst wie in der
 * Vorlage gegen leere Zellen stehen („⚠“ oder „✔“ ohne Grundlage).
 */
export function withoutGlobalAssessment(c: Cells, approach: string, sizes: readonly CellAddress[], pending: Pending, assessment: CellAddress): void {
  if (approach === 'global' && sizes.some((size) => blockedGlobal(c, size, pending))) c[assessment] = null
}

/**
 * Globale Neuberechnung in `cell` bei AE = TE nicht anwendbar (Division durch
 * null) – auch dann, wenn sie nur offen ist, weil eine Pflichteingabe fehlt, und
 * mit dieser als 0 (wie die Vorlage) nicht anwendbar wäre (TE = AE ≠ 0).
 */
export function blockedGlobal(c: Cells, cell: CellAddress, pending: Pending): boolean {
  return globalBlocked(c[cell]) || (pending(cell) && pending.likeTemplate?.(cell) === SIZE_NOT_APPLICABLE)
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
