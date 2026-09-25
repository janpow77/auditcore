/**
 * Ziehen mit Maus, Stift und Touch über Pointer Events (eigene Umsetzung, keine
 * Fremdbibliothek). Die bewegte Karte erscheint als Vorschau an der Zielposition;
 * ein schwebendes Abbild folgt dem Zeiger. Unerlaubte Ziele zeigen keine Vorschau.
 */
import { onBeforeUnmount, reactive, type Ref } from 'vue'
import type { Card } from '@flowaudit/kanban-core'
import { siblingsOf } from './movePreview'
import type { MoveController } from './useMoveController'

const THRESHOLD = 5

interface DragState {
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
  if (on) {
    window.addEventListener('pointermove', listeners.pointermove)
    window.addEventListener('pointerup', listeners.pointerup)
    window.addEventListener('pointercancel', listeners.pointercancel)
    window.addEventListener('keydown', listeners.keydown, true)
    return
  }
  window.removeEventListener('pointermove', listeners.pointermove)
  window.removeEventListener('pointerup', listeners.pointerup)
  window.removeEventListener('pointercancel', listeners.pointercancel)
  window.removeEventListener('keydown', listeners.keydown, true)
}

export function usePointerDrag(controller: MoveController, root: Ref<HTMLElement | null>, enabled: () => boolean) {
  const drag = reactive<DragState>({ card: null, pointerId: -1, startX: 0, startY: 0, x: 0, y: 0, width: 0, offsetX: 0, offsetY: 0, active: false })
  let suppressClick = false

  function onPointerDown(event: PointerEvent, card: Card): void {
    if (!enabled() || event.button !== 0 || interactive(event.target) || controller.grabbed.value) return
    const element = event.currentTarget as HTMLElement
    const box = element.getBoundingClientRect()
    Object.assign(drag, { card, pointerId: event.pointerId, startX: event.clientX, startY: event.clientY, x: event.clientX, y: event.clientY, width: box.width, offsetX: event.clientX - box.left, offsetY: event.clientY - box.top, active: false })
    listen(true)
  }

  // Fensterweite Listener: die Karte kann während der Vorschau neu gerendert werden.
  const listen = (on: boolean): void => toggleListeners(on, { pointermove: onPointerMove, pointerup: onPointerUp, pointercancel: reset, keydown: onKeydown })


  function onPointerMove(event: PointerEvent): void {
    const card = drag.card
    if (!card || event.pointerId !== drag.pointerId) return
    drag.x = event.clientX
    drag.y = event.clientY
    if (!drag.active && Math.hypot(drag.x - drag.startX, drag.y - drag.startY) < THRESHOLD) return
    drag.active = true
    const place = dropTarget(root.value, drag.x, drag.y, card.id)
    if (place && controller.allowed(card.id, place.columnId)) {
      const size = siblingsOf(controller.columns.value, place.columnId, card.id).length
      controller.preview.value = { cardId: card.id, columnId: place.columnId, index: Math.min(place.index, size) }
    }
  }

  function onPointerUp(event: PointerEvent): void {
    const card = drag.card
    if (!card || event.pointerId !== drag.pointerId) return
    const wasActive = drag.active
    const preview = controller.preview.value
    reset()
    if (!wasActive) return
    suppressClick = true
    if (preview) void controller.commit(card.id, preview)
  }

  function reset(): void {
    listen(false)
    Object.assign(drag, { card: null, pointerId: -1, active: false })
    if (!controller.grabbed.value) controller.preview.value = null
  }

  function onKeydown(event: KeyboardEvent): void {
    if (drag.active && event.key === 'Escape') {
      event.preventDefault()
      reset()
    }
  }

  /** Klick nach einem Ziehen öffnet keine Details. */
  function consumeClick(): boolean {
    const suppressed = suppressClick
    suppressClick = false
    return suppressed
  }

  onBeforeUnmount(() => listen(false))

  return { drag, onPointerDown, consumeClick, cancel: reset }
}

export type PointerDrag = ReturnType<typeof usePointerDrag>
