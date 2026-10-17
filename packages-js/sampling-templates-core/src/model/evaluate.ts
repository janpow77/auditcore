/**
 * Auswertung eines Blatts unter der Richtlinie für fehlende Angaben
 * (`policy.ts`): Rechenkern, danach je Fallart „Angabe fehlt“ oder „mit 0
 * berechnet“. Arbeitsstand, Anzeige, Export und Abgleich rechnen hierüber.
 */
import { isBlank } from '../excel/index'
import { inputFields, rowNumber, strataColumnsOf } from './definition'
import { silentInputs } from './dependence'
import { policyOf } from './policy'
import { isEmptyReference, type AvailableSheet, type ZeroAssumption } from './sheet'
import type { CellAddress, CellMap, CellValue, Cells, Deviation, MissingPolicy, SheetContext, SheetId } from './types'

/** Ergebnis der Auswertung eines Blatts. */
export interface SheetEvaluation {
  /** Zellwerte, wie die Webfassung sie zeigt. */
  cells: CellMap
  /** Fehlende Eingaben, mit denen als 0 gerechnet wurde, samt der betroffenen Zellen. */
  assumed: readonly ZeroAssumption[]
  /** Offene Zelle → fehlende Eingaben („Angabe fehlt“). */
  lacking: ReadonlyMap<CellAddress, readonly string[]>
  /**
   * Zellen, die bei vollständigen Pflichteingaben den Wert der Vorlage zeigen,
   * obwohl ihm die Grundlage fehlt (z. B. „✔ ≥ 3“ ohne Umfang bei „TE ≤ AE“).
   * Die Anzeige kennzeichnet sie; unterdrückt wird nichts.
   */
  withoutBasis: readonly CellAddress[]
  /**
   * Stille Lücken: leere, nicht freiwillige Eingaben, von denen ein gezeigtes
   * Ergebnis abhängt, ohne dass die Vorlage es zeigt (`model/dependence.ts`).
   * Nur mit `notes` ermittelt.
   */
  silent: readonly CellAddress[]
  /** Alle Pflichteingaben des Blatts und der Blätter, aus denen es Werte bezieht, sind vorhanden. */
  complete: boolean
}

/** Rechnet das Blatt noch einmal; die genannten leeren Eingaben zählen dabei wie in der Vorlage als 0. */
export function computeWithZeros(sheet: AvailableSheet, inputs: CellMap, references: readonly string[], context: SheetContext): CellMap {
  const own: Cells = { ...inputs }
  const sheets: Record<SheetId, CellMap> = { ...context.sheets }
  for (const reference of references) {
    if (!reference.includes('!')) own[reference] = 0
    else {
      const [name, cell] = reference.split('!') as [string, string]
      sheets[name] = { ...sheets[name], [cell]: 0 }
    }
  }
  return sheet.compute(own, { ...context, sheets })
}

/** Abweichungen des Blatts je Zelle (nur Pflichteingaben; Prüfhinweise ohne Grundlage regelt der Rechenkern). */
const byCell = new WeakMap<AvailableSheet, Map<CellAddress, Deviation[]>>()

function requiredEntries(sheet: AvailableSheet): Map<CellAddress, Deviation[]> {
  let cells = byCell.get(sheet)
  if (!cells) {
    cells = new Map()
    for (const entry of sheet.deviations) {
      if ((entry.kind ?? 'requiredInput') !== 'requiredInput') continue
      const list = cells.get(entry.cell)
      if (list) list.push(entry)
      else cells.set(entry.cell, [entry])
    }
    byCell.set(sheet, cells)
  }
  return cells
}

/** Offene Zellen mit ihren leeren Pflichteingaben und dem Wert, den die Vorlage dort zeigt. */
function openCells(sheet: AvailableSheet, inputs: CellMap, base: CellMap, context: SheetContext): { cell: CellAddress; inputs: string[]; shown: CellValue }[] {
  const runs = new Map<string, CellMap>()
  const open: { cell: CellAddress; inputs: string[]; shown: CellValue }[] = []
  for (const [cell, entries] of requiredEntries(sheet)) {
    if (!isBlank(base[cell])) continue
    const empty = [...new Set(entries.flatMap((entry) => entry.whenEmpty.filter((reference) => isEmptyReference(reference, base, context.sheets))))]
    if (empty.length === 0) continue
    const key = empty.join('|')
    const run = runs.get(key) ?? computeWithZeros(sheet, inputs, empty, context)
    runs.set(key, run)
    const shown = run[cell] ?? null
    // Zeigt auch die Vorlage nichts, fehlt hier keine Angabe.
    if (!isBlank(shown)) open.push({ cell, inputs: empty, shown })
  }
  return open
}

function merge(assumed: ZeroAssumption[], input: CellAddress, cell: CellAddress): void {
  const existing = assumed.find((entry) => entry.input === input && entry.kind === 'requiredInput')
  if (existing) (existing.cells as CellAddress[]).push(cell)
  else assumed.push({ input, cells: [cell], kind: 'requiredInput' })
}

/**
 * Fehlende Eingaben für die Anzeige: Bei Schichtzeilen nennt `whenEmpty` die
 * Zellen aller Schichtspalten. Genannt werden nur die belegter Schichten
 * (Spalten, in denen irgendeine Eingabe steht); ist keine Schicht belegt, die
 * der ersten. Die Rechnung mit 0 verwendet weiterhin alle.
 */
function namedInputs(sheet: AvailableSheet, base: CellMap, inputs: readonly string[]): string[] {
  const columns = strataColumnsOf(sheet.definition)
  if (columns.length === 0) return [...inputs]
  const column = (reference: string): string | undefined => (reference.includes('!') ? undefined : columns.find((entry) => entry === reference.replace(/\d+$/, '')))
  if (!inputs.some((reference) => column(reference))) return [...inputs]
  const rows = strataInputRows(sheet)
  const used = new Set(columns.filter((entry) => rows.some((row) => !isBlank(base[`${entry}${row}`]))))
  // Ist keine Schicht belegt, nennt die Anzeige die erste; für die Frage „fehlt eine Pflichteingabe?“ zählt sie ebenso.
  const shown = used.size > 0 ? used : new Set(columns.slice(0, 1))
  return inputs.filter((reference) => {
    const own = column(reference)
    return own === undefined || shown.has(own)
  })
}

/** Zeilen der Schichteingaben eines Blatts. */
const inputRows = new WeakMap<AvailableSheet, string[]>()

function strataInputRows(sheet: AvailableSheet): string[] {
  let rows = inputRows.get(sheet)
  if (!rows) {
    rows = inputFields(sheet.definition).filter((field) => field.columns).map((field) => rowNumber(field.cell))
    inputRows.set(sheet, rows)
  }
  return rows
}

type Lacking = Map<CellAddress, string[]>

const note = (lacking: Lacking, cell: CellAddress, inputs: readonly string[]): void => void lacking.set(cell, [...(lacking.get(cell) ?? []), ...inputs])

/** Vom Blatt gemeldete, mit 0 gerechnete Eingaben: ausweisen oder – je nach Richtlinie – die abhängigen Zellen offen lassen. */
function applyReported(sheet: AvailableSheet, base: CellMap, cells: Cells, policy: MissingPolicy, lacking: Lacking): ZeroAssumption[] {
  const assumed: ZeroAssumption[] = []
  for (const entry of sheet.zeroAssumed?.(base) ?? []) {
    if (policy[entry.kind ?? 'sampleDeviation'] === 'zero') assumed.push(entry)
    else {
      for (const cell of entry.cells) {
        cells[cell] = null
        note(lacking, cell, [entry.input])
      }
    }
  }
  return assumed
}

/**
 * Blatt rechnen und die Richtlinie für fehlende Angaben anwenden. `notes: false`
 * spart die Gegenrechnungen, wenn nur die Zellwerte gebraucht werden und
 * Pflichteingaben ohnehin offen bleiben (`lacking` ist dann unvollständig).
 */
export function evaluateSheet(sheet: AvailableSheet, inputs: CellMap, context: SheetContext, notes = true): SheetEvaluation {
  // Anzeige, Hinweise und Ergebnisspalte fragen nacheinander mit denselben Objekten; die letzte Auswertung je Blatt bleibt stehen.
  const last = lastEvaluation.get(sheet)
  if (last && last.inputs === inputs && last.context === context && (last.notes || !notes)) return last.evaluation
  const evaluation = evaluate(sheet, inputs, context, notes)
  lastEvaluation.set(sheet, { inputs, context, notes, evaluation })
  return evaluation
}

const lastEvaluation = new WeakMap<AvailableSheet, { inputs: CellMap; context: SheetContext; notes: boolean; evaluation: SheetEvaluation }>()

/**
 * Sind alle Pflichteingaben vorhanden? Pflichteingaben sind die Eingaben, die
 * die Abweichungen des Blatts als Auslöser nennen (Fallart `requiredInput`);
 * bei Schichtzeilen zählen nur belegte Schichten.
 */
function isComplete(sheet: AvailableSheet, base: CellMap, context: SheetContext): boolean {
  if (context.sourceIncomplete) return false
  for (const entries of requiredEntries(sheet).values()) {
    for (const entry of entries.filter((candidate) => !candidate.local)) {
      const empty = entry.whenEmpty.filter((reference) => isEmptyReference(reference, base, context.sheets))
      if (empty.length && namedInputs(sheet, base, empty).length) return false
    }
  }
  return true
}

/**
 * Verbindliche Regel: Sind alle Pflichteingaben vorhanden, zeigt die Webfassung
 * immer, was die Vorlage zeigt. Werte ohne Grundlage (`withoutBasis`) bleiben
 * nur offen, solange eine Eingabe fehlt; bei vollständigen Eingaben erscheinen
 * sie wie in der Vorlage und werden als solche gemeldet.
 */
function computeShown(sheet: AvailableSheet, inputs: CellMap, context: SheetContext, policy: MissingPolicy): { base: CellMap; withoutBasis: CellAddress[]; complete: boolean; used: SheetContext } {
  const open = sheet.compute(inputs, context)
  const complete = isComplete(sheet, open, context)
  if (policy.withoutBasis !== 'open' || !complete) return { base: open, withoutBasis: [], complete, used: context }
  const used = { ...context, policy: { ...policy, withoutBasis: 'template' as const } }
  const shown = sheet.compute(inputs, used)
  return { base: shown, withoutBasis: Object.keys(shown).filter((cell) => isBlank(open[cell]) && !isBlank(shown[cell])), complete, used }
}

function evaluate(sheet: AvailableSheet, inputs: CellMap, context: SheetContext, notes: boolean): SheetEvaluation {
  const policy = policyOf(context)
  const { base, withoutBasis, complete, used } = computeShown(sheet, inputs, context, policy)
  const cells: Cells = { ...base }
  const lacking: Lacking = new Map()
  const assumed = applyReported(sheet, base, cells, policy, lacking)
  const zero = policy.requiredInput === 'zero'
  // Gegenrechnung im selben Kontext wie die gezeigten Werte (`used`): Bei vollständigen Pflichteingaben zählen Werte ohne Grundlage wie in der Vorlage.
  for (const entry of notes || zero ? openCells(sheet, inputs, base, used) : []) {
    if (!zero) note(lacking, entry.cell, namedInputs(sheet, base, entry.inputs))
    else {
      cells[entry.cell] = entry.shown
      for (const input of entry.inputs) merge(assumed, input, entry.cell)
    }
  }
  const silent = notes ? silentInputs(sheet, inputs, base, used, new Set(assumed.map((entry) => entry.input))) : []
  return { cells, assumed, lacking, withoutBasis, silent, complete }
}
