/**
 * Anzeigemodell eines Rechenblatts: aus Methodendefinition, Eingaben und
 * Ergebnissen entstehen die Zeilen des Formulars. Rein und ohne Framework,
 * damit Vue (und später React) nur noch darstellen. Für eine andere Sprache
 * das Blatt vorher mit `localizeSheet` übersetzen.
 */
import { isBlank, toneOf } from '../excel/index'
import { fieldOptions, formatFieldInput, formatFieldValue, type ChoiceOption } from '../format/numbers'
import type { Translate } from '../i18n/messages'
import { cellsOf, type FieldDefinition, type FieldKind, type SubsampleRole, type ValueType } from '../model/definition'
import { evaluateSheet, type SheetEvaluation } from '../model/evaluate'
import type { AvailableSheet, ZeroAssumption } from '../model/sheet'
import { carriedLimitations, inputName, isQualified, limitationsOf } from './limits'

export { inputName } from './limits'
import { translateValue } from '../model/texts'
import type { CellAddress, CellMap, CellValue, SheetContext, SheetId, Tone } from '../model/types'

/** Bedienelement einer Zeile. */
export type RowControl = 'text' | 'number' | 'select' | 'output' | 'check'

/** Wert einer einzelnen Zelle in der Anzeige. */
export interface CellView {
  cell: CellAddress
  value: CellValue
  /** Text im Eingabefeld. */
  inputText: string
  /** Anzeige eines berechneten Werts bzw. Prüfhinweises. */
  display: string
  tone: Tone
  /** Die Vorlage rechnet hier mit 0 weiter; die Webfassung zeigt „Angabe fehlt“. */
  missing: boolean
  /** Zu `missing`: welche Eingaben fehlen („Es fehlt: …“), sonst leer. */
  missingNote: string
  /** Hinweis der Webfassung, wenn eine fehlende Eingabe wie in der Vorlage als 0 gerechnet ist; sonst leer. */
  zeroNote: string
  /** Hinweis an der Würdigung, wenn ein bestandener Befund durch Hinweise der Webfassung eingeschränkt ist; sonst leer. */
  caveatNote: string
}

export interface RowView extends CellView {
  kind: FieldKind
  type: ValueType
  control: RowControl
  label: string
  hint: string
  formula: string
  /** Erläuterung zu „Auslegung der Vorlage“ oder leer. */
  interpretation: string
  options: readonly ChoiceOption[]
  /** Zentrale Ergebnisgröße (in der Vorlage grün und fett). */
  key: boolean
  /** Feld der Webfassung ohne Entsprechung in der Vorlage. */
  web: boolean
  /** Feld nimmt eine Summe aus den Unterstichproben auf. */
  subsample: SubsampleRole | null
  /** Verknüpfung: Quelle und ob die Vorbelegung überschrieben ist. */
  link: { sheet: SheetId; overridden: boolean } | null
  /** Schichtzeile: Summenzelle (falls vorhanden) und je Schichtspalte eine Zelle. */
  strata: { total: CellView | null; cells: readonly CellView[] } | null
}

export interface SectionView {
  id: string
  title: string
  reference: string
  rows: readonly RowView[]
}

interface Scope {
  /** Auswertung unter der Richtlinie für fehlende Angaben. */
  evaluation: SheetEvaluation
  /** Zelle → fehlende Eingaben, die als 0 gerechnet sind. */
  assumed: ReadonlyMap<CellAddress, readonly CellAddress[]>
  /** Hinweise der Webfassung in Warnfarbe schränken das Ergebnis ein (eigene und die des liefernden Verfahrens). */
  qualified: boolean
  sheet: AvailableSheet
  inputs: CellMap
  results: CellMap
  context: SheetContext
  t: Translate
}

function controlOf(field: FieldDefinition): RowControl {
  if (field.type === 'check') return 'check'
  if (field.kind === 'formula' || field.kind === 'result') return 'output'
  if (field.list || field.options) return 'select'
  return field.type === 'text' ? 'text' : 'number'
}

/** Leere Pflichteingaben, derentwegen die Zelle offen ist („Angabe fehlt“); leer, wenn auch die Vorlage keinen Wert zeigte. */
function missingInputs(scope: Scope, cell: CellAddress): readonly string[] {
  return isBlank(scope.results[cell]) ? (scope.evaluation.lacking.get(cell) ?? []) : []
}

function displayOf(scope: Scope, field: FieldDefinition, value: CellValue, missing: boolean): string {
  if (typeof value === 'string' && value !== '') return translateValue(scope.sheet.texts, value)
  if (!isBlank(value)) return formatFieldValue(field, value)
  if (missing) return scope.t('missing')
  return field.type === 'check' ? scope.t('noValue') : formatFieldValue(field, null)
}

/**
 * Nicht uneingeschränkt grün: die Würdigung, solange ein Hinweis in Warnfarbe das
 * Ergebnis einschränkt, und jeder bestandene Prüfhinweis, den die Webfassung wie
 * die Vorlage zeigt, obwohl ihm die Grundlage fehlt.
 */
function isRestricted(scope: Scope, field: FieldDefinition, cell: CellAddress, tone: Tone): boolean {
  return tone === 'success' && ((scope.qualified && field.alias === ASSESSMENT) || scope.evaluation.withoutBasis.includes(cell))
}

function cellOf(scope: Scope, field: FieldDefinition, cell: CellAddress, isInput: boolean): CellView {
  const value = scope.results[cell] ?? null
  const lacking = isInput ? [] : missingInputs(scope, cell)
  const assumed = scope.assumed.get(cell) ?? []
  const tone = field.type === 'check' ? toneOf(value) : 'neutral'
  const caveat = isRestricted(scope, field, cell, tone)
  return {
    cell,
    value,
    inputText: isInput ? formatFieldInput(field, value) : '',
    display: displayOf(scope, field, value, lacking.length > 0),
    tone: caveat ? 'warning' : tone,
    missing: lacking.length > 0,
    missingNote: lacking.length ? scope.t('missingInputs', { inputs: lacking.map((input) => inputName(scope.sheet, input)).join('; ') }) : '',
    zeroNote: assumed.length ? scope.t('zeroAssumedInput', { input: assumed.map((input) => inputName(scope.sheet, input)).join('; ') }) : '',
    caveatNote: caveat ? scope.t('qualifiedNote') : '',
  }
}

/** Alias der Würdigung in den Methodenblättern und in Blatt 18. */
const ASSESSMENT = 'assessment'

/** Unveränderliche Angaben der Zeile aus der Definition. */
function textsOf(field: FieldDefinition): Pick<RowView, 'kind' | 'type' | 'label' | 'hint' | 'formula' | 'interpretation' | 'key' | 'web' | 'subsample'> {
  return {
    kind: field.kind,
    type: field.type,
    label: field.label,
    hint: field.hint ?? '',
    formula: field.formula ?? '',
    interpretation: field.interpretation ?? '',
    key: field.kind === 'result',
    web: field.web === true,
    subsample: field.subsample ?? null,
  }
}

function optionsOf(scope: Scope, field: FieldDefinition): ChoiceOption[] {
  return fieldOptions(field, scope.context.parameters, scope.t('outsideAnnex')).map((option) => ({ ...option, label: translateValue(scope.sheet.texts, option.label) }))
}

function rowOf(scope: Scope, field: FieldDefinition): RowView {
  const isInput = field.kind === 'input' || field.kind === 'link'
  const strata = field.columns
    ? { total: field.total ? cellOf(scope, field, field.total, false) : null, cells: cellsOf(field).map((cell) => cellOf(scope, field, cell, isInput)) }
    : null
  return {
    ...cellOf(scope, field, field.cell, isInput),
    ...textsOf(field),
    control: controlOf(field),
    options: optionsOf(scope, field),
    link: field.link ? { sheet: field.link.sheet, overridden: !isBlank(scope.inputs[field.cell]) } : null,
    strata,
  }
}

/** Betroffene Zelle → fehlende Eingaben, die wie in der Vorlage als 0 gerechnet sind. */
export function assumedCells(assumed: readonly ZeroAssumption[]): Map<CellAddress, CellAddress[]> {
  const cells = new Map<CellAddress, CellAddress[]>()
  for (const assumption of assumed) {
    for (const cell of assumption.cells) cells.set(cell, [...(cells.get(cell) ?? []), assumption.input])
  }
  return cells
}

/** Abschnitte und Zeilen eines Blatts in der Reihenfolge der Vorlage. */
export function buildSections(sheet: AvailableSheet, inputs: CellMap, results: CellMap, context: SheetContext, t: Translate): SectionView[] {
  const evaluation = evaluateSheet(sheet, inputs, context)
  const qualified = isQualified([...limitationsOf(sheet, inputs, results, context, t), ...carriedLimitations(sheet, context, t)])
  const scope: Scope = { sheet, inputs, results, context, t, assumed: assumedCells(evaluation.assumed), evaluation, qualified }
  return sheet.definition.sections.map((section) => ({
    id: section.id,
    title: section.title,
    reference: section.reference ?? '',
    rows: section.fields.map((field) => rowOf(scope, field)),
  }))
}

/** Zeilen der Schichtzeilen eines Blatts (für die Zahl der belegten Schichten). */
export function strataRows(sheet: AvailableSheet): string[] {
  return sheet.definition.sections.flatMap((section) => section.fields.filter((field) => field.columns && (field.kind === 'input' || field.kind === 'link')).map((field) => field.cell.replace(/^[A-Z]+/, '')))
}
