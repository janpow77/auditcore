/**
 * Rechenkern Blatt 20_Druck_KOM: Druckfassung für die Kommission. Die Kennzahlen
 * stammen aus Blatt 02, aus der Ergebnisübersicht des aktiven Verfahrens
 * (in der Vorlage `INDIRECT` über `18_GFQ_AnhIII!C4`) und aus Blatt 18; eigene
 * Rechnung sind nur die Tabelle der Fehlerfälle und die Restfehlerquote nach der
 * Logik der Kommissionsvorlage (F = A − E, G = D × F, I = F − H, J = G − H,
 * K = J / I). Jede Zuweisung bildet die Formel der gleichnamigen Zelle nach.
 */
import { count, divide, eq, gt, guard, isBlank, isNumber, left, minus, n, required, sum } from '../../excel/index'
import { unfounded } from '../../model/policy'
import { resolveInputs } from '../../model/sheet'
import type { CellMap, CellValue, Cells, SheetContext } from '../../model/types'
import { CASE_ROWS, definition } from './definition'

const POPULATION_SHEET = '02_Grundgesamtheit'
const TOTAL_ERROR_RATE_SHEET = '18_GFQ_AnhIII'

/** Feste Werte der Formel in G43: „Wesentlichkeitsschwelle von 2 %“ und der Teiler 0,98. */
const MATERIALITY = 0.02
const REMAINDER = 0.98

/** Text der Vorlage, wenn Blatt 18 keine Zahl liefert (nichtstatistische Verfahren). */
export const NOT_CALCULATED = 'nicht berechnet'

/** Längste Zeichenkette einer Zelle; `left` liefert damit den Text, wie ihn `&` verkettet. */
const WHOLE = 32767
const text = (value: CellValue | undefined): string => left(value, WHOLE)

/** Wert einer Zelle eines anderen Blatts bei einem unmittelbaren Bezug (`=Blatt!Zelle`). */
const linked = (sheet: CellMap, cell: string): CellValue => sheet[cell] ?? null

/** Eigene Eingabe, wie sie die Druckseite zeigt: `=IF($J$6="";"";$J$6)`. */
const shown = (value: CellValue | undefined): CellValue => (isBlank(value) ? null : value)

/** Kopf der Seite: Programm, CCI, Geschäftsjahr und Status (A6), Stand (G6). */
function head(c: Cells, population: CellMap): void {
  // Der Programmname steht fest in der Formel der Vorlage; die Vorlage ist auf dieses Programm festgelegt.
  c.A6 = `EFRE-Programm Hessen 2021–2027 · CCI ${left(population.C9, 15)} · Geschäftsjahr ${text(population.C12)}${isBlank(c.J5) ? '' : ` · ${text(c.J5)}`}`
  c.G6 = shown(c.J4)
}

/** Abschnitt 1: Grundgesamtheit aus Blatt 02 (F11–G13). */
function population(c: Cells, sheet02: CellMap): void {
  c.F11 = guard(() => required(sheet02.C23) * 1)
  c.G11 = guard(() => required(sheet02.C16) * 1)
  c.F12 = linked(sheet02, 'C52')
  c.G12 = linked(sheet02, 'C51')
  c.F13 = linked(sheet02, 'C55')
  c.G13 = linked(sheet02, 'C56')
}

/** Abschnitt 1: Stichprobe aus dem aktiven Verfahren (F14–D15). */
function sample(c: Cells, context: SheetContext): void {
  // In Blatt 18 steht in C4 das übernommene Verfahren; ohne Übernahme (kein Verfahren, Altvorlage) bleibt es leer.
  const adopted = isBlank(context.sheets[TOTAL_ERROR_RATE_SHEET]?.C4) ? undefined : context.method
  c.F14 = guard(() => required(adopted?.sampleSize) * 1)
  c.G14 = shown(c.J6)
  c.D15 = adopted?.method ?? null
}

/** `SUMIF(G20:G27;"vorläufig*";D20:D27)`: Fälle, deren Stand mit „vorläufig“ beginnt (ohne Beachtung der Groß- und Kleinschreibung). */
function preliminarySum(c: Cells): number {
  const preliminary = (value: CellValue | undefined): boolean => typeof value === 'string' && value.toLowerCase().startsWith('vorläufig')
  return sum(CASE_ROWS.filter((row) => preliminary(c[`G${row}`])).map((row) => c[`D${row}`]))
}

/** Abschnitt 2: Fehlerquote je Fall und Summen der Tabelle der Fehlerfälle (E20–G28). */
function cases(c: Cells): void {
  for (const row of CASE_ROWS) {
    const bookValue = c[`C${row}`]
    const error = c[`D${row}`]
    // =IF(OR(C20="";D20="");"";D20/C20) – ohne IFERROR: Bei Buchwert 0 zeigt die Vorlage #DIV/0!, die Webfassung keinen Wert.
    c[`E${row}`] = isBlank(bookValue) || isBlank(error) ? null : guard(() => divide(required(error), required(bookValue)))
  }
  const bookValues = CASE_ROWS.map((row) => c[`C${row}`])
  const errors = CASE_ROWS.map((row) => c[`D${row}`])
  c.C28 = eq(count(bookValues), 0) ? null : sum(bookValues)
  c.D28 = eq(count(errors), 0) ? null : sum(errors)
  c.F28 = 'davon vorläufig: '
  c.G28 = eq(count(errors), 0) ? null : preliminarySum(c)
}

/** „nicht berechnet“, wenn Blatt 18 dort einen Text trägt; ist die Zelle dort nur offen, hätte der Text keine Grundlage. */
function numberOrNote(value: CellValue | undefined, context: SheetContext): CellValue {
  if (isNumber(value)) return value
  return isBlank(value) ? unfounded(context, NOT_CALCULATED) : NOT_CALCULATED
}

/** A37: Satz zur Würdigung gegen die Wesentlichkeitsschwelle aus Blatt 18. */
function statement(rate: CellValue | undefined, threshold: CellValue | undefined): CellValue {
  if (!isNumber(rate) || !isNumber(threshold)) return null
  return gt(rate, threshold) ? 'Die Gesamtfehlerquote liegt über der Wesentlichkeitsschwelle.' : 'Die Gesamtfehlerquote liegt unter der Wesentlichkeitsschwelle.'
}

/** Abschnitt 3: Kennzahlen aus Blatt 18 (G32–A37). */
function projection(c: Cells, context: SheetContext): void {
  const sheet18 = context.sheets[TOTAL_ERROR_RATE_SHEET] ?? {}
  c.G32 = linked(sheet18, 'C26')
  c.G33 = linked(sheet18, 'C24')
  c.G34 = numberOrNote(sheet18.C25, context)
  c.G35 = numberOrNote(sheet18.C28, context)
  c.G36 = linked(sheet18, 'C27')
  c.A37 = statement(sheet18.C26, sheet18.C29)
}

/** Abschnitt 4: Restfehlerquote nach Finanzkorrekturen und hochgerechnete Finanzkorrektur (G40–G43). */
function residual(c: Cells, context: SheetContext): void {
  const sheet18 = context.sheets[TOTAL_ERROR_RATE_SHEET] ?? {}
  c.G40 = shown(c.J7)
  c.G41 = shown(c.J8)
  // J = D × F − H und I = F − H mit F = A − E (A: Hochrechnungsbasis ohne TH, D: Gesamtfehlerquote).
  const remainingError = (): number => minus(required(sheet18.C26) * minus(required(sheet18.C14), n(c.J7)), n(c.J8))
  const remainingBase = (): number => minus(minus(required(sheet18.C14), n(c.J7)), n(c.J8))
  c.G42 = guard(() => divide(remainingError(), remainingBase()))
  const correction = guard(() => minus(remainingError(), MATERIALITY * remainingBase()) / REMAINDER)
  if (isNumber(c.G42)) c.G43 = gt(c.G42, MATERIALITY) ? correction : 0
  // Ohne Restfehlerquote (Text "") wertet die Vorlage `"">0,02` als wahr und zeigt die Korrektur trotzdem; sie hat dann keine Grundlage.
  else c.G43 = correction === null ? null : unfounded(context, correction)
}

/** Berechnet alle Formelzellen des Blatts 20; Eingaben und Ergebnisse tragen die Zelladressen der Vorlage. */
export function compute(inputs: CellMap, context: SheetContext): CellMap {
  const c = resolveInputs(definition, inputs, context)
  const sheet02 = context.sheets[POPULATION_SHEET] ?? {}
  head(c, sheet02)
  population(c, sheet02)
  sample(c, context)
  cases(c)
  projection(c, context)
  residual(c, context)
  return c
}
