/**
 * Speicher-/Rechte-Port der Oberfläche: Komponenten rufen nie eine API direkt,
 * sondern einen Port. Implementierungen: `MemoryBoardPort` (Demo, Tests),
 * `RestBoardPort` (REST-Vertrag docs/kanban/rest-api.md) oder eine eigene.
 */
import type { BoardPatch } from './boardCommands'
import type { Change, Placement } from './commands'
import type { Board, Column, SharePermission, TransitionPolicy } from './model'

export interface MutationResult {
  board: Board
  warnings: string[]
}

export interface UserRef {
  id: string
  name: string
  email?: string
}

export interface BoardSummary {
  id: string
  title: string
  icon: string
  pinned: boolean
  updated_at: string
  owner_id: string
  /** Rolle des aktuellen Nutzers: owner, edit oder read. */
  role: string
  stats: { total: number; done: number; progress: number }
}

export interface BoardEvent extends Change {
  seq: number
  board_id: string
  version: number
  actor: string
  at: string
}

export interface BoardPort {
  /** Aktueller Nutzer; Grundlage der Rechteanzeige in der Oberfläche. */
  readonly userId: string
  load(boardId: string): Promise<Board>
  createCard(boardId: string, fields: Readonly<Record<string, unknown>>): Promise<MutationResult>
  updateCard(boardId: string, cardId: string, fields: Readonly<Record<string, unknown>>): Promise<MutationResult>
  moveCard(boardId: string, cardId: string, columnId: string, placement: Placement): Promise<MutationResult>
  deleteCard(boardId: string, cardId: string): Promise<MutationResult>
  configureColumns(boardId: string, columns: readonly Column[], transitions?: TransitionPolicy): Promise<MutationResult>
  updateBoard(boardId: string, patch: BoardPatch): Promise<MutationResult>
  share(boardId: string, userId: string, permission: SharePermission): Promise<MutationResult>
  revokeShare(boardId: string, userId: string): Promise<MutationResult>
  /** Nutzersuche für den Teilen-Dialog (optional). */
  searchUsers?(query: string): Promise<UserRef[]>
  /** Boards des Nutzers für die Seitenleiste (optional). */
  listBoards?(): Promise<BoardSummary[]>
  createBoard?(title: string, icon: string, templateKey?: string): Promise<Board>
  deleteBoard?(boardId: string): Promise<void>
  /** Ereignisse seit `since` (optional, für Protokoll/Abgleich). */
  events?(boardId: string, since?: number): Promise<BoardEvent[]>
}
