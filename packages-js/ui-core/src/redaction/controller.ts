// Zustandsautomat von <flowaudit-pdf-redaction> (Vue und React): Katalog laden,
// Datei und Suchkriterien wählen, Plan holen, Auswahl prüfen und ergänzen,
// geschwärzte PDF anfordern. Geschwärzt wird ausschließlich über den Port; der
// Plan enthält Klartext und bleibt nur im Arbeitsspeicher.

import { createRunner, createStore, IDLE, type RequestState, type Store } from '../store'
import {
  defaultRedactionBox,
  initialRedactionSelection,
  nudgeRedactionBox,
  redactionBoxFromPoints,
  redactionBoxIsTooSmall,
  redactionGroups,
  redactionSelectionPayload,
  redactionTerms,
  REDACTION_GROUP_PAGE,
  resizeRedactionBox,
  type RedactionArrow,
} from './model'
import type { RedactionArea, RedactionBox, RedactionCandidate, RedactionCatalogue, RedactionCriteria, RedactionLimits, RedactionPlan, RedactionPort, RedactionResult } from './types'

export type RedactionBusy = 'load' | 'plan' | 'apply'
export type RedactionValidation = 'needFile' | 'tooLarge' | 'needCriteria' | 'tooManyTerms' | 'termTooLong' | null
export type RedactionOption = 'caseSensitive' | 'wholeWord' | 'sanitize'

export interface RedactionCallbacks {
  planned?: (plan: RedactionPlan) => void
  completed?: (result: RedactionResult) => void
  failed?: (message: string) => void
}

/** Erzeugen und Freigeben von Objekt-URLs (Seitenbild, Download); in Tests ersetzbar. */
export interface RedactionUrls {
  create: (blob: Blob) => string
  revoke: (url: string) => void
}

/** Laufendes Aufziehen oder Vergrößern mit dem Zeiger. */
export type RedactionGesture =
  | { kind: 'draw'; start: readonly [number, number]; box: RedactionBox }
  | { kind: 'resize'; id: string }

export interface RedactionData extends RequestState<string> {
  catalogue: RedactionCatalogue | null
  file: Blob | null
  filename: string
  patterns: readonly string[]
  terms: string
  caseSensitive: boolean
  wholeWord: boolean
  sanitize: boolean
  validation: RedactionValidation
  plan: RedactionPlan | null
  selected: ReadonlySet<string>
  areas: readonly RedactionArea[]
  page: number
  /** Objekt-URL des Seitenbilds der aktuellen Seite (`null` solange es lädt). */
  preview: string | null
  previewError: string | null
  gesture: RedactionGesture | null
  areaLimitHit: boolean
  filter: string
  expanded: ReadonlySet<string>
  groupLimit: number
  result: RedactionResult | null
  resultUrl: string | null
}

export interface RedactionSource {
  port: () => RedactionPort | null | undefined
  callbacks?: () => RedactionCallbacks
  urls?: RedactionUrls
}

export const INITIAL_REDACTION: RedactionData = {
  ...IDLE,
  catalogue: null,
  file: null,
  filename: '',
  patterns: [],
  terms: '',
  caseSensitive: false,
  wholeWord: true,
  sanitize: true,
  validation: null,
  plan: null,
  selected: new Set(),
  areas: [],
  page: 1,
  preview: null,
  previewError: null,
  gesture: null,
  areaLimitHit: false,
  filter: '',
  expanded: new Set(),
  groupLimit: REDACTION_GROUP_PAGE,
  result: null,
  resultUrl: null,
}

/** Zurück auf die Prüfansicht eines neuen Plans (ohne Datei und Kriterien). */
const REVIEW_RESET: Partial<RedactionData> = {
  areas: [], page: 1, preview: null, previewError: null, gesture: null, areaLimitHit: false,
  filter: '', expanded: new Set(), groupLimit: REDACTION_GROUP_PAGE, result: null, resultUrl: null,
}

const errorText = (error: unknown): string => (error instanceof Error ? error.message : String(error))

const browserUrls: RedactionUrls = {
  create: (blob) => URL.createObjectURL(blob),
  revoke: (url) => URL.revokeObjectURL(url),
}

export function redactionCriteria(state: RedactionData): RedactionCriteria {
  return { patterns: [...state.patterns], terms: redactionTerms(state.terms), case_sensitive: state.caseSensitive, whole_word: state.wholeWord }
}

/** Prüfung vor dem Senden (reine Funktion). */
export function redactionValidation(state: RedactionData): RedactionValidation {
  if (!state.file) return 'needFile'
  const limits = state.catalogue?.limits
  if (limits && state.file.size > limits.max_upload_bytes) return 'tooLarge'
  const terms = redactionTerms(state.terms)
  if (!state.patterns.length && !terms.length) return 'needCriteria'
  return limits ? termValidation(terms, limits) : null
}

function termValidation(terms: readonly string[], limits: RedactionLimits): RedactionValidation {
  if (terms.length > limits.max_terms) return 'tooManyTerms'
  if (terms.some((term) => term.length > limits.max_term_length)) return 'termTooLong'
  return null
}

function toggled(set: ReadonlySet<string>, ids: Iterable<string>, on: boolean): ReadonlySet<string> {
  const next = new Set(set)
  for (const id of ids) {
    if (on) next.add(id)
    else next.delete(id)
  }
  return next
}

type RedactionStore = Store<RedactionData>

/** Objekt-URLs von Seitenbildern und Ergebnis; Seitenbilder werden je Seite zwischengespeichert. */
function createResources(store: RedactionStore, source: RedactionSource) {
  const urls = source.urls ?? browserUrls
  let previews = new Map<number, string>()
  let generation = 0

  function dropPreviews(): void {
    for (const url of previews.values()) urls.revoke(url)
    previews = new Map()
    generation += 1
  }

  function dropResult(): void {
    const url = store.get().resultUrl
    if (url) urls.revoke(url)
  }

  async function loadPreview(page: number): Promise<void> {
    const cached = previews.get(page)
    if (cached) {
      store.set({ preview: cached, previewError: null })
      return
    }
    const { file, filename, plan } = store.get()
    const port = source.port()
    if (!file || !plan || !port) return
    const token = generation
    store.set({ preview: null, previewError: null })
    try {
      const image = await port.preview(file, filename, page)
      if (token !== generation) return
      const url = urls.create(image)
      previews.set(page, url)
      if (store.get().page === page) store.set({ preview: url })
    } catch (caught) {
      if (token === generation && store.get().page === page) store.set({ previewError: errorText(caught) })
    }
  }

  return {
    urls,
    loadPreview,
    dropResult,
    /** Seitenbilder und Ergebnis freigeben. */
    dropAll(): void {
      dropPreviews()
      dropResult()
    },
  }
}

/** Auswahl der Fundstellen: einzeln, alle, je Quelle, je Gruppe; Liste aufklappen und filtern. */
function selectionActions(store: RedactionStore) {
  const ids = (filter: (item: RedactionCandidate) => boolean): string[] => (store.get().plan?.candidates ?? []).filter(filter).map((item) => item.id)
  const select = (list: Iterable<string>, on: boolean): void => store.set((state) => ({ selected: toggled(state.selected, list, on) }))
  return {
    toggle: (id: string) => select([id], !store.get().selected.has(id)),
    setAll: (on: boolean) => select(ids(() => true), on),
    setSource: (sourceId: string, on: boolean) => select(ids((item) => item.source === sourceId), on),
    setGroup(key: string, on: boolean): void {
      const group = redactionGroups(store.get().plan?.candidates ?? []).find((entry) => entry.key === key)
      if (group) select(group.items.map((item) => item.id), on)
    },
    toggleExpanded(key: string): void {
      store.set((state) => ({ expanded: toggled(state.expanded, [key], !state.expanded.has(key)) }))
    },
    setFilter: (filter: string) => store.set({ filter, groupLimit: REDACTION_GROUP_PAGE }),
    showMore: () => store.set((state) => ({ groupLimit: state.groupLimit + REDACTION_GROUP_PAGE })),
  }
}

/** Eigene Bereiche: anlegen (Zeiger oder Tastatur), verschieben, vergrößern, entfernen. */
function areaActions(store: RedactionStore) {
  let areaCounter = 0

  function updateArea(id: string, change: (box: RedactionBox) => RedactionBox): void {
    store.set((state) => ({ areas: state.areas.map((area) => (area.id === id ? { ...area, rect: change(area.rect) } : area)) }))
  }

  function limitReached(state: RedactionData): boolean {
    const limits = state.catalogue?.limits
    if (!limits) return false
    const onPage = state.areas.filter((area) => area.page === state.page).length
    return state.areas.length >= limits.max_areas || onPage >= limits.max_areas_per_page
  }

  /** Neuer Bereich auf der aktuellen Seite; `false` bei zu kleinem Rechteck oder erreichter Grenze. */
  function addArea(rect: RedactionBox): boolean {
    const state = store.get()
    if (!state.plan || redactionBoxIsTooSmall(rect)) return false
    if (limitReached(state)) {
      store.set({ areaLimitHit: true })
      return false
    }
    areaCounter += 1
    store.set({ areaLimitHit: false, areas: [...state.areas, { id: `bereich-${areaCounter}`, page: state.page, rect }] })
    return true
  }

  return {
    addArea,
    /** Tastaturweg: Bereich in der Seitenmitte anlegen. */
    addDefaultArea: (): boolean => addArea(defaultRedactionBox(store.get().areas.filter((area) => area.page === store.get().page).length)),
    removeArea(id: string): void {
      store.set((state) => ({ areas: state.areas.filter((area) => area.id !== id), areaLimitHit: false }))
    },
    nudgeArea(id: string, key: RedactionArrow, mode: 'resize' | 'move', large: boolean): void {
      updateArea(id, (box) => nudgeRedactionBox(box, key, mode, large))
    },
    /** Zeiger gedrückt auf der Seite (Punkt in Anteilen 0…1). */
    pointerDown(point: readonly [number, number]): void {
      if (!store.get().plan) return
      const start = redactionBoxFromPoints(point, point)
      store.set({ gesture: { kind: 'draw', start: [start[0], start[1]], box: start } })
    },
    startResize(id: string): void {
      store.set({ gesture: { kind: 'resize', id } })
    },
    pointerMove(point: readonly [number, number]): void {
      const gesture = store.get().gesture
      if (gesture?.kind === 'draw') store.set({ gesture: { ...gesture, box: redactionBoxFromPoints(gesture.start, point) } })
      else if (gesture?.kind === 'resize') updateArea(gesture.id, (box) => resizeRedactionBox(box, point))
    },
    pointerUp(point: readonly [number, number]): void {
      const gesture = store.get().gesture
      if (!gesture) return
      store.set({ gesture: null })
      if (gesture.kind === 'draw') addArea(redactionBoxFromPoints(gesture.start, point))
    },
    cancelGesture: () => store.set({ gesture: null }),
  }
}

/** Datei und Suchkriterien bis zum Plan. */
function criteriaActions(store: RedactionStore, source: RedactionSource, resources: Resources, run: Runner) {
  return {
    async load(): Promise<void> {
      const catalogue = await run('load', (port) => port.catalogue())
      if (!catalogue) return
      const known = new Set(catalogue.patterns.filter((pattern) => pattern.available).map((pattern) => pattern.id))
      store.set((state) => ({ catalogue, patterns: state.patterns.filter((id) => known.has(id)) }))
    },
    /** Datei wählen (`null` = Auswahl aufheben); ein vorhandener Plan verfällt. */
    selectFile(file: File | null): void {
      resources.dropAll()
      store.set({ ...REVIEW_RESET, file, filename: file?.name ?? '', plan: null, selected: new Set(), validation: null })
    },
    setPattern(id: string, on: boolean): void {
      store.set((state) => ({ patterns: on ? [...new Set([...state.patterns, id])] : state.patterns.filter((entry) => entry !== id), validation: null }))
    },
    setTerms: (terms: string) => store.set({ terms, validation: null }),
    setOption: (option: RedactionOption, value: boolean) => store.set({ [option]: value } as Partial<RedactionData>),
    async plan(): Promise<void> {
      const state = store.get()
      const validation = redactionValidation(state)
      store.set({ validation })
      if (validation || !state.file) return
      const { file, filename } = state
      const plan = await run('plan', (port) => port.plan(file, filename, redactionCriteria(state)))
      if (!plan || store.get().file !== file) return
      resources.dropAll()
      store.set({ ...REVIEW_RESET, plan, selected: initialRedactionSelection(plan) })
      source.callbacks?.().planned?.(plan)
      await resources.loadPreview(1)
    },
  }
}

/** Prüfansicht verlassen, Seiten wechseln, schwärzen und Ergebnis. */
function flowActions(store: RedactionStore, source: RedactionSource, resources: Resources, run: Runner) {
  return {
    /** Zurück zu den Suchkriterien; Auswahl und Bereiche verfallen. */
    back(): void {
      resources.dropAll()
      store.set({ ...REVIEW_RESET, plan: null, selected: new Set() })
    },
    async showPage(page: number): Promise<void> {
      const plan = store.get().plan
      if (!plan || page < 1 || page > plan.page_count || page === store.get().page) return
      store.set({ page, gesture: null, areaLimitHit: false })
      await resources.loadPreview(page)
    },
    async apply(): Promise<void> {
      const state = store.get()
      if (!state.plan || !state.file) return
      const { file, filename } = state
      const selection = redactionSelectionPayload(state.plan, state.selected, state.areas, state.sanitize)
      const result = await run('apply', (port) => port.apply(file, filename, selection))
      if (!result || store.get().plan !== state.plan) return
      resources.dropResult()
      store.set({ result, resultUrl: resources.urls.create(result.blob) })
      source.callbacks?.().completed?.(result)
    },
    /** Vom Ergebnis zurück zur Auswahl (Plan, Auswahl und Bereiche bleiben). */
    editAgain(): void {
      resources.dropResult()
      store.set({ result: null, resultUrl: null })
    },
    /** Neues Dokument: alles außer Katalog und Kriterien verwerfen. */
    reset(): void {
      resources.dropAll()
      store.set({ ...REVIEW_RESET, file: null, filename: '', plan: null, selected: new Set(), validation: null, error: null })
    },
    /** Objekt-URLs freigeben (beim Entfernen der Komponente). */
    dispose(): void {
      resources.dropAll()
      store.set({ preview: null, resultUrl: null })
    },
  }
}

type Resources = ReturnType<typeof createResources>
type Runner = ReturnType<typeof createRunner<RedactionPort, string, RedactionData>>

export function createRedactionController(source: RedactionSource) {
  const store: RedactionStore = createStore<RedactionData>({ ...INITIAL_REDACTION })
  const run: Runner = createRunner<RedactionPort, string, RedactionData>(store, () => source.port() ?? null, errorText, (message) => source.callbacks?.().failed?.(message))
  const resources = createResources(store, source)
  return {
    store,
    ...criteriaActions(store, source, resources, run),
    ...selectionActions(store),
    ...areaActions(store),
    ...flowActions(store, source, resources, run),
  }
}

export type RedactionController = ReturnType<typeof createRedactionController>
