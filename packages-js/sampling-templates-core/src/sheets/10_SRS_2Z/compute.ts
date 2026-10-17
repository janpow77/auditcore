/**
 * Rechenkern Blatt 10_SRS_2Z: einfaches Zufallsstichprobenverfahren mit
 * Verhältnisschätzung, zwei Stichprobenzeiträume, nicht geschichtet (Anhang II
 * Nr. 2.2 DelVO (EU) 2023/67). Jede Zuweisung bildet die Formel der
 * gleichnamigen Zelle der Vorlage nach; Rundung, Schwellen und
 * Rechenreihenfolge sind unverändert.
 */
import { divide, guard, isBlank, isNumber, le, minus, n, required, roundUp, squareRoot } from '../../excel/index'
import { unfounded } from '../../model/policy'
import { resolveInputs } from '../../model/sheet'
import type { CellAddress, CellMap, Cells, SheetContext } from '../../model/types'
import { zValue } from '../01_Parameter/index'
import { type Pending, type Recalculation, additionalUnits, appliedRandomSize, checkAnnualMinimum, checkLimitKept, computeBesideTemplate, conclusion, globalComputedSize, increasedSize, minimumRandomSize, netLimitedSize, NOT_APPLICABLE, periodSize, ratioProjection, recalculationOf, share, summary, weightedDeviation } from '../shared/srs'
import { checkConfidence, checkMateriality, checkTolerableError, computedSampleSize, limitedSampleSize } from '../shared/statistical'
import { definition } from './definition'

/**
 * Eingaben, mit denen die Vorlage leer als 0 weiterrechnet; die Webfassung
 * zeigt in den abhängigen Zellen „Angabe fehlt“ (deviations.ts).
 */
export const REQUIRED_INPUTS: readonly CellAddress[] = ['C7', 'C8', 'C14', 'C15', 'C23', 'C26', 'C29', 'C30', 'C49', 'C50', 'C56']

/** Text der Vorlage in C63 bei nicht positivem Nenner. */
export const NOT_APPLICABLE_GLOBAL = `${NOT_APPLICABLE} – globale Neuberechnung`

/** Abschnitt H: Zufallsschicht des Zeitraums 1 und Prognose für das Geschäftsjahr (C12–C17). */
function population(c: Cells): void {
  c.C12 = guard(() => minus(required(c.C7), n(c.C9)))
  c.C13 = guard(() => minus(required(c.C8), n(c.C10)))
  c.C16 = guard(() => required(c.C7) + required(c.C14))
  c.C17 = guard(() => required(c.C13) + required(c.C15))
}

/** Abschnitt I: z, zulässiger und voraussichtlicher Fehler, gewichtete Standardabweichung (C21–C31). */
function parameters(c: Cells, context: SheetContext): void {
  c.C21 = guard(() => zValue(context.parameters, c.C19, c.C20))
  c.C22 = checkConfidence(c.C18, c.C19)
  c.C24 = checkMateriality(c.C23)
  c.C25 = guard(() => required(c.C23) * required(c.C16))
  c.C27 = guard(() => required(c.C26) * required(c.C16))
  c.C28 = checkTolerableError(c.C25, c.C27, c.C26)
  c.C31 = weightedDeviation([[c.C13, c.C29], [c.C15, c.C30]], c.C17)
}

/**
 * Abschnitt J: Gesamtumfang und Aufteilung auf die Zeiträume (C33–C43).
 * Die Formel in C33 lautet (z · N₁₊₂ · σ_ew / (TE − AE))²; `computedSampleSize`
 * multipliziert in dieser Reihenfolge.
 */
function sampleSize(c: Cells, pending: Pending): void {
  c.C33 = computedSampleSize({ z: c.C21, bookValue: c.C17, deviation: c.C31, tolerable: c.C25, anticipated: c.C27 })
  const [check, limit] = limitedSampleSize(c.C36, c.C35, c.C34)
  c.C37 = check
  c.C38 = limit
  c.C39 = minimumRandomSize(6, c.C10)
  c.C40 = netLimitedSize(limit, c.C11)
  c.C41 = appliedRandomSize(c.C33, c.C39, c.C40, pending('C33'))
  c.C42 = share(c.C13, c.C17, c.C41)
  c.C43 = share(c.C15, c.C17, c.C41)
}

/** Abschnitt L, erster Teil: Ist-Werte des Zeitraums 2, aktualisierte Fehler, Standardneuberechnung (C54–C63). */
function standardRecalculation(c: Cells): void {
  c.C54 = guard(() => minus(required(c.C49), n(c.C51)))
  c.C55 = guard(() => minus(required(c.C50), n(c.C52)))
  c.C58 = guard(() => required(c.C7) + required(c.C49))
  c.C59 = guard(() => required(c.C23) * required(c.C58))
  // =IF(C57="";C26;C57)*C58 – leer = Wert aus I.
  c.C60 = guard(() => required(isBlank(c.C57) ? c.C26 : c.C57) * required(c.C58))
  // =IF(C46="";C29;C46) – leer = ersatzweise die voraussichtliche Standardabweichung.
  c.C61 = (isBlank(c.C46) ? c.C29 : c.C46) ?? null
  // =(C59-C60)^2-C21^2*C13^2/C42*C61^2
  c.C62 = guard(() => minus(minus(required(c.C59), required(c.C60)) ** 2, divide(required(c.C21) ** 2 * required(c.C13) ** 2, required(c.C42)) * required(c.C61) ** 2))
  // =IF(C62<=0;"✖ …";ROUNDUP((C21*C55*C56)^2/C62;0))
  c.C63 = guard(() => (le(required(c.C62), 0) ? NOT_APPLICABLE_GLOBAL : roundUp(divide((required(c.C21) * required(c.C55) * required(c.C56)) ** 2, required(c.C62)))))
}

/**
 * Abschnitt L, zweiter Teil: globale Neuberechnung und Erhöhung bei begrenztem Umfang (C64–C71).
 * Anders als in C33 prüft die Vorlage in C66 nicht auf TE ≤ AE.
 */
function globalRecalculation(c: Cells, pending: Pending): void {
  c.C64 = guard(() => required(c.C13) + required(c.C55))
  c.C65 = weightedDeviation([[c.C13, c.C61], [c.C55, c.C56]], c.C64)
  c.C66 = globalComputedSize(c.C21, c.C64, c.C65, c.C59, c.C60)
  c.C67 = netLimitedSize(c.C38, c.C11, c.C53)
  c.C68 = appliedRandomSize(c.C66, minimumRandomSize(6, c.C10, c.C52), c.C67, pending('C66'))
  c.C69 = additionalUnits(c.C13, c.C64, c.C68, c.C42)
  c.C70 = share(c.C55, c.C64, c.C68)
  c.C71 = guard(() => increasedSize(c.C43, [[c.C49, c.C14], [c.C55, c.C15]]))
}

/** Zelle des Umfangs für Zeitraum 2 nach dem gewählten Ansatz (C32). */
const CHOSEN: Readonly<Record<Recalculation, CellAddress>> = { standard: 'C63', global: 'C70', increase: 'C71', none: 'C43' }

/**
 * Abschnitt L, dritter Teil: endgültige Umfänge und ihre Prüfung (C72–C76).
 *
 * C73 = MAX(gewählter Umfang; 3; 30 − n₁ − N(N_e1) − N(N_e2)). Der gewählte
 * Umfang ist ein Bezug: Steht dort der Text „✖ nicht anwendbar …“ (Nenner ≤ 0)
 * oder nichts, übergeht `MAX` ihn, und es bleiben die Untergrenzen – gemessen
 * mit den Fällen „Negativer Nenner …“. Fehlt der gewählte Umfang nur, weil eine
 * Angabe fehlt, bleibt C73 offen; fehlt er ganz, ohne dass der Ansatz „nicht
 * anwendbar“ ist, sind die Untergrenzen ein Wert ohne Grundlage (`periodSize`).
 */
function finalSizes(c: Cells, pending: Pending, context: SheetContext): void {
  const approach = recalculationOf(c.C32)
  const chosen = c[CHOSEN[approach]]
  c.C72 = guard(() => required(c.C42) + (approach === 'global' ? required(c.C69) : 0))
  c.C73 = periodSize(chosen, { open: pending(CHOSEN[approach]), notApplicable: typeof chosen === 'string' }, context, () => minus(minus(minus(30, required(c.C72)), n(c.C10)), n(c.C52)))
  c.C74 = guard(() => required(c.C72) + required(c.C73) + n(c.C10) + n(c.C52))
  c.C75 = isNumber(c.C73) ? guard(() => checkAnnualMinimum(required(c.C74))) : null
  const limit = c.C38
  c.C76 = isNumber(limit) ? guard(() => checkLimitKept(required(c.C72) + required(c.C73) + n(c.C11) + n(c.C53), limit)) : null
}

/**
 * Abschnitt N: Hochrechnung und Genauigkeit (C82–C85). Fehlt die
 * Standardabweichung der Variablen q eines Zeitraums (C47, C80) oder die
 * Fehlersumme eines von zwei Zeiträumen (C45, C78), rechnet die Webfassung wie
 * die Vorlage mit 0 und weist das aus (`zeroAssumed`). Trägt kein Zeitraum eine
 * Fehlersumme, ist die Hochrechnung 0 der Vorlage ein Wert ohne Grundlage.
 */
function projection(c: Cells, context: SheetContext): void {
  const anyErrorSum = isNumber(c.C45) || isNumber(c.C78)
  const projected = guard(() => ratioProjection(c.C12, c.C45, c.C44) + ratioProjection(c.C54, c.C78, c.C77))
  c.C82 = n(c.C48) + n(c.C81)
  c.C83 = anyErrorSum ? projected : unfounded(context, projected)
  c.C84 = anyErrorSum ? guard(() => required(c.C82) + required(c.C83)) : null
  // =C21*SQRT(C13^2*C47^2/C72+C55^2*C80^2/C73)
  c.C85 = guard(() => required(c.C21) * squareRoot(divide(required(c.C13) ** 2 * n(c.C47) ** 2, required(c.C72)) + divide(required(c.C55) ** 2 * n(c.C80) ** 2, required(c.C73))))
}

/** Alle Formelzellen in Blattreihenfolge; `pending` siehe `computeBesideTemplate`. */
function evaluate(c: Cells, pending: Pending, context: SheetContext): void {
  population(c)
  parameters(c, context)
  sampleSize(c, pending)
  standardRecalculation(c)
  globalRecalculation(c, pending)
  finalSizes(c, pending, context)
  projection(c, context)
  conclusion(c, 84, { bookValue: 'C58', testType: 'C20', materiality: 'C23' }, pending('C85'))
  summary(c, { method: 'Einfaches Zufallsstichprobenverfahren, 2 Zeiträume', bookValue: 'C58', first: 84, exhaustive: 'C82', sampleSize: c.C74 })
}

/** Berechnet alle Formelzellen des Blatts 10; Eingaben und Ergebnisse tragen die Zelladressen der Vorlage. */
export function compute(inputs: CellMap, context: SheetContext): CellMap {
  return computeBesideTemplate(resolveInputs(definition, inputs, context), REQUIRED_INPUTS, context, evaluate)
}
