// Zustand und Aktionen der Screening-Trefferprüfung über einen ScreeningPort.

import { computed, reactive, ref, shallowRef, type ComputedRef, type Ref, type ShallowRef } from 'vue'
import { RestError } from '../rest'
import type {
  HitView,
  LogView,
  Outcome,
  RunRequest,
  RunSummary,
  RunView,
  ScreeningPort,
  SettingsView,
  SourcesView,
  SubjectView,
} from './types'
import { emptyFilter, filterSubjects, findHit, nextOpenHit, replaceHit, type HitFilter } from './view'

/** Fehler einer Portanfrage: Meldung des Servers bzw. `network_error` mit Status 0. */
export interface ScreeningError {
  code: string
  message: string
  status: number
}

export interface ReviewEvents {
  onRunCreated?: (run: RunView) => void
  onDecided?: (payload: { runId: string; hitId: string; status: string }) => void
  onError?: (error: ScreeningError) => void
  /** Meldung für Fehler ohne Serverantwort (Netz, Programmfehler). */
  networkMessage?: (message: string) => string
}

function asScreeningError(error: unknown, events: ReviewEvents): ScreeningError {
  if (error instanceof RestError) return { code: error.code, message: error.message, status: error.status }
  const raw = error instanceof Error ? error.message : String(error)
  return { code: 'network_error', message: events.networkMessage?.(raw) ?? raw, status: 0 }
}

interface DecisionContext {
  client: ScreeningPort
  events: ReviewEvents
  run: ShallowRef<RunView | null>
  log: ShallowRef<LogView | null>
  runs: ShallowRef<RunSummary[]>
  selected: ComputedRef<{ subject: SubjectView; hit: HitView } | null>
  guard: <T>(action: () => Promise<T>) => Promise<T | null>
}

function decisionActions(ctx: DecisionContext) {
  const { client, events, run, log, runs, selected, guard } = ctx

  async function refresh(runId: string, hitId: string, status: string): Promise<void> {
    const [view, entries, list] = await Promise.all([client.run(runId), client.log(runId), client.runs()])
    run.value = view
    log.value = entries
    runs.value = list.runs
    events.onDecided?.({ runId, hitId, status })
  }

  async function decide(outcome: Outcome, reason: string, fourEyes: boolean): Promise<boolean> {
    const current = selected.value
    const view = run.value
    if (!current || !view) return false
    const hit = await guard(() =>
      client.decide(view.run_id, current.hit.hit_id, {
        outcome,
        reason,
        four_eyes: fourEyes,
        expected_sequence: current.hit.review.sequence,
      }),
    )
    if (!hit) return false
    run.value = replaceHit(view, hit)
    await guard(() => refresh(view.run_id, hit.hit_id, hit.review.status))
    return true
  }

  async function secondReview(approve: boolean, reason: string): Promise<boolean> {
    const current = selected.value
    const view = run.value
    if (!current || !view) return false
    const hit = await guard(() =>
      client.secondReview(view.run_id, current.hit.hit_id, {
        approve,
        reason,
        expected_sequence: current.hit.review.sequence,
      }),
    )
    if (!hit) return false
    run.value = replaceHit(view, hit)
    await guard(() => refresh(view.run_id, hit.hit_id, hit.review.status))
    return true
  }

  return { decide, secondReview }
}

interface LoadContext {
  client: ScreeningPort
  events: ReviewEvents
  settings: ShallowRef<SettingsView | null>
  sources: ShallowRef<SourcesView | null>
  runs: ShallowRef<RunSummary[]>
  run: ShallowRef<RunView | null>
  log: ShallowRef<LogView | null>
  selectedHitId: Ref<string | null>
  guard: <T>(action: () => Promise<T>) => Promise<T | null>
}

function loadActions(ctx: LoadContext) {
  const { client, events, settings, sources, runs, run, log, selectedHitId, guard } = ctx

  async function load(): Promise<void> {
    await guard(async () => {
      const [s, src, list] = await Promise.all([client.settings(), client.sources(), client.runs()])
      settings.value = s
      sources.value = src
      runs.value = list.runs
    })
  }

  async function openRun(runId: string): Promise<void> {
    await guard(async () => {
      const [view, entries] = await Promise.all([client.run(runId), client.log(runId)])
      run.value = view
      log.value = entries
      selectedHitId.value = nextOpenHit(view.subjects, null)
    })
  }

  async function createRun(request: RunRequest): Promise<boolean> {
    const created = await guard(() => client.createRun(request))
    if (!created) return false
    run.value = created
    selectedHitId.value = nextOpenHit(created.subjects, null)
    log.value = await client.log(created.run_id).catch(() => null)
    runs.value = (await client.runs().catch(() => ({ runs: runs.value }))).runs
    events.onRunCreated?.(created)
    return true
  }

  return { load, openRun, createRun }
}

/** Leitet jede Anfrage an den aktuell gesetzten Port weiter (Web Components setzen ihn erst nach dem Einhängen). */
function delegate(port: () => ScreeningPort | null): ScreeningPort {
  const active = (): ScreeningPort => {
    const current = port()
    if (!current) throw new Error('no_port')
    return current
  }
  return {
    settings: () => active().settings(),
    sources: () => active().sources(),
    runs: () => active().runs(),
    createRun: (request) => active().createRun(request),
    run: (runId, query) => active().run(runId, query),
    log: (runId) => active().log(runId),
    decide: (runId, hitId, decision) => active().decide(runId, hitId, decision),
    secondReview: (runId, hitId, review) => active().secondReview(runId, hitId, review),
  }
}

export function useScreeningReview(port: () => ScreeningPort | null, events: ReviewEvents = {}) {
  const client = delegate(port)
  const settings = shallowRef<SettingsView | null>(null)
  const sources = shallowRef<SourcesView | null>(null)
  const runs = shallowRef<RunSummary[]>([])
  const run = shallowRef<RunView | null>(null)
  const log = shallowRef<LogView | null>(null)
  const selectedHitId = ref<string | null>(null)
  const filter = reactive<HitFilter>(emptyFilter())
  const busy = ref(false)
  const error = ref<ScreeningError | null>(null)

  const visibleSubjects = computed(() => (run.value ? filterSubjects(run.value.subjects, filter) : []))
  const selected = computed(() => findHit(run.value, selectedHitId.value))

  async function guard<T>(action: () => Promise<T>): Promise<T | null> {
    busy.value = true
    error.value = null
    try {
      return await action()
    } catch (caught) {
      const failure = asScreeningError(caught, events)
      error.value = failure
      events.onError?.(failure)
      return null
    } finally {
      busy.value = false
    }
  }

  const context = { client, events, settings, sources, runs, run, log, selectedHitId, selected, guard }
  const { load, openRun, createRun } = loadActions(context)
  const { decide, secondReview } = decisionActions(context)

  function selectNext(): void {
    if (run.value) selectedHitId.value = nextOpenHit(run.value.subjects, selectedHitId.value)
  }

  return {
    settings,
    sources,
    runs,
    run,
    log,
    filter,
    busy,
    error,
    selectedHitId,
    selected,
    visibleSubjects,
    load,
    openRun,
    createRun,
    decide,
    secondReview,
    selectNext,
  }
}

export type ScreeningReviewState = ReturnType<typeof useScreeningReview>
