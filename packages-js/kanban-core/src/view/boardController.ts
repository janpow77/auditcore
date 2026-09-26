/**
 * Zustandsautomat eines Boards (Vue und React): lädt über den Port, wendet
 * Änderungen sofort mit der Kernlogik an (optimistisch) und übernimmt danach
 * den Stand des Ports; bei Fehlern wird zurückgerollt. Änderungen laufen
 * nacheinander. Die Anzeige leitet `selectBoardView` rein funktional ab.
 */
import type { CommandContext } from '../commands'
import type { KanbanError } from '../errors'
import { todayIso, type CardFilter } from '../filtering'
import type { Board } from '../model'
import { roleOf } from '../permissions'
import type { BoardPort } from '../port'
import { boardStats, type BoardStats } from '../stats'
import { createKanbanActions, type KanbanActions } from './actions'
import { columnViews, toKanbanError, uiCapabilities, type ColumnView, type UiCapabilities } from './board'
import { createMutator, type Mutate } from './mutator'
import { createKanbanStore, type KanbanStore } from './store'

export interface BoardState {
  board: Board | null
  loading: boolean
  error: KanbanError | null
  warnings: string[]
}

export interface BoardControllerOptions {
  port: () => BoardPort | null | undefined
  boardId: () => string
  onError?: (error: KanbanError) => void
  onChange?: (board: Board) => void
}

export interface BoardViewInputs {
  userId: string
  criteria: CardFilter
  readOnly?: boolean
  today?: string
}

export interface BoardView {
  role: string | null
  can: UiCapabilities
  today: string
  stats: BoardStats | null
  columns: ColumnView[]
}

export interface BoardController {
  store: KanbanStore<BoardState>
  load: (keepError?: boolean) => Promise<void>
  mutate: Mutate
  actions: KanbanActions
  userId: () => string
}

/** Alles, was die Oberfläche aus Stand und Eingaben anzeigt (reine Funktion). */
export function selectBoardView(state: BoardState, inputs: BoardViewInputs): BoardView {
  const board = state.board
  const today = inputs.today ?? todayIso()
  return {
    role: board ? roleOf(board, inputs.userId) : null,
    can: uiCapabilities(board, inputs.userId, inputs.readOnly ?? false),
    today,
    stats: board ? boardStats(board) : null,
    columns: columnViews(board, inputs.criteria, today),
  }
}

const temporaryId = (): string => `tmp-${Math.random().toString(36).slice(2, 10)}`

export function createBoardController(options: BoardControllerOptions): BoardController {
  const store = createKanbanStore<BoardState>({ board: null, loading: false, error: null, warnings: [] })
  const userId = (): string => options.port()?.userId ?? ''

  function fail(caught: unknown): KanbanError {
    const failure = toKanbanError(caught)
    store.set({ error: failure })
    options.onError?.(failure)
    return failure
  }

  /** Lädt das Board; `keepError` lässt eine vorherige Meldung (z. B. Versionskonflikt) stehen. */
  async function load(keepError = false): Promise<void> {
    const port = options.port()
    if (!port) return
    store.set(keepError ? { loading: true } : { loading: true, error: null })
    try {
      store.set({ board: await port.load(options.boardId()) })
    } catch (caught) {
      store.set({ board: null })
      fail(caught)
    } finally {
      store.set({ loading: false })
    }
  }

  const mutate = createMutator({
    getBoard: () => store.get().board,
    setBoard: (board) => store.set({ board }),
    port: options.port,
    fail,
    reload: () => void load(true),
    context: (): CommandContext => ({ actor: userId(), now: new Date().toISOString(), newId: temporaryId }),
    settled: (result) => {
      store.set({ warnings: result.warnings, error: null })
      options.onChange?.(result.board)
    },
  })

  return { store, load, mutate, actions: createKanbanActions(mutate, () => store.get().board), userId }
}
