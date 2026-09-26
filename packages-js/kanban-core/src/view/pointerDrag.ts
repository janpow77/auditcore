/**
 * Ziehen mit Maus, Stift und Touch über Pointer Events (eigene Umsetzung, keine
 * Fremdbibliothek). Die bewegte Karte erscheint als Vorschau an der Zielposition;
 * ein schwebendes Abbild folgt dem Zeiger. Unerlaubte Ziele zeigen keine Vorschau.
 */
import type { Card } from '../model'
import type { ColumnView } from './board'
import type { MoveController } from './moveController'
import { siblingsOf } from './movePreview'
import { createKanbanStore, type KanbanStore } from './store'

const THRESHOLD = 5

export interface DragState {
  card: Card | null
  pointerId: number
  startX: number
  startY: number
  x: number
  y: number
  width: number
  offsetX: number
  offsetY: number
  active: boolean
}

/** Die Teile eines Zeigerereignisses, die das Ziehen braucht (DOM- und React-Ereignis). */
export interface PointerInput {
  button: number
  pointerId: number
  clientX: number
  clientY: number
  target: EventTarget | null
  currentTarget: EventTarget | null
}

export interface PointerDragOptions {
  mover: MoveController
  root: () => HTMLElement | null
  enabled: () => boolean
  /** Angezeigte Spalten (mit Vorschau). */
  columns: () => readonly ColumnView[]
}

export interface PointerDrag {
  store: KanbanStore<DragState>
  onPointerDown: (event: PointerInput, card: Card) => void
  /** Klick nach einem Ziehen öffnet keine Details. */
  consumeClick: () => boolean
  cancel: () => void
}

const IDLE: DragState = { card: null, pointerId: -1, startX: 0, startY: 0, x: 0, y: 0, width: 0, offsetX: 0, offsetY: 0, active: false }

function interactive(target: EventTarget | null): boolean {
  return target instanceof Element && Boolean(target.closest('button, a, input, select, textarea, [data-no-drag]'))
}

/** Einfügeposition in einer Kartenliste anhand der Zeigerhöhe (Kartenmitte). */
export function indexAt(list: Element, cardId: string, y: number): number {
  const items = Array.from(list.querySelectorAll<HTMLElement>('[data-card-id]')).filter((item) => item.dataset.cardId !== cardId)
  const next = items.findIndex((item) => {
    const box = item.getBoundingClientRect()
    return y < box.top + box.height / 2
  })
  return next < 0 ? items.length : next
}

/** Spalte und Einfügeposition unter dem Zeiger innerhalb des Boards. */
export function dropTarget(root: HTMLElement | null, x: number, y: number, cardId: string): { columnId: string; index: number } | null {
  const column = document.elementFromPoint(x, y)?.closest<HTMLElement>('[data-column-id]')
  if (!column || !root?.contains(column)) return null
  const list = column.querySelector('[data-card-list]') ?? column
  return { columnId: column.dataset.columnId ?? '', index: indexAt(list, cardId, y) }
}

type Listeners = { pointermove: (event: PointerEvent) => void; pointerup: (event: PointerEvent) => void; pointercancel: () => void; keydown: (event: KeyboardEvent) => void }

function toggleListeners(on: boolean, listeners: Listeners): void {
  const method = on ? window.addEventListener.bind(window) : window.removeEventListener.bind(window)
  method('pointermove', listeners.pointermove as EventListener)
  method('pointerup', listeners.pointerup as EventListener)
  method('pointercancel', listeners.pointercancel)
  method('keydown', listeners.keydown as EventListener, true)
}

export function createPointerDrag(options: PointerDragOptions): PointerDrag {
  const store = createKanbanStore<DragState>(IDLE)
  const { mover } = options
  let suppressClick = false
  // Fensterweite Listener: die Karte kann während der Vorschau neu gerendert werden.
  const listen = (on: boolean): void => toggleListeners(on, { pointermove: onPointerMove, pointerup: onPointerUp, pointercancel: reset, keydown: onKeydown })

  function onPointerDown(event: PointerInput, card: Card): void {
    if (!options.enabled() || event.button !== 0 || interactive(event.target) || mover.store.get().grabbed) return
    const box = (event.currentTarget as HTMLElement).getBoundingClientRect()
    const { clientX: x, clientY: y } = event
    store.set({ card, pointerId: event.pointerId, startX: x, startY: y, x, y, width: box.width, offsetX: x - box.left, offsetY: y - box.top, active: false })
    listen(true)
  }

  function onPointerMove(event: PointerEvent): void {
    const drag = store.get()
    if (!drag.card || event.pointerId !== drag.pointerId) return
    const moved = Math.hypot(event.clientX - drag.startX, event.clientY - drag.startY) >= THRESHOLD
    store.set({ x: event.clientX, y: event.clientY, active: drag.active || moved })
    if (store.get().active) previewAt(drag.card, event.clientX, event.clientY)
  }

  function previewAt(card: Card, x: number, y: number): void {
    const place = dropTarget(options.root(), x, y, card.id)
    if (!place || !mover.allowed(card.id, place.columnId)) return
    const size = siblingsOf(options.columns(), place.columnId, card.id).length
    mover.setPreview({ cardId: card.id, columnId: place.columnId, index: Math.min(place.index, size) })
  }

  function onPointerUp(event: PointerEvent): void {
    const drag = store.get()
    if (!drag.card || event.pointerId !== drag.pointerId) return
    const preview = mover.store.get().preview
    reset()
    if (!drag.active) return
    suppressClick = true
    if (preview) void mover.commit(drag.card.id, preview)
  }

  function reset(): void {
    listen(false)
    store.set({ card: null, pointerId: -1, active: false })
    if (!mover.store.get().grabbed) mover.setPreview(null)
  }

  function onKeydown(event: KeyboardEvent): void {
    if (!store.get().active || event.key !== 'Escape') return
    event.preventDefault()
    reset()
  }

  function consumeClick(): boolean {
    const suppressed = suppressClick
    suppressClick = false
    return suppressed
  }

  return { store, onPointerDown, consumeClick, cancel: reset }
}
