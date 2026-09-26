/**
 * React-Anbindung der Board-Zustandsautomaten aus `@flowaudit/kanban-core`
 * (Board, Verschieben, Zeiger, Tastenkürzel) – dieselbe Logik wie die
 * Vue-Composables in `@flowaudit/ui`.
 */
import { useEffect, useMemo, useRef, useState, type RefObject } from 'react'
import {
  EMPTY_FILTER,
  MemoryBoardPort,
  createBoardController,
  createMoveController,
  createPointerDrag,
  filterCriteria,
  isFilterActive,
  listenBoardShortcuts,
  previewColumns,
  selectBoardView,
  type Board,
  type BoardPort,
  type BoardShortcut,
  type KanbanError,
  type KanbanFilterState,
  type MoveTranslate,
  type UserRef,
} from '@flowaudit/kanban-core'
import { useStoreState } from '../store'

export interface BoardSource {
  port?: BoardPort | null
  boardId?: string
  board?: Board | null
  userId?: string
  users?: readonly UserRef[]
  readOnly?: boolean
  today?: string
  onError?: (error: KanbanError) => void
  onBoardChange?: (board: Board) => void
}

/** Die jeweils neuesten Werte für Rückrufe der Controller (stabile Controller, frische Props). */
function useLatest<T>(value: T): { readonly current: T } {
  const ref = useRef(value)
  ref.current = value
  return ref
}

/** Ohne Port wird `board` lokal (In-Memory) bearbeitet, wie in der Vue-Fassung. */
function useLocalPort(source: BoardSource): BoardPort | null {
  const users = useLatest(source.users)
  const { board, userId } = source
  return useMemo(() => (board ? new MemoryBoardPort({ userId: userId || board.owner_id, boards: [board], users: users.current ?? [] }) : null), [board, userId, users])
}

export function useBoard(source: BoardSource) {
  const localPort = useLocalPort(source)
  const port = source.port ?? localPort
  const boardId = source.boardId || source.board?.id || ''
  const latest = useLatest({ port, boardId, source })
  const [controller] = useState(() =>
    createBoardController({
      port: () => latest.current.port,
      boardId: () => latest.current.boardId,
      onError: (error) => latest.current.source.onError?.(error),
      onChange: (board) => latest.current.source.onBoardChange?.(board),
    }),
  )
  const state = useStoreState(controller.store)
  useEffect(() => {
    void controller.load()
  }, [controller, port, boardId])
  const [filter, setFilter] = useState<KanbanFilterState>(EMPTY_FILTER)
  const criteria = useMemo(() => filterCriteria(filter), [filter])
  const userId = port?.userId ?? ''
  const view = useMemo(() => selectBoardView(state, { userId, criteria, readOnly: source.readOnly, today: source.today }), [state, userId, criteria, source.readOnly, source.today])
  return { controller, state, view, port, filter, setFilter, filterActive: isFilterActive(criteria) }
}

export type BoardBinding = ReturnType<typeof useBoard>

export function focusCardIn(root: HTMLElement | null, cardId: string): void {
  root?.querySelector<HTMLElement>(`[data-card-id="${CSS.escape(cardId)}"]`)?.focus()
}

/** Verschieben per Tastatur und Zeiger über dem Board-Controller. */
export function useMover(binding: BoardBinding, t: MoveTranslate, root: RefObject<HTMLElement | null>) {
  const latest = useLatest({ binding, t })
  const [mover] = useState(() =>
    createMoveController({
      board: binding.controller,
      columns: () => latest.current.binding.view.columns,
      canMove: () => latest.current.binding.view.can.move,
      t: () => latest.current.t,
      // Nach dem nächsten Rendern (Karte kann in eine andere Spalte umgezogen sein).
      focusCard: (cardId) => void setTimeout(() => focusCardIn(root.current, cardId), 0),
    }),
  )
  const move = useStoreState(mover.store)
  const columns = useMemo(() => previewColumns(binding.view.columns, move), [binding.view.columns, move])
  const shown = useLatest(columns)
  const [pointer] = useState(() =>
    createPointerDrag({ mover, root: () => root.current, enabled: () => latest.current.binding.view.can.move, columns: () => shown.current }),
  )
  const drag = useStoreState(pointer.store)
  useEffect(() => () => pointer.cancel(), [pointer])
  return { mover, move, columns, pointer, drag }
}

/** Tastenkürzel N, F und /, solange das Board angezeigt wird. */
export function useBoardShortcuts(root: RefObject<HTMLElement | null>, handle: (shortcut: BoardShortcut) => void): void {
  const latest = useLatest(handle)
  useEffect(() => listenBoardShortcuts(() => root.current, (shortcut) => latest.current(shortcut)), [root, latest])
}
