/** Boardliste (Seitenleiste): eigene und geteilte Boards, Anheften, Löschen, Anlegen aus Vorlagen. */
import { computed, ref } from 'vue'
import { KanbanError, type Board, type BoardPort, type BoardSummary } from '@flowaudit/kanban-core'
import { toKanbanError } from './useKanbanBoard'

/** Angeheftete zuerst, dann zuletzt geändert (WorkspaceSidebar.sortedBoards). */
export function sortBoards(boards: readonly BoardSummary[]): BoardSummary[] {
  return [...boards].sort((a, b) => Number(b.pinned) - Number(a.pinned) || b.updated_at.localeCompare(a.updated_at))
}

export function useBoardList(port: () => BoardPort | null | undefined) {
  const boards = ref<BoardSummary[]>([])
  const loading = ref(false)
  const error = ref<KanbanError | null>(null)
  const own = computed(() => sortBoards(boards.value.filter((board) => board.role === 'owner')))
  const shared = computed(() => sortBoards(boards.value.filter((board) => board.role !== 'owner')))

  async function run<T>(action: (current: BoardPort) => Promise<T>): Promise<T | null> {
    const current = port()
    if (!current) return null
    try {
      error.value = null
      return await action(current)
    } catch (caught) {
      error.value = toKanbanError(caught)
      return null
    }
  }

  async function load(): Promise<void> {
    loading.value = true
    const list = await run((current) => current.listBoards?.() ?? Promise.resolve([]))
    boards.value = list ?? []
    loading.value = false
  }

  async function togglePin(summary: BoardSummary): Promise<void> {
    const result = await run((current) => current.updateBoard(summary.id, { pinned: !summary.pinned }))
    if (result) boards.value = boards.value.map((entry) => (entry.id === summary.id ? { ...entry, pinned: result.board.pinned } : entry))
  }

  async function remove(summary: BoardSummary): Promise<void> {
    const done = await run(async (current) => {
      await current.deleteBoard?.(summary.id)
      return true
    })
    if (done) boards.value = boards.value.filter((entry) => entry.id !== summary.id)
  }

  async function create(title: string, icon: string, template?: string): Promise<Board | null> {
    const board = await run((current) => current.createBoard?.(title, icon, template) ?? Promise.resolve(null))
    if (board) await load()
    return board
  }

  const canCreate = computed(() => Boolean(port()?.createBoard))
  return { boards, own, shared, loading, error, canCreate, load, togglePin, remove, create }
}
