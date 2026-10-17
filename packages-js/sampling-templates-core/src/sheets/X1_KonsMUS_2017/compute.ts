/**
 * Rechenkern Blatt X1_KonsMUS_2017: konservativer MUS-Ansatz der Vorlage von
 * 2017 (Template 1). Jede Zuweisung bildet die Formel der gleichnamigen Zelle
 * nach; Rundung, Mindestumfang und Rechenreihenfolge sind unverändert. Die
 * Altvorlage prüft nicht, ob der Nenner des Stichprobenumfangs positiv ist:
 * Ein negativer Nenner ergibt den Mindestumfang 30, ein Nenner von 0 keinen Wert.
 */
import { divide, minus, plus, roundUp, sum } from '../../excel/index'
import { resolveInputs } from '../../model/sheet'
import type { CellAddress, CellMap, SheetContext } from '../../model/types'
import { LEGACY_EXPANSION_FACTOR, LEGACY_MATERIALITY, LEGACY_NOTICE, LEGACY_RELIABILITY_FACTOR, LegacyCells, atLeastMinimum, levelFactor } from '../shared/legacy'
import { definition } from './definition'

/** Pflichteingaben: alle Eingaben, die eine Formel liest. */
export const MANDATORY: ReadonlySet<CellAddress> = new Set(['C1', 'C4', 'C7', 'C13', 'C14', 'C16'])

/** Abschnitt B: Faktoren, voraussichtlicher und zulässiger Fehler, Umfang und Auswahlintervall (C5–C12). */
function sampleSize(s: LegacyCells): void {
  s.set('C5', ['C4'], () => levelFactor(s.cells.C4, LEGACY_RELIABILITY_FACTOR))
  s.set('C6', ['C4'], () => levelFactor(s.cells.C4, LEGACY_EXPANSION_FACTOR))
  s.set('C8', ['C7', 'C1'], () => s.input('C7') * s.input('C1'))
  s.set('C10', ['C1'], () => s.value('C9') * s.input('C1'))
  // n = RF · BV / (TE − AE · EF), aufgerundet, mindestens 30.
  s.set('C11', ['C5', 'C1', 'C10', 'C8', 'C6'], () => atLeastMinimum(roundUp(divide(s.value('C5') * s.input('C1'), minus(s.value('C10'), s.value('C8') * s.value('C6'))))))
  s.set('C12', ['C1', 'C11'], () => divide(s.input('C1'), s.value('C11')))
}

/** Abschnitt D: Genauigkeit, Hochrechnung und obere Fehlergrenze (C15–C22). */
function projection(s: LegacyCells): void {
  s.set('C15', ['C5', 'C12'], () => s.value('C5') * s.value('C12'))
  s.set('C17', ['C15', 'C16'], () => plus(s.value('C15'), s.input('C16')))
  // Die Vorlage summiert hier über den Bereich C15:C16; eine Zelle ohne Wert zählt in der Summe nicht.
  s.set('C18', ['C15', 'C16', 'C1'], () => divide(sum([s.cells.C15, s.cells.C16]), s.input('C1')))
  s.set('C19', ['C14', 'C12', 'C13'], () => plus(s.input('C14') * s.value('C12'), s.input('C13')))
  s.set('C20', ['C19', 'C16', 'C15'], () => plus(plus(s.value('C19'), s.input('C16')), s.value('C15')))
  s.set('C21', ['C19', 'C1'], () => divide(s.value('C19'), s.input('C1')))
  s.set('C22', ['C20', 'C1'], () => divide(s.value('C20'), s.input('C1')))
}

/** Berechnet alle Formelzellen des Blatts X1; Schlüssel sind die Zelladressen der Vorlage. */
export function compute(inputs: CellMap, context: SheetContext): CellMap {
  const cells = resolveInputs(definition, inputs, context)
  cells.G1 = LEGACY_NOTICE
  cells.C9 = LEGACY_MATERIALITY
  const s = new LegacyCells(cells, MANDATORY)
  sampleSize(s)
  projection(s)
  return cells
}
