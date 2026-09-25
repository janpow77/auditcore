/**
 * Paritätsprüfung gegen die von auditcore_kanban (Python) erzeugten Fixtures:
 * TypeScript muss in jedem Fall dasselbe entscheiden.
 */
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { describe, expect, it } from 'vitest'
import {
  authorize,
  boardFromJson,
  cardsIn,
  checkCapacity,
  checkMove,
  checkRevoke,
  checkShare,
  columnsFromJson,
  configureColumns,
  createCard,
  deadlineState,
  decisionToJson,
  filterCards,
  getCard,
  isValidRank,
  KanbanError,
  moveCard,
  parseCardFields,
  rankBetween,
  RankError,
  roleOf,
  spreadRanks,
  toggleDone,
  validateColumns,
  DEFAULT_LIMITS,
  type Action,
  type Board,
  type CardFilter,
  type CommandContext,
  type CommandResult,
} from '../src'

// Fixture-JSON ist dynamisch (Form je Datei in docs/kanban/parity-fixtures.md); daher bewusst untypisiert.
type Json = ReturnType<typeof JSON.parse>
interface Case { name: string; input: Json; expected: Json }

const DIR = process.env.KANBAN_PARITY_DIR ?? fileURLToPath(new URL('../../../packages/auditcore_kanban/tests/fixtures/parity/', import.meta.url))

function load(name: string): Case[] {
  return JSON.parse(readFileSync(`${DIR.replace(/\/?$/, '/')}${name}.json`, 'utf8')) as Case[]
}

function rankCase(input: Json): Json {
  try {
    if (input.op === 'between') return rankBetween(input.a, input.b)
    if (input.op === 'spread') return spreadRanks(input.count)
    if (input.op === 'valid') return isValidRank(input.key)
    const keys: string[] = []
    for (const step of input.steps as { a: string | null; b: string | null; key: string }[]) {
      const key = rankBetween(step.a, step.b)
      expect(key).toBe(step.key)
      keys.push(key)
    }
    return [...keys].sort()
  } catch (error) {
    if (error instanceof RankError) return { error: error.code }
    throw error
  }
}

function outcome(run: () => Json): Json {
  try {
    return { ok: true, value: run() }
  } catch (error) {
    if (error instanceof KanbanError) return { ok: false, code: error.code, message: error.message }
    throw error
  }
}

function orders(board: Board): Json {
  return Object.fromEntries(board.columns.map((column) => [column.id, cardsIn(board, column.id).map((card) => [card.id, card.rank])]))
}

function commandCase(input: Json): Json {
  const board = boardFromJson(input.board)
  const ctx: CommandContext = { actor: input.actor, now: input.now, newId: () => input.new_id ?? 'new' }
  const run: Record<string, () => CommandResult> = {
    move: () => moveCard(board, ctx, input.card_id, input.column_id, { before_id: input.before_id, after_id: input.after_id, index: input.index }),
    toggle_done: () => toggleDone(board, ctx, input.card_id),
    create: () => createCard(board, ctx, input.fields),
    configure: () => configureColumns(board, ctx, columnsFromJson(input.columns)),
  }
  const operation = run[input.op as string]
  if (!operation) throw new Error(`unbekannte Operation ${String(input.op)}`)
  try {
    const result = operation()
    return { orders: orders(result.board), version: result.board.version }
  } catch (error) {
    if (error instanceof KanbanError) return { error: error.code }
    throw error
  }
}

function permissionCase(input: Json): Json {
  const board = boardFromJson(input.board)
  if (input.op === 'authorize') {
    const inherited = input.inherited ?? undefined
    return { role: roleOf(board, input.user_id, inherited), decision: decisionToJson(authorize(board, input.user_id, input.action as Action, inherited)) }
  }
  if (input.op === 'share') return decisionToJson(checkShare(board, input.actor, input.target_user, input.permission))
  return decisionToJson(checkRevoke(board, input.actor, input.target_user))
}

describe('Parität mit auditcore_kanban', () => {
  it.each(load('rank'))('Rang: $name', ({ input, expected }) => {
    expect(rankCase(input)).toEqual(expected)
  })

  it.each(load('transitions'))('Übergang: $name', ({ input, expected }) => {
    const board = boardFromJson(input.board)
    expect(decisionToJson(checkMove(board, getCard(board, input.card_id), input.target))).toEqual(expected)
  })

  it.each(load('wip'))('WIP: $name', ({ input, expected }) => {
    expect(decisionToJson(checkCapacity(boardFromJson(input.board), input.column_id, input.exclude_card_id))).toEqual(expected)
  })

  it.each(load('filter'))('Filter: $name', ({ input, expected }) => {
    const cards = filterCards(boardFromJson(input.board), input.filter as CardFilter, input.today)
    expect(cards.map((card) => card.id)).toEqual(expected)
  })

  it.each(load('deadline'))('Frist: $name', ({ input, expected }) => {
    expect(deadlineState(input.due, input.today)).toBe(expected)
  })

  it.each(load('permissions'))('Rechte: $name', ({ input, expected }) => {
    expect(permissionCase(input)).toEqual(expected)
  })

  it.each(load('validation'))('Validierung: $name', ({ input, expected }) => {
    const run = input.op === 'columns'
      ? () => validateColumns(columnsFromJson(input.columns), DEFAULT_LIMITS)
      : () => parseCardFields(input.fields, DEFAULT_LIMITS)
    expect(outcome(run)).toEqual(expected)
  })

  it.each(load('commands'))('Befehl: $name', ({ input, expected }) => {
    expect(commandCase(input)).toEqual(expected)
  })
})
