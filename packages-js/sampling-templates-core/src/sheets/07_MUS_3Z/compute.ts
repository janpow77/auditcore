/**
 * Rechenkern Blatt 07_MUS_3Z: MUS-Standardansatz, drei Stichprobenzeiträume,
 * nicht geschichtet (Anhang II Nr. 1.3 DelVO (EU) 2023/67). Jede Zuweisung
 * bildet die Formel der gleichnamigen Zelle der Vorlage nach; Rundung,
 * Schwellen und Rechenreihenfolge sind unverändert.
 */
import { divide, guard, isBlank, isNumber, minus, n, required, roundUp, squareRoot } from '../../excel/index'
import { projectionWithoutErrors } from '../../model/policy'
import { resolveInputs } from '../../model/sheet'
import type { CellAddress, CellMap, Cells, SheetContext } from '../../model/types'
import { zValue } from '../01_Parameter/index'
import {
  type Approach,
  type Pending,
  additionalUnits,
  appliedPeriodSize,
  appliedTotalSize,
  approachOf,
  checkLimitKept,
  checkYearMinimum,
  computeTwice,
  errorLimits,
  globalComputedSize,
  remembered,
  selection,
  share,
  standardDenominator,
  standardSize,
  summary,
  underestimationFactor,
  weightedDeviation,
} from '../shared/mus'
import { checkConfidence, checkMateriality, checkTolerableError, computedSampleSize, limitedSampleSize } from '../shared/statistical'
import { definition } from './definition'
import { blockedGlobal, withoutGlobalAssessment } from '../shared/periods'

/**
 * Eingaben, mit denen die Vorlage leer als 0 weiterrechnet; die Webfassung
 * zeigt in den abhängigen Zellen „Angabe fehlt“ (deviations.ts).
 */
export const REQUIRED_INPUTS: readonly CellAddress[] = ['C7', 'C8', 'C9', 'C18', 'C21', 'C24', 'C25', 'C26', 'C51', 'C53', 'C55', 'C56', 'C90', 'C92']

/** Begrenzter Umfang, gewählter Ansatz, Kontext des Laufs und die Auskunft über offene Zellen (`computeTwice`). */
interface Run {
  pending: Pending
  context: SheetContext
  limit: number | null
  approach: Approach
}

/** Abschnitte H und I: prognostizierter Buchwert, z, zulässiger und voraussichtlicher Fehler (C12–C27). */
function parameters(c: Cells, context: SheetContext): void {
  c.C12 = guard(() => required(c.C7) + required(c.C8) + required(c.C9))
  c.C16 = guard(() => zValue(context.parameters, c.C14, c.C15))
  c.C17 = checkConfidence(c.C13, c.C14)
  c.C19 = checkMateriality(c.C18)
  c.C20 = guard(() => required(c.C18) * required(c.C12))
  c.C22 = guard(() => required(c.C21) * required(c.C12))
  c.C23 = checkTolerableError(c.C20, c.C22, c.C21)
  c.C27 = weightedDeviation([[c.C7, c.C24], [c.C8, c.C25], [c.C9, c.C26]], c.C12)
}

/** Abschnitt J: Gesamtumfang und Aufteilung auf die Zeiträume (C29–C38); Rückgabe: begrenzter Umfang. */
function sampleSize(c: Cells, pending: Pending, context: SheetContext): number | null {
  c.C29 = computedSampleSize({ z: c.C16, bookValue: c.C12, deviation: c.C27, tolerable: c.C20, anticipated: c.C22 })
  const [check, limit] = limitedSampleSize(c.C32, c.C31, c.C30)
  c.C33 = check
  c.C34 = limit
  c.C35 = appliedTotalSize(c.C29, limit, pending('C29'), context)
  c.C36 = share(c.C7, c.C12, c.C35)
  c.C37 = share(c.C8, c.C12, c.C35)
  c.C38 = share(c.C9, c.C12, c.C35)
  return limit
}

/** Abschnitt L, erster Teil: aktualisierte Größen und Standardneuberechnung für die Zeiträume 2 und 3 (C58–C67). */
function secondStandard(c: Cells): void {
  c.C58 = guard(() => required(c.C7) + required(c.C51) + required(c.C53))
  c.C59 = guard(() => required(c.C18) * required(c.C58))
  c.C60 = guard(() => required(isBlank(c.C57) ? c.C21 : c.C57) * required(c.C58))
  c.C61 = isBlank(c.C50) ? (c.C24 ?? null) : (c.C50 ?? null)
  c.C62 = guard(() => required(c.C51) + required(c.C53))
  c.C63 = weightedDeviation([[c.C51, c.C55], [c.C53, c.C56]], c.C62)
  c.C64 = standardDenominator(c.C16, c.C59, c.C60, [[c.C7, c.C36, c.C61]])
  c.C65 = standardSize(c.C64, () => (required(c.C16) * required(c.C62) * required(c.C63)) ** 2)
  c.C66 = share(c.C51, c.C62, c.C65)
  c.C67 = share(c.C53, c.C62, c.C65)
}

/** Umfang nach dem gewählten Ansatz: Zelle je Ansatz (C28). */
type Choice = Readonly<Record<Approach, CellAddress>>
const PERIOD2: Choice = { standard: 'C66', global: 'C72', increase: 'C74', none: 'C37' }
/** Planumfang Zeitraum 3: Die Vorlage schreibt ihn bei „Erhöhung“ nicht fort (C38). */
const PLANNED3: Choice = { standard: 'C67', global: 'C73', increase: 'C38', none: 'C38' }
const PERIOD3: Choice = { standard: 'C99', global: 'C105', increase: 'C106', none: 'C38' }

/** Abschnitt L, zweiter Teil: globale Neuberechnung, Erhöhung und anzuwendende Umfänge (C68–C77). */
function secondSizes(c: Cells, run: Run): void {
  c.C68 = weightedDeviation([[c.C7, c.C61], [c.C51, c.C55], [c.C53, c.C56]], c.C58)
  c.C69 = globalComputedSize(c.C16, c.C58, c.C68, c.C59, c.C60)
  c.C70 = appliedTotalSize(c.C69, run.limit, run.pending('C69'), run.context, true)
  c.C71 = additionalUnits(share(c.C7, c.C58, c.C70), c.C36)
  c.C72 = share(c.C51, c.C58, c.C70)
  c.C73 = share(c.C53, c.C58, c.C70)
  c.C74 = guard(() => roundUp(required(c.C37) * underestimationFactor(c.C51, c.C8, c.C52, c.C10)))
  // Globaler Ansatz bei AE = TE nicht anwendbar (Division durch null): Umfang offen statt Untergrenze.
  const blocked = run.approach === 'global' && blockedGlobal(c, 'C69', run.pending)
  c.C75 = appliedPeriodSize(c[PERIOD2[run.approach]], run.pending(PERIOD2[run.approach]) || blocked, run.context)
  c.C76 = c[PLANNED3[run.approach]] ?? null
  c.C77 = guard(() => required(c.C36) + (run.approach === 'global' ? required(c.C71) : 0))
}

/** Abschnitt N, erster Teil: Größen nach Zeitraum 2 und die drei Ansätze für Zeitraum 3 (C94–C106). */
function thirdRecalculation(c: Cells, run: Run): void {
  c.C94 = guard(() => required(c.C7) + required(c.C51) + required(c.C90))
  c.C95 = guard(() => required(c.C18) * required(c.C94))
  const rate = isBlank(c.C93) ? (isBlank(c.C57) ? c.C21 : c.C57) : c.C93
  c.C96 = guard(() => required(rate) * required(c.C94))
  c.C97 = isBlank(c.C89) ? (c.C55 ?? null) : (c.C89 ?? null)
  c.C98 = standardDenominator(c.C16, c.C95, c.C96, [[c.C7, c.C77, c.C61], [c.C51, c.C75, c.C97]])
  c.C99 = standardSize(c.C98, () => (required(c.C16) * required(c.C90) * required(c.C92)) ** 2)
  c.C100 = weightedDeviation([[c.C7, c.C61], [c.C51, c.C97], [c.C90, c.C92]], c.C94)
  c.C101 = globalComputedSize(c.C16, c.C94, c.C100, c.C95, c.C96)
  c.C102 = appliedTotalSize(c.C101, run.limit, run.pending('C101'), run.context, true)
  c.C103 = additionalUnits(share(c.C7, c.C94, c.C102), c.C77)
  c.C104 = additionalUnits(share(c.C51, c.C94, c.C102), c.C75)
  c.C105 = share(c.C90, c.C94, c.C102)
  c.C106 = guard(() => roundUp(required(c.C76) * underestimationFactor(c.C90, c.C53, c.C91, c.C54)))
}

/** Abschnitt N, zweiter Teil: endgültige Umfänge und ihre Prüfung (C107–C111). */
function finalSizes(c: Cells, run: Run): void {
  const extra = (cell: CellAddress): number => (run.approach === 'global' ? required(c[cell]) : 0)
  c.C107 = guard(() => required(c.C77) + extra('C103'))
  c.C108 = guard(() => required(c.C75) + extra('C104'))
  const blocked = run.approach === 'global' && (blockedGlobal(c, 'C69', run.pending) || blockedGlobal(c, 'C101', run.pending))
  c.C109 = appliedPeriodSize(c[PERIOD3[run.approach]], run.pending(PERIOD3[run.approach]) || blocked, run.context, () => minus(minus(30, required(c.C107)), required(c.C108)))
  const total = (): number => required(c.C107) + required(c.C108) + required(c.C109)
  c.C110 = checkLimitKept(run.limit, total, '⚠ Umfang überschritten – Art. 5 Abs. 7 UAbs. 4')
  c.C111 = isNumber(c.C109) ? checkYearMinimum(total) : null
}

/**
 * Abschnitt P: Hochrechnung und Genauigkeit (C126–C129). Fehlt die
 * Standardabweichung der Stichprobe eines Zeitraums (C50, C89, C123), rechnet die
 * Webfassung wie die Vorlage mit 0 und weist das aus (`zeroAssumed`).
 */
function projection(c: Cells, context: SheetContext): void {
  const term = (bookValue: CellAddress, units: CellAddress, power: number): number => divide(required(c[bookValue]) ** power, required(c[units]))
  c.C126 = n(c.C48) + n(c.C87) + n(c.C121)
  c.C127 = projectionWithoutErrors(context, [c.C49, c.C88, c.C122].some(isNumber), guard(() => term('C42', 'C124', 1) * n(c.C49) + term('C81', 'C125', 1) * n(c.C88) + term('C115', 'C116', 1) * n(c.C122)))
  c.C128 = [c.C49, c.C88, c.C122].some(isNumber) ? guard(() => required(c.C126) + required(c.C127)) : null
  c.C129 = guard(() => required(c.C16) * squareRoot(term('C42', 'C124', 2) * n(c.C50) ** 2 + term('C81', 'C125', 2) * n(c.C89) ** 2 + term('C115', 'C116', 2) * n(c.C123) ** 2))
}

/** Alle Formelzellen in Blattreihenfolge; `pending` siehe `computeTwice`. */
function evaluate(c: Cells, pending: Pending, context: SheetContext): void {
  parameters(c, context)
  const run: Run = { pending, context, limit: sampleSize(c, pending, context), approach: approachOf(c.C28) }
  selection(c, 39, c.C7, c.C36)
  secondStandard(c)
  secondSizes(c, run)
  selection(c, 78, c.C51, c.C75)
  thirdRecalculation(c, run)
  finalSizes(c, run)
  selection(c, 112, c.C90, c.C109)
  c.C124 = guard(() => minus(required(c.C107), n(c.C40)))
  c.C125 = guard(() => minus(required(c.C108), n(c.C79)))
  projection(c, context)
  errorLimits(c, 128, c.C15, c.C94, c.C18)
  summary(c, 'MUS-Standardansatz, 3 Zeiträume', 128, c.C94, c.C126, () => required(c.C107) + required(c.C108) + required(c.C109))
  withoutGlobalAssessment(c, run.approach, ['C69', 'C101'], pending, 'C138')
}

const calculate = remembered((cells, context) => computeTwice(cells, REQUIRED_INPUTS, context, evaluate))

/** Berechnet alle Formelzellen des Blatts 07; Eingaben und Ergebnisse tragen die Zelladressen der Vorlage. */
export function compute(inputs: CellMap, context: SheetContext): CellMap {
  return calculate(resolveInputs(definition, inputs, context), context)
}
