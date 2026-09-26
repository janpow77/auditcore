/** Lokale Bearbeitung des Spaltensatzes (Einstellungsdialog) mit Prüfung über die Kernlogik. */
import { KanbanError } from '../errors'
import type { Column } from '../model'
import { DEFAULT_LIMITS, uniqueColumnId, validateColumns } from '../validation'
import { COLUMN_COLORS } from './cardView'
import { createKanbanStore, type KanbanStore } from './store'

export interface ColumnEditorState {
  draft: Column[]
  original: Column[]
  problem: string
}

export interface ColumnEditorView {
  canAdd: boolean
  canRemove: boolean
  dirty: boolean
  removed: Column[]
}

export interface ColumnEditor {
  store: KanbanStore<ColumnEditorState>
  maxColumns: number
  reset: (columns: readonly Column[]) => void
  add: (label: string) => void
  remove: (index: number) => void
  move: (index: number, step: -1 | 1) => void
  update: (index: number, patch: Partial<Column>) => void
  /** Geprüfter Spaltensatz oder null (Fehlermeldung in `problem`). */
  validated: () => Column[] | null
}

const copy = (columns: readonly Column[]): Column[] => columns.map((column) => ({ ...column, status_aliases: [...column.status_aliases] }))

export function selectColumnEditor(state: ColumnEditorState, maxColumns: number = DEFAULT_LIMITS.columns_max): ColumnEditorView {
  return {
    canAdd: state.draft.length < maxColumns,
    canRemove: state.draft.length > 1,
    dirty: JSON.stringify(state.draft) !== JSON.stringify(state.original),
    removed: state.original.filter((column) => !state.draft.some((entry) => entry.id === column.id)),
  }
}

function moved(draft: readonly Column[], index: number, step: -1 | 1): Column[] | null {
  const target = index + step
  if (target < 0 || target >= draft.length) return null
  const next = [...draft]
  const [column] = next.splice(index, 1)
  if (column) next.splice(target, 0, column)
  return next
}

export function createColumnEditor(maxColumns: number = DEFAULT_LIMITS.columns_max): ColumnEditor {
  const store = createKanbanStore<ColumnEditorState>({ draft: [], original: [], problem: '' })
  const draft = (): Column[] => store.get().draft
  const view = (): ColumnEditorView => selectColumnEditor(store.get(), maxColumns)

  function add(label: string): void {
    if (!view().canAdd) return
    const id = uniqueColumnId(label, draft().map((column) => column.id))
    const color = COLUMN_COLORS[draft().length % COLUMN_COLORS.length] ?? '#6b7280'
    store.set({ draft: [...draft(), { id, label, color, wip_limit: null, done: false, status_aliases: [] }] })
  }

  function update(index: number, patch: Partial<Column>): void {
    store.set({
      draft: draft().map((column, position) => {
        if (position !== index) return patch.done ? { ...column, done: false } : column
        return { ...column, ...patch }
      }),
    })
  }

  function validated(): Column[] | null {
    try {
      store.set({ problem: '' })
      return validateColumns(draft())
    } catch (error) {
      store.set({ problem: error instanceof KanbanError ? error.message : String(error) })
      return null
    }
  }

  return {
    store,
    maxColumns,
    reset: (columns) => store.set({ original: copy(columns), draft: copy(columns), problem: '' }),
    add,
    remove: (index) => {
      if (view().canRemove) store.set({ draft: draft().filter((_, position) => position !== index) })
    },
    move: (index, step) => {
      const next = moved(draft(), index, step)
      if (next) store.set({ draft: next })
    },
    update,
    validated,
  }
}
