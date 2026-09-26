// Zustandsautomat von <flowaudit-synopsis> (Vue und React): Laden über den
// Port, lokale Zeilenänderungen, Filter, Navigation zwischen Änderungen, Exporte.

import { createStore } from '../store'
import { exportFilename, toHtml, toMarkdown } from './exporters'
import type { SynopsisPort } from './port'
import {
  CHANGE_STATUSES,
  type ClientExportFormat,
  type Comparison,
  type ComparisonResult,
  type CompareRow,
  type ExportPayload,
  type RowUpdate,
  type ServerExportFormat,
} from './types'
import {
  applyRowOverrides,
  buildSynopsisView,
  changeIds,
  filterRows,
  positionText,
  stepChange,
  type RowView,
  type SynopsisTranslate,
  type SynopsisView,
} from './viewModel'

/** Eingaben der Komponente (Props). */
export interface SynopsisInputs {
  comparison?: Comparison | null
  result?: ComparisonResult | null
  comparisonId?: string
  port?: SynopsisPort | null
  title?: string
  oldLabel?: string
  newLabel?: string
}

export interface SynopsisFilterState {
  statuses: string[]
  query: string
  onlySelected: boolean
  /** `null`: Vorgabe aus `metadata.highlight_words`. */
  highlight: boolean | null
}

export interface SynopsisData {
  loaded: Comparison | null
  loading: boolean
  error: string
  overrides: ReadonlyMap<string, Partial<CompareRow>>
  filter: SynopsisFilterState
  activeId: string | null
}

export interface ServerExportLink {
  label: string
  href: string
}

/** Alles, was die Oberfläche aus Stand und Eingaben anzeigt (reine Funktion). */
export interface SynopsisSelection {
  currentId: string | undefined
  result: ComparisonResult | null
  view: SynopsisView | null
  rows: RowView[]
  selectedText: string
  highlight: boolean
  activeId: string | null
  position: string
  canPrev: boolean
  canNext: boolean
  serverExports: ServerExportLink[]
}

const SERVER_FORMATS: ReadonlyArray<[ServerExportFormat, 'serverDocx' | 'serverPdf' | 'serverJson']> = [
  ['docx', 'serverDocx'],
  ['pdf', 'serverPdf'],
  ['json', 'serverJson'],
]

/** Kennung des angezeigten Vergleichs (für Speichern und Server-Exporte). */
export function synopsisId(state: SynopsisData, inputs: SynopsisInputs): string | undefined {
  return (inputs.comparison ?? state.loaded)?.id ?? inputs.comparisonId
}

/** Ergebnisobjekt vor lokalen Änderungen: Prop `result`, sonst gespeicherter oder geladener Vergleich. */
export function synopsisBase(state: SynopsisData, inputs: SynopsisInputs): ComparisonResult | null {
  return inputs.result ?? (inputs.comparison ?? state.loaded)?.result ?? null
}

function serverExports(port: SynopsisPort | null | undefined, id: string | undefined, t: SynopsisTranslate): ServerExportLink[] {
  if (!id || !port?.exportUrl) return []
  return SERVER_FORMATS.map(([format, key]) => ({ label: t(key), href: port.exportUrl?.(id, format) ?? '' }))
}

function buildView(state: SynopsisData, inputs: SynopsisInputs, result: ComparisonResult, t: SynopsisTranslate): SynopsisView {
  return buildSynopsisView(result, t, {
    title: inputs.title || (inputs.comparison ?? state.loaded)?.title,
    oldLabel: inputs.oldLabel,
    newLabel: inputs.newLabel,
    highlight: state.filter.highlight ?? undefined,
  })
}

interface Navigation {
  activeId: string | null
  position: string
  canPrev: boolean
  canNext: boolean
}

/** Position unter den sichtbaren Änderungen; eine ausgeblendete aktive Zeile gilt als keine. */
function navigation(rows: readonly RowView[], active: string | null, t: SynopsisTranslate): Navigation {
  const ids = changeIds(rows)
  const activeId = active !== null && ids.includes(active) ? active : null
  const index = activeId === null ? -1 : ids.indexOf(activeId)
  return {
    activeId,
    position: positionText(ids, activeId, t),
    canPrev: ids.length > 0 && index !== 0,
    canNext: ids.length > 0 && index !== ids.length - 1,
  }
}

function selectedText(view: SynopsisView | null, t: SynopsisTranslate): string {
  const all = view?.rows ?? []
  return t('selectedCount', { count: all.filter((row) => row.selected).length, total: all.length })
}

/** Wortweise Hervorhebung: Auswahl der Werkzeugleiste, sonst Vorgabe des Ergebnisses, sonst an. */
function highlightOf(state: SynopsisData, result: ComparisonResult | null): boolean {
  return state.filter.highlight ?? result?.metadata?.highlight_words ?? true
}

export function selectSynopsis(state: SynopsisData, inputs: SynopsisInputs, t: SynopsisTranslate): SynopsisSelection {
  const currentId = synopsisId(state, inputs)
  const base = synopsisBase(state, inputs)
  const result = base ? { ...base, rows: applyRowOverrides(base.rows, state.overrides) } : null
  const view = result ? buildView(state, inputs, result, t) : null
  const rows = view ? filterRows(view.rows, state.filter) : []
  return {
    currentId,
    result,
    view,
    rows,
    selectedText: selectedText(view, t),
    highlight: highlightOf(state, result),
    ...navigation(rows, state.activeId, t),
    serverExports: serverExports(inputs.port, currentId, t),
  }
}

/** Export der sichtbaren Zeilen (HTML, Markdown, Druckansicht). */
export function buildSynopsisExport(selection: SynopsisSelection, format: ClientExportFormat, t: SynopsisTranslate, lang: string): ExportPayload | null {
  const view = selection.view
  if (!view) return null
  const input = { view, rows: selection.rows, t, lang }
  if (format === 'markdown') {
    return { format, filename: exportFilename(view.title, 'md'), mimeType: 'text/markdown;charset=utf-8', content: toMarkdown(input) }
  }
  return { format, filename: exportFilename(view.title, 'html'), mimeType: 'text/html;charset=utf-8', content: toHtml(input) }
}

const INITIAL: SynopsisData = {
  loaded: null,
  loading: false,
  error: '',
  overrides: new Map(),
  filter: { statuses: [...CHANGE_STATUSES], query: '', onlySelected: false, highlight: null },
  activeId: null,
}

export function createSynopsisController(t: () => SynopsisTranslate) {
  const store = createStore<SynopsisData>(INITIAL)
  const setFilter = (patch: Partial<SynopsisFilterState>): void => store.set((state) => ({ filter: { ...state.filter, ...patch } }))

  /** Mit `comparisonId` und `port`, aber ohne `comparison`/`result`: Vergleich laden. */
  async function reload(inputs: SynopsisInputs): Promise<void> {
    const { comparisonId: id, port } = inputs
    if (!id || !port || inputs.comparison || inputs.result) return
    store.set({ loading: true, error: '' })
    try {
      store.set({ loaded: await port.load(id) })
    } catch {
      store.set({ error: t()('loadError') })
    } finally {
      store.set({ loading: false })
    }
  }

  async function updateRow(inputs: SynopsisInputs, id: string, patch: Omit<RowUpdate, 'row_id'>): Promise<RowUpdate> {
    store.set((state) => {
      const overrides = new Map(state.overrides)
      overrides.set(id, { ...overrides.get(id), ...patch })
      return { overrides }
    })
    const update: RowUpdate = { row_id: id, ...patch }
    const target = synopsisId(store.get(), inputs)
    if (inputs.port?.updateRows && target) {
      try {
        await inputs.port.updateRows(target, [update])
        store.set({ error: '' })
      } catch {
        store.set({ error: t()('saveError') })
      }
    }
    return update
  }

  function toggleStatus(status: string, enabled: boolean): void {
    const next = new Set(store.get().filter.statuses)
    if (enabled) next.add(status)
    else next.delete(status)
    setFilter({ statuses: [...next] })
  }

  /** Zur nächsten/vorigen Änderung; liefert die neue Zeile oder `null`. */
  function go(selection: SynopsisSelection, direction: 1 | -1): string | null {
    const next = stepChange(changeIds(selection.rows), selection.activeId, direction)
    if (next !== null) store.set({ activeId: next })
    return next
  }

  return {
    store,
    reload,
    updateRow,
    toggleStatus,
    go,
    setAllChanges: () => setFilter({ statuses: [...CHANGE_STATUSES] }),
    setQuery: (query: string) => setFilter({ query }),
    setOnlySelected: (onlySelected: boolean) => setFilter({ onlySelected }),
    setHighlight: (highlight: boolean) => setFilter({ highlight }),
    activate: (id: string | null) => store.set({ activeId: id }),
    /** Neues Ergebnisobjekt: lokale Zeilenänderungen verwerfen. */
    resetOverrides: () => {
      if (store.get().overrides.size) store.set({ overrides: new Map() })
    },
  }
}

export type SynopsisController = ReturnType<typeof createSynopsisController>
