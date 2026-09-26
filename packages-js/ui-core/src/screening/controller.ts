// Zustandsautomat der Screening-Trefferprüfung (<flowaudit-screening-review>,
// Vue und React): Laden über den ScreeningPort, Prüfläufe, Filter, Auswahl,
// Entscheidung und Zweitprüfung. Reine Selektoren liefern die Anzeige.

import { RestError } from '@auditcore/common'
import { createStore, type Store } from '../store'
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

export interface ScreeningData {
  settings: SettingsView | null
  sources: SourcesView | null
  runs: RunSummary[]
  run: RunView | null
  log: LogView | null
  selectedHitId: string | null
  filter: HitFilter
  busy: boolean
  error: ScreeningError | null
}

export interface ScreeningSelection {
  visibleSubjects: SubjectView[]
  selected: { subject: SubjectView; hit: HitView } | null
}

export function selectScreening(state: ScreeningData): ScreeningSelection {
  return {
    visibleSubjects: state.run ? filterSubjects(state.run.subjects, state.filter) : [],
    selected: findHit(state.run, state.selectedHitId),
  }
}

export function asScreeningError(error: unknown, events: ReviewEvents): ScreeningError {
  if (error instanceof RestError) return { code: error.code, message: error.message, status: error.status }
  const raw = error instanceof Error ? error.message : String(error)
  return { code: 'network_error', message: events.networkMessage?.(raw) ?? raw, status: 0 }
}

/** Leitet jede Anfrage an den aktuell gesetzten Port weiter (Web Components setzen ihn erst nach dem Einhängen). */
function delegate(port: () => ScreeningPort | null | undefined): ScreeningPort {
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

type Guard = <T>(action: () => Promise<T>) => Promise<T | null>

interface Context {
  client: ScreeningPort
  events: () => ReviewEvents
  store: Store<ScreeningData>
  guard: Guard
}

function loadActions({ client, events, store, guard }: Context) {
  async function load(): Promise<void> {
    await guard(async () => {
      const [settings, sources, list] = await Promise.all([client.settings(), client.sources(), client.runs()])
      store.set({ settings, sources, runs: list.runs })
    })
  }

  async function openRun(runId: string): Promise<void> {
    await guard(async () => {
      const [run, log] = await Promise.all([client.run(runId), client.log(runId)])
      store.set({ run, log, selectedHitId: nextOpenHit(run.subjects, null) })
    })
  }

  async function createRun(request: RunRequest): Promise<boolean> {
    const created = await guard(() => client.createRun(request))
    if (!created) return false
    store.set({ run: created, selectedHitId: nextOpenHit(created.subjects, null) })
    store.set({ log: await client.log(created.run_id).catch(() => null) })
    store.set({ runs: (await client.runs().catch(() => ({ runs: store.get().runs }))).runs })
    events().onRunCreated?.(created)
    return true
  }

  return { load, openRun, createRun }
}

function decisionActions({ client, events, store, guard }: Context) {
  async function refresh(runId: string, hitId: string, status: string): Promise<void> {
    const [run, log, list] = await Promise.all([client.run(runId), client.log(runId), client.runs()])
    store.set({ run, log, runs: list.runs })
    events().onDecided?.({ runId, hitId, status })
  }

  /** Sendet eine Aktion zum ausgewählten Treffer mit der gelesenen Sequenz und aktualisiert danach Lauf und Protokoll. */
  async function submit(send: (run: RunView, hit: HitView) => Promise<HitView>): Promise<boolean> {
    const current = selectScreening(store.get()).selected
    const view = store.get().run
    if (!current || !view) return false
    const hit = await guard(() => send(view, current.hit))
    if (!hit) return false
    store.set({ run: replaceHit(view, hit) })
    await guard(() => refresh(view.run_id, hit.hit_id, hit.review.status))
    return true
  }

  const decide = (outcome: Outcome, reason: string, fourEyes: boolean): Promise<boolean> =>
    submit((run, hit) =>
      client.decide(run.run_id, hit.hit_id, { outcome, reason, four_eyes: fourEyes, expected_sequence: hit.review.sequence }),
    )

  const secondReview = (approve: boolean, reason: string): Promise<boolean> =>
    submit((run, hit) => client.secondReview(run.run_id, hit.hit_id, { approve, reason, expected_sequence: hit.review.sequence }))

  return { decide, secondReview }
}

const INITIAL: ScreeningData = {
  settings: null,
  sources: null,
  runs: [],
  run: null,
  log: null,
  selectedHitId: null,
  filter: emptyFilter(),
  busy: false,
  error: null,
}

export function createScreeningController(port: () => ScreeningPort | null | undefined, events: () => ReviewEvents = () => ({})) {
  const store = createStore<ScreeningData>({ ...INITIAL, filter: emptyFilter() })

  const guard: Guard = async (action) => {
    store.set({ busy: true, error: null })
    try {
      return await action()
    } catch (caught) {
      const failure = asScreeningError(caught, events())
      store.set({ error: failure })
      events().onError?.(failure)
      return null
    } finally {
      store.set({ busy: false })
    }
  }

  const context: Context = { client: delegate(port), events, store, guard }
  return {
    store,
    ...loadActions(context),
    ...decisionActions(context),
    select: (hitId: string | null) => store.set({ selectedHitId: hitId }),
    setFilter: (filter: HitFilter) => store.set({ filter: { ...filter } }),
    selectNext(): void {
      const { run, selectedHitId } = store.get()
      if (run) store.set({ selectedHitId: nextOpenHit(run.subjects, selectedHitId) })
    },
  }
}

export type ScreeningController = ReturnType<typeof createScreeningController>
