/** Tastenbelegung einer Karte als deklarative Tabellen. */
import type { Card } from '@flowaudit/kanban-core'
import type { MoveController } from './useMoveController'

type Delta = readonly [-1 | 0 | 1, -1 | 0 | 1]

const ARROWS: Readonly<Record<string, Delta>> = {
  ArrowUp: [0, -1],
  ArrowDown: [0, 1],
  ArrowLeft: [-1, 0],
  ArrowRight: [1, 0],
}

function grabbedKey(event: KeyboardEvent, controller: MoveController): boolean {
  const arrow = ARROWS[event.key]
  if (arrow) controller.step(arrow[0], arrow[1])
  else if (event.key === ' ' || event.key === 'Enter') void controller.drop()
  else if (event.key === 'Escape') controller.cancel()
  else return false
  return true
}

function idleKey(event: KeyboardEvent, card: Card, controller: MoveController, open: (card: Card) => void): boolean {
  const arrow = ARROWS[event.key]
  if (arrow && event.ctrlKey) void controller.nudge(card, arrow[0], arrow[1])
  else if (event.key === 'Enter') open(card)
  else if (event.key === ' ') controller.grab(card)
  else return false
  return true
}

/** Verarbeitet eine Taste auf einer Karte; true, wenn sie verbraucht wurde. */
export function handleCardKey(event: KeyboardEvent, card: Card, controller: MoveController, open: (card: Card) => void): boolean {
  if (event.target !== event.currentTarget || event.altKey || event.metaKey) return false
  return controller.grabbed.value === card.id ? grabbedKey(event, controller) : idleKey(event, card, controller, open)
}

/** Tastenkürzel des Boards (N, F, /, Escape), nicht während der Texteingabe. */
export function isTyping(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false
  return target.isContentEditable || ['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName)
}

export type BoardShortcut = 'new-card' | 'fullscreen' | 'search'

const SHORTCUTS: Readonly<Record<string, BoardShortcut>> = { n: 'new-card', f: 'fullscreen', '/': 'search' }

export function boardShortcut(event: KeyboardEvent): BoardShortcut | null {
  if (event.ctrlKey || event.metaKey || event.altKey || isTyping(event.target)) return null
  return SHORTCUTS[event.key.toLowerCase()] ?? null
}
