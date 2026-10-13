/**
 * Rechenkern Blatt 05_MUS_2Z: MUS-Standardansatz, zwei Stichprobenzeiträume,
 * nicht geschichtet (Anhang II Nr. 1.2 DelVO (EU) 2023/67). Jede Zuweisung
 * bildet die Formel der gleichnamigen Zelle der Vorlage nach; Rundung,
 * Schwellen und Rechenreihenfolge sind unverändert.
 */
import { divide, guard, isBlank, isNumber, minus, n, required, roundUp, squareRoot } from '../../excel/index'
import { projectionWithoutErrors } from '../../model/policy'
import { resolveInputs } from '../../model/sheet'
import type { CellAddress, CellMap, Cells, SheetContext } from '../../model/types'
import { zValue } from '../01_Parameter/index'
import {
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

/**
 * Eingaben, mit denen die Vorlage leer als 0 weiterrechnet; die Webfassung
 * zeigt in den abhängigen Zellen „Angabe fehlt“ (deviations.ts).
 */
export const REQUIRED_INPUTS: readonly CellAddress[] = ['C7', 'C8', 'C17', 'C20', 'C23', 'C24', 'C48', 'C50']

/** Text der Vorlage in C57 bei nicht positivem Nenner. */
export const NOT_APPLICABLE_GLOBAL = '✖ nicht anwendbar (Nenner ≤ 0) – globale Neuberechnung'

/** Abschnitte H und I: prognostizierter Buchwert, z, zulässiger und voraussichtlicher Fehler (C11–C25). */
function parameters(c: Cells, context: SheetContext): void {
  c.C11 = guard(() => required(c.C7) + required(c.C8))
  c.C15 = guard(() => zValue(context.parameters, c.C13, c.C14))
  c.C16 = checkConfidence(c.C12, c.C13)
  c.C18 = checkMateriality(c.C17)
  c.C19 = guard(() => required(c.C17) * required(c.C11))
  c.C21 = guard(() => required(c.C20) * required(c.C11))
  c.C22 = checkTolerableError(c.C19, c.C21, c.C20)
  c.C25 = weightedDeviation([[c.C7, c.C23], [c.C8, c.C24]], c.C11)
}

/** Abschnitt J: Gesamtumfang und Aufteilung auf die Zeiträume (C27–C35); Rückgabe: begrenzter Umfang. */
function sampleSize(c: Cells, pending: Pending, context: SheetContext): number | null {
  c.C27 = computedSampleSize({ z: c.C15, bookValue: c.C11, deviation: c.C25, tolerable: c.C19, anticipated: c.C21 })
  const [check, limit] = limitedSampleSize(c.C30, c.C29, c.C28)
  c.C31 = check
  c.C32 = limit
  c.C33 = appliedTotalSize(c.C27, limit, pending('C27'), context)
  c.C34 = share(c.C7, c.C11, c.C33)
  c.C35 = share(c.C8, c.C11, c.C33)
  return limit
}

/** Abschnitt M, erster Teil: aktualisierte Größen und die drei Ansätze der Neuberechnung (C52–C65). */
function recalculation(c: Cells, pending: Pending, limit: number | null, context: SheetContext): void {
  c.C52 = guard(() => required(c.C7) + required(c.C48))
  c.C53 = guard(() => required(c.C17) * required(c.C52))
  c.C54 = guard(() => required(isBlank(c.C51) ? c.C20 : c.C51) * required(c.C52))
  c.C55 = isBlank(c.C47) ? (c.C23 ?? null) : (c.C47 ?? null)
  c.C56 = standardDenominator(c.C15, c.C53, c.C54, [[c.C7, c.C34, c.C55]])
  c.C57 = standardSize(c.C56, () => (required(c.C15) * required(c.C48) * required(c.C50)) ** 2, NOT_APPLICABLE_GLOBAL)
  c.C58 = weightedDeviation([[c.C7, c.C55], [c.C48, c.C50]], c.C52)
  c.C59 = globalComputedSize(c.C15, c.C52, c.C58, c.C53, c.C54)
  c.C60 = appliedTotalSize(c.C59, limit, pending('C59'), context)
  c.C61 = share(c.C7, c.C52, c.C60)
  c.C62 = additionalUnits(c.C61, c.C34)
  c.C63 = share(c.C48, c.C52, c.C60)
  c.C64 = guard(() => underestimationFactor(c.C48, c.C8, c.C49, c.C10))
  c.C65 = guard(() => roundUp(required(c.C35) * required(c.C64)))
}

/** Zelle des Umfangs für Zeitraum 2 nach dem gewählten Ansatz (C26). */
const CHOSEN: Readonly<Record<ReturnType<typeof approachOf>, CellAddress>> = { standard: 'C57', global: 'C63', increase: 'C65', none: 'C35' }

/**
 * Abschnitt M, zweiter Teil: endgültige Umfänge und ihre Prüfung (C66–C69).
 * Liefert der gewählte Ansatz keinen Umfang (Text oder leer), bleiben in der
 * Vorlage nur die Untergrenzen; die Webfassung lässt den Umfang dann offen.
 */
function finalSizes(c: Cells, pending: Pending, limit: number | null, context: SheetContext): void {
  const approach = approachOf(c.C26)
  c.C66 = guard(() => required(c.C34) + (approach === 'global' ? required(c.C62) : 0))
  c.C67 = appliedPeriodSize(c[CHOSEN[approach]], pending(CHOSEN[approach]), context, () => minus(30, required(c.C66)))
  const total = (): number => required(c.C66) + required(c.C67)
  c.C68 = checkLimitKept(limit, total, '⚠ Umfang überschritten – Art. 5 Abs. 7 UAbs. 4 Buchst. a oder b')
  c.C69 = isNumber(c.C67) ? checkYearMinimum(total) : null
}

/**
 * Abschnitt P: Hochrechnung und Genauigkeit (C83–C86). Fehlt die
 * Standardabweichung der Stichprobe eines Zeitraums (C47, C82), rechnet die
 * Webfassung wie die Vorlage mit 0 und weist das aus (`zeroAssumed`).
 */
function projection(c: Cells, context: SheetContext): void {
  c.C83 = n(c.C45) + n(c.C80)
  c.C84 = projectionWithoutErrors(context, isNumber(c.C46) || isNumber(c.C81), guard(() => divide(required(c.C39), required(c.C79)) * n(c.C46) + divide(required(c.C73), required(c.C74)) * n(c.C81)))
  c.C85 = isNumber(c.C46) || isNumber(c.C81) ? guard(() => required(c.C83) + required(c.C84)) : null
  c.C86 = guard(
    () => required(c.C15) * squareRoot(divide(required(c.C39) ** 2, required(c.C79)) * n(c.C47) ** 2 + divide(required(c.C73) ** 2, required(c.C74)) * n(c.C82) ** 2),
  )
}

/** Alle Formelzellen in Blattreihenfolge; `pending` und `context` siehe `computeTwice`. */
function evaluate(c: Cells, pending: Pending, context: SheetContext): void {
  parameters(c, context)
  const limit = sampleSize(c, pending, context)
  selection(c, 36, c.C7, c.C34)
  recalculation(c, pending, limit, context)
  finalSizes(c, pending, limit, context)
  selection(c, 70, c.C48, c.C67)
  c.C79 = guard(() => minus(required(c.C66), n(c.C37)))
  projection(c, context)
  errorLimits(c, 85, c.C14, c.C52, c.C17)
  summary(c, 'MUS-Standardansatz, 2 Zeiträume', 85, c.C52, c.C83, () => required(c.C66) + required(c.C67))
}

const calculate = remembered((cells, context) => computeTwice(cells, REQUIRED_INPUTS, context, evaluate))

/** Berechnet alle Formelzellen des Blatts 05; Eingaben und Ergebnisse tragen die Zelladressen der Vorlage. */
export function compute(inputs: CellMap, context: SheetContext): CellMap {
  return calculate(resolveInputs(definition, inputs, context), context)
}
