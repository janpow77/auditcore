/**
 * Formeln, die in den nichtstatistischen Blättern 13–16 wortgleich vorkommen
 * (nur die Zellbezüge unterscheiden sich): Zulässigkeit des Verfahrens,
 * Mindesterfassung von 10 % der Stichprobeneinheiten, Aufteilung des
 * Stichprobenumfangs auf Schichten, extrapolierter Fehler, Fehlerquoten,
 * Würdigung und Ergebnisübersicht. Jedes Blatt ruft sie mit seinen Zellen auf;
 * so stehen die Texte der Vorlage genau einmal im Quelltext.
 *
 * Beim nichtstatistischen Verfahren gibt es weder Genauigkeit noch obere
 * Fehlergrenze (Art. 8 Abs. 2 DelVO (EU) 2023/67).
 */
import { divide, eq, ge, gt, guard, isBlank, isNumber, lt, n, plus, required, roundUp } from '../../excel/index'
import type { ZeroAssumption } from '../../model/sheet'
import { STRATA_COLUMNS, TEMPLATE_STRATA, stratumCell, totalRow, usedStrata } from '../../model/strata'
import type { CellAddress, CellMap, CellValue, Cells, SheetContext, WebHint } from '../../model/types'

type Value = CellValue | undefined

/** Text der Zelle N7 in allen vier Blättern. */
export const NO_PRECISION = 'n. a. (Art. 8 Abs. 2)'

/**
 * Zulässigkeit des nichtstatistischen Verfahrens (N < 300).
 * `=IF(N="";"";IF(N<300;"✔ …";"⚠ …"))`
 */
export function checkAdmissibility(units: Value): CellValue {
  if (isBlank(units)) return null
  // Ein Text ist im Größenvergleich größer als jede Zahl: `Text < 300` ist falsch.
  return isNumber(units) && lt(units, 300) ? '✔ N < 300: zulässig (Art. 79 Abs. 2 VO (EU) 2021/1060; Art. 6 Abs. 1)' : '⚠ N ≥ 300: nur im Fall des Art. 6 Abs. 3 zulässig'
}

/** Mindesterfassung 10 % der Stichprobeneinheiten, aufgerundet: `=ROUNDUP(0,1*N;0)`. */
export function minimumCoverage(units: Value): CellValue {
  return guard(() => roundUp(0.1 * required(units)))
}

/**
 * Prüfung Mindesterfassung: `=IF(n="";"";IF(n>=Mindesterfassung;"✔ …";"✖ …"))`.
 * Die Mindesterfassung ist in der Vorlage immer eine Zahl; fehlt sie hier, fehlt
 * der Umfang der Grundgesamtheit („Angabe fehlt“).
 */
export function checkCoverage(sample: Value, minimum: Value): CellValue {
  if (!isNumber(sample) || !isNumber(minimum)) return null
  return ge(sample, minimum) ? '✔ Mindesterfassung erreicht' : '✖ Mindesterfassung von 10 % nicht erreicht'
}

/**
 * Umfang je Schicht: `=IF(D11="";"";MAX(1;ROUNDUP(D11/$C$11*$C$16;0)))`.
 * `share` ist die Größe der Schicht (Einheiten bzw. Buchwert), `total` ihre
 * Summe über alle Schichten, `size` der Stichprobenumfang.
 */
export function stratumSampleSize(share: Value, total: Value, size: Value): CellValue {
  if (isBlank(share)) return null
  return guard(() => Math.max(1, roundUp(divide(required(share), required(total)) * required(size))))
}

/**
 * Extrapolierter Fehler EE: `=IF(COUNT(Fehler)=0;"";EE_e+EE_s)`. `entered` ist
 * die Anzahl der eingetragenen Fehlerwerte der Zufallsschicht(en).
 */
export function projectedError(entered: number, exhaustive: Value, random: Value): CellValue {
  if (eq(entered, 0)) return null
  return guard(() => plus(required(exhaustive), required(random)))
}

/**
 * Summe einer berechneten Schichtzeile, die für unbelegte Schichten 0 trägt
 * (`IF(D11="";0;…)`): summiert werden die belegten Schichten (`key` ist die
 * Zeile, deren Wert eine Schicht als belegt kennzeichnet). Trägt keine belegte
 * Schicht einen Wert, zeigt die Vorlage die Summe der Nullen der unbelegten
 * Spalten – ein Wert ohne Grundlage (`totalRow`).
 */
export function usedTotal(c: Readonly<Cells>, row: number, key: number, context: Pick<SheetContext, 'policy'> | undefined): CellValue {
  return totalRow(c, row, context, STRATA_COLUMNS.filter((column) => !isBlank(c[stratumCell(column, key)])))
}

/** Extrapolierte Zufallsfehlerquote: `=EE/BV`. */
export function projectedErrorRate(error: Value, bookValue: Value): CellValue {
  return guard(() => divide(required(error), required(bookValue)))
}

/** Gesamtfehlerquote: `=(EE+N(systembedingt)+N(anomal))/BV`. */
export function totalErrorRate(error: Value, systemic: Value, anomalous: Value, bookValue: Value): CellValue {
  return guard(() => divide(plus(plus(required(error), n(systemic)), n(anomalous)), required(bookValue)))
}

/**
 * Würdigung gegen die Wesentlichkeitsschwelle:
 * `=IF(GFQ="";"";IF(GFQ>Schwelle;"✖ …";"✔ …"))`. Ohne Schwelle vergliche die
 * Vorlage gegen 0; die Webfassung zeigt „Angabe fehlt“.
 */
export function assessment(rate: Value, materiality: Value): CellValue {
  if (!isNumber(rate) || !isNumber(materiality)) return null
  return gt(rate, materiality) ? '✖ Gesamtfehlerquote über der Wesentlichkeitsschwelle' : '✔ Gesamtfehlerquote unter der Wesentlichkeitsschwelle'
}

/** Zellen eines Blatts, aus denen die Ergebnisübersicht N3–N11 entsteht. */
export interface SummarySources {
  /** N3: Name der Methode. */
  method: string
  bookValue: CellAddress
  projectedError: CellAddress
  exhaustiveError: CellAddress
  systemicErrors: CellAddress
  anomalousErrors: CellAddress
  sampleSize: CellAddress
  totalErrorRate: CellAddress
}

/** Ergebnisübersicht für Blatt 18 (feste Zellen N3–N11); N7 ist beim nichtstatistischen Verfahren ein Text. */
export function fillSummary(c: Cells, sources: SummarySources): void {
  c.N3 = sources.method
  c.N4 = c[sources.bookValue] ?? null
  c.N5 = c[sources.projectedError] ?? null
  c.N6 = c[sources.exhaustiveError] ?? null
  c.N7 = NO_PRECISION
  c.N8 = n(c[sources.systemicErrors])
  c.N9 = n(c[sources.anomalousErrors])
  c.N10 = c[sources.sampleSize] ?? null
  c.N11 = c[sources.totalErrorRate] ?? null
}

/** Hinweise der Webfassung zu den Blättern 13–16; sie verändern kein Rechenergebnis. */
const HINTS = {
  'size-exceeds-population': 'Stichprobenumfang übersteigt die Anzahl der Einheiten der Grundgesamtheit',
  'strata-sum-exceeds-size': 'Summe der aufgerundeten Schichtumfänge ist größer als der gewählte Stichprobenumfang',
  'strata-beyond-template': 'Mehr als sieben Schichten: Die Vorlage sieht sieben Spalten vor; die 8. bis 20. Schicht ist eine Erweiterung der Webfassung',
} as const

/** Hinweise der Webfassung zu einer einzelnen Schicht; die Kennung trägt die Schichtnummer (`stratum-ignored-3`). */
const STRATUM_HINTS = {
  'stratum-not-projected': 'Der extrapolierte Fehler ist nicht bestimmbar; wie in der Vorlage ist die Schicht in der Summe nicht enthalten',
  'stratum-ignored': 'Angaben vorhanden, aber kein Wert in der ersten Schichtzeile; wie in der Vorlage gilt die Schicht als nicht belegt',
} as const

type StratumHintId = keyof typeof STRATUM_HINTS

/** Je betroffener Schicht ein Hinweis: „Schicht 3: …“ mit der Kennung `<id>-3`. */
function stratumHints(id: StratumHintId, affected: (column: string) => boolean): WebHint[] {
  return STRATA_COLUMNS.flatMap((column, index): WebHint[] => (affected(column) ? [{ id: `${id}-${index + 1}`, tone: 'warning', text: `Schicht ${index + 1}: ${STRATUM_HINTS[id]}` }] : []))
}

export type HintId = keyof typeof HINTS

/** Hinweis der Webfassung, wenn die Bedingung zutrifft. */
export function hintIf(condition: boolean, id: HintId, tone: WebHint['tone'] = 'warning'): WebHint[] {
  return condition ? [{ id, tone, text: HINTS[id] }] : []
}

/** `larger > smaller`, wenn beide Zellen Zahlen sind. */
export function exceeds(larger: Value, smaller: Value): boolean {
  return isNumber(larger) && isNumber(smaller) && gt(larger, smaller)
}

/** Zeilen eines geschichteten Blatts, an denen die Hinweise und die mit 0 gerechneten Eingaben hängen. */
export interface StrataRows {
  /** Zeile, deren Wert eine Schicht als belegt kennzeichnet (`IF(D9="";…)`). */
  key: number
  /** Weitere Eingabezeilen je Schicht. */
  inputs: readonly number[]
  /** Eingabezeile der Fehlersumme bzw. Summe der Fehlerquoten der Zufallsschicht. */
  errors: number
  /** Zeile des extrapolierten Fehlers je Schicht. */
  projected: number
  /** Zelle des extrapolierten Fehlers EE. */
  total: CellAddress
}

/**
 * Hinweise der Webfassung zu den Schichten: je Schicht, deren extrapolierter
 * Fehler in der ausgewiesenen Summe fehlt, und je Schicht mit Angaben ohne Wert
 * in der ersten Schichtzeile ein Hinweis mit der Schichtnummer; dazu die
 * Erweiterung über sieben Schichten.
 */
export function strataHints(inputs: CellMap, results: CellMap, rows: StrataRows): WebHint[] {
  const used = (column: string): boolean => !isBlank(results[stratumCell(column, rows.key)])
  const totalled = isNumber(results[rows.total])
  return [
    ...stratumHints('stratum-not-projected', (column) => totalled && used(column) && isBlank(results[stratumCell(column, rows.projected)])),
    ...stratumHints('stratum-ignored', (column) => !used(column) && rows.inputs.some((row) => !isBlank(results[stratumCell(column, row)]))),
    ...hintIf(gt(usedStrata(inputs, [rows.key, ...rows.inputs]), TEMPLATE_STRATA.length), 'strata-beyond-template', 'neutral'),
  ]
}

/**
 * Fehlt die Fehlersumme einer belegten Schicht, während andere Schichten eine
 * tragen, rechnet die Vorlage diese Schicht mit 0 (`N(D25)`); die Webfassung
 * rechnet genauso und weist die Eingabe aus (Fallart `partialErrorSum` der
 * Richtlinie in `model/policy.ts`). `affected` sind die Zellen, die außer dem
 * Fehler der Schicht davon abhängen, einschließlich N5 und N11.
 */
export function strataZeroAssumed(results: CellMap, rows: StrataRows, affected: readonly CellAddress[]): ZeroAssumption[] {
  if (!isNumber(results[rows.total])) return []
  return STRATA_COLUMNS.filter((column) => !isBlank(results[stratumCell(column, rows.key)]) && isBlank(results[stratumCell(column, rows.errors)]) && isNumber(results[stratumCell(column, rows.projected)])).map((column) => ({
    input: stratumCell(column, rows.errors),
    cells: [stratumCell(column, rows.projected), ...affected],
    kind: 'partialErrorSum',
  }))
}

/** Hinweise der Webfassung in der englischen Arbeitsübersetzung. */
export const HINTS_EN: Readonly<Record<HintId, string>> = {
  'size-exceeds-population': 'Sample size exceeds the number of units of the population',
  'strata-sum-exceeds-size': 'Sum of the rounded-up stratum sample sizes is larger than the chosen sample size',
  'strata-beyond-template': 'More than seven strata: the template provides seven columns; strata 8 to 20 are an extension of the web version',
}

const STRATUM_HINTS_EN: Readonly<Record<StratumHintId, string>> = {
  'stratum-not-projected': 'the extrapolated error cannot be determined; as in the template the stratum is not included in the total',
  'stratum-ignored': 'entries present but no value in the first stratum row; as in the template the stratum is treated as not in use',
}

/** Hinweise der Webfassung zu den Schichten in der englischen Arbeitsübersetzung, je Schichtnummer (`stratum-ignored-3`). */
export const STRATA_HINTS_EN: Readonly<Record<string, string>> = Object.fromEntries(
  (Object.keys(STRATUM_HINTS_EN) as StratumHintId[]).flatMap((id) => STRATA_COLUMNS.map((_, index) => [`${id}-${index + 1}`, `Stratum ${index + 1}: ${STRATUM_HINTS_EN[id]}`])),
)

/** Texte, die die Rechenkerne der Blätter 13–16 liefern, in der englischen Arbeitsübersetzung. */
export const VALUES_EN: Readonly<Record<string, string>> = {
  [NO_PRECISION]: 'n/a (Art. 8(2))',
  '✔ N < 300: zulässig (Art. 79 Abs. 2 VO (EU) 2021/1060; Art. 6 Abs. 1)': '✔ N < 300: admissible (Art. 79(2) of Regulation (EU) 2021/1060; Art. 6(1))',
  '⚠ N ≥ 300: nur im Fall des Art. 6 Abs. 3 zulässig': '⚠ N ≥ 300: admissible only in the case of Art. 6(3)',
  '✔ Mindesterfassung erreicht': '✔ minimum coverage reached',
  '✖ Mindesterfassung von 10 % nicht erreicht': '✖ minimum coverage of 10 % not reached',
  '✔ ≥ 3 Einheiten': '✔ ≥ 3 units',
  '✖ < 3 Einheiten (Art. 5 Abs. 5)': '✖ < 3 units (Art. 5(5))',
  '✔ keine weitere Iteration': '✔ no further iteration',
  '⚠ Einheiten umgliedern und Intervall neu berechnen': '⚠ reassign units and recalculate the interval',
  '✖ Gesamtfehlerquote über der Wesentlichkeitsschwelle': '✖ total error rate above the materiality threshold',
  '✔ Gesamtfehlerquote unter der Wesentlichkeitsschwelle': '✔ total error rate below the materiality threshold',
}
