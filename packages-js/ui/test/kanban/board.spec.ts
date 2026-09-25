import { mount, type VueWrapper } from '@vue/test-utils'
import { afterEach, describe, expect, it } from 'vitest'
import { KanbanBoard, KanbanBoardList, KanbanCard } from '../../src'
import { board, card, flush, port } from './fixtures'

let wrapper: VueWrapper | null = null

afterEach(() => {
  wrapper?.unmount()
  wrapper = null
  document.body.innerHTML = ''
})

async function mountBoard(props: Record<string, unknown>): Promise<VueWrapper> {
  wrapper = mount(KanbanBoard, { props: { today: '2026-09-25', ...props }, attachTo: document.body })
  await flush()
  await flush()
  return wrapper
}

const ids = (root: VueWrapper, column: string) => root.findAll(`[data-column-id="${column}"] [data-card-id]`).map((node) => node.attributes('data-card-id'))
const live = (): string => document.querySelector('[role="status"]')?.textContent ?? ''

function key(root: VueWrapper, cardId: string, init: KeyboardEventInit): void {
  const element = root.find(`[data-card-id="${cardId}"]`).element as HTMLElement
  element.dispatchEvent(new KeyboardEvent('keydown', { bubbles: true, cancelable: true, ...init }))
}

describe('KanbanBoard', () => {
  it('rendert Spalten, Zähler mit WIP-Limit und zugängliche Karten', async () => {
    const root = await mountBoard({ port: port(), boardId: 'b1' })
    expect(root.findAll('[data-column-id]')).toHaveLength(3)
    expect(ids(root, 'offen')).toEqual(['a', 'b'])
    expect(root.find('[data-column-id="arbeit"] .fa-kanban-column__count').text()).toBe('1/1')
    const first = root.find('[data-card-id="a"]')
    expect(first.attributes('role')).toBe('listitem')
    expect(first.attributes('aria-roledescription')).toBe('Karte')
    expect(first.attributes('aria-label')).toContain('Belegliste anfordern')
    expect(root.find('[role="progressbar"]').attributes('aria-valuenow')).toBe('0')
  })

  it('verschiebt per Tastatur mit Ansage und respektiert das WIP-Limit', async () => {
    const root = await mountBoard({ port: port(), boardId: 'b1' })
    key(root, 'a', { key: ' ' })
    await flush()
    expect(live()).toContain('aufgenommen')
    key(root, 'a', { key: 'ArrowRight' })
    await flush()
    expect(live()).toContain('Spalte Erledigt')
    key(root, 'a', { key: 'Enter' })
    await flush()
    await flush()
    expect(ids(root, 'fertig')).toEqual(['a'])
    expect(live()).toContain('abgelegt in Erledigt')
    key(root, 'b', { key: 'ArrowRight', ctrlKey: true })
    await flush()
    await flush()
    // Strg+Pfeil behält die Position (cockpit: min(Index, Länge)) – b landet vor a.
    expect(ids(root, 'fertig')).toEqual(['b', 'a'])
    expect(root.emitted('board-change')).toBeTruthy()
  })

  it('markiert Karten als erledigt und öffnet sie wieder', async () => {
    const root = await mountBoard({ port: port(), boardId: 'b1' })
    await root.find('[data-card-id="b"] .fa-kanban-card__check').trigger('click')
    await flush()
    expect(ids(root, 'fertig')).toEqual(['b'])
    await root.find('[data-card-id="b"] .fa-kanban-card__check').trigger('click')
    await flush()
    expect(ids(root, 'offen')).toEqual(['b', 'a'])
  })

  it('legt Karten an, öffnet die Details und speichert Änderungen', async () => {
    const root = await mountBoard({ port: port(), boardId: 'b1' })
    await root.find('[data-column-id="fertig"] .fa-kanban-column__add').trigger('click')
    await flush()
    await flush()
    expect(ids(root, 'fertig')).toHaveLength(1)
    const dialog = document.querySelector('[role="dialog"]') as HTMLElement
    expect(dialog.textContent).toContain('Neue Aufgabe')
    const title = dialog.querySelector('input[placeholder=""]') ?? dialog.querySelectorAll('input')[1]
    ;(title as HTMLInputElement).value = 'Prüfvermerk schreiben'
    title?.dispatchEvent(new Event('input'))
    title?.dispatchEvent(new FocusEvent('focusout', { bubbles: true }))
    await flush()
    await flush()
    expect(root.find('[data-column-id="fertig"]').text()).toContain('Prüfvermerk schreiben')
  })

  it('zeigt Leserinnen ein Nur-Lesen-Banner ohne Bearbeitungselemente', async () => {
    const root = await mountBoard({ port: port('leser'), boardId: 'b1' })
    expect(root.find('.fa-kanban__banner').text()).toContain('Nur Lesezugriff')
    expect(root.findAll('.fa-kanban-column__add')).toHaveLength(0)
    expect(root.findAll('.fa-kanban-card__check')).toHaveLength(0)
    key(root, 'a', { key: ' ' })
    await flush()
    expect(root.find('[data-card-id="a"]').attributes('aria-pressed')).toBeUndefined()
  })

  it('bearbeitet ohne Port ein übergebenes Board lokal und meldet change', async () => {
    const root = await mountBoard({ board: board(), userId: 'owner' })
    key(root, 'a', { key: 'ArrowDown', ctrlKey: true })
    await flush()
    await flush()
    expect(ids(root, 'offen')).toEqual(['b', 'a'])
    const changed = root.emitted('board-change')?.at(-1)?.[0] as { version: number }
    expect(changed.version).toBe(2)
  })

  it('filtert über die Werkzeugleiste und setzt den Filter zurück', async () => {
    const root = await mountBoard({ port: port(), boardId: 'b1' })
    await root.find('input[type="search"]').setValue('efre')
    expect(ids(root, 'offen')).toEqual(['a'])
    await root.find('.fa-kanban-toolbar__tools .fa-button--ghost').trigger('click')
    expect(ids(root, 'offen')).toEqual(['a', 'b'])
  })
})

describe('KanbanCard', () => {
  it('zeigt Frist, Checkliste und Kennung und meldet Öffnen', async () => {
    const view = mount(KanbanCard, {
      props: { today: '2026-09-25', now: Date.parse('2026-09-25T12:00:00Z'), card: card('x', 'offen', 'V', { badge: 'VP-19', due: '2026-09-24', checklist: [{ text: 'a', done: true }, { text: 'b', done: false }], tags: ['a', 'b', 'c', 'd'] }) },
    })
    expect(view.find('.fa-kanban-card__due').classes()).toContain('is-overdue')
    expect(view.text()).toContain('1/2')
    expect(view.text()).toContain('+1')
    expect(view.find('.fa-kanban-card__badge').attributes('style')).toContain('background')
    await view.trigger('click')
    expect(view.emitted('open')).toHaveLength(1)
  })
})

describe('KanbanBoardList', () => {
  it('listet eigene Boards und legt neue aus Vorlagen an', async () => {
    const list = mount(KanbanBoardList, { props: { port: port() }, attachTo: document.body })
    await flush()
    expect(list.text()).toContain('Prüfung 2026')
    await list.find('.fa-kanban-boards .fa-button').trigger('click')
    await list.find('input').setValue('Systemprüfung S03')
    await list.findAll('.fa-kanban-boards__template')[4]?.trigger('click')
    await list.find('form').trigger('submit')
    await flush()
    await flush()
    expect(list.emitted('board-select')).toBeTruthy()
    expect(list.text()).toContain('Systemprüfung S03')
    list.unmount()
  })
})
