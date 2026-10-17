/**
 * Abgeleitete Sicht einer Sitzung: Blätter in der Sprache der Oberfläche,
 * Ergebnisse aller Blätter, das Blatt des aktuellen Arbeitsschritts mit seinen
 * Anzeigemodellen, der Wegweiser und die Übersicht der Unterstichproben.
 */
import {
  buildGuide,
  buildListView,
  buildReport,
  buildSections,
  buildSummary,
  computeWorkspace,
  contextFor,
  findAvailableSheet,
  findField,
  listRows,
  localizeSheet,
  pasteColumns,
  POPULATION_SHEET,
  SHARED_TEXTS,
  strataColumnsOf,
  strataRows,
  usedStrata,
  WORKFLOW_STEPS,
  type AvailableSheet,
  type CellMap,
  type GuideView,
  type ListView,
  type ReportPage,
  type SectionView,
  type SheetContext,
  type SheetId,
  type SheetModule,
  type SummaryView,
  type Translate,
  type WorkflowStep,
  type WorkspaceState,
  UNREADABLE_INPUT,
} from '@auditcore/sampling-templates-core'
import { computed, type ComputedRef, type Ref, type ShallowRef } from 'vue'

export type StepId = WorkflowStep['id']

export interface ViewOptions {
  /** Eingaben, deren Text nicht lesbar ist; die Anzeige meldet sie als ungültig. */
  invalid?: ReadonlySet<string>
  sheets: () => readonly SheetModule[]
  locale: () => 'de' | 'en'
  t: Translate
}

export interface SessionView {
  /** Gewähltes Methodenblatt. */
  activeSheet: ComputedRef<AvailableSheet | null>
  /** Blatt des aktuellen Arbeitsschritts. */
  currentSheet: ComputedRef<AvailableSheet | null>
  context: ComputedRef<SheetContext>
  sections: ComputedRef<SectionView[]>
  summary: ComputedRef<SummaryView | null>
  guide: ComputedRef<GuideView>
  /** Belegte Schichten des aktuellen Blatts; 0 ohne Schichtzeilen. */
  usedStrata: ComputedRef<number>
  hasStrata: ComputedRef<boolean>
  listView: ComputedRef<ListView | null>
  report: ComputedRef<ReportPage | null>
  pasteColumns: ComputedRef<string>
  find: (id: SheetId | null) => AvailableSheet | null
}

/** Eingaben eines Formularblatts aus dem Arbeitsstand. */
export function ownInputs(state: WorkspaceState, id: SheetId): CellMap {
  const inputs = state.sheets[id]
  return inputs && !Array.isArray(inputs) ? (inputs as CellMap) : {}
}

/** Blatt der Druckfassung; es wird als Berichtsseite gezeigt, nicht als Formular. */
const REPORT_SHEET = '20_Druck_KOM'

const isList = (sheet: AvailableSheet | null): boolean => sheet?.definition.layout === 'list'

/**
 * Arbeitsstand für die Rechnung: Ein vorbelegtes Feld (z. B. BV aus Blatt 02)
 * mit nicht lesbarer Eingabe fällt nicht still auf den Wert des anderen Blatts
 * zurück; es zählt als ungültig, und die Folgegrößen bleiben offen. Erst ein
 * geleertes Feld übernimmt wieder die Vorbelegung.
 */
function withUnreadable(state: WorkspaceState, sheet: AvailableSheet | null, invalid: ReadonlySet<string>): WorkspaceState {
  if (!sheet || isList(sheet)) return state
  const linked = [...invalid].filter((cell) => findField(sheet.definition, cell)?.link)
  if (linked.length === 0) return state
  return { ...state, sheets: { ...state.sheets, [sheet.id]: { ...ownInputs(state, sheet.id), ...Object.fromEntries(linked.map((cell) => [cell, UNREADABLE_INPUT])) } } }
}

export function useSessionView(workspace: ShallowRef<WorkspaceState>, step: Ref<StepId>, selectedUnit: Ref<number>, options: ViewOptions): SessionView {
  const find = (id: SheetId | null): AvailableSheet | null => {
    const sheet = id ? findAvailableSheet(id, options.sheets()) : undefined
    return sheet ? localizeSheet(sheet, options.locale(), options.locale() === 'de' ? {} : SHARED_TEXTS[options.locale() as 'en']) : null
  }
  const activeSheet = computed(() => find(workspace.value.activeMethod))
  const currentSheet = computed(() => (step.value === 'method' ? activeSheet.value : find(WORKFLOW_STEPS.find((entry) => entry.id === step.value)?.sheet ?? null)))
  /** Abzug der reaktiven Menge: Die Ansicht rechnet neu, sobald ein Feld ungültig oder wieder gültig wird. */
  const invalid = (): ReadonlySet<string> => new Set(options.invalid ?? [])
  const computedState = computed(() => withUnreadable(workspace.value, currentSheet.value, invalid()))
  const results = computed(() => computeWorkspace(computedState.value, options.sheets()))
  /** Derselbe Kontext wie in der Rechnung des Arbeitsstands (für Blatt 18 mit der Ergebnisübersicht des gewählten Verfahrens). */
  const context = computed(() => contextFor(currentSheet.value?.id ?? '', computedState.value, results.value))
  /** Eingaben und Zellwerte des angezeigten Formulars: das Blatt selbst oder die gewählte Einheit einer Liste. */
  const form = computed(() => {
    const sheet = currentSheet.value
    if (!sheet) return null
    if (!isList(sheet)) return { sheet, inputs: ownInputs(computedState.value, sheet.id), cells: results.value[sheet.id] ?? {} }
    const row = listRows(workspace.value, sheet.id)[selectedUnit.value]
    return row ? { sheet, inputs: row, cells: sheet.compute(row, context.value) } : null
  })
  const strata = computed(() => (form.value ? strataRows(form.value.sheet) : []))
  return {
    find,
    activeSheet,
    currentSheet,
    context,
    sections: computed(() => (form.value ? buildSections(form.value.sheet, form.value.inputs, form.value.cells, context.value, options.t, invalid()) : [])),
    summary: computed(() => (form.value ? buildSummary(form.value.sheet, form.value.inputs, form.value.cells, context.value, options.t, invalid()) : null)),
    guide: computed(() => buildGuide(find(POPULATION_SHEET) ?? undefined, results.value[POPULATION_SHEET], context.value.parameters, options.t)),
    hasStrata: computed(() => strata.value.length > 0),
    usedStrata: computed(() => (form.value ? usedStrata(form.value.inputs, strata.value, strataColumnsOf(form.value.sheet.definition)) : 0)),
    listView: computed(() => {
      const sheet = currentSheet.value
      return sheet && isList(sheet) ? buildListView(sheet, listRows(workspace.value, sheet.id), activeSheet.value, context.value, options.t) : null
    }),
    /** Berichtsseite (Blatt 20), solange der Schritt „Bericht“ angezeigt wird. */
    report: computed(() => (form.value && form.value.sheet.id === REPORT_SHEET ? buildReport(form.value.sheet, form.value.inputs, form.value.cells, context.value, options.t, options.sheets()) : null)),
    pasteColumns: computed(() => (currentSheet.value ? pasteColumns(currentSheet.value.definition).map((field) => `${field.label} (${field.cell})`).join('; ') : '')),
  }
}
