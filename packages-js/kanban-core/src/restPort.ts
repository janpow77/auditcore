/**
 * Port gegen den REST-Vertrag von auditcore_kanban (docs/kanban/rest-api.md).
 * `fetch` ist injizierbar (Authentisierung, CSRF, Tests). Änderungsantworten
 * enthalten nur die geänderten Karten; der Port führt sie in seinen Stand ein.
 */
import type { BoardPatch } from './boardCommands'
import type { Placement } from './commands'
import { KanbanError } from './errors'
import { isPlainObject } from './fields'
import { cloneJson, type Board, type Card, type Column, type SharePermission, type TransitionPolicy } from './model'
import type { BoardEvent, BoardPort, BoardSummary, MutationResult, UserRef } from './port'
import { boardFromJson } from './serialization'

export type FetchLike = (input: string, init?: RequestInit) => Promise<Response>

export interface RestPortOptions {
  /** Einhängepunkt des Routers, z. B. `/api/kanban`. */
  baseUrl: string
  userId: string
  fetch?: FetchLike
  headers?: Readonly<Record<string, string>>
  /** Erwartete Version mitsenden (409 VERSION_CONFLICT bei fremder Änderung). */
  optimisticLocking?: boolean
  /** Nutzersuche des Consumers; der REST-Vertrag kennt keine Nutzerverwaltung. */
  searchUsers?: (query: string) => Promise<UserRef[]>
}

interface ChangeResponse {
  version: number
  card: Card | null
  changed_cards: Card[]
  warnings: string[]
}

type Method = 'GET' | 'POST' | 'PATCH' | 'PUT' | 'DELETE'

async function errorFrom(response: Response): Promise<KanbanError> {
  try {
    const body: unknown = await response.json()
    const error = isPlainObject(body) && isPlainObject(body.error) ? body.error : null
    if (error && typeof error.code === 'string' && typeof error.message === 'string') return new KanbanError(error.code, error.message)
  } catch {
    // Kein JSON-Fehlerkörper: allgemeiner Fehler mit HTTP-Status.
  }
  return new KanbanError('INVALID_REQUEST', `HTTP ${response.status}`)
}

export class RestBoardPort implements BoardPort {
  readonly userId: string
  readonly searchUsers?: (query: string) => Promise<UserRef[]>
  private readonly cache = new Map<string, Board>()

  constructor(private readonly options: RestPortOptions) {
    this.userId = options.userId
    this.searchUsers = options.searchUsers
  }

  private async call(method: Method, path: string, body?: Readonly<Record<string, unknown>>): Promise<unknown> {
    const fetchImpl = this.options.fetch ?? ((input: string, init?: RequestInit) => globalThis.fetch(input, init))
    const headers: Record<string, string> = { Accept: 'application/json', ...this.options.headers }
    if (body !== undefined) headers['Content-Type'] = 'application/json'
    const response = await fetchImpl(`${this.options.baseUrl.replace(/\/$/, '')}${path}`, { method, headers, body: body === undefined ? undefined : JSON.stringify(body) })
    if (!response.ok) throw await errorFrom(response)
    return response.status === 204 ? null : response.json()
  }

  private versioned(boardId: string, body: Readonly<Record<string, unknown>> = {}): Record<string, unknown> {
    const current = this.cache.get(boardId)
    return this.options.optimisticLocking === false || !current ? { ...body } : { ...body, expected_version: current.version }
  }

  private remember(raw: unknown): Board {
    const board = boardFromJson(isPlainObject(raw) ? raw.board : undefined)
    this.cache.set(board.id, board)
    return cloneJson(board)
  }

  /** Führt eine Änderungsantwort in den gespeicherten Stand ein. */
  private merge(boardId: string, raw: unknown, removed?: string): MutationResult {
    const current = this.cache.get(boardId)
    if (!current || !isPlainObject(raw)) throw new KanbanError('INVALID_DOCUMENT', 'Unerwartete Antwort')
    const change = raw as unknown as ChangeResponse
    const updates = new Map<string, Card>([...(change.changed_cards ?? []), ...(change.card ? [change.card] : [])].map((card) => [card.id, card]))
    const kept = current.cards.filter((card) => card.id !== removed).map((card) => updates.get(card.id) ?? card)
    const added = [...updates.values()].filter((card) => card.id !== removed && !current.cards.some((entry) => entry.id === card.id))
    const board: Board = { ...current, version: change.version, cards: [...kept, ...added] }
    this.cache.set(boardId, board)
    return { board: cloneJson(board), warnings: change.warnings ?? [] }
  }

  private path(boardId: string, rest = ''): string {
    return `/boards/${encodeURIComponent(boardId)}${rest}`
  }

  private card(boardId: string, cardId: string, rest = ''): string {
    return this.path(boardId, `/cards/${encodeURIComponent(cardId)}${rest}`)
  }

  async load(boardId: string): Promise<Board> {
    return this.remember(await this.call('GET', this.path(boardId)))
  }

  async createCard(boardId: string, fields: Readonly<Record<string, unknown>>): Promise<MutationResult> {
    return this.merge(boardId, await this.call('POST', this.path(boardId, '/cards'), this.versioned(boardId, fields)))
  }

  async updateCard(boardId: string, cardId: string, fields: Readonly<Record<string, unknown>>): Promise<MutationResult> {
    return this.merge(boardId, await this.call('PATCH', this.card(boardId, cardId), this.versioned(boardId, fields)))
  }

  async moveCard(boardId: string, cardId: string, columnId: string, placement: Placement): Promise<MutationResult> {
    const body = this.versioned(boardId, { column_id: columnId, ...placement })
    return this.merge(boardId, await this.call('POST', this.card(boardId, cardId, '/move'), body))
  }

  async deleteCard(boardId: string, cardId: string): Promise<MutationResult> {
    return this.merge(boardId, await this.call('DELETE', this.card(boardId, cardId), this.versioned(boardId)), cardId)
  }

  async configureColumns(boardId: string, columns: readonly Column[], transitions?: TransitionPolicy): Promise<MutationResult> {
    const body = this.versioned(boardId, transitions ? { columns, transitions } : { columns })
    return { board: this.remember(await this.call('PUT', this.path(boardId, '/columns'), body)), warnings: [] }
  }

  async updateBoard(boardId: string, patch: BoardPatch): Promise<MutationResult> {
    return { board: this.remember(await this.call('PATCH', this.path(boardId), this.versioned(boardId, { ...patch }))), warnings: [] }
  }

  async share(boardId: string, userId: string, permission: SharePermission): Promise<MutationResult> {
    await this.call('PUT', this.path(boardId, `/shares/${encodeURIComponent(userId)}`), { permission })
    return { board: await this.load(boardId), warnings: [] }
  }

  async revokeShare(boardId: string, userId: string): Promise<MutationResult> {
    await this.call('DELETE', this.path(boardId, `/shares/${encodeURIComponent(userId)}`))
    return { board: await this.load(boardId), warnings: [] }
  }

  async listBoards(): Promise<BoardSummary[]> {
    const raw = await this.call('GET', '/boards')
    return isPlainObject(raw) && Array.isArray(raw.boards) ? (raw.boards as BoardSummary[]) : []
  }

  async createBoard(title: string, icon: string, templateKey?: string): Promise<Board> {
    return this.remember(await this.call('POST', '/boards', templateKey ? { title, icon, template: templateKey } : { title, icon }))
  }

  async deleteBoard(boardId: string): Promise<void> {
    await this.call('DELETE', this.path(boardId))
    this.cache.delete(boardId)
  }

  async events(boardId: string, since = 0): Promise<BoardEvent[]> {
    const raw = await this.call('GET', this.path(boardId, `/events?since=${since}`))
    return isPlainObject(raw) && Array.isArray(raw.events) ? (raw.events as BoardEvent[]) : []
  }
}
