/**
 * Abgeleitete Sicht einer Sitzung: Blätter in der Sprache der Oberfläche,
 * Ergebnisse aller Blätter, das Blatt des aktuellen Arbeitsschritts mit seinen
 * Anzeigemodellen, der Wegweiser und die Übersicht der Unterstichproben.
 */
import {
  buildGuide,
  buildListView,
  buildSections,
  buildSummary,
  computeWorkspace,
  contextFor,
  findAvailableSheet,
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
  type SectionView,
  type SheetContext,
  type SheetId,
  type SheetModule,
  type SummaryView,
  type Translate,
  type WorkflowStep,
  type WorkspaceState,
} from '@auditcore/sampling-templates-core'
import { computed, type ComputedRef, type Ref, type ShallowRef } from 'vue'

export type StepId = WorkflowStep['id']

export interface ViewOptions {
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
  pasteColumns: ComputedRef<string>
  find: (id: SheetId | null) => AvailableSheet | null
}

/** Eingaben eines Formularblatts aus dem Arbeitsstand. */
export function ownInputs(state: WorkspaceState, id: SheetId): CellMap {
  const inputs = state.sheets[id]
  return inputs && !Array.isArray(inputs) ? (inputs as CellMap) : {}
}

const isList = (sheet: AvailableSheet | null): boolean => sheet?.definition.layout === 'list'

export function useSessionView(workspace: ShallowRef<WorkspaceState>, step: Ref<StepId>, selectedUnit: Ref<number>, options: ViewOptions): SessionView {
  const find = (id: SheetId | null): AvailableSheet | null => {
    const sheet = id ? findAvailableSheet(id, options.sheets()) : undefined
    return sheet ? localizeSheet(sheet, options.locale(), options.locale() === 'de' ? {} : SHARED_TEXTS[options.locale() as 'en']) : null
  }
  const results = computed(() => computeWorkspace(workspace.value, options.sheets()))
  const activeSheet = computed(() => find(workspace.value.activeMethod))
  const currentSheet = computed(() => (step.value === 'method' ? activeSheet.value : find(WORKFLOW_STEPS.find((entry) => entry.id === step.value)?.sheet ?? null)))
  /** Derselbe Kontext wie in der Rechnung des Arbeitsstands (für Blatt 18 mit der Ergebnisübersicht des gewählten Verfahrens). */
  const context = computed(() => contextFor(currentSheet.value?.id ?? '', workspace.value, results.value))
  /** Eingaben und Zellwerte des angezeigten Formulars: das Blatt selbst oder die gewählte Einheit einer Liste. */
  const form = computed(() => {
    const sheet = currentSheet.value
    if (!sheet) return null
    if (!isList(sheet)) return { sheet, inputs: ownInputs(workspace.value, sheet.id), cells: results.value[sheet.id] ?? {} }
    const row = listRows(workspace.value, sheet.id)[selectedUnit.value]
    return row ? { sheet, inputs: row, cells: sheet.compute(row, context.value) } : null
  })
  const strata = computed(() => (form.value ? strataRows(form.value.sheet) : []))
  return {
    find,
    activeSheet,
    currentSheet,
    context,
    sections: computed(() => (form.value ? buildSections(form.value.sheet, form.value.inputs, form.value.cells, context.value, options.t) : [])),
    summary: computed(() => (form.value ? buildSummary(form.value.sheet, form.value.inputs, form.value.cells, context.value, options.t) : null)),
    guide: computed(() => buildGuide(find(POPULATION_SHEET) ?? undefined, results.value[POPULATION_SHEET], context.value.parameters, options.t)),
    hasStrata: computed(() => strata.value.length > 0),
    usedStrata: computed(() => (form.value ? usedStrata(form.value.inputs, strata.value, strataColumnsOf(form.value.sheet.definition)) : 0)),
    listView: computed(() => {
      const sheet = currentSheet.value
      return sheet && isList(sheet) ? buildListView(sheet, listRows(workspace.value, sheet.id), activeSheet.value, context.value, options.t) : null
    }),
    pasteColumns: computed(() => (currentSheet.value ? pasteColumns(currentSheet.value.definition).map((field) => `${field.label} (${field.cell})`).join('; ') : '')),
  }
}
