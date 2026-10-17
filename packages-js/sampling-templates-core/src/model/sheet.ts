/**
 * Ein Blatt der Vorlage als Modul: Definition, Rechenkern, Beispielwerte und
 * begründete Abweichungen. Blätter ohne Rechenkern sind als geplant geführt.
 */
import { isBlank } from '../excel/index'
import { PARAMETERS } from '../sheets/01_Parameter/index'
import { cellsOf, inputFields, type MethodDefinition, type SubsampleRole } from './definition'
import type { DataTable } from './table'
import { localizeDefinition, type SheetTexts, type SheetTranslations, type TranslationLocale } from './texts'
import type { CellAddress, CellMap, CellValue, Cells, Compute, Deviation, MethodSummary, SheetContext, SheetId, WebHint } from './types'

/** Erfundene Beispielwerte eines Blatts; die Oberfläche kennzeichnet sie als Beispiel. */
export interface SampleInputs {
  inputs: CellMap
}

/**
 * Blatt ohne Rechenkern: entweder noch geplant oder – mit `table` – eine
 * Nachschlagetabelle der Vorlage (Blatt X1a), die als Datentabelle angezeigt wird.
 */
export interface PlannedSheet {
  id: SheetId
  available: false
  table?: DataTable
}

/** Blatt mit Rechenkern und Methodendefinition. */
export interface AvailableSheet {
  id: SheetId
  available: true
  definition: MethodDefinition
  compute: Compute
  /** Erfundene Beispielwerte. */
  sample: SampleInputs
  /** Begründete Abweichungen vom Verhalten der Vorlage bei leeren Eingaben. */
  deviations: readonly Deviation[]
  /** Zusätzliche Hinweise der Webfassung; ohne Einfluss auf das Rechenergebnis. */
  webHints?: (inputs: CellMap, results: CellMap, context: SheetContext) => readonly WebHint[]
  /**
   * Eingaben, die fehlen und die die Webfassung – wie die Vorlage – als 0 rechnet,
   * mit den davon betroffenen Zellen. Die Oberfläche weist sie als Hinweis der
   * Webfassung aus („Keine Angabe, daher mit 0 berechnet.“).
   */
  zeroAssumed?: (results: CellMap) => readonly ZeroAssumption[]
  /**
   * Zellen, die die Webfassung bewusst anders bildet als die Vorlage (z. B. die
   * Kopfzeile des Berichts, die in der Vorlage ein festes Programm nennt). Die
   * einzige Ausnahme vom Grundsatz „nie ein anderer Wert als die Vorlage“; jede
   * steht in docs/abweichungen.md.
   */
  adapted?: readonly Adaptation[]
  /** Nur Listenblätter (Blatt 17): Summen über alle Einheiten für die Übernahme in ein Methodenblatt. */
  totals?: (rows: readonly CellMap[], context: SheetContext, needs?: SubsampleNeeds) => SubsampleTotals
  /** Arbeitsübersetzungen der Texte des Blatts; Deutsch ist der Wortlaut der Vorlage. */
  translations?: SheetTranslations
  /** Von `localizeSheet` gesetzt: die Übersetzung, in der das Blatt gerade angezeigt wird. */
  texts?: SheetTexts
}

/** Bewusst anders gebildete Zelle: was die Webfassung zeigt, ausgedrückt durch den Wert der Vorlage. */
export interface Adaptation {
  cell: CellAddress
  reason: string
  /**
   * Wert der Webfassung zu dem Wert, den die Vorlage zeigt (in Excel auch ein
   * Wahrheitswert oder ein Fehlerwert wie `#DIV/0!`); `results` sind die Zellwerte der Webfassung.
   */
  fromTemplate: (shown: CellValue | boolean, results: CellMap) => CellValue
}

/** Wert der Vorlage als Zellwert: Ein Wahrheitswert zählt wie in Excel als 1 bzw. 0. */
export function templateNumber(shown: CellValue | boolean): CellValue {
  return typeof shown === 'boolean' ? Number(shown) : shown
}

/** Eine fehlende Eingabe, mit der wie in der Vorlage als 0 gerechnet wurde. */
export interface ZeroAssumption {
  /** Leere Eingabezelle. */
  input: CellAddress
  /** Zellen, deren Wert davon abhängt. */
  cells: readonly CellAddress[]
  /** Fallart der Richtlinie (`model/policy.ts`); Standard `sampleDeviation`. */
  kind?: 'sampleDeviation' | 'partialErrorSum' | 'requiredInput'
}

/** Summen der Unterstichproben je Rolle; `null`, solange keine Einheit dazu beiträgt. */
export type SubsampleTotals = Readonly<Record<SubsampleRole, number | null>> & {
  /** Anzahl der Einheiten in der Liste. */
  units: number
  /** Einheiten, deren Fehler bzw. Fehlerquote noch nicht bestimmt ist. */
  incomplete: number
  /** Summen je Schicht und Zeitraum, soweit das Methodenblatt danach unterscheidet (`needs`). */
  groups?: readonly SubsampleGroup[]
  /** Einheiten ohne die Schicht- bzw. Zeitraumangabe, die das Methodenblatt braucht; sie gehen in keine Gruppe ein. */
  unassigned?: number
}

/** Wonach das Methodenblatt die Summen der Unterstichproben unterscheidet. */
export interface SubsampleNeeds {
  /** Geschichtetes Verfahren: Summen je Schicht. */
  stratum: boolean
  /** Mehrere Stichprobenzeiträume: Summen je Zeitraum. */
  period: boolean
}

/** Summen der Einheiten einer Schicht und eines Zeitraums; `null` heißt „nicht unterschieden“. */
export type SubsampleGroup = Readonly<Record<SubsampleRole, number | null>> & {
  stratum: number | null
  period: number | null
}

export type SheetModule = PlannedSheet | AvailableSheet

/** Platzhalter für ein Blatt ohne Rechenkern. */
export function plannedSheet(id: SheetId): PlannedSheet {
  return { id, available: false }
}

/** Nachschlagetabelle anmelden: kein Rechenblatt, aber als Datentabelle anzeigbar. */
export function tableSheet(id: SheetId, table: DataTable): PlannedSheet {
  return { id, available: false, table }
}

/** Blatt mit Rechenkern anmelden. */
export function defineSheet(sheet: Omit<AvailableSheet, 'available'>): AvailableSheet {
  return { ...sheet, available: true }
}

/**
 * Blatt in der Sprache der Oberfläche: Definition mit übersetzten Texten;
 * `shared` sind Übersetzungen, die für alle Blätter gelten (Listen aus Blatt 01).
 * Deutsch (`de`) und Blätter ohne Übersetzung bleiben unverändert.
 */
export function localizeSheet(sheet: AvailableSheet, locale: 'de' | TranslationLocale, shared: Readonly<Record<string, string>> = {}): AvailableSheet {
  if (locale === 'de') return sheet
  const own = sheet.translations?.[locale] ?? {}
  const texts: SheetTexts = { ...own, values: { ...shared, ...own.values } }
  return { ...sheet, definition: localizeDefinition(sheet.definition, texts), texts }
}

/** Kontext mit den Parametern aus Blatt 01; weitere Angaben überschreiben die Vorgaben. */
export function createContext(partial: Partial<SheetContext> = {}): SheetContext {
  return { parameters: PARAMETERS, sheets: {}, ...partial }
}

/**
 * Wert einer Eingabe, deren Text die Oberfläche nicht als Zahl lesen kann. Die
 * Eingabe zählt als leer, fällt aber nicht auf die Vorbelegung aus einem
 * anderen Blatt zurück: Ein vorbelegtes Feld mit „abc“ rechnet nicht still mit
 * dem Wert aus Blatt 02 weiter, die Folgegrößen bleiben offen.
 */
export const UNREADABLE_INPUT = '#WERT!'

/**
 * Eingaben eines Blatts auflösen: eigene Werte der Eingabezellen, bei
 * Verknüpfungen der Wert des anderen Blatts aus dem Kontext, solange die
 * Prüfbehörde ihn nicht überschrieben hat (`UNREADABLE_INPUT`: leer, ohne Vorbelegung).
 */
export function resolveInputs(definition: MethodDefinition, inputs: CellMap, context: SheetContext): Cells {
  const cells: Cells = {}
  for (const field of inputFields(definition)) {
    const linked = field.link ? context.sheets[field.link.sheet]?.[field.link.cell] : undefined
    for (const cell of cellsOf(field)) {
      const own = inputs[cell]
      cells[cell] = own === UNREADABLE_INPUT ? null : isBlank(own) ? (linked ?? null) : own
    }
  }
  return cells
}

/**
 * Ist die Zelle leer? Ohne Blattangabe eine Zelle des eigenen Blatts,
 * `Blatt!Zelle` eine Zelle eines anderen Blatts aus dem Kontext.
 */
export function isEmptyReference(reference: string, own: CellMap, sheets: Readonly<Record<SheetId, CellMap>>): boolean {
  if (!reference.includes('!')) return isBlank(own[reference])
  const [sheet, cell] = reference.split('!') as [string, string]
  return isBlank(sheets[sheet]?.[cell])
}

/**
 * Gegenrechnung „wie die Vorlage“: Alle leeren Eingaben, die in den begründeten
 * Abweichungen des Blatts genannt sind, zählen als 0. Hat eine Zelle dort einen
 * Wert und in der Webfassung keinen, fehlt eine Angabe („Angabe fehlt“).
 */
export function computeLikeTemplate(sheet: AvailableSheet, inputs: CellMap, results: CellMap, context: SheetContext): CellMap {
  const references = new Set(sheet.deviations.flatMap((entry) => entry.whenEmpty.filter((reference) => isEmptyReference(reference, results, context.sheets))))
  if (references.size === 0) return results
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

/** Feste Zellen der Ergebnisübersicht, die jedes Methodenblatt für Blatt 18 füllt. */
export const SUMMARY_CELLS = {
  method: 'N3',
  bookValue: 'N4',
  projectedError: 'N5',
  exhaustiveError: 'N6',
  precision: 'N7',
  systemicErrors: 'N8',
  anomalousErrors: 'N9',
  sampleSize: 'N10',
  totalErrorRate: 'N11',
} as const

/** Ergebnisübersicht eines Methodenblatts für den Kontext von Blatt 18. */
export function summaryOf(sheet: SheetId, results: CellMap): MethodSummary {
  const summary = { sheet } as MethodSummary
  for (const [name, cell] of Object.entries(SUMMARY_CELLS) as [keyof typeof SUMMARY_CELLS, string][]) {
    summary[name] = results[cell] ?? null
  }
  return summary
}
