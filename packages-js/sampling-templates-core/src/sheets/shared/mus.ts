/**
 * Formeln, die die MUS-Blätter mit mehreren Stichprobenzeiträumen teilen
 * (05, 06, 07; Anhang II Nr. 1.2 und 1.3 DelVO (EU) 2023/67): Aufteilung des
 * Umfangs auf die Zeiträume, Standard- und globale Neuberechnung, Erhöhung bei
 * begrenztem Umfang, Auswahl je Zeitraum, Fehlergrenzen und Ergebnisübersicht.
 * Die Blätter rufen sie mit ihren Zellen auf; Texte der Vorlage stehen einmal hier.
 *
 * Was auch die Blätter 10–12 teilen (Ansatz der Neuberechnung, globale
 * Neuberechnung), liegt in `periods.ts` und wird hier weitergereicht.
 */
import { divide, ge, guard, ifError, isBlank, isNumber, le, minus, n, required, roundUp } from '../../excel/index'
import { unfounded } from '../../model/policy'
import type { ZeroAssumption } from '../../model/sheet'
import type { FieldTexts } from '../../model/texts'
import type { CellAddress, CellMap, CellValue, Cells, SheetContext, WebHint } from '../../model/types'
import { NOT_APPLICABLE, appliedPeriodSize as periodSize } from './periods'
import { appliedSampleSize, assessment, checkIteration, checkMinimumUnits, lowerErrorLimit } from './statistical'

type Value = CellValue | undefined

export { INCREASE_INTERPRETATION, NOT_APPLICABLE, computeBesideTemplate as computeTwice, globalComputedSize, share, weightedDeviation, type Pending } from './periods'
export { recalculationOf as approachOf, type Recalculation as Approach } from './periods'

/** Laufende Nummer je Objekt (Parameter, Richtlinie) als Teil des Schlüssels in `remembered`; die Objekte selbst werden nicht gelesen. */
const identities = new WeakMap<object, number>()
let identityCount = 0

function identityOf(value: object | undefined): number {
  if (!value) return 0
  const known = identities.get(value)
  if (known) return known
  identityCount += 1
  identities.set(value, identityCount)
  return identityCount
}

/**
 * Merkt sich die zuletzt gerechneten Belegungen eines Blatts. Die Auswertung
 * (`evaluateSheet`) rechnet ein Blatt je Anzeige mehrfach und für jede Gruppe
 * leerer Pflichteingaben noch einmal mit 0 – bei Schichtblättern mit mehreren
 * Zeiträumen einige Dutzend Läufe, die sich bei unveränderter Eingabe
 * wiederholen. Der Rechenkern bleibt eine reine Funktion: Schlüssel sind die
 * aufgelösten Eingaben, die Parameter und die Richtlinie des Kontexts; das
 * gemerkte Ergebnis ist eingefroren.
 *
 * `relevant`: Schlüssel aus den Eingaben, die das Ergebnis bestimmen. Ein Blatt
 * kann darin Eingaben auslassen, die keine Formel liest (Blatt 06: die
 * Standardabweichungen unbelegter Schichten). Unterscheidet sich ein Aufruf nur
 * in solchen Eingaben, stammen die Formelzellen aus dem gemerkten Ergebnis und
 * die Eingabezellen aus dem Aufruf.
 */
export function remembered(compute: (cells: Cells, context: SheetContext) => Cells, relevant?: (cells: Cells) => string, limit = 96): (cells: Cells, context: SheetContext) => CellMap {
  const results = new Map<string, CellMap>()
  const formulas = new Map<string, CellMap>()
  const keep = (cache: Map<string, CellMap>, key: string, result: CellMap): void => {
    if (ge(cache.size, limit)) cache.delete(cache.keys().next().value as string)
    cache.set(key, result)
  }
  return (cells, context) => {
    const scope = `${identityOf(context.parameters)}|${identityOf(context.policy)}|`
    const inputs = scope + JSON.stringify(cells)
    const known = results.get(inputs)
    if (known) return known
    const key = relevant ? scope + relevant(cells) : inputs
    const same = relevant ? formulas.get(key) : undefined
    const result = Object.freeze(same ? { ...same, ...cells } : compute(cells, context))
    keep(results, inputs, result)
    if (relevant && !same) keep(formulas, key, result)
    return result
  }
}

/**
 * Anzuwendender Gesamtumfang: mindestens 30, gegebenenfalls begrenzt
 * (`appliedSampleSize`). Ist ein begrenzter Umfang gewählt und der rechnerische
 * Umfang kein Zahlenwert, zeigt die Vorlage den begrenzten Umfang. Bei „TE ≤ AE“
 * ist das die Begrenzung eines nicht bestimmbaren Umfangs; ist die Zelle des
 * rechnerischen Umfangs dagegen leer (etwa ohne Konfidenzniveau), gibt es
 * nichts zu begrenzen – ein Wert ohne Grundlage (`unfounded`).
 */
export function appliedTotalSize(computed: Value, limit: number | null, open: boolean, context: Pick<SheetContext, 'policy'>): CellValue {
  const size = appliedSampleSize(computed, limit, open)
  return open || !isBlank(computed) ? size : unfounded(context, size)
}

/**
 * Anzuwendender Umfang eines neu berechneten Zeitraums:
 * `MAX(gewählter Umfang;3[;Auffüllung auf 30])`. Der gewählte Umfang ist in der
 * Vorlage ein Bezug; steht dort ein Text („✖ nicht anwendbar …“) oder `""`,
 * übergeht `MAX` ihn und es bleiben die Untergrenzen 3 bzw. die Auffüllung auf
 * 30 – ein Wert ohne Grundlage (`unfounded`), weil es keinen Umfang gibt, den
 * die Untergrenzen sichern könnten. `open`: Der gewählte Umfang fehlt nur, weil
 * eine Angabe fehlt.
 */
export function appliedPeriodSize(chosen: Value, open: boolean, context: Pick<SheetContext, 'policy'>, shortfall?: () => number): CellValue {
  const size = periodSize(chosen, open, shortfall)
  return open || isNumber(chosen) ? size : unfounded(context, size)
}

/** Nenner der Standardneuberechnung: `(TE − AE)² − Σ z² · BV_t² / n_t · s²_rt` über die geprüften Zeiträume. */
export function standardDenominator(z: Value, tolerable: Value, anticipated: Value, periods: readonly (readonly [bookValue: Value, size: Value, deviation: Value])[]): CellValue {
  return guard(() =>
    periods.reduce(
      (value, [bookValue, size, deviation]) => minus(value, divide(required(z) ** 2 * required(bookValue) ** 2, required(size)) * required(deviation) ** 2),
      minus(required(tolerable), required(anticipated)) ** 2,
    ),
  )
}

/** Standardneuberechnung: `IF(Nenner <= 0; Text; ROUNDUP(Zähler / Nenner; 0))`. */
export function standardSize(denominator: Value, numerator: () => number, notApplicable: string = NOT_APPLICABLE): CellValue {
  return guard(() => (le(required(denominator), 0) ? notApplicable : roundUp(divide(numerator(), required(denominator)))))
}

/** Zusatzeinheiten eines bereits geprüften Zeitraums: `MAX(0; neuer Umfang − bisheriger Umfang)`. */
export function additionalUnits(recalculated: Value, current: Value): CellValue {
  return guard(() => Math.max(0, minus(required(recalculated), required(current))))
}

/**
 * Faktor der Unterschätzung `MAX(1; IFERROR(BV / BVᵖ; 1); IFERROR(N / Nᵖ; 1))`
 * für die Erhöhung bei begrenztem Umfang. Ist-Buchwert und Prognose sind
 * Pflichteingaben (die Vorlage rechnet sie leer als 0 und kommt so auf 0 bzw.
 * den Ersatzwert 1); eine fehlende Anzahl der Einheiten zählt wie in der Vorlage 1.
 */
export function underestimationFactor(bookValue: Value, planned: Value, units: Value, plannedUnits: Value): number {
  const [actual, forecast] = [required(bookValue), required(planned)]
  return Math.max(1, ifError(() => divide(actual, forecast), 1), ifError(() => divide(n(units), n(plannedUnits)), 1))
}

/** Einhaltung des begrenzten Stichprobenumfangs; `exceeded` ist der Text der Vorlage bei Überschreitung. */
export function checkLimitKept(limit: Value, total: () => number, exceeded: string): CellValue {
  if (!isNumber(limit)) return null
  return guard(() => (le(total(), limit) ? '✔ begrenzter Umfang eingehalten' : exceeded))
}

/** Mindestumfang des Geschäftsjahres (Art. 5 Abs. 5). */
export function checkYearMinimum(total: () => number): CellValue {
  return guard(() => (ge(total(), 30) ? '✔ ≥ 30 Einheiten' : '✖ < 30 Einheiten (Art. 5 Abs. 5)'))
}

/**
 * Auswahl eines Zeitraums in den ungeschichteten Blättern: neun Zeilen ab `row`
 * in der Reihenfolge der Vorlage – Grenzwert, Anzahl und Buchwert der
 * hochwertigen Einheiten (Eingaben), Buchwert und Einheiten der Zufallsschicht,
 * Prüfung „mindestens drei“, Auswahlintervall, Iteration (Eingabe) und ihre Prüfung.
 */
export function selection(c: Cells, row: number, bookValue: Value, size: Value): void {
  const cell = (offset: number): CellAddress => `C${row + offset}`
  c[cell(0)] = guard(() => divide(required(bookValue), required(size)))
  c[cell(3)] = guard(() => minus(required(bookValue), n(c[cell(2)])))
  c[cell(4)] = guard(() => minus(required(size), n(c[cell(1)])))
  c[cell(5)] = checkMinimumUnits(c[cell(4)])
  c[cell(6)] = guard(() => divide(required(c[cell(3)]), required(c[cell(4)])))
  c[cell(8)] = checkIteration(c[cell(7)])
}

/**
 * Fehlergrenzen und Würdigung: elf Zeilen ab `row` in der Reihenfolge der
 * Vorlage – EE, SE (beide schon berechnet), systembedingte und anomale Fehler
 * (Eingaben), obere und untere Fehlergrenze, relative Genauigkeit,
 * Zufallsfehlerquote, Gesamtfehlerquote, obere Fehlergrenze in % und Würdigung.
 */
export function errorLimits(c: Cells, row: number, testType: Value, bookValue: Value, materiality: Value): void {
  const cell = (offset: number): CellAddress => `C${row + offset}`
  const [projected, precision, systemic, anomalous] = [c[cell(0)], c[cell(1)], c[cell(2)], c[cell(3)]]
  c[cell(4)] = guard(() => required(projected) + required(precision) + n(systemic) + n(anomalous))
  c[cell(5)] = lowerErrorLimit(testType, projected, precision, systemic, anomalous)
  c[cell(6)] = guard(() => divide(required(precision), required(bookValue)))
  c[cell(7)] = guard(() => divide(required(projected), required(bookValue)))
  c[cell(8)] = guard(() => divide(required(projected) + n(systemic) + n(anomalous), required(bookValue)))
  c[cell(9)] = guard(() => divide(required(c[cell(4)]), required(bookValue)))
  c[cell(10)] = assessment(c[cell(8)], c[cell(9)], materiality)
}

/** Ergebnisübersicht für Blatt 18 (N3–N11); `row` ist die Zeile des extrapolierten Fehlers wie in `errorLimits`. */
export function summary(c: Cells, method: string, row: number, bookValue: Value, exhaustive: Value, size: () => number): void {
  c.N3 = method
  c.N4 = bookValue ?? null
  c.N5 = c[`C${row}`] ?? null
  c.N6 = exhaustive ?? null
  c.N7 = c[`C${row + 1}`] ?? null
  c.N8 = n(c[`C${row + 2}`])
  c.N9 = n(c[`C${row + 3}`])
  c.N10 = guard(size)
  c.N11 = c[`C${row + 8}`] ?? null
}

/**
 * Fehlt die Summe der Fehlerquoten eines Zeitraums bzw. einer Schicht, während
 * eine andere eingetragen ist, rechnet die Vorlage sie mit `N(…)` als 0 und zeigt
 * ein Ergebnis. Die Webfassung zeigt es ebenfalls und weist die leere Eingabe aus
 * (Fallart `partialErrorSum`). `projected`: Zelle des extrapolierten Fehlers;
 * `cells`: alle Zellen, die von der leeren Eingabe abhängen.
 */
export function partialErrorSums(results: CellMap, projected: CellAddress, inputs: readonly (readonly [input: CellAddress, cells: readonly CellAddress[]])[]): ZeroAssumption[] {
  if (!isNumber(results[projected])) return []
  return inputs.filter(([input]) => isBlank(results[input])).map(([input, cells]) => ({ input, cells, kind: 'partialErrorSum' as const }))
}

/** Zellen ab dem extrapolierten Fehler (`row`, wie in `errorLimits`), die von einer Summe der Fehlerquoten abhängen, samt N5 und N11. */
export function errorDependents(row: number): CellAddress[] {
  return [0, 4, 5, 7, 8, 9, 10].map((offset) => `C${row + offset}`).concat(['N5', 'N11'])
}

/**
 * Hinweis der Webfassung: Begrenzter Umfang gewählt, aber kein rechnerischer
 * Umfang – der anzuwendende Umfang bleibt offen statt auf die Begrenzung zu fallen.
 */
export function limitWithoutSize(results: CellMap, limit: CellAddress, computed: CellAddress, applied: CellAddress): WebHint[] {
  if (!isNumber(results[limit]) || !isBlank(results[computed]) || !isBlank(results[applied])) return []
  return [{ id: 'limited-size-open', tone: 'neutral', text: 'Begrenzter Stichprobenumfang gewählt, der rechnerische Gesamtumfang ist aber nicht bestimmt: Der anzuwendende Gesamtumfang bleibt offen' }]
}

/**
 * Englische Arbeitsübersetzung (nicht amtlich) der Texte, die die Rechenkerne der
 * MUS-Blätter 04–07 liefern: Prüfhinweise aus `statistical.ts`, `periods.ts` und
 * dieser Datei. Begriffe nach der englischen Fassung der DelVO (EU) 2023/67.
 */
export const VALUES_EN: Readonly<Record<string, string>> = {
  '✔ mind. 90 % eingehalten': '✔ at least 90 % observed',
  '✖ gering: mind. 90 % erforderlich': '✖ low: at least 90 % required',
  '✔ mind. 60 % eingehalten': '✔ at least 60 % observed',
  '✖ hoch: mind. 60 % erforderlich': '✖ high: at least 60 % required',
  '✔ mittel: Wert zwischen den Eckwerten': '✔ average: value between the two minimum levels',
  '⚠ mittel: Wert zwischen 60 % und 90 % begründen': '⚠ average: justify a value between 60 % and 90 %',
  '✔ ≤ 2 %': '✔ ≤ 2 %',
  '✖ unzulässig: höchstens 2 %': '✖ not permitted: maximum 2 %',
  '✔ TE > AE': '✔ TE > AE',
  '✖ TE ≤ AE: Stichprobenumfang nicht bestimmbar': '✖ TE ≤ AE: sample size cannot be determined',
  'TE ≤ AE': 'TE ≤ AE',
  'Nicht angewandt – Anh. I und II gelten': 'Not applied – Annexes I and II apply',
  '✔ 30 Einheiten (Art. 83 VO (EU) 2021/1060)': '✔ 30 sampling units (Art. 83 of Regulation (EU) 2021/1060)',
  '✔ 50 Einheiten zulässig (Art. 5 Abs. 7)': '✔ 50 sampling units permitted (Art. 5(7))',
  '✖ unzulässig: nur Kategorie 1 oder 2': '✖ not permitted: category 1 or 2 only',
  '✔ ≥ 3 Einheiten': '✔ ≥ 3 units',
  '✖ < 3 Einheiten (Art. 5 Abs. 5)': '✖ < 3 units (Art. 5(5))',
  '✔ ≥ 3': '✔ ≥ 3',
  '✖ < 3': '✖ < 3',
  '✔ keine weitere Iteration': '✔ no further iteration',
  '⚠ Einheiten umgliedern und Intervall neu berechnen': '⚠ reassign units and recalculate the interval',
  'n. a. (einseitiger Test)': 'n/a (unilateral testing)',
  '✖ Gesamtfehlerquote über der Wesentlichkeitsschwelle': '✖ total error rate above the materiality threshold',
  '⚠ GFQ unter, obere Fehlergrenze über der Schwelle – weitere Würdigung': '⚠ total error rate below, upper error limit above the threshold – further assessment',
  '✔ GFQ und obere Fehlergrenze unter der Schwelle': '✔ total error rate and upper error limit below the threshold',
  [NOT_APPLICABLE]: '✖ not applicable (denominator ≤ 0)',
  '✔ begrenzter Umfang eingehalten': '✔ capped sample size observed',
  '⚠ Umfang überschritten – Art. 5 Abs. 7 UAbs. 4': '⚠ sample size exceeded – Art. 5(7), fourth subparagraph',
  '✔ ≥ 30 Einheiten': '✔ ≥ 30 units',
  '✖ < 30 Einheiten (Art. 5 Abs. 5)': '✖ < 30 units (Art. 5(5))',
}

/** Erläuterung „Auslegung der Vorlage“ zur Erhöhung bei begrenztem Umfang in der englischen Arbeitsübersetzung. */
export const INCREASE_INTERPRETATION_EN =
  'The Delegated Regulation does not lay down how the increase under Art. 5(7), fourth subparagraph, point (a) is calculated; the template proposes a proportional increase.'

/** Hinweise der Webfassung, die mehrere MUS-Blätter verwenden, in der englischen Arbeitsübersetzung. */
export const HINTS_EN = {
  'confidence-outside-annex': 'Confidence level 95 % is outside the table in Annex I',
  'limited-size-open': 'Capped sample size selected, but the calculated total sample size is not determined: the total sample size to be applied remains open',
  'size-exceeds-population': 'Sample size exceeds the number of units of the population',
  'strata-sum-exceeds-size': 'Sum of the rounded-up stratum sample sizes is larger than the sample size to be applied',
  'strata-beyond-template': 'More than seven strata: the template provides seven columns; strata 8 to 20 are an extension of the web version',
} as const

/** Hinweis „Stichprobenumfang übersteigt die Anzahl der Einheiten“ je Zeitraum (`size-exceeds-population-<n>`). */
export function periodExceedsEn(period: number): string {
  return `Sample size for period ${period} exceeds the number of units of the period`
}

/** Englische Arbeitsübersetzung zur Auswahl eines Zeitraums: neun Zeilen ab `row` (Grenzwert bis Prüfung Iteration), wie `selection`. */
export function selectionEn(row: number, period: number): Record<CellAddress, FieldTexts> {
  const cell = (offset: number): CellAddress => `C${row + offset}`
  return {
    [cell(0)]: { label: `Cut-off value for high value units (BV${period}/n${period}) (BV/n)`, hint: 'Art. 5(2), second subparagraph: high value units above the interval of selection are audited in full.' },
    [cell(1)]: { label: 'Number of high value units (BV > cut-off value) (n_e)' },
    [cell(2)]: { label: 'Book value of the high value units (BV_e)' },
    [cell(3)]: { label: 'Book value of the random stratum (low value units) (BV_s)' },
    [cell(4)]: { label: 'Number of units to be selected in the random stratum (n_s)' },
    [cell(5)]: { label: 'At least three units in the random stratum' },
    [cell(6)]: { label: 'Interval of selection (BV_s / n_s) (SI)', hint: 'Art. 2(9); Art. 5(2), second subparagraph DR.' },
    [cell(7)]: { label: 'Units of the random stratum with BV > interval of selection (iteration)', hint: 'Such units are to be assigned to the high value stratum; cut-off value and interval are to be recalculated.' },
    [cell(8)]: { label: 'Check of the iteration' },
  }
}

/** Englische Arbeitsübersetzung zu den Prüfergebnissen eines Zeitraums: drei Zeilen ab `row`. */
export function findingsEn(row: number): Record<CellAddress, FieldTexts> {
  return {
    [`C${row}`]: { label: 'Sum of the errors in the high value units (ΣE_e)', hint: 'In the case of subsampling: error extrapolated to the sampling unit (Art. 8(3); sheet 17).' },
    [`C${row + 1}`]: { label: 'Sum of the error rates of the sample of the random stratum (Σ E_i/BV_i)' },
    [`C${row + 2}`]: { label: 'Standard deviation of the error rates in the sample of the random stratum (s_r)', hint: 'Calculated from the same sample used to extrapolate the errors (Annex II point 1).' },
  }
}
