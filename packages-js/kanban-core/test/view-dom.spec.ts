// @vitest-environment happy-dom
import { afterEach, describe, expect, it, vi } from 'vitest'
import { boardShortcut, createPointerDrag, handleCardKey, indexAt, listenBoardShortcuts, type Card, type MoveController } from '../src'

afterEach(() => {
  document.body.innerHTML = ''
})

const card = { id: 'a' } as Card
const mover = () => ({ step: vi.fn(), drop: vi.fn(), cancel: vi.fn(), nudge: vi.fn(), grab: vi.fn() })
const key = (init: Partial<KeyboardEventInit> & { key: string }, target: EventTarget | null = null) => ({ ctrlKey: false, altKey: false, metaKey: false, target, currentTarget: target, ...init })

describe('Tastenbelegung', () => {
  it('Leertaste nimmt auf, Pfeile verschieben, Escape bricht ab, Enter öffnet', () => {
    const controller = mover()
    const open = vi.fn()
    expect(handleCardKey(key({ key: ' ' }), card, null, controller, open)).toBe(true)
    expect(controller.grab).toHaveBeenCalledWith(card)
    expect(handleCardKey(key({ key: 'ArrowLeft' }), card, 'a', controller, open)).toBe(true)
    expect(controller.step).toHaveBeenCalledWith(-1, 0)
    handleCardKey(key({ key: 'Escape' }), card, 'a', controller, open)
    expect(controller.cancel).toHaveBeenCalled()
    handleCardKey(key({ key: 'ArrowDown', ctrlKey: true }), card, null, controller, open)
    expect(controller.nudge).toHaveBeenCalledWith(card, 0, 1)
    handleCardKey(key({ key: 'Enter' }), card, null, controller, open)
    expect(open).toHaveBeenCalledWith(card)
    expect(handleCardKey(key({ key: 'x' }), card, null, controller, open)).toBe(false)
    expect(handleCardKey({ ...key({ key: ' ' }), currentTarget: document.body }, card, null, controller, open)).toBe(false)
  })

  it('Board-Kürzel greifen nicht in Eingabefeldern', () => {
    const input = document.createElement('input')
    expect(boardShortcut(key({ key: 'N' }))).toBe('new-card')
    expect(boardShortcut(key({ key: 'n' }, input))).toBeNull()
    const root = document.createElement('div')
    document.body.append(root)
    const handle = vi.fn()
    const stop = listenBoardShortcuts(() => root, handle)
    document.dispatchEvent(new KeyboardEvent('keydown', { key: '/' }))
    expect(handle).toHaveBeenCalledWith('search')
    stop()
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'f' }))
    expect(handle).toHaveBeenCalledTimes(1)
  })
})

describe('Ziehen mit dem Zeiger', () => {
  it('berechnet die Einfügeposition und legt nach der Schwelle ab', () => {
    const root = document.createElement('div')
    root.innerHTML = '<section data-column-id="fertig"><div data-card-list><article data-card-id="x"></article></div></section>'
    document.body.append(root)
    const list = root.querySelector('[data-card-list]')!
    expect(indexAt(list, 'x', 0)).toBe(0)
    expect(indexAt(list, 'a', 100)).toBe(1)
    const setPreview = vi.fn()
    const commit = vi.fn()
    const preview = { cardId: 'a', columnId: 'fertig', index: 0 }
    const move = { store: { get: () => ({ grabbed: null, preview }) }, allowed: () => true, setPreview, commit } as unknown as MoveController
    const drag = createPointerDrag({ mover: move, root: () => root, enabled: () => true, columns: () => [] })
    document.elementFromPoint = () => root.querySelector('article')
    const element = document.createElement('article')
    drag.onPointerDown({ button: 0, pointerId: 1, clientX: 0, clientY: 0, target: element, currentTarget: element }, card)
    window.dispatchEvent(new PointerEvent('pointermove', { pointerId: 1, clientX: 20, clientY: 20 }))
    expect(drag.store.get().active).toBe(true)
    expect(setPreview).toHaveBeenCalledWith({ cardId: 'a', columnId: 'fertig', index: 0 })
    window.dispatchEvent(new PointerEvent('pointerup', { pointerId: 1 }))
    expect(commit).toHaveBeenCalledWith('a', preview)
    expect(drag.consumeClick()).toBe(true)
    expect(drag.consumeClick()).toBe(false)
  })
})
