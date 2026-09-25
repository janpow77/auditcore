/** Lokale Bearbeitung des Spaltensatzes (Einstellungsdialog) mit Prüfung über die Kernlogik. */
import { computed, ref } from 'vue'
import { DEFAULT_LIMITS, KanbanError, uniqueColumnId, validateColumns, type Column } from '@flowaudit/kanban-core'
import { COLUMN_COLORS } from './cardView'

export function useColumnEditor(maxColumns = DEFAULT_LIMITS.columns_max) {
  const draft = ref<Column[]>([])
  const original = ref<Column[]>([])
  const problem = ref('')

  function reset(columns: readonly Column[]): void {
    original.value = columns.map((column) => ({ ...column, status_aliases: [...column.status_aliases] }))
    draft.value = columns.map((column) => ({ ...column, status_aliases: [...column.status_aliases] }))
    problem.value = ''
  }

  const canAdd = computed(() => draft.value.length < maxColumns)
  const canRemove = computed(() => draft.value.length > 1)
  const dirty = computed(() => JSON.stringify(draft.value) !== JSON.stringify(original.value))
  const removed = computed(() => original.value.filter((column) => !draft.value.some((entry) => entry.id === column.id)))

  function add(label: string): void {
    if (!canAdd.value) return
    const id = uniqueColumnId(label, draft.value.map((column) => column.id))
    const color = COLUMN_COLORS[draft.value.length % COLUMN_COLORS.length] ?? '#6b7280'
    draft.value = [...draft.value, { id, label, color, wip_limit: null, done: false, status_aliases: [] }]
  }

  function remove(index: number): void {
    if (canRemove.value) draft.value = draft.value.filter((_, position) => position !== index)
  }

  function move(index: number, step: -1 | 1): void {
    const target = index + step
    if (target < 0 || target >= draft.value.length) return
    const next = [...draft.value]
    const [column] = next.splice(index, 1)
    if (column) next.splice(target, 0, column)
    draft.value = next
  }

  function update(index: number, patch: Partial<Column>): void {
    draft.value = draft.value.map((column, position) => {
      if (position !== index) return patch.done ? { ...column, done: false } : column
      return { ...column, ...patch }
    })
  }

  /** Geprüfter Spaltensatz oder null (Fehlermeldung in `problem`). */
  function validated(): Column[] | null {
    try {
      problem.value = ''
      return validateColumns(draft.value)
    } catch (error) {
      problem.value = error instanceof KanbanError ? error.message : String(error)
      return null
    }
  }

  return { draft, problem, canAdd, canRemove, dirty, removed, reset, add, remove, move, update, validated }
}
