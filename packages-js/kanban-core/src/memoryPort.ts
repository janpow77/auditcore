/** In-Memory-Port: gleiche Regeln wie der Server (reine Befehle), ohne Netzwerk. */
import { createBoard, configureColumns, revokeShare, shareBoard, updateBoard, type BoardPatch } from './boardCommands'
import { createCard, deleteCard, moveCard, updateCard, type CommandContext, type CommandResult, type Placement } from './commands'
import { KanbanError, raiseIfDenied } from './errors'
import { cloneJson, type Board, type Column, type SharePermission, type TransitionPolicy } from './model'
import { authorize, roleOf } from './permissions'
import type { BoardEvent, BoardPort, BoardSummary, MutationResult, UserRef } from './port'
import { boardStats } from './stats'
import { findTemplate } from './templates'

export interface MemoryPortOptions {
  userId: string
  boards?: readonly Board[]
  users?: readonly UserRef[]
  /** Künstliche Verzögerung in ms (Demo). */
  latency?: number
  clock?: () => string
  newId?: () => string
}

let sequence = 0

export class MemoryBoardPort implements BoardPort {
  userId: string
  private readonly boards = new Map<string, Board>()
  private readonly log: BoardEvent[] = []
  private readonly users: readonly UserRef[]
  private readonly options: MemoryPortOptions

  constructor(options: MemoryPortOptions) {
    this.options = options
    this.userId = options.userId
    this.users = options.users ?? []
    for (const board of options.boards ?? []) this.boards.set(board.id, cloneJson(board))
  }

  /** Nutzer wechseln (Demo der Rechte). */
  switchUser(userId: string): void {
    this.userId = userId
  }

  private context(): CommandContext {
    return { actor: this.userId, now: (this.options.clock ?? (() => new Date().toISOString()))(), newId: this.options.newId }
  }

  private async delay(): Promise<void> {
    if (this.options.latency) await new Promise((resolve) => setTimeout(resolve, this.options.latency))
  }

  private get(boardId: string): Board {
    const board = this.boards.get(boardId)
    if (!board) throw new KanbanError('BOARD_NOT_FOUND', 'Board nicht gefunden')
    return board
  }

  private async apply(boardId: string, run: (board: Board, ctx: CommandContext) => CommandResult): Promise<MutationResult> {
    await this.delay()
    const ctx = this.context()
    const result = run(this.get(boardId), ctx)
    this.boards.set(boardId, cloneJson(result.board))
    for (const change of result.changes) {
      sequence += 1
      this.log.push({ ...change, seq: sequence, board_id: boardId, version: result.board.version, actor: ctx.actor, at: ctx.now })
    }
    return { board: cloneJson(result.board), warnings: result.warnings }
  }

  async load(boardId: string): Promise<Board> {
    await this.delay()
    const board = this.get(boardId)
    raiseIfDenied(authorize(board, this.userId, 'read'))
    return cloneJson(board)
  }

  createCard(boardId: string, fields: Readonly<Record<string, unknown>>): Promise<MutationResult> {
    return this.apply(boardId, (board, ctx) => createCard(board, ctx, fields))
  }

  updateCard(boardId: string, cardId: string, fields: Readonly<Record<string, unknown>>): Promise<MutationResult> {
    return this.apply(boardId, (board, ctx) => updateCard(board, ctx, cardId, fields))
  }

  moveCard(boardId: string, cardId: string, columnId: string, placement: Placement): Promise<MutationResult> {
    return this.apply(boardId, (board, ctx) => moveCard(board, ctx, cardId, columnId, placement))
  }

  deleteCard(boardId: string, cardId: string): Promise<MutationResult> {
    return this.apply(boardId, (board, ctx) => deleteCard(board, ctx, cardId))
  }

  configureColumns(boardId: string, columns: readonly Column[], transitions?: TransitionPolicy): Promise<MutationResult> {
    return this.apply(boardId, (board, ctx) => configureColumns(board, ctx, columns, transitions))
  }

  updateBoard(boardId: string, patch: BoardPatch): Promise<MutationResult> {
    return this.apply(boardId, (board, ctx) => updateBoard(board, ctx, patch))
  }

  share(boardId: string, userId: string, permission: SharePermission): Promise<MutationResult> {
    if (!this.users.some((user) => user.id === userId)) return Promise.reject(new KanbanError('USER_NOT_FOUND', 'Benutzer nicht gefunden'))
    return this.apply(boardId, (board, ctx) => shareBoard(board, ctx, userId, permission))
  }

  revokeShare(boardId: string, userId: string): Promise<MutationResult> {
    return this.apply(boardId, (board, ctx) => revokeShare(board, ctx, userId))
  }

  async searchUsers(query: string): Promise<UserRef[]> {
    const needle = query.trim().toLowerCase()
    return this.users.filter((user) => user.id !== this.userId && [user.name, user.email ?? '', user.id].some((text) => text.toLowerCase().includes(needle)))
  }

  async listBoards(): Promise<BoardSummary[]> {
    await this.delay()
    return [...this.boards.values()]
      .map((board) => ({ board, role: roleOf(board, this.userId) }))
      .filter((entry): entry is { board: Board; role: string } => entry.role !== null && !entry.board.archived)
      .map(({ board, role }) => {
        const stats = boardStats(board)
        return { id: board.id, title: board.title, icon: board.icon, pinned: board.pinned, updated_at: board.updated_at, owner_id: board.owner_id, role, stats: { total: stats.total, done: stats.done, progress: stats.progress } }
      })
  }

  async createBoard(title: string, icon: string, templateKey?: string): Promise<Board> {
    await this.delay()
    const ctx = this.context()
    const id = (this.options.newId ?? (() => `board-${Date.now().toString(36)}`))()
    if (this.boards.has(id)) throw new KanbanError('BOARD_EXISTS', 'Board existiert bereits')
    const board = createBoard(ctx, id, title, icon, templateKey ? findTemplate(templateKey) : undefined).board
    this.boards.set(id, board)
    return cloneJson(board)
  }

  async deleteBoard(boardId: string): Promise<void> {
    await this.delay()
    raiseIfDenied(authorize(this.get(boardId), this.userId, 'delete_board'))
    this.boards.delete(boardId)
  }

  async events(boardId: string, since = 0): Promise<BoardEvent[]> {
    return this.log.filter((event) => event.board_id === boardId && event.seq > since).map((event) => cloneJson(event))
  }
}
