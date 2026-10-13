/**
 * Rechenkern Blatt X3_DiffSch_S_2017: geschichtete Differenzschätzung der
 * Vorlage von 2017 (Template 11). Jede Zuweisung bildet die Formel der
 * gleichnamigen Zelle nach; Rundung, Mindestumfang und Rechenreihenfolge sind
 * unverändert. Die Schichten stehen in den Spalten E–K (Webfassung: zusätzlich
 * AA–AM), die Werte des Blatts in Spalte D.
 *
 * Eine Schicht gilt als belegt, sobald Buchwert, Umfang oder die
 * Standardabweichung der Planung eingetragen ist; dann sind alle drei
 * Pflichtangaben. Für eine nicht belegte Schicht liefert die Vorlage den
 * Umfang 0 (Zeile 17) und sonst keinen Wert – die Webfassung ebenso.
 *
 * Fehlende Angaben (`model/policy.ts`): Die Summen D1, D3 und D23 zeigen in der
 * Vorlage 0, wenn keine Schicht einen Wert trägt; die Webfassung lässt sie
 * offen (`totalRow`), und alles, was darauf aufbaut, ebenso. Der Fehler der
 * Stichprobe (Zeile 19) ist Pflichtangabe, solange keine belegte Schicht einen
 * trägt; trägt eine Schicht einen, zählt der fehlende einer anderen wie in der
 * Vorlage 0 und wird ausgewiesen (`zeroAssumed`, `partialErrorSum`).
 */
import { divide, isBlank, minus, plus, roundUp, squareRoot, sum } from '../../excel/index'
import { resolveInputs } from '../../model/sheet'
import { stratumCell as at, totalRow } from '../../model/strata'
import type { CellAddress, CellMap, CellValue, SheetContext } from '../../model/types'
import { LEGACY_MATERIALITY, LEGACY_NOTICE, LEGACY_STRATA, LEGACY_Z, LegacyCells, atLeastMinimum, levelFactor } from '../shared/legacy'
import { definition } from './definition'

/** Zeilen der Schichteingaben: Buchwert, Umfang, σ der Planung, Fehler der Stichprobe. */
const BOOK_VALUE = 6
const UNITS = 7
const DEVIATION = 8
const ERRORS = 19
/** Standardabweichung der Stichprobe: keine Pflichtangabe, fehlend mit 0 gerechnet (`zeroAssumed`). */
const SAMPLE_DEVIATION = 21

const row = (number: number, columns: readonly string[] = LEGACY_STRATA): CellAddress[] => columns.map((column) => at(column, number))

/** Pflichteingaben; für die Schichtzeilen zählen nur die Zellen belegter Schichten (siehe `Strata`). */
export const MANDATORY: ReadonlySet<CellAddress> = new Set(['D9', 'D11', ...row(BOOK_VALUE), ...row(UNITS), ...row(DEVIATION), ...row(ERRORS)])

/** Belegte Schichten: Buchwert, Umfang oder σ der Planung ist eingetragen. */
export function usedStrata(cells: CellMap): string[] {
  return LEGACY_STRATA.filter((column) => [BOOK_VALUE, UNITS, DEVIATION].some((line) => !isBlank(cells[at(column, line)])))
}

interface Strata {
  s: LegacyCells
  /** Spalten der belegten Schichten. */
  used: readonly string[]
  /** Zellen einer Zeile in den belegten Schichten. */
  cellsOf: (line: number) => CellAddress[]
  /** Summe einer Zeile über alle Schichtspalten; Zellen ohne Wert zählen nicht. */
  total: (line: number) => number
  /** Angezeigte Summe einer Zeile: offen, wenn keine Schicht einen Wert trägt (die Vorlage zeigt dann 0). */
  shown: (line: number) => CellValue
  /** Trägt mindestens eine belegte Schicht einen Fehler der Stichprobe (Zeile 19)? */
  errorsGiven: boolean
}

/** Gewichtete Summe der Varianzen: Σ N_h / N · σ_h², mit den Angaben der Zeile `line`. */
function weighted(strata: Strata, units: number, line: number): number {
  return LEGACY_STRATA.reduce((total, column) => total + divide(strata.s.input(at(column, UNITS)), units) * strata.s.input(at(column, line)) ** 2, 0)
}

/** Abschnitte A und B: Summen, z, Fehlerbeträge und Stichprobenumfang (D1–D15). */
function sampleSize(strata: Strata): void {
  const { s } = strata
  s.set('D1', strata.cellsOf(BOOK_VALUE), () => strata.shown(BOOK_VALUE))
  s.set('D3', strata.cellsOf(UNITS), () => strata.shown(UNITS))
  s.set('D4', ['D3', ...strata.cellsOf(DEVIATION)], () => weighted(strata, s.value('D3'), DEVIATION))
  s.set('D10', ['D9'], () => levelFactor(s.cells.D9, LEGACY_Z))
  s.set('D12', ['D11', 'D1'], () => s.input('D11') * s.value('D1'))
  s.set('D14', ['D1'], () => s.value('D13') * s.value('D1'))
  // n = (N · z · √Varianz / (TE − AE))², aufgerundet, mindestens 30.
  s.set('D15', ['D3', 'D10', 'D4', 'D14', 'D12'], () => atLeastMinimum(roundUp(divide(s.value('D3') * s.value('D10') * squareRoot(s.value('D4')), minus(s.value('D14'), s.value('D12'))) ** 2)))
}

/** Schichtzeilen 17, 20 und 22: Umfang, mittlerer Fehler und hochgerechneter Fehler je Schicht. */
function strataRows(strata: Strata): void {
  const { s } = strata
  for (const column of LEGACY_STRATA) {
    // Fehler der Stichprobe: Pflichtangabe der belegten Schicht, solange keine Schicht einen trägt; sonst zählt der fehlende 0.
    const own = strata.used.includes(column) && !strata.errorsGiven ? [at(column, ERRORS)] : []
    s.set(at(column, 17), ['D15', 'D3'], () => roundUp(divide(s.value('D15') * s.input(at(column, UNITS)), s.value('D3'))))
    s.set(at(column, 20), [...own, at(column, 17)], () => divide(s.input(at(column, ERRORS)), s.value(at(column, 17))))
    s.set(at(column, 22), [at(column, 20)], () => s.value(at(column, 20)) * s.input(at(column, UNITS)))
  }
}

/** Abschnitt C: Hochrechnung, Genauigkeit und Grenzen (D23–D30). */
function projection(strata: Strata): void {
  const { s } = strata
  s.set('D23', strata.cellsOf(22), () => strata.shown(22))
  s.set('D24', ['D23', 'D1'], () => divide(s.value('D23'), s.value('D1')))
  s.set('D25', ['D1', 'D23'], () => minus(s.value('D1'), s.value('D23')))
  // SE = N · z · √(Σ N_h / N · s_h²) / √Σn_h; N ist hier die Summe der Zeile 7.
  s.set('D26', ['D3', 'D10', ...row(17)], () => {
    const units = strata.total(UNITS)
    return divide(units * s.value('D10') * squareRoot(weighted(strata, units, SAMPLE_DEVIATION)), squareRoot(strata.total(17)))
  })
  s.set('D27', ['D26', 'D1'], () => divide(s.value('D26'), s.value('D1')))
  s.set('D28', ['D23', 'D26', 'D1'], () => divide(plus(s.value('D23'), s.value('D26')), s.value('D1')))
  s.set('D29', ['D25', 'D26'], () => minus(s.value('D25'), s.value('D26')))
  s.set('D30', ['D1', 'D14'], () => minus(s.value('D1'), s.value('D14')))
}

/** Berechnet alle Formelzellen des Blatts X3; Schlüssel sind die Zelladressen der Vorlage. */
export function compute(inputs: CellMap, context: SheetContext): CellMap {
  const cells = resolveInputs(definition, inputs, context)
  cells.M1 = LEGACY_NOTICE
  cells.D13 = LEGACY_MATERIALITY
  const used = usedStrata(cells)
  const strata: Strata = {
    s: new LegacyCells(cells, MANDATORY),
    used,
    cellsOf: (line) => row(line, used),
    total: (line) => sum(row(line).map((cell) => cells[cell])),
    shown: (line) => totalRow(cells, line, context, LEGACY_STRATA),
    errorsGiven: used.some((column) => !isBlank(cells[at(column, ERRORS)])),
  }
  sampleSize(strata)
  strataRows(strata)
  projection(strata)
  return cells
}
