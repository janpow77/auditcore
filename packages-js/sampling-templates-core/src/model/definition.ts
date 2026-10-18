/**
 * Deklarative Methodendefinition eines Blatts: Abschnitte und Felder in der
 * Reihenfolge der Vorlage. Aus ihr entstehen Formular, Ergebnisspalte, Export
 * und die Prüfung der Arbeitsstandsdatei. Texte stammen wörtlich aus der
 * Vorlage (Spalte B: Bezeichnung, Spalte D bzw. K: Fundstelle).
 */
import type { CellAddress, CellMap, CellValue, ListKey, SheetId } from './types'

/** Art der Zelle wie in der Legende der Vorlage: Eingabe, Verknüpfung, Formel, Ergebnis. */
export type FieldKind = 'input' | 'link' | 'formula' | 'result'

/** Darstellung und Eingabeprüfung eines Werts. */
export type ValueType = 'text' | 'amount' | 'integer' | 'percent' | 'decimal' | 'choice' | 'check'

export interface FieldDefinition {
  /** Zelle der Vorlage; bei Schichtzeilen die Summenzelle bzw. die erste Schichtzelle. */
  cell: CellAddress
  /** Lesbarer englischer Name (Alias des Zellschlüssels). */
  alias: string
  kind: FieldKind
  type: ValueType
  /** Bezeichnung (Spalte B). */
  label: string
  /** Fundstelle und Erläuterung (Spalte D bzw. K), wörtlich. */
  hint?: string
  /** Kurzschreibweise der Formel unter der Bezeichnung. */
  formula?: string
  /** Zahlenformat der Vorlage, z. B. `#,##0.00" €"`; steuert auch den Excel-Export. */
  format?: string
  /** Auswahlliste aus Blatt 01. */
  list?: ListKey
  /** Eigene Auswahl eines Felds der Webfassung (statt einer Liste aus Blatt 01). */
  options?: readonly (string | number)[]
  /** Vorgabe der Vorlage (z. B. Signifikanzschwelle 2 %). */
  default?: CellValue
  /** Verknüpfung: vorbelegt aus einem anderen Blatt, überschreibbar. */
  link?: { sheet: SheetId; cell: CellAddress }
  /** Hinweis „Auslegung der Vorlage“ mit kurzer Erläuterung. */
  interpretation?: string
  /**
   * Schichtzeile: Spalten der Schichten (`STRATA_COLUMNS`); `cell` ist die Zelle der
   * ersten Schicht (`D9`), die übrigen heißen `<Spalte><Zeile>`.
   */
  columns?: readonly string[]
  /** Schichtzeile: Summenzelle der Zeile (`C9`), wenn die Vorlage eine hat. */
  total?: CellAddress
  /** Feld der Webfassung ohne Entsprechung in der Vorlage; als „Hinweis der Webfassung“ gekennzeichnet. */
  web?: boolean
  /** Ziel der Übernahme aus den Unterstichproben (Blatt 17) in ein Methodenblatt. */
  subsample?: SubsampleRole
  /**
   * Stichprobenzeitraum des Felds (1–3) in Blättern mit mehreren Zeiträumen. Ordnet die
   * Übernahme aus den Unterstichproben zu: Übernommen werden nur Einheiten dieses Zeitraums.
   */
  period?: number
  /**
   * Freiwillige Eingabe: Leer heißt „gibt es nicht“ (z. B. keine systembedingten
   * Fehler). `true`: für sich freiwillig. Ein Name: Die Felder mit demselben Namen
   * gehören zusammen (z. B. Anzahl, Buchwert und Fehler der hochwertigen
   * Einheiten) – leer dürfen sie nur gemeinsam sein. Alle anderen Eingaben sind
   * Pflicht, sobald ein gezeigtes Ergebnis von ihnen abhängt (`model/dependence.ts`).
   * `false`: Pflicht, auch wenn der Name des Felds sonst auf eine freiwillige Angabe deutet.
   */
  optional?: boolean | string
}

/**
 * Summen aus Blatt 17, die ein Methodenblatt per Schaltfläche übernimmt:
 * Fehler der hochwertigen Einheiten, Summe der Fehlerquoten bzw. Fehler und
 * Buchwerte der Zufallsschicht.
 */
export type SubsampleRole = 'highValueErrors' | 'errorRateSum' | 'errorSum' | 'bookValueSum'

export interface SectionDefinition {
  /** Kennbuchstabe des Abschnitts (`H`, `I` …). */
  id: string
  title: string
  /** Rechtsgrundlage des Abschnitts. */
  reference?: string
  fields: readonly FieldDefinition[]
}

/** Zeile der mitlaufenden Ergebnisspalte. */
export interface SummaryRow {
  cell: CellAddress
  label: string
  strong?: boolean
}

/** Mitlaufende Ergebnisspalte: Hauptgröße, Kennzahlen und Skala gegen die Signifikanzschwelle. */
export interface SummaryDefinition {
  /** `reason`: Zelle, deren Text erklärt, warum die Hauptgröße fehlt (z. B. „TE ≤ AE“). */
  primary: { cell: CellAddress; label: string; unit: string; reason?: CellAddress }
  rows: readonly SummaryRow[]
  /**
   * Skala gegen die Signifikanzschwelle. `upper` entfällt, wo es keine obere
   * Fehlergrenze gibt (nichtstatistische Verfahren). `rateLabel`/`upperLabel`:
   * Begriffe des Blatts, wenn sie von „Gesamtfehlerquote“/„obere Fehlergrenze“
   * abweichen (Altvorlagen).
   */
  gauge?: { threshold: CellAddress; rate: CellAddress; upper?: CellAddress; rateLabel?: string; upperLabel?: string }
}

export interface MethodDefinition {
  sheet: SheetId
  /** Blattnummer wie in der Vorlage (`03`, `X1`). */
  number: string
  /** Titel des Blatts (Zelle A1 ohne Nummer). */
  title: string
  /** Kurzname für Kopfzeile und Dateinamen. */
  shortTitle: string
  /** Rechtsgrundlagen des Blatts (Zelle A2). */
  legalBasis: string
  sections: readonly SectionDefinition[]
  summary: SummaryDefinition
  /** `list`: Das Blatt wird je Stichprobeneinheit ausgefüllt (Blatt 17); Standard `form`. */
  layout?: 'form' | 'list'
  /** Listenblatt: Zellen, die die Übersicht der Einheiten als Spalten zeigt. */
  listColumns?: readonly CellAddress[]
  /** Nachschlagetabellen der Vorlage, die zu diesem Verfahren gehören (Blatt X1: X1a). */
  tables?: readonly SheetId[]
}

/** Alle Felder in der Reihenfolge der Vorlage. */
export function fieldsOf(definition: MethodDefinition): FieldDefinition[] {
  return definition.sections.flatMap((section) => [...section.fields])
}

/** Felder, die die Prüfbehörde ausfüllt (Eingaben und überschreibbare Verknüpfungen). */
export function inputFields(definition: MethodDefinition): FieldDefinition[] {
  return fieldsOf(definition).filter((field) => field.kind === 'input' || field.kind === 'link')
}

/** Zeilennummer einer Zelle (`D9` → `9`). */
export function rowNumber(cell: CellAddress): string {
  return cell.replace(/^[A-Z]+/, '')
}

/** Alle Zellen eines Felds: die Zelle selbst oder, bei Schichtzeilen, eine Zelle je Schichtspalte. */
export function cellsOf(field: FieldDefinition): CellAddress[] {
  return field.columns ? field.columns.map((column) => `${column}${rowNumber(field.cell)}`) : [field.cell]
}

/**
 * Schichtspalten des Blatts in der Reihenfolge der Schichten: die Spalten der
 * ersten Schichtzeile (in den Blättern 04–16 D–J und AA–AM, in der Altvorlage
 * X3 E–K und AA–AM); leer bei Blättern ohne Schichten.
 */
export function strataColumnsOf(definition: MethodDefinition): readonly string[] {
  return fieldsOf(definition).find((field) => field.columns)?.columns ?? []
}

/** Alle Eingabezellen eines Blatts (Schichtzeilen aufgelöst). */
export function inputCells(definition: MethodDefinition): CellAddress[] {
  return inputFields(definition).flatMap(cellsOf)
}

/** Zelle → Feld je Definition; Definitionen sind unveränderlich, der Index entsteht einmal. */
const fieldIndex = new WeakMap<MethodDefinition, Map<CellAddress, FieldDefinition>>()

function indexOfFields(definition: MethodDefinition): Map<CellAddress, FieldDefinition> {
  let index = fieldIndex.get(definition)
  if (!index) {
    index = new Map()
    for (const field of fieldsOf(definition)) {
      for (const cell of [field.cell, ...(field.total ? [field.total] : []), ...(field.columns ? cellsOf(field) : [])]) {
        if (!index.has(cell)) index.set(cell, field)
      }
    }
    fieldIndex.set(definition, index)
  }
  return index
}

/** Feld zu einer Zelle; auch Schichtzellen und Summenzellen einer Schichtzeile werden gefunden. */
export function findField(definition: MethodDefinition, cell: CellAddress): FieldDefinition | undefined {
  return indexOfFields(definition).get(cell)
}

/** Vorgaben der Vorlage für ein leeres Formular. */
export function defaultInputs(definition: MethodDefinition): CellMap {
  const defaults: Record<CellAddress, CellValue> = {}
  for (const field of inputFields(definition)) {
    if (field.default !== undefined && field.default !== null) defaults[field.cell] = field.default
  }
  return defaults
}

/** Zellwerte unter den lesbaren Namen der Definition; bei Schichtzeilen die Summenzelle, sonst die erste Schicht. */
export function named(definition: MethodDefinition, cells: CellMap): Record<string, CellValue> {
  const result: Record<string, CellValue> = {}
  for (const field of fieldsOf(definition)) result[field.alias] = cells[field.columns ? (field.total ?? field.cell) : field.cell] ?? null
  return result
}
