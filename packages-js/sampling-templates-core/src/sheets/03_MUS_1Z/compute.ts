/**
 * Rechenkern Blatt 03_MUS_1Z: MUS-Standardansatz, ein Stichprobenzeitraum,
 * nicht geschichtet (Anhang II Nr. 1.1 DelVO (EU) 2023/67). Jede Zuweisung
 * bildet die Formel der gleichnamigen Zelle der Vorlage nach; Rundung,
 * Schwellen und Rechenreihenfolge sind unverändert.
 */
import { divide, guard, isNumber, minus, n, required, squareRoot } from '../../excel/index'
import { resolveInputs } from '../../model/sheet'
import type { CellMap, Cells, SheetContext } from '../../model/types'
import { zValue } from '../01_Parameter/index'
import {
  appliedSampleSize,
  assessment,
  checkConfidence,
  checkIteration,
  checkMateriality,
  checkMinimumUnits,
  checkTolerableError,
  computedSampleSize,
  isSizePending,
  limitedSampleSize,
  lowerErrorLimit,
} from '../shared/statistical'
import { definition } from './definition'

/** Abschnitt I: z, zulässiger und voraussichtlicher Fehler (C12–C19). */
function parameters(c: Cells, context: SheetContext): void {
  c.C12 = guard(() => zValue(context.parameters, c.C10, c.C11))
  c.C13 = checkConfidence(c.C9, c.C10)
  c.C15 = checkMateriality(c.C14)
  c.C16 = guard(() => required(c.C14) * required(c.C7))
  c.C18 = guard(() => required(c.C17) * required(c.C7))
  c.C19 = checkTolerableError(c.C16, c.C18, c.C17)
}

/**
 * Abschnitt J: rechnerischer, begrenzter und anzuwendender Stichprobenumfang
 * (C21–C27). Fehlt die voraussichtliche Fehlerquote oder Standardabweichung,
 * rechnet die Vorlage mit 0 weiter und zeigt einen Umfang; die Webfassung
 * zeigt dann „Angabe fehlt“ – auch beim anzuwendenden Umfang (docs/abweichungen.md).
 */
function sampleSize(c: Cells): void {
  c.C21 = computedSampleSize({ z: c.C12, bookValue: c.C7, deviation: c.C20, tolerable: c.C16, anticipated: c.C18 })
  const [check, limit] = limitedSampleSize(c.C24, c.C23, c.C22)
  c.C25 = check
  c.C26 = limit
  c.C27 = appliedSampleSize(c.C21, limit, isSizePending(c.C21, c.C16, c.C12))
}

/** Abschnitt K: Grenzwert, Zufallsschicht und Auswahlintervall (C28–C36). */
function selection(c: Cells): void {
  c.C28 = guard(() => divide(required(c.C7), required(c.C27)))
  c.C31 = guard(() => minus(required(c.C7), n(c.C30)))
  c.C32 = guard(() => minus(required(c.C27), n(c.C29)))
  c.C33 = checkMinimumUnits(c.C32)
  c.C34 = guard(() => divide(required(c.C31), required(c.C32)))
  c.C36 = checkIteration(c.C35)
}

/** Abschnitt M: Hochrechnung, Genauigkeit und Fehlergrenzen (C40–C51). */
function projection(c: Cells): void {
  c.C40 = n(c.C37)
  c.C41 = guard(() => required(c.C34) * n(c.C38))
  c.C42 = isNumber(c.C38) ? guard(() => n(c.C40) + required(c.C41)) : null
  c.C43 = guard(() => divide(required(c.C12) * required(c.C31), squareRoot(required(c.C32))) * n(c.C39))
  c.C46 = guard(() => required(c.C42) + required(c.C43) + n(c.C44) + n(c.C45))
  c.C47 = lowerErrorLimit(c.C11, c.C42, c.C43, c.C44, c.C45)
  c.C48 = guard(() => divide(required(c.C43), required(c.C7)))
  c.C49 = guard(() => divide(required(c.C42), required(c.C7)))
  c.C50 = guard(() => divide(required(c.C42) + n(c.C44) + n(c.C45), required(c.C7)))
  c.C51 = guard(() => divide(required(c.C46), required(c.C7)))
}

/** Ergebnisübersicht für Blatt 18 (feste Zellen N3–N11). */
function summary(c: Cells): void {
  c.N3 = 'MUS-Standardansatz, 1 Zeitraum'
  c.N4 = c.C7 ?? null
  c.N5 = c.C42 ?? null
  c.N6 = c.C40 ?? null
  c.N7 = c.C43 ?? null
  c.N8 = n(c.C44)
  c.N9 = n(c.C45)
  c.N10 = c.C27 ?? null
  c.N11 = c.C50 ?? null
}

/** Berechnet alle Formelzellen des Blatts 03; Eingaben und Ergebnisse tragen die Zelladressen der Vorlage. */
export function compute(inputs: CellMap, context: SheetContext): CellMap {
  const c = resolveInputs(definition, inputs, context)
  parameters(c, context)
  sampleSize(c)
  selection(c)
  projection(c)
  c.C52 = assessment(c.C50, c.C51, c.C14)
  summary(c)
  return c
}
