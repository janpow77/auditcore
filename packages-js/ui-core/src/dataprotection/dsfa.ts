// Zustandsautomat von <flowaudit-dsfa> (Vue und React): Übersicht, Erhebung mit
// Vorschau der Bibliothek, Entscheidung, DSB-Stellungnahme, Freigabe, Neubewertung.

import { saveFile } from '@flowaudit/common/browser'
import { createDelay, createRunner, createStore, IDLE, type RequestState, type Store } from '../store'
import { sameSurvey, surveyFrom, type TabItem } from './dsfaView'
import type { DataProtectionKey, DataProtectionTranslate } from './messages'
import { asError, type DataProtectionError, type RequestHooks } from './requests'
import type {
  AssessmentExportFormat,
  AssessmentView,
  DataProtectionPort,
  DataProtectionProfile,
  DecisionInput,
  OverviewRow,
  Proposal,
  SurveyInput,
} from './types'

export type DsfaStep = 'saved' | 'decided' | 'dpo' | 'released' | 'started'
export type DsfaTab = 'screening' | 'risk' | 'result'

export interface DsfaHooks extends RequestHooks {
  onChanged?: (step: DsfaStep, view: AssessmentView) => void
  /** Wartezeit der Vorschau nach einer Eingabe (ms). */
  previewDelay?: number
}

export interface DsfaData extends RequestState<DataProtectionError> {
  profile: DataProtectionProfile | null
  rows: OverviewRow[]
  view: AssessmentView | null
  survey: SurveyInput | null
  preview: Proposal | null
  tab: DsfaTab
}

export interface DsfaDerived {
  dirty: boolean
  proposal: Proposal | null
  /** Vorschau anzeigen: ungespeicherte Eingaben und eine berechnete Vorschau liegen vor. */
  showPreview: boolean
}

export function dsfaDerived(state: DsfaData): DsfaDerived {
  const saved = state.view && state.profile ? surveyFrom(state.view, state.profile) : null
  const dirty = !!state.survey && !sameSurvey(state.survey, saved)
  const proposal = dirty && state.preview ? state.preview : state.view?.proposal ?? null
  return { dirty, proposal, showPreview: dirty && !!state.preview }
}

/** Nur lesen: nicht bearbeitbar oder gesperrte (freigegebene) Fassung. */
export function dsfaReadonly(state: DsfaData, editable: boolean): boolean {
  return !editable || !!state.view?.locked
}

export function dsfaTabs(t: DataProtectionTranslate): TabItem[] {
  return [
    { key: 'screening', label: t('stepScreening') },
    { key: 'risk', label: t('stepRisk') },
    { key: 'result', label: t('stepResult') },
  ]
}

export const DSFA_NOTICES: Readonly<Record<DsfaStep, DataProtectionKey>> = {
  saved: 'assessmentSaved', decided: 'decisionSaved', dpo: 'dpoSaved', released: 'assessmentReleased', started: 'assessmentSaved',
}

const INITIAL: DsfaData = { ...IDLE, profile: null, rows: [], view: null, survey: null, preview: null, tab: 'screening' }

type Run = ReturnType<typeof createRunner<DataProtectionPort, DataProtectionError, DsfaData>>

function show(store: Store<DsfaData>, next: AssessmentView): void {
  const profile = store.get().profile
  store.set({ view: next, preview: null, survey: profile ? surveyFrom(next, profile) : null })
}

/** Lesen: Profil und Übersicht, einzelne Abschätzung, Vorschau der Bibliothek. */
function readActions(store: Store<DsfaData>, run: Run, hooks: DsfaHooks) {
  const delay = createDelay(() => hooks.previewDelay ?? 400)

  async function load(): Promise<void> {
    const loaded = await run('load', async (active) => Promise.all([active.profile(), active.overview()]))
    if (loaded) store.set({ profile: loaded[0], rows: loaded[1].items })
  }

  async function open(assessmentId: string): Promise<void> {
    const found = await run('open', (active) => active.assessment(assessmentId))
    if (found) show(store, found)
  }

  async function openActivity(activityId: string): Promise<void> {
    const row = store.get().rows.find((entry) => entry.id === activityId)
    if (row?.dsfa) await open(row.dsfa.id)
  }

  async function calculate(): Promise<void> {
    const current = store.get().survey
    if (!current) return
    const result = await run('preview', (active) => active.calculate(current.answers, current.scenarios))
    if (result && store.get().survey === current) store.set({ preview: result })
  }

  function edit(next: SurveyInput): void {
    store.set({ survey: next })
    delay.schedule(() => void calculate())
  }

  return { load, open, openActivity, calculate, edit, dispose: delay.cancel }
}

type Task = (active: DataProtectionPort, current: AssessmentView) => Promise<AssessmentView>

/** Schreiben: jede Aktion ersetzt die angezeigte Fassung und liest die Übersicht neu. */
function writeActions(store: Store<DsfaData>, run: Run, changed: (step: DsfaStep, view: AssessmentView) => void) {
  async function refreshRows(): Promise<void> {
    const overview = await run('overview', (active) => active.overview())
    if (overview) store.set({ rows: overview.items })
  }

  async function step(kind: DsfaStep, task: Task): Promise<AssessmentView | null> {
    const current = store.get().view
    if (!current) return null
    const next = await run(kind, (active) => task(active, current))
    if (!next) return null
    show(store, next)
    changed(kind, next)
    await refreshRows()
    return next
  }

  async function start(activityId: string): Promise<void> {
    const created = await run('started', (active) => active.startAssessment(activityId))
    if (!created) return
    show(store, created)
    changed('started', created)
    await refreshRows()
  }

  function payload(current: AssessmentView): SurveyInput {
    const { survey, profile } = store.get()
    const data = survey ?? surveyFrom(current, profile as DataProtectionProfile)
    return profile?.dossier_fields.length ? data : { ...data, dossier: undefined }
  }

  return {
    start,
    save: () => step('saved', (active, current) => active.updateAssessment(current.id, current.revision, payload(current))),
    decide: (decision: DecisionInput) => step('decided', (active, current) => active.decide(current.id, current.revision, decision)),
    requestDpo: (from: string, on: string) => step('dpo', (active, current) => active.requestDpo(current.id, current.revision, from, on)),
    release: () => step('released', (active, current) => active.releaseAssessment(current.id, current.revision)),
    reassess: () => step('started', (active, current) => active.reassess(current.id)),
  }
}

export interface DsfaControllerOptions extends DsfaHooks {
  port: () => DataProtectionPort | null
  t: () => DataProtectionTranslate
}

export function createDsfaController(options: DsfaControllerOptions) {
  const store = createStore<DsfaData>(INITIAL)
  const hooks: DsfaHooks = { ...options, networkMessage: options.networkMessage ?? ((message) => options.t()('networkError', { message })) }
  const run = createRunner(store, options.port, (error) => asError(error, hooks), hooks.onError)
  const changed = (step: DsfaStep, view: AssessmentView): void => {
    store.set({ notice: options.t()(DSFA_NOTICES[step], { revision: view.revision, version: view.version }) })
    hooks.onChanged?.(step, view)
  }

  async function exportReport(format: AssessmentExportFormat): Promise<boolean> {
    const current = store.get().view
    if (!current) return false
    const file = await run('export', (active) => active.exportAssessment(current.id, format))
    if (!file) return false
    if (typeof URL.createObjectURL === 'function') saveFile(file)
    return true
  }

  /** Beim Setzen eines Ports: Profil und Übersicht laden, optional eine Tätigkeit öffnen. */
  async function connect(activityId: string): Promise<void> {
    await read.load()
    if (activityId) await read.openActivity(activityId)
  }

  const read = readActions(store, run, hooks)
  return {
    store,
    connect,
    exportReport,
    setTab: (tab: string) => store.set({ tab: tab as DsfaTab }),
    setNotice: (notice: string) => store.set({ notice }),
    ...read,
    ...writeActions(store, run, changed),
  }
}

export type DsfaController = ReturnType<typeof createDsfaController>
