/**
 * Zustand und Aktionen eines Boards: lädt über den Port, wendet Änderungen
 * sofort mit der Kernlogik an (optimistisch) und übernimmt danach den Stand
 * des Ports; bei Fehlern wird zurückgerollt. Änderungen laufen nacheinander.
 */
import { computed, ref, shallowRef, watch, type Ref } from 'vue'
import {
  boardStats,
  capabilities,
  cardsIn,
  filterCards,
  KanbanError,
  roleOf,
  todayIso,
  wipStates,
  type Board,
  type BoardPort,
  type Card,
  type CardFilter,
  type Column,
  type CommandContext,
  type WipState,
} from '@flowaudit/kanban-core'
import { createMutator } from './mutator'

export interface ColumnView {
  column: Column
  cards: Card[]
  total: number
  wip: WipState | undefined
}

export interface KanbanBoardOptions {
  port: () => BoardPort | null | undefined
  boardId: () => string
  criteria: () => CardFilter
  readOnly?: () => boolean
  today?: () => string | undefined
  onError?: (error: KanbanError) => void
  onChange?: (board: Board) => void
}

export function toKanbanError(error: unknown): KanbanError {
  if (error instanceof KanbanError) return error
  const message = error instanceof Error ? error.message : String(error)
  return new KanbanError('INVALID_REQUEST', message)
}

type Capabilities = Record<'read' | 'create' | 'edit' | 'move' | 'delete' | 'rename' | 'configure' | 'share', boolean>

/** Rechte des Nutzers für die Oberfläche; `locked` (readOnly) sperrt alle Schreibrechte. */
export function uiCapabilities(board: Board | null, userId: string, locked: boolean): Capabilities {
  const allowed = board ? capabilities(board, userId) : null
  const grant = (action: keyof NonNullable<typeof allowed>): boolean => !locked && Boolean(allowed?.[action])
  return {
    read: Boolean(allowed?.read), create: grant('create_card'), edit: grant('edit_card'), move: grant('move_card'),
    delete: grant('delete_card'), rename: grant('rename'), configure: grant('configure'), share: grant('share'),
  }
}

/** Spaltenansicht: sichtbare (gefilterte) Karten, Gesamtzahl und WIP-Zustand je Spalte. */
export function columnViews(board: Board | null, criteria: CardFilter, today: string): ColumnView[] {
  if (!board) return []
  const visible = new Set(filterCards(board, criteria, today).map((card) => card.id))
  const wip = wipStates(board)
  return board.columns.map((column) => {
    const all = cardsIn(board, column.id)
    return { column, cards: all.filter((card) => visible.has(card.id)), total: all.length, wip: wip.find((state) => state.column_id === column.id) }
  })
}

export function useKanbanBoard(options: KanbanBoardOptions) {
  const board = shallowRef<Board | null>(null)
  const loading = ref(false)
  const error: Ref<KanbanError | null> = ref(null)
  const warnings = ref<string[]>([])
  const userId = computed(() => options.port()?.userId ?? '')
  const role = computed(() => (board.value ? roleOf(board.value, userId.value) : null))
  const can = computed(() => uiCapabilities(board.value, userId.value, options.readOnly?.() ?? false))
  const today = computed(() => options.today?.() ?? todayIso())
  const stats = computed(() => (board.value ? boardStats(board.value) : null))
  const columns = computed(() => columnViews(board.value, options.criteria(), today.value))

  function fail(caught: unknown): KanbanError {
    const failure = toKanbanError(caught)
    error.value = failure
    options.onError?.(failure)
    return failure
  }

  /** Lädt das Board; `keepError` lässt eine vorherige Meldung (z. B. Versionskonflikt) stehen. */
  async function load(keepError = false): Promise<void> {
    const port = options.port()
    if (!port) return
    loading.value = true
    if (!keepError) error.value = null
    try {
      board.value = await port.load(options.boardId())
    } catch (caught) {
      board.value = null
      fail(caught)
    } finally {
      loading.value = false
    }
  }

  const mutate = createMutator({
    board, port: options.port, fail, reload: () => void load(true),
    context: (): CommandContext => ({ actor: userId.value, now: new Date().toISOString(), newId: () => `tmp-${Math.random().toString(36).slice(2, 10)}` }),
    settled: (result) => {
      warnings.value = result.warnings
      error.value = null
      options.onChange?.(result.board)
    },
  })

  watch([() => options.port(), () => options.boardId()], () => void load())

  return { board, loading, error, warnings, userId, role, can, today, stats, columns, load, mutate }
}

export type KanbanBoardState = ReturnType<typeof useKanbanBoard>
