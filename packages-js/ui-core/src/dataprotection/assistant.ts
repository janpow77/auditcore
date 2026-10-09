// Zustandsautomat des Datenschutz-Assistenten (Vue und React): Laden,
// Antworten, geführter oder freier Modus, Checkliste. Der Assistent ist
// optional: im freien Modus ist jeder Schritt erreichbar, im geführten Modus
// geht es Schritt für Schritt. Alle Prüfungen laufen auf dem Server.

import { requestJson, type RestOptions } from '@auditcore/common'
import { createRunner, createStore, IDLE, type RequestState } from '../store'
import type {
  AssistantMode,
  AssistantPort,
  AssistantQuestion,
  AssistantStep,
  ChecklistChange,
  WorkspaceOverview,
} from './assistantTypes'
import type { DataProtectionTranslate } from './messages'
import { asError, prefixedLabel, type DataProtectionError, type RequestHooks } from './requests'

const segment = encodeURIComponent

/** Port auf die Arbeitsbereichs-Endpunkte von `auditcore_dataprotection.web`. */
export function createAssistantRestPort(options: RestOptions): AssistantPort {
  const one = (id: string, action: string): string => `/activities/${segment(id)}${action}`
  return {
    workspace: (id) => requestJson(options, one(id, '/workspace')),
    answer: (id, questionId, value, justification, expectedRevision) =>
      requestJson(options, one(id, '/answers'), {
        question_id: questionId,
        value,
        justification,
        expected_revision: expectedRevision,
      }),
    confirm: (id, questionId, expectedRevision) =>
      requestJson(options, one(id, '/answers/confirm'), { question_id: questionId, expected_revision: expectedRevision }),
    navigate: (id, mode, step, expectedRevision) =>
      requestJson(options, one(id, '/navigate'), { mode, step, expected_revision: expectedRevision }),
    checklist: (id, itemId, change, expectedRevision) =>
      requestJson(options, one(id, `/checklist/${segment(itemId)}`), { ...change, expected_revision: expectedRevision }),
  }
}

export interface Draft {
  value: string
  justification: string
}

export type AssistantTab = 'assistent' | 'checkliste' | 'status'

export interface AssistantData extends RequestState<DataProtectionError> {
  overview: WorkspaceOverview | null
  drafts: Readonly<Record<string, Draft>>
  /** Fehler je Frage (GUI-08: Sprung zum Feld, Eingabe bleibt erhalten). */
  fieldErrors: Readonly<Record<string, string>>
  tab: AssistantTab
}

export interface AssistantView {
  mode: AssistantMode
  step: AssistantStep | null
  steps: AssistantStep[]
  position: number
  completed: number
  previous: string | null
  next: string | null
  openTasks: number
}

const EMPTY_ASSISTANT = {
  mode: 'gefuehrt' as AssistantMode,
  current_step: '',
  previous_step: null,
  next_step: null,
  steps: [] as AssistantStep[],
  tasks: [] as unknown[],
}

/** Abgeleitete Werte für beide Oberflächen (reine Funktion). */
export function assistantView(state: AssistantData): AssistantView {
  const assistant = state.overview?.assistent ?? EMPTY_ASSISTANT
  const steps = assistant.steps
  const step = steps.find((entry) => entry.id === assistant.current_step) ?? steps[0] ?? null
  return {
    mode: assistant.mode,
    step,
    steps,
    position: step ? steps.indexOf(step) + 1 : 0,
    completed: steps.filter((entry) => entry.status === 'vollstaendig').length,
    previous: assistant.previous_step,
    next: assistant.next_step,
    openTasks: assistant.tasks.length,
  }
}

/** Eingabe einer Frage: lokaler Entwurf, sonst gespeicherte Antwort bzw. Verzeichniswert. */
export function draftOf(state: AssistantData, question: AssistantQuestion): Draft {
  return (
    state.drafts[question.id] ?? {
      value: question.answer?.value ?? question.value ?? '',
      justification: question.answer?.justification ?? '',
    }
  )
}

/** Vorschläge aus Vorlage, Import oder KI sind bis zur Bestätigung unbestätigt (GUI-16). */
export function isSuggestion(question: AssistantQuestion): boolean {
  return question.answer !== null && question.answer.origin !== 'bestaetigt'
}

export function needsJustification(question: AssistantQuestion, value: string): boolean {
  return value === 'nicht_anwendbar' || question.justify_values.includes(value)
}

const DPIA_TARGET = /^(screening|assessment):/

function expectedRevision(overview: WorkspaceOverview | null, question?: AssistantQuestion): number | null {
  if (!overview) return null
  if (question && DPIA_TARGET.test(question.target)) return overview.folgenabschaetzung?.revision ?? null
  return overview.register.status === 'entwurf' ? overview.register.revision : null
}

export interface AssistantControllerOptions extends RequestHooks {
  port: () => AssistantPort | null
  activityId: () => string
  t: () => DataProtectionTranslate
  onChange?: (overview: WorkspaceOverview) => void
}

const INITIAL: AssistantData = { ...IDLE, overview: null, drafts: {}, fieldErrors: {}, tab: 'assistent' }

type Store = ReturnType<typeof createStore<AssistantData>>
type Run = ReturnType<typeof createRunner<AssistantPort, DataProtectionError, AssistantData>>
type Accept = (overview: WorkspaceOverview | null, notice?: string) => void

function findQuestion(store: Store, questionId: string): AssistantQuestion | undefined {
  return store.get().overview?.assistent.steps.flatMap((step) => step.questions).find((entry) => entry.id === questionId)
}

/** Antworten und Vorschläge übernehmen; Fehler bleiben an der Frage stehen (GUI-08). */
function answerActions(store: Store, run: Run, accept: Accept, options: AssistantControllerOptions) {
  async function answer(questionId: string): Promise<boolean> {
    const current = findQuestion(store, questionId)
    if (!current) return false
    const draft = draftOf(store.get(), current)
    const revision = expectedRevision(store.get().overview, current)
    const result = await run('answer', (port) =>
      port.answer(options.activityId(), questionId, draft.value, draft.justification, revision),
    )
    if (!result) {
      const message = store.get().error?.message ?? ''
      store.set((state) => ({ fieldErrors: { ...state.fieldErrors, [questionId]: message } }))
      return false
    }
    store.set((state) => {
      const { [questionId]: _done, ...drafts } = state.drafts
      const { [questionId]: _fixed, ...fieldErrors } = state.fieldErrors
      return { drafts, fieldErrors }
    })
    accept(result, options.t()('assistantSaved'))
    return true
  }

  async function confirm(questionId: string): Promise<void> {
    const revision = expectedRevision(store.get().overview, findQuestion(store, questionId))
    const result = await run('confirm', (port) => port.confirm(options.activityId(), questionId, revision))
    accept(result, options.t()('assistantConfirmed'))
  }

  function setDraft(questionId: string, draft: Draft): void {
    store.set((state) => ({ drafts: { ...state.drafts, [questionId]: draft } }))
  }

  return { answer, confirm, setDraft }
}

/** Schritte, Modus und Checkliste. */
function moveActions(store: Store, run: Run, accept: Accept, options: AssistantControllerOptions) {
  async function navigate(mode: AssistantMode, step: string): Promise<void> {
    const revision = expectedRevision(store.get().overview)
    accept(await run('navigate', (port) => port.navigate(options.activityId(), mode, step, revision)))
  }

  async function goTo(step: string | null): Promise<void> {
    if (step) await navigate(assistantView(store.get()).mode, step)
  }

  async function setMode(mode: AssistantMode): Promise<void> {
    const view = assistantView(store.get())
    if (view.step) await navigate(mode, view.step.id)
  }

  async function changeItem(itemId: string, change: ChecklistChange): Promise<void> {
    const revision = expectedRevision(store.get().overview)
    const result = await run('checklist', (port) => port.checklist(options.activityId(), itemId, change, revision))
    accept(result, options.t()('assistantSaved'))
  }

  return {
    goTo,
    setMode,
    changeItem,
    next: () => goTo(assistantView(store.get()).next),
    previous: () => goTo(assistantView(store.get()).previous),
  }
}

export function createAssistantController(options: AssistantControllerOptions) {
  const store = createStore<AssistantData>(INITIAL)
  const hooks: RequestHooks = { ...options, networkMessage: options.networkMessage ?? ((message) => options.t()('networkError', { message })) }
  const run = createRunner(store, options.port, (error) => asError(error, hooks), hooks.onError)

  function accept(overview: WorkspaceOverview | null, notice = ''): void {
    if (!overview) return
    store.set({ overview, notice })
    options.onChange?.(overview)
  }

  async function load(): Promise<void> {
    accept(await run('load', (port) => port.workspace(options.activityId())))
  }

  return {
    store,
    load,
    ...answerActions(store, run, accept, options),
    ...moveActions(store, run, accept, options),
    setTab: (tab: AssistantTab) => store.set({ tab }),
  }
}

export type AssistantController = ReturnType<typeof createAssistantController>

const CLOSED_VALUES: Readonly<Partial<Record<AssistantQuestion['kind'], readonly string[]>>> = {
  ja_nein_unklar: ['ja', 'nein', 'unklar'],
  umsetzung: ['nicht_begonnen', 'geplant', 'umgesetzt', 'wirksam_nachgewiesen'],
}

/** Auswahlwerte einer Frage mit Beschriftung; „nicht anwendbar“ nur, wo vorgesehen. */
export function questionOptions(t: DataProtectionTranslate, question: AssistantQuestion): { key: string; title: string }[] {
  const closed = CLOSED_VALUES[question.kind]
  const base = closed ? closed.map((key) => ({ key, title: prefixedLabel(t, 'value', key) })) : question.choices
  return question.na_allowed ? [...base, { key: 'nicht_anwendbar', title: t('value_nicht_anwendbar') }] : base
}

/** Feldkennung einer Frage im DOM (Sprungziel der Fehlerübersicht). */
export function questionFieldId(question: { id: string }): string {
  return `fa-q-${question.id.replace(/[^A-Za-z0-9_-]/g, '-')}`
}

/** Beschriftung eines Statuswerts (Unterstriche als Leerzeichen, falls kein Text hinterlegt). */
export function axisValueLabel(value: string): string {
  return value.replace(/_/g, ' ')
}

/** Geführt: zurück zu jedem früheren Schritt, vorwärts nur zum nächsten; frei: jeder Schritt. */
export function stepReachable(view: AssistantView, index: number): boolean {
  if (view.mode === 'frei') return true
  return index < view.position || view.steps[index]?.id === view.next
}
