/** Boardliste (Seitenleiste): eigene und geteilte Boards, Anheften, Löschen, Anlegen aus Vorlagen. */
import type { KanbanError } from '../errors'
import type { Board } from '../model'
import type { BoardPort, BoardSummary } from '../port'
import { sortBoards, toKanbanError } from './board'
import { createKanbanStore, type KanbanStore } from './store'

export interface BoardListState {
  boards: BoardSummary[]
  loading: boolean
  error: KanbanError | null
}

export interface BoardListView {
  own: BoardSummary[]
  shared: BoardSummary[]
}

export interface BoardListController {
  store: KanbanStore<BoardListState>
  load: () => Promise<void>
  togglePin: (summary: BoardSummary) => Promise<void>
  remove: (summary: BoardSummary) => Promise<void>
  create: (title: string, icon: string, template?: string) => Promise<Board | null>
  canCreate: () => boolean
}

export function selectBoardList(state: BoardListState): BoardListView {
  return {
    own: sortBoards(state.boards.filter((board) => board.role === 'owner')),
    shared: sortBoards(state.boards.filter((board) => board.role !== 'owner')),
  }
}

export function createBoardListController(port: () => BoardPort | null | undefined): BoardListController {
  const store = createKanbanStore<BoardListState>({ boards: [], loading: false, error: null })
  const boards = (): BoardSummary[] => store.get().boards

  async function run<T>(action: (current: BoardPort) => Promise<T>): Promise<T | null> {
    const current = port()
    if (!current) return null
    try {
      store.set({ error: null })
      return await action(current)
    } catch (caught) {
      store.set({ error: toKanbanError(caught) })
      return null
    }
  }

  async function load(): Promise<void> {
    store.set({ loading: true })
    const list = await run((current) => current.listBoards?.() ?? Promise.resolve([]))
    store.set({ boards: list ?? [], loading: false })
  }

  async function togglePin(summary: BoardSummary): Promise<void> {
    const result = await run((current) => current.updateBoard(summary.id, { pinned: !summary.pinned }))
    if (result) store.set({ boards: boards().map((entry) => (entry.id === summary.id ? { ...entry, pinned: result.board.pinned } : entry)) })
  }

  async function remove(summary: BoardSummary): Promise<void> {
    const done = await run(async (current) => {
      await current.deleteBoard?.(summary.id)
      return true
    })
    if (done) store.set({ boards: boards().filter((entry) => entry.id !== summary.id) })
  }

  async function create(title: string, icon: string, template?: string): Promise<Board | null> {
    const board = await run((current) => current.createBoard?.(title, icon, template) ?? Promise.resolve(null))
    if (board) await load()
    return board
  }

  return { store, load, togglePin, remove, create, canCreate: () => Boolean(port()?.createBoard) }
}
