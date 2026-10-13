/**
 * Rechenkern Blatt X4_DiffSch_2Z_2017: Differenzschätzung über zwei Zeiträume
 * der Vorlage von 2017 (Template 12). Jede Zuweisung bildet die Formel der
 * gleichnamigen Zelle nach; Rundung und Rechenreihenfolge sind unverändert.
 * Die Altvorlage kennt hier keinen Mindestumfang und prüft den Nenner der
 * Neuberechnung nicht: Ein negativer Nenner ergibt einen negativen Umfang für
 * den zweiten Zeitraum, mit dem die Vorlage weiterrechnet.
 */
import { divide, isBlank, minus, plus, roundUp, squareRoot, sum } from '../../excel/index'
import { resolveInputs } from '../../model/sheet'
import type { CellAddress, CellMap, SheetContext } from '../../model/types'
import { LEGACY_MATERIALITY, LEGACY_NOTICE, LEGACY_Z, LegacyCells, levelFactor } from '../shared/legacy'
import { definition } from './definition'

/**
 * Pflichteingaben. Dazu gehört die Standardabweichung der Fehler in der
 * Stichprobe des ersten Zeitraums (C22): Sie bestimmt den neu berechneten
 * Umfang des zweiten Zeitraums (C31) und über ihn die Hochrechnung, nicht nur
 * die Genauigkeit. Nicht dazu gehört die Standardabweichung des zweiten
 * Zeitraums (C35): Fehlt sie, rechnet die Webfassung wie die Vorlage mit 0 und
 * weist das aus (`zeroAssumed`). Die Fehler der Stichproben (C21, C34) sind
 * Pflichteingaben, solange keiner von beiden eingetragen ist; trägt ein
 * Zeitraum einen, zählt der fehlende des anderen wie in der Vorlage 0 und wird
 * ausgewiesen (`zeroAssumed`, `partialErrorSum`).
 */
export const MANDATORY: ReadonlySet<CellAddress> = new Set(['C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C10', 'C12', 'C21', 'C22', 'C23', 'C25', 'C26', 'C27', 'C34'])

/** Gewichtetes Mittel der Varianzen: N₁/(N₁+N₂) · σ₁² + N₂/(N₁+N₂) · σ₂² (in C9 und noch einmal in C16). */
function weightedVariance(s: LegacyCells): number {
  const units = (): number => sum([s.cells.C5, s.cells.C6])
  return divide(s.input('C5'), units()) * s.input('C7') ** 2 + divide(s.input('C6'), units()) * s.input('C8') ** 2
}

/** Abschnitte A und B: Planung des ersten Zeitraums (C1–C18). */
function firstPeriod(s: LegacyCells): void {
  const variance = ['C5', 'C6', 'C7', 'C8']
  s.set('C1', ['C3', 'C4'], () => sum([s.cells.C3, s.cells.C4]))
  s.set('C9', variance, () => weightedVariance(s))
  s.set('C11', ['C10'], () => levelFactor(s.cells.C10, LEGACY_Z))
  s.set('C13', ['C12', 'C1'], () => s.input('C12') * s.value('C1'))
  s.set('C15', ['C1'], () => s.value('C14') * s.value('C1'))
  // n = ((N₁ + N₂) · z · √Varianz / (TE − AE))², aufgerundet; kein Mindestumfang.
  s.set('C16', [...variance, 'C11', 'C15', 'C13'], () =>
    roundUp(divide(plus(s.input('C5'), s.input('C6')) * s.value('C11') * squareRoot(weightedVariance(s)), minus(s.value('C15'), s.value('C13'))) ** 2),
  )
  s.set('C17', ['C5', 'C6', 'C16'], () => roundUp(divide(s.input('C5'), plus(s.input('C5'), s.input('C6'))) * s.value('C16')))
  s.set('C18', ['C16', 'C17'], () => minus(s.value('C16'), s.value('C17')))
}

/** Abschnitt D: Neuberechnung des Umfangs für den zweiten Zeitraum (C24–C31). */
function secondPeriod(s: LegacyCells): void {
  s.set('C24', ['C25', 'C3'], () => plus(s.input('C25'), s.input('C3')))
  s.set('C28', ['C27', 'C24'], () => s.input('C27') * s.value('C24'))
  s.set('C30', ['C24'], () => s.value('C29') * s.value('C24'))
  // n₂ = (z · N₂ · σ₂)² / ((TE − AE)² − z² · (N₁² / n₁) · s₁²), aufgerundet.
  s.set('C31', ['C11', 'C26', 'C23', 'C30', 'C28', 'C5', 'C17', 'C22'], () => {
    const spread = s.value('C11') ** 2 * divide(s.input('C5') ** 2, s.value('C17')) * s.input('C22') ** 2
    return roundUp(divide((s.value('C11') * s.input('C26') * s.input('C23')) ** 2, minus(minus(s.value('C30'), s.value('C28')) ** 2, spread)))
  })
}

/** Abschnitt E: Hochrechnung, Genauigkeit und Grenzen (C36–C43). */
function projection(s: LegacyCells): void {
  // Fehler der Stichproben: Pflichteingabe, solange keiner eingetragen ist; sonst zählt der fehlende 0.
  const errors = isBlank(s.cells.C21) && isBlank(s.cells.C34) ? ['C21', 'C34'] : []
  s.set('C36', [...errors, 'C17', 'C5', 'C31', 'C26'], () => plus(divide(s.input('C21'), s.value('C17')) * s.input('C5'), divide(s.input('C34'), s.value('C31')) * s.input('C26')))
  s.set('C37', ['C36', 'C24'], () => divide(s.value('C36'), s.value('C24')))
  s.set('C38', ['C24', 'C36'], () => minus(s.value('C24'), s.value('C36')))
  s.set('C39', ['C11', 'C5', 'C22', 'C17', 'C26', 'C35', 'C31'], () => {
    const first = divide(s.input('C5') ** 2 * s.input('C22') ** 2, s.value('C17'))
    const second = divide(s.input('C26') ** 2 * s.input('C35') ** 2, s.value('C31'))
    return s.value('C11') * squareRoot(plus(first, second))
  })
  s.set('C40', ['C39', 'C24'], () => divide(s.value('C39'), s.value('C24')))
  s.set('C41', ['C36', 'C39', 'C24'], () => divide(plus(s.value('C36'), s.value('C39')), s.value('C24')))
  s.set('C42', ['C38', 'C39'], () => minus(s.value('C38'), s.value('C39')))
  s.set('C43', ['C24', 'C30'], () => minus(s.value('C24'), s.value('C30')))
}

/** Berechnet alle Formelzellen des Blatts X4; Schlüssel sind die Zelladressen der Vorlage. */
export function compute(inputs: CellMap, context: SheetContext): CellMap {
  const cells = resolveInputs(definition, inputs, context)
  cells.F1 = LEGACY_NOTICE
  cells.C14 = LEGACY_MATERIALITY
  cells.C29 = LEGACY_MATERIALITY
  const s = new LegacyCells(cells, MANDATORY)
  firstPeriod(s)
  secondPeriod(s)
  projection(s)
  return cells
}
