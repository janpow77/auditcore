/**
 * Rechenkern Blatt X2_DiffSch_2017: Differenzschätzung der Vorlage von 2017
 * (Template 10). Jede Zuweisung bildet die Formel der gleichnamigen Zelle
 * nach; Rundung, Mindestumfang und Rechenreihenfolge sind unverändert. Die
 * Altvorlage prüft nicht, ob TE größer als AE ist: Der Nenner wird quadriert,
 * sodass auch ein negativer Nenner einen Umfang ergibt.
 */
import { divide, minus, plus, roundUp, squareRoot } from '../../excel/index'
import { resolveInputs } from '../../model/sheet'
import type { CellAddress, CellMap, SheetContext } from '../../model/types'
import { LEGACY_MATERIALITY, LEGACY_NOTICE, LEGACY_Z, LegacyCells, atLeastMinimum, levelFactor } from '../shared/legacy'
import { definition } from './definition'

/**
 * Pflichteingaben. Die Standardabweichung der Fehler in der Stichprobe (C15)
 * gehört nicht dazu: Fehlt sie, rechnet die Webfassung wie die Vorlage mit 0
 * und weist das aus (`zeroAssumed`).
 */
export const MANDATORY: ReadonlySet<CellAddress> = new Set(['C1', 'C3', 'C4', 'C5', 'C7', 'C13'])

/** Abschnitt B: z, voraussichtlicher und zulässiger Fehler, Stichprobenumfang (C6–C11). */
function sampleSize(s: LegacyCells): void {
  s.set('C6', ['C5'], () => levelFactor(s.cells.C5, LEGACY_Z))
  s.set('C8', ['C7', 'C1'], () => s.input('C7') * s.input('C1'))
  s.set('C10', ['C1'], () => s.value('C9') * s.input('C1'))
  // n = (N · z · σ_e / (TE − AE))², aufgerundet, mindestens 30.
  s.set('C11', ['C3', 'C6', 'C4', 'C10', 'C8'], () => atLeastMinimum(roundUp(divide(s.input('C3') * s.value('C6') * s.input('C4'), minus(s.value('C10'), s.value('C8'))) ** 2)))
}

/** Abschnitte C und D: mittlerer Fehler, Hochrechnung, Genauigkeit und Grenzen (C14–C23). */
function projection(s: LegacyCells): void {
  s.set('C14', ['C13', 'C11'], () => divide(s.input('C13'), s.value('C11')))
  s.set('C16', ['C14', 'C3'], () => s.value('C14') * s.input('C3'))
  s.set('C17', ['C16', 'C1'], () => divide(s.value('C16'), s.input('C1')))
  s.set('C18', ['C1', 'C16'], () => minus(s.input('C1'), s.value('C16')))
  s.set('C19', ['C3', 'C6', 'C15', 'C11'], () => divide(s.input('C3') * s.value('C6') * s.input('C15'), squareRoot(s.value('C11'))))
  s.set('C20', ['C19', 'C1'], () => divide(s.value('C19'), s.input('C1')))
  s.set('C21', ['C16', 'C19', 'C1'], () => divide(plus(s.value('C16'), s.value('C19')), s.input('C1')))
  s.set('C22', ['C18', 'C19'], () => minus(s.value('C18'), s.value('C19')))
  s.set('C23', ['C1', 'C10'], () => minus(s.input('C1'), s.value('C10')))
}

/** Berechnet alle Formelzellen des Blatts X2; Schlüssel sind die Zelladressen der Vorlage. */
export function compute(inputs: CellMap, context: SheetContext): CellMap {
  const cells = resolveInputs(definition, inputs, context)
  cells.E1 = LEGACY_NOTICE
  cells.C9 = LEGACY_MATERIALITY
  const s = new LegacyCells(cells, MANDATORY)
  sampleSize(s)
  projection(s)
  return cells
}
