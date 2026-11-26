// Zustandsautomat von <flowaudit-pdf-redaction> (Vue und React): Katalog laden,
// Datei und Suchkriterien wählen, Plan holen, Auswahl prüfen und ergänzen,
// geschwärzte PDF anfordern. Geschwärzt wird ausschließlich über den Port; der
// Plan enthält Klartext und bleibt nur im Arbeitsspeicher.

import { createRunner, createStore } from '../store'
import {
  defaultRedactionBox,
  initialRedactionSelection,
  moveRedactionBox,
  nudgeRedactionBox,
  redactionBoxFromPoints,
  redactionBoxIsTooSmall,
  redactionGroups,
  redactionSelectionPayload,
  REDACTION_GROUP_PAGE,
  resizeRedactionBox,
  type RedactionArrow,
} from './model'
import { createResources, errorText, type Resources } from './resources'
import { createPresetQueue, type PresetQueue } from './presets'
import { INITIAL_REDACTION, locked, redactionCriteria, redactionValidation, REVIEW_RESET, toggled, type RedactionData, type RedactionGesture, type RedactionOption, type RedactionPresets, type RedactionSource, type RedactionStore } from './state'
import type { RedactionBox, RedactionCandidate, RedactionCriteria, RedactionPort } from './types'

export {
  INITIAL_REDACTION,
  redactionCriteria,
  redactionValidation,
  type RedactionBusy,
  type RedactionCallbacks,
  type RedactionData,
  type RedactionGesture,
  type RedactionOption,
  type RedactionPresets,
  type RedactionSource,
  type RedactionUrls,
  type RedactionValidation,
} from './state'


/** Dateiname einer bereitgestellten Datei: Vorgabe, sonst Name der Datei, sonst Ersatz. */
function providedName(file: Blob, filename: string | undefined): string {
  const name = filename?.trim() || (typeof File !== 'undefined' && file instanceof File ? file.name : '')
  return name || 'dokument.pdf'
}



/** Auswahl der Fundstellen: einzeln, alle, je Quelle, je Gruppe; Liste aufklappen und filtern. */
function selectionActions(store: RedactionStore) {
  const ids = (filter: (item: RedactionCandidate) => boolean): string[] => (store.get().plan?.candidates ?? []).filter(filter).map((item) => item.id)
  const select = (list: Iterable<string>, on: boolean): void => {
    if (!locked(store)) store.set((state) => ({ selected: toggled(state.selected, list, on) }))
  }
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
    if (locked(store)) return
    store.set((state) => ({ areas: state.areas.map((area) => (area.id === id ? { ...area, rect: change(area.rect) } : area)) }))
  }

  function startGesture(gesture: RedactionGesture): void {
    if (store.get().plan && !locked(store)) store.set({ gesture })
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
    if (!state.plan || locked(store) || redactionBoxIsTooSmall(rect)) return false
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
      if (!locked(store)) store.set((state) => ({ areas: state.areas.filter((area) => area.id !== id), areaLimitHit: false }))
    },
    nudgeArea(id: string, key: RedactionArrow, mode: 'resize' | 'move', large: boolean): void {
      updateArea(id, (box) => nudgeRedactionBox(box, key, mode, large))
    },
    /** Zeiger gedrückt auf der Seite (Punkt in Anteilen 0…1). */
    pointerDown(point: readonly [number, number]): void {
      const start = redactionBoxFromPoints(point, point)
      startGesture({ kind: 'draw', start: [start[0], start[1]], box: start })
    },
    /** Zeiger gedrückt auf einem eigenen Bereich: Verschieben beginnt. */
    startMove(id: string, point: readonly [number, number]): void {
      const area = store.get().areas.find((entry) => entry.id === id)
      if (area) startGesture({ kind: 'move', id, from: [point[0], point[1]], origin: area.rect })
    },
    startResize: (id: string) => startGesture({ kind: 'resize', id }),
    pointerMove(point: readonly [number, number]): void {
      const gesture = store.get().gesture
      if (gesture?.kind === 'draw') store.set({ gesture: { ...gesture, box: redactionBoxFromPoints(gesture.start, point) } })
      else if (gesture?.kind === 'move') updateArea(gesture.id, () => moveRedactionBox(gesture.origin, point[0] - gesture.from[0], point[1] - gesture.from[1]))
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

/**
 * Gehört eine Planantwort noch zum Zustand? Andere Datei oder Generation: nein.
 * Kriterien inzwischen geändert (Eingabe während der Suche): nein, mit Hinweis.
 */
function planStillCurrent(store: RedactionStore, resources: Resources, sent: { file: Blob; generation: number; criteria: RedactionCriteria }): boolean {
  const state = store.get()
  if (state.file !== sent.file || resources.generation() !== sent.generation) return false
  if (JSON.stringify(redactionCriteria(state)) === JSON.stringify(sent.criteria)) return true
  store.set({ criteriaNotice: 'edited' })
  return false
}

/** Datei und Suchkriterien bis zum Plan. */
function criteriaActions(store: RedactionStore, source: RedactionSource, resources: Resources, run: Runner, presets: PresetQueue) {
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
      store.set({ ...REVIEW_RESET, file, filename: file?.name ?? '', fileFixed: false, plan: null, selected: new Set(), validation: null, error: null })
      presets.flush()
    },
    /**
     * Datei der Anwendung übernehmen (z. B. vom Server zusammengestellt); das
     * Dateifeld entfällt. `null` hebt die Vorgabe auf. Ein vorhandener Plan verfällt.
     */
    provideFile(file: Blob | null, filename?: string): void {
      const state = store.get()
      if (!file && !state.fileFixed) return
      if (file && state.fileFixed && state.file === file && state.filename === providedName(file, filename)) return
      resources.dropAll()
      store.set({
        ...REVIEW_RESET,
        file,
        filename: file ? providedName(file, filename) : '',
        fileFixed: Boolean(file),
        plan: null,
        selected: new Set(),
        validation: null,
        error: null,
      })
      presets.flush()
    },
    /**
     * Startwerte für Begriffe und Muster; nicht angebotene Muster entfallen. Ein
     * Plan zu alten Kriterien verfällt; während des Schwärzens und im Ergebnis
     * werden die Werte vorgemerkt.
     */
    presetCriteria(values: RedactionPresets): void {
      presets.offer(values)
    },
    setPattern(id: string, on: boolean): void {
      store.set((state) => ({ patterns: on ? [...new Set([...state.patterns, id])] : state.patterns.filter((entry) => entry !== id), validation: null }))
    },
    setTerms: (terms: string) => store.set({ terms, validation: null }),
    setOption(option: RedactionOption, value: boolean): void {
      if (!locked(store)) store.set({ [option]: value } as Partial<RedactionData>)
    },
    async plan(): Promise<void> {
      const state = store.get()
      const validation = redactionValidation(state)
      store.set({ validation, criteriaNotice: null })
      if (validation || !state.file) return
      const { file, filename } = state
      const generation = resources.generation()
      const criteria = redactionCriteria(state)
      const plan = await run('plan', (port) => current(port.plan(file, filename, criteria), resources, generation))
      if (!plan || !planStillCurrent(store, resources, { file, generation, criteria })) return
      resources.dropAll()
      store.set({ ...REVIEW_RESET, plan, selected: initialRedactionSelection(plan) })
      source.callbacks?.().planned?.(plan)
      await resources.loadPreview(1)
    },
  }
}

/** Prüfansicht verlassen, Seiten wechseln, schwärzen und Ergebnis. */
function flowActions(store: RedactionStore, source: RedactionSource, resources: Resources, run: Runner, presets: PresetQueue) {
  return {
    /** Zurück zu den Suchkriterien; Auswahl und Bereiche verfallen. */
    back(): void {
      resources.dropAll()
      store.set({ ...REVIEW_RESET, plan: null, selected: new Set() })
      presets.flush()
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
      const generation = resources.generation()
      const result = await run('apply', (port) => current(port.apply(file, filename, selection), resources, generation))
      if (!result || store.get().plan !== state.plan || resources.generation() !== generation) {
        presets.flush()
        return
      }
      resources.dropResult()
      store.set({ result, resultUrl: resources.urls.create(result.blob) })
      source.callbacks?.().completed?.(result)
    },
    /** Vom Ergebnis zurück zur Auswahl (Plan, Auswahl und Bereiche bleiben). */
    editAgain(): void {
      resources.dropResult()
      store.set({ result: null, resultUrl: null })
      presets.flush()
    },
    /** Neues Dokument: alles außer Katalog und Kriterien verwerfen; eine bereitgestellte Datei bleibt. */
    reset(): void {
      resources.dropAll()
      const fixed = store.get().fileFixed
      store.set({
        ...REVIEW_RESET,
        ...(fixed ? {} : { file: null, filename: '' }),
        plan: null,
        selected: new Set(),
        validation: null,
        error: null,
      })
      presets.flush()
    },
    /** Objekt-URLs freigeben (beim Entfernen der Komponente); noch laufende Antworten verfallen. */
    dispose(): void {
      resources.dropAll()
      store.set({ preview: null, resultUrl: null })
    },
  }
}

/**
 * Antwort einer Anfrage; ist das Dokument inzwischen ein anderes, verfällt auch
 * ein Fehler (er kann Textauszüge des alten Dokuments enthalten).
 */
async function current<T>(request: Promise<T>, resources: Resources, generation: number): Promise<T | null> {
  try {
    return await request
  } catch (caught) {
    if (resources.generation() !== generation) return null
    throw caught
  }
}

type Runner = ReturnType<typeof createRunner<RedactionPort, string, RedactionData>>

export function createRedactionController(source: RedactionSource) {
  const store: RedactionStore = createStore<RedactionData>({ ...INITIAL_REDACTION })
  const run: Runner = createRunner<RedactionPort, string, RedactionData>(store, () => source.port() ?? null, errorText, (message) => source.callbacks?.().failed?.(message))
  const resources = createResources(store, source)
  const presets = createPresetQueue(store, resources)
  return {
    store,
    ...criteriaActions(store, source, resources, run, presets),
    ...selectionActions(store),
    ...areaActions(store),
    ...flowActions(store, source, resources, run, presets),
  }
}

export type RedactionController = ReturnType<typeof createRedactionController>
