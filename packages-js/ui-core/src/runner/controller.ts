// Zustandsautomat von <flowaudit-runner-console> (Vue und React): lädt Status,
// Profil und Werkzeuge über den Port, verwaltet den Profil-Entwurf mit Prüfen,
// Anwenden und Konfliktauflösung sowie die Werkzeug-Einstellungen. Vue bindet
// ihn mit useStore, React mit useStoreState.

import { createRunner, createStore, IDLE, type RequestState, type Store } from '../store'
import type { MessageParams } from '../i18n'
import type { RunnerMessageKey } from './messages'
import type { RunnerFeldArt } from './eingabe'
import { createRunnerRestPort } from './port'
import { klassenAktionen, profilAktionen, werkzeugAktionen, type RunnerKontext } from './aktionen'
import type { RunnerPfad, RunnerPrioritaet, RunnerUnterschied } from './profil'
import type {
  RunnerAnsicht,
  RunnerPort,
  RunnerProfil,
  RunnerProfilStand,
  RunnerPruefung,
  RunnerStatus,
  RunnerWerkzeugEinstellung,
  RunnerWerkzeuge,
  RunnerWerkzeugProfile,
} from './types'

export interface RunnerCallbacks {
  applied?: (version: number) => void
  failed?: (message: string) => void
}

export interface RunnerKonfliktStand {
  gespeichert: RunnerProfilStand
  meldung: string
  unterschiede: readonly RunnerUnterschied[]
}

/** Rückmeldung nach einer Aktion (übersetzt in der Ansicht). */
export interface RunnerMeldung {
  key: RunnerMessageKey
  params?: MessageParams
  ton: 'success' | 'warning'
}

/** Stand; `error` ist die Meldung der letzten abgelehnten Anfrage. */
export interface RunnerData extends RequestState<string> {
  ansicht: RunnerAnsicht
  status: RunnerStatus | null
  stand: RunnerProfilStand | null
  entwurf: RunnerProfil | null
  pruefung: RunnerPruefung | null
  konflikt: RunnerKonfliktStand | null
  werkzeuge: RunnerWerkzeuge | null
  werkzeugEntwurf: RunnerWerkzeugProfile | null
  meldung: RunnerMeldung | null
  /** Rohtext der Eingabefelder je Feld-ID, solange getippt wird (Zahlen, Listen). */
  eingaben: Readonly<Record<string, string>>
  /** Entwürfe der Klassennamen beim Umbenennen (bisheriger Name → Eingabe). */
  klassenNamen: Readonly<Record<string, string>>
  /** Eingabe „Neue Klasse“. */
  neueKlasse: string
}

export interface RunnerSource {
  /** Fachlogik; hat Vorrang vor `api`. */
  port: () => RunnerPort | null | undefined
  /** Basis-URL der JSON-API (z. B. `/api`), wenn kein Port übergeben wird. */
  api?: () => string | null | undefined
  callbacks?: () => RunnerCallbacks
}

export interface RunnerController {
  store: Store<RunnerData>
  load: () => Promise<void>
  zeige: (ansicht: RunnerAnsicht) => void
  setze: (pfad: RunnerPfad, wert: unknown) => void
  /** Eingabe eines Formularfelds: Rohtext merken, umgesetzten Wert in den Entwurf. */
  eingabe: (pfad: RunnerPfad, art: RunnerFeldArt, roh: string | boolean) => void
  verwerfen: () => void
  pruefen: () => Promise<void>
  anwenden: () => Promise<void>
  gespeichertUebernehmen: () => void
  entwurfTrotzdemAnwenden: () => Promise<void>
  verschiebe: (index: number, richtung: -1 | 1) => void
  prioritaet: (index: number, aenderung: Partial<Pick<RunnerPrioritaet, 'verdraengbar' | 'min'>>) => void
  werkzeug: (profil: string, werkzeug: string, aenderung: Partial<RunnerWerkzeugEinstellung>) => void
  /** Zahleneingabe (Zeitlimit, Priorität) eines Werkzeugs; ungültiger Rohtext bleibt nur sichtbar. */
  werkzeugZahl: (profil: string, werkzeug: string, feld: 'zeitlimit_s' | 'prioritaet', roh: string) => void
  werkzeugeSpeichern: () => Promise<void>
  neueKlasseEingabe: (roh: string) => void
  klasseHinzufuegen: () => void
  klassenNameEingabe: (alt: string, roh: string) => void
  klasseUmbenennen: (alt: string) => void
}

export const INITIAL_RUNNER: RunnerData = {
  ...IDLE,
  ansicht: 'status',
  status: null,
  stand: null,
  entwurf: null,
  pruefung: null,
  konflikt: null,
  werkzeuge: null,
  werkzeugEntwurf: null,
  meldung: null,
  eingaben: {},
  klassenNamen: {},
  neueKlasse: '',
}

export const RUNNER_ANSICHTEN: readonly RunnerAnsicht[] = ['status', 'einstellungen', 'werkzeuge', 'prioritaeten']

const errorText = (error: unknown): string => (error instanceof Error ? error.message : String(error))

function resolvePort(source: RunnerSource): RunnerPort | null {
  const port = source.port()
  if (port) return port
  const api = source.api?.()
  return api ? createRunnerRestPort({ baseUrl: api }) : null
}

export function createRunnerController(source: RunnerSource): RunnerController {
  const store = createStore<RunnerData>({ ...INITIAL_RUNNER })
  const run = createRunner(store, () => resolvePort(source), errorText, (message) => source.callbacks?.().failed?.(message))
  const kontext: RunnerKontext = { store, run, applied: (version) => source.callbacks?.().applied?.(version) }
  return {
    store,
    async load() {
      const daten = await run('load', (port) => Promise.all([port.status(), port.profil(), port.werkzeuge()]))
      if (!daten) return
      const [status, stand, werkzeuge] = daten
      store.set({ status, werkzeuge, werkzeugEntwurf: werkzeuge.profile, stand, entwurf: stand.profil, pruefung: null, konflikt: null, eingaben: {}, klassenNamen: {}, neueKlasse: '' })
    },
    zeige(ansicht) {
      store.set({ ansicht })
    },
    ...profilAktionen(kontext),
    ...werkzeugAktionen(kontext),
    ...klassenAktionen(kontext),
  }
}
