/** Tastenbelegung einer Karte und des Boards als deklarative Tabellen (DOM-Ereignisse beider Frameworks). */
import type { Card } from '../model'
import type { MoveController } from './moveController'

type Delta = readonly [-1 | 0 | 1, -1 | 0 | 1]

/** Die Teile eines Tastaturereignisses, die die Belegung braucht (DOM- und React-Ereignis). */
export interface KeyInput {
  key: string
  ctrlKey: boolean
  altKey: boolean
  metaKey: boolean
  target: EventTarget | null
  currentTarget: EventTarget | null
}

type Mover = Pick<MoveController, 'step' | 'drop' | 'cancel' | 'nudge' | 'grab'>

const ARROWS: Readonly<Record<string, Delta>> = {
  ArrowUp: [0, -1],
  ArrowDown: [0, 1],
  ArrowLeft: [-1, 0],
  ArrowRight: [1, 0],
}

function grabbedKey(event: KeyInput, controller: Mover): boolean {
  const arrow = ARROWS[event.key]
  if (arrow) controller.step(arrow[0], arrow[1])
  else if (event.key === ' ' || event.key === 'Enter') void controller.drop()
  else if (event.key === 'Escape') controller.cancel()
  else return false
  return true
}

function idleKey(event: KeyInput, card: Card, controller: Mover, open: (card: Card) => void): boolean {
  const arrow = ARROWS[event.key]
  if (arrow && event.ctrlKey) void controller.nudge(card, arrow[0], arrow[1])
  else if (event.key === 'Enter') open(card)
  else if (event.key === ' ') controller.grab(card)
  else return false
  return true
}

/** Verarbeitet eine Taste auf einer Karte; true, wenn sie verbraucht wurde. */
export function handleCardKey(event: KeyInput, card: Card, grabbedId: string | null, controller: Mover, open: (card: Card) => void): boolean {
  if (event.target !== event.currentTarget || event.altKey || event.metaKey) return false
  return grabbedId === card.id ? grabbedKey(event, controller) : idleKey(event, card, controller, open)
}

/** Tastenkürzel des Boards (N, F, /, Escape), nicht während der Texteingabe. */
export function isTyping(target: EventTarget | null): boolean {
  if (typeof HTMLElement === 'undefined' || !(target instanceof HTMLElement)) return false
  return target.isContentEditable || ['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName)
}

export type BoardShortcut = 'new-card' | 'fullscreen' | 'search'

const SHORTCUTS: Readonly<Record<string, BoardShortcut>> = { n: 'new-card', f: 'fullscreen', '/': 'search' }

export function boardShortcut(event: Pick<KeyInput, 'key' | 'ctrlKey' | 'metaKey' | 'altKey' | 'target'>): BoardShortcut | null {
  if (event.ctrlKey || event.metaKey || event.altKey || isTyping(event.target)) return null
  return SHORTCUTS[event.key.toLowerCase()] ?? null
}

/**
 * Meldet die Tastenkürzel N, F und / am Dokument an, wenn der Fokus im Board
 * oder auf der Seite (body) liegt; liefert die Abmeldung.
 */
export function listenBoardShortcuts(root: () => HTMLElement | null, handle: (shortcut: BoardShortcut) => void): () => void {
  function onKeydown(event: KeyboardEvent): void {
    const focus = document.activeElement
    const inside = focus === document.body || (focus !== null && Boolean(root()?.contains(focus)))
    const shortcut = inside ? boardShortcut(event) : null
    if (!shortcut) return
    event.preventDefault()
    handle(shortcut)
  }
  document.addEventListener('keydown', onKeydown)
  return () => document.removeEventListener('keydown', onKeydown)
}
