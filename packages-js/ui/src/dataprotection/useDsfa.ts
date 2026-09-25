// Zustand und Aktionen von <flowaudit-dsfa> über einen DataProtectionPort.

import { computed, shallowRef, type ComputedRef, type ShallowRef } from 'vue'
import { saveFile } from '../rest'
import { sameSurvey, surveyFrom } from './dsfaView'
import { createRequests, type RequestHooks, type Requests } from './requests'
import type {
  AssessmentExportFormat,
  AssessmentView,
  DataProtectionPort,
  DecisionInput,
  OverviewRow,
  DataProtectionProfile,
  Proposal,
  SurveyInput,
} from './types'

export type DsfaStep = 'saved' | 'decided' | 'dpo' | 'released' | 'started'

export interface DsfaHooks extends RequestHooks {
  onChanged?: (step: DsfaStep, view: AssessmentView) => void
  /** Wartezeit der Vorschau nach einer Eingabe (ms). */
  previewDelay?: number
}

export interface DsfaState extends Requests<DataProtectionPort> {
  profile: ShallowRef<DataProtectionProfile | null>
  rows: ShallowRef<OverviewRow[]>
  view: ShallowRef<AssessmentView | null>
  survey: ShallowRef<SurveyInput | null>
  preview: ShallowRef<Proposal | null>
  dirty: ComputedRef<boolean>
  proposal: ComputedRef<Proposal | null>
  load: () => Promise<void>
  open: (assessmentId: string) => Promise<void>
  openActivity: (activityId: string) => Promise<void>
  start: (activityId: string) => Promise<void>
  edit: (survey: SurveyInput) => void
  calculate: () => Promise<void>
  save: () => Promise<AssessmentView | null>
  decide: (decision: DecisionInput) => Promise<AssessmentView | null>
  requestDpo: (from: string, on: string) => Promise<AssessmentView | null>
  release: () => Promise<AssessmentView | null>
  reassess: () => Promise<AssessmentView | null>
  exportReport: (format: AssessmentExportFormat) => Promise<boolean>
}

interface Core {
  requests: Requests<DataProtectionPort>
  hooks: DsfaHooks
  profile: ShallowRef<DataProtectionProfile | null>
  rows: ShallowRef<OverviewRow[]>
  view: ShallowRef<AssessmentView | null>
  survey: ShallowRef<SurveyInput | null>
  preview: ShallowRef<Proposal | null>
}

function show(core: Core, next: AssessmentView): void {
  core.view.value = next
  core.preview.value = null
  core.survey.value = core.profile.value ? surveyFrom(next, core.profile.value) : null
}

async function refreshRows(core: Core): Promise<void> {
  const overview = await core.requests.run('overview', (active) => active.overview())
  if (overview) core.rows.value = overview.items
}

/** Lesen: Profil und Übersicht, einzelne Abschätzung, Vorschau der Bibliothek. */
function readActions(core: Core) {
  const { requests, profile, rows, survey, preview, hooks } = core
  let timer: ReturnType<typeof setTimeout> | undefined

  async function load(): Promise<void> {
    const loaded = await requests.run('load', async (active) => Promise.all([active.profile(), active.overview()]))
    if (!loaded) return
    profile.value = loaded[0]
    rows.value = loaded[1].items
  }

  async function open(assessmentId: string): Promise<void> {
    const found = await requests.run('open', (active) => active.assessment(assessmentId))
    if (found) show(core, found)
  }

  async function openActivity(activityId: string): Promise<void> {
    const row = rows.value.find((entry) => entry.id === activityId)
    if (row?.dsfa) await open(row.dsfa.id)
  }

  async function calculate(): Promise<void> {
    const current = survey.value
    if (!current) return
    const result = await requests.run('preview', (active) => active.calculate(current.answers, current.scenarios))
    if (result && survey.value === current) preview.value = result
  }

  function edit(next: SurveyInput): void {
    survey.value = next
    clearTimeout(timer)
    timer = setTimeout(() => void calculate(), hooks.previewDelay ?? 400)
  }

  return { load, open, openActivity, calculate, edit }
}

type Task = (active: DataProtectionPort, current: AssessmentView) => Promise<AssessmentView>

/** Schreiben: jede Aktion ersetzt die angezeigte Fassung und liest die Übersicht neu. */
function writeActions(core: Core) {
  const { requests, profile, view, survey, hooks } = core

  async function step(kind: DsfaStep, task: Task): Promise<AssessmentView | null> {
    const current = view.value
    if (!current) return null
    const next = await requests.run(kind, (active) => task(active, current))
    if (!next) return null
    show(core, next)
    hooks.onChanged?.(kind, next)
    await refreshRows(core)
    return next
  }

  async function start(activityId: string): Promise<void> {
    const created = await requests.run('started', (active) => active.startAssessment(activityId))
    if (!created) return
    show(core, created)
    hooks.onChanged?.('started', created)
    await refreshRows(core)
  }

  function payload(current: AssessmentView): SurveyInput {
    const data = survey.value ?? surveyFrom(current, profile.value as DataProtectionProfile)
    return profile.value?.dossier_fields.length ? data : { ...data, dossier: undefined }
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

export function useDsfa(port: () => DataProtectionPort | null, hooks: DsfaHooks = {}): DsfaState {
  const core: Core = {
    requests: createRequests(port, hooks),
    hooks,
    profile: shallowRef<DataProtectionProfile | null>(null),
    rows: shallowRef<OverviewRow[]>([]),
    view: shallowRef<AssessmentView | null>(null),
    survey: shallowRef<SurveyInput | null>(null),
    preview: shallowRef<Proposal | null>(null),
  }
  const { requests, profile, view, survey, preview } = core
  const saved = computed(() => (view.value && profile.value ? surveyFrom(view.value, profile.value) : null))
  const dirty = computed(() => !!survey.value && !sameSurvey(survey.value, saved.value))
  const proposal = computed(() => (dirty.value && preview.value ? preview.value : view.value?.proposal ?? null))

  async function exportReport(format: AssessmentExportFormat): Promise<boolean> {
    const current = view.value
    if (!current) return false
    const file = await requests.run('export', (active) => active.exportAssessment(current.id, format))
    if (!file) return false
    if (typeof URL.createObjectURL === 'function') saveFile(file)
    return true
  }

  return { ...requests, ...core, dirty, proposal, exportReport, ...readActions(core), ...writeActions(core) }
}
