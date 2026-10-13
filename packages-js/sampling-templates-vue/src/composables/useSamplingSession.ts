/**
 * Zustand einer Sitzung des Stichprobenrechners: Arbeitsstand, Arbeitsschritt,
 * Status (Dateiname, geändert, Beispielwerte), Hinweise und die daraus
 * abgeleiteten Anzeigemodelle. Gerechnet und geprüft wird ausschließlich im Kern.
 */
import {
  availableSheets,
  defaultInputs,
  emptyWorkspace,
  findVariant,
  listRows,
  type AvailableSheet,
  type CellAddress,
  type CellMap,
  type CellValue,
  type SheetId,
  type SheetModule,
  type Translate,
  type WorkspaceState,
} from '@auditcore/sampling-templates-core'
import { ref, shallowRef, type Ref, type ShallowRef } from 'vue'
import { useSheetActions, type SheetActions } from './sessionActions'
import { ownInputs, useSessionView, type SessionView, type StepId } from './sessionView'

export type { StepId } from './sessionView'

export interface SessionMeta {
  /** Name der zuletzt gespeicherten bzw. geöffneten Datei. */
  fileName: string | null
  /** Es gibt Änderungen, die nicht als Datei gespeichert sind. */
  dirty: boolean
  /** Das Formular zeigt die erfundenen Beispielwerte. */
  sample: boolean
}

export type NoticeTone = 'info' | 'warning' | 'danger'

export interface SessionNotice {
  id: number
  tone: NoticeTone
  text: string
}

interface Messages {
  notices: Ref<SessionNotice[]>
  /** Kurze Rückmeldung nach einer Aktion („Arbeitsstand gespeichert.“). */
  flash: Ref<string>
  notify: (tone: NoticeTone, text: string) => void
  dismiss: (id: number) => void
  say: (text: string) => void
}

export interface SamplingSession extends Messages, Omit<SessionView, 'find' | 'context' | 'usedStrata'>, SheetActions {
  workspace: ShallowRef<WorkspaceState>
  meta: Ref<SessionMeta>
  /** Die Verfahrensauswahl ist geöffnet. */
  pickerOpen: Ref<boolean>
  /** Aktueller Arbeitsschritt der Vorlage. */
  step: Ref<StepId>
  /** Gewählte Einheit eines Listenblatts. */
  selectedUnit: Ref<number>
  selectMethod: (id: SheetId) => void
  setStep: (step: StepId) => void
  setInput: (cell: CellAddress, value: CellValue) => void
  reset: () => void
  loadSample: () => void
  replace: (state: WorkspaceState, meta: SessionMeta, notices?: readonly Omit<SessionNotice, 'id'>[]) => void
  markSaved: (fileName: string) => void
}

export interface SessionOptions {
  sheets: () => readonly SheetModule[]
  t: Translate
  /** Sprache der Vorlagentexte (Standard Deutsch = Wortlaut der Vorlage). */
  locale?: () => 'de' | 'en'
  initial?: WorkspaceState
}

const FLASH_MS = 4000

/** Hinweise oberhalb des Rechenblatts und die kurze Rückmeldung nach einer Aktion. */
function useMessages(): Messages & { set: (added: readonly Omit<SessionNotice, 'id'>[]) => void } {
  const notices = ref<SessionNotice[]>([])
  const flash = ref('')
  let nextId = 0
  let timer: ReturnType<typeof setTimeout> | undefined
  const numbered = (notice: Omit<SessionNotice, 'id'>): SessionNotice => ({ ...notice, id: (nextId += 1) })
  return {
    notices,
    flash,
    set: (added) => (notices.value = added.map(numbered)),
    notify: (tone, text) => (notices.value = [...notices.value, numbered({ tone, text })]),
    dismiss: (id) => (notices.value = notices.value.filter((notice) => notice.id !== id)),
    say(text) {
      flash.value = text
      clearTimeout(timer)
      timer = setTimeout(() => (flash.value = ''), FLASH_MS)
    },
  }
}

/**
 * Jedes Formularblatt mit Rechenkern trägt die Vorgaben der Vorlage, auch wenn
 * es noch nicht geöffnet wurde – wie die Arbeitsmappe, in der sie immer stehen.
 */
function withDefaults(state: WorkspaceState, sheets: readonly SheetModule[]): WorkspaceState {
  const filled: Record<SheetId, WorkspaceState['sheets'][SheetId]> = { ...state.sheets }
  for (const sheet of availableSheets(sheets)) {
    if (!(sheet.id in filled) && sheet.definition.layout !== 'list') filled[sheet.id] = defaultInputs(sheet.definition)
  }
  return { ...state, sheets: filled }
}

/** Beispielwerte aller Blätter mit Rechenkern; Listenblätter erhalten eine Beispieleinheit. */
function sampleState(method: AvailableSheet | undefined, sheets: readonly SheetModule[]): WorkspaceState {
  if (!method) return withDefaults(emptyWorkspace(), sheets)
  const inputs: Record<SheetId, WorkspaceState['sheets'][SheetId]> = {}
  for (const sheet of availableSheets(sheets)) {
    const isMethod = findVariant(sheet.id) !== undefined
    if (sheet.definition.layout === 'list') inputs[sheet.id] = [sheet.sample.inputs]
    else if (!isMethod || sheet.id === method.id) inputs[sheet.id] = sheet.sample.inputs
  }
  return withDefaults({ ...emptyWorkspace(), activeMethod: method.id, sheets: inputs }, sheets)
}

const firstMethod = (sheets: readonly SheetModule[]): AvailableSheet | undefined => availableSheets(sheets).find((sheet) => findVariant(sheet.id) !== undefined)

export function useSamplingSession(options: SessionOptions): SamplingSession {
  const sheets = options.sheets
  const workspace = shallowRef<WorkspaceState>(withDefaults(options.initial ?? emptyWorkspace(), sheets()))
  const meta = ref<SessionMeta>({ fileName: null, dirty: false, sample: false })
  const step = ref<StepId>('method')
  const selectedUnit = ref(0)
  const messages = useMessages()
  const { find, context, usedStrata: _used, ...view } = useSessionView(workspace, step, selectedUnit, { sheets, t: options.t, locale: options.locale ?? (() => 'de') })
  const pickerOpen = ref(view.activeSheet.value === null)

  /** Eingaben eines Blatts schreiben; der Arbeitsstand gilt danach als geändert. */
  function write(id: SheetId, inputs: WorkspaceState['sheets'][SheetId]): void {
    workspace.value = { ...workspace.value, sheets: { ...workspace.value.sheets, [id]: inputs } }
    meta.value = { ...meta.value, dirty: true }
  }

  function selectMethod(id: SheetId): void {
    if (!find(id)) return
    const changed = workspace.value.activeMethod !== null && workspace.value.activeMethod !== id
    workspace.value = { ...workspace.value, activeMethod: id }
    if (changed) meta.value = { ...meta.value, dirty: true }
    step.value = 'method'
    pickerOpen.value = false
  }

  function setInput(cell: CellAddress, value: CellValue): void {
    const sheet = view.currentSheet.value
    if (!sheet) return
    if (sheet.definition.layout !== 'list') return write(sheet.id, { ...ownInputs(workspace.value, sheet.id), [cell]: value })
    const rows = listRows(workspace.value, sheet.id).map((row: CellMap, index) => (index === selectedUnit.value ? { ...row, [cell]: value } : row))
    write(sheet.id, rows)
  }

  function replace(state: WorkspaceState, next: SessionMeta, added: readonly Omit<SessionNotice, 'id'>[] = []): void {
    workspace.value = withDefaults(state, sheets())
    meta.value = next
    messages.set(added)
    selectedUnit.value = 0
    step.value = 'method'
    pickerOpen.value = find(state.activeMethod) === null
  }

  /** Neu: leere Formulare mit den Vorgaben der Vorlage; das gewählte Verfahren bleibt. */
  const reset = (): void => replace({ ...emptyWorkspace(), activeMethod: view.activeSheet.value?.id ?? null }, { fileName: null, dirty: false, sample: false })

  /** Beispielwerte laden; ohne gewähltes Verfahren das erste Methodenblatt mit Rechenkern. */
  const loadSample = (): void => replace(sampleState(view.activeSheet.value ?? firstMethod(sheets()), sheets()), { fileName: null, dirty: false, sample: true })

  const actions = useSheetActions({ view: { ...view, find, context, usedStrata: _used }, selectedUnit, write, state: () => workspace.value, t: options.t, say: messages.say, notify: messages.notify })
  const { set: _set, ...shared } = messages
  return {
    workspace,
    meta,
    pickerOpen,
    step,
    selectedUnit,
    ...view,
    ...shared,
    ...actions,
    selectMethod,
    setStep: (next) => (step.value = next),
    setInput,
    reset,
    loadSample,
    replace,
    markSaved: (fileName) => (meta.value = { fileName, dirty: false, sample: false }),
  }
}
