import { KanbanBoard, KanbanBoardList } from '@flowaudit/ui'
import { act, fireEvent } from '@testing-library/react'
import { flushPromises } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import { kanbanPort, NOW, TODAY, USERS } from '../../../kanban-core/test/parity/cases'
import { formState, normalizeDom } from '../../../ui-core/test/parity/dom'
import { FlowauditKanbanBoard } from '../../src/kanban/FlowauditKanbanBoard'
import { FlowauditKanbanBoards } from '../../src/kanban/FlowauditKanbanBoards'
import { renderBoth, tick, type Rendered } from './setup'

type Find = (root: HTMLElement) => Element | null | undefined
type Act = (target: Element) => void

async function settle(): Promise<void> {
  await flushPromises()
  await tick()
  await flushPromises()
  await tick()
}

/** Dialoge liegen im `body`; Zuordnung über die Framework-Markierung am Element. */
function dialogOf(framework: 'vue' | 'react'): HTMLElement | null {
  const all = Array.from(document.body.querySelectorAll<HTMLElement>(':scope > .fa-dialog'))
  const isReact = (element: HTMLElement): boolean => Object.keys(element).some((key) => key.startsWith('__react'))
  return all.find((element) => (framework === 'react') === isReact(element)) ?? null
}

function expectSame(rendered: Rendered): void {
  expect(normalizeDom(rendered.react)).toBe(normalizeDom(rendered.vue))
  expect(formState(rendered.react)).toEqual(formState(rendered.vue))
  const vue = dialogOf('vue')
  const react = dialogOf('react')
  expect(Boolean(react)).toBe(Boolean(vue))
  if (vue && react) {
    expect(normalizeDom(react)).toBe(normalizeDom(vue))
    expect(formState(react)).toEqual(formState(vue))
  }
}

/** Dieselbe Bedienung an Vue und React (Ziel im Board oder im eigenen Dialog), danach vergleichen. */
async function both(rendered: Rendered, find: Find, action: Act, inDialog = false): Promise<void> {
  for (const framework of ['vue', 'react'] as const) {
    const root = inDialog ? dialogOf(framework) : rendered[framework]
    const target = root ? find(root) : null
    expect(target, `Ziel fehlt (${framework})`).toBeTruthy()
    await act(async () => action(target as Element))
    await settle()
  }
  expectSame(rendered)
}

const byLabel = (label: string): Find => (root) => root.querySelector(`[aria-label="${label}"]`)
const byText = (text: string): Find => (root) => Array.from(root.querySelectorAll('button')).find((node) => node.textContent?.trim() === text)
const card = (id: string): Find => (root) => root.querySelector(`[data-card-id="${id}"]`)
const key = (value: string, init: KeyboardEventInit = {}): Act => (target) => fireEvent.keyDown(target, { key: value, ...init })
const click: Act = (target) => fireEvent.click(target)
const type = (value: string): Act => (target) => fireEvent.input(target, { target: { value } })

async function renderBoard(): Promise<Rendered> {
  const props = { port: kanbanPort(), boardId: 'b1', today: TODAY, users: USERS }
  return renderBoth(KanbanBoard, props, <FlowauditKanbanBoard {...props} port={kanbanPort()} />)
}

describe('Parität Kanban nach Interaktion', () => {
  it('Tastatur: aufnehmen, verschieben, ablegen, abbrechen, Strg+Pfeil', async () => {
    const rendered = await renderBoard()
    await both(rendered, card('b'), key(' '))
    await both(rendered, card('b'), key('ArrowUp'))
    await both(rendered, card('b'), key('ArrowRight'))
    await both(rendered, card('b'), key('Escape'))
    await both(rendered, card('a'), key(' '))
    await both(rendered, card('a'), key('ArrowRight'))
    await both(rendered, card('a'), key(' '))
    expect(rendered.react.querySelector('[role="status"]')?.textContent).toContain('abgelegt in Erledigt')
    await both(rendered, card('d'), key('ArrowUp', { ctrlKey: true }))
    await both(rendered, card('b'), key('ArrowLeft', { ctrlKey: true }))
  })

  it('Karte öffnen, Felder ändern, Checkliste, Tags, Farbe, löschen', async () => {
    const rendered = await renderBoard()
    await both(rendered, card('a'), click)
    await both(rendered, byText('Niedrig'), click, true)
    await both(rendered, byLabel('Neuer Tag + Enter'), type('Prüfpfad'), true)
    await both(rendered, byLabel('Neuer Tag + Enter'), key('Enter'), true)
    await both(rendered, byLabel('Frist setzen'), click, true)
    await both(rendered, byLabel('Rot'), click, true)
    await both(rendered, byLabel('Tag EFRE entfernen'), click, true)
    await both(rendered, byText('Aufgabe löschen'), click, true)
    await both(rendered, byText('Wirklich löschen?'), click, true)
    expect(rendered.react.querySelector('[data-card-id="a"]')).toBeNull()
  })

  it('Suche und Filter, zurücksetzen, Erledigt umschalten', async () => {
    const rendered = await renderBoard()
    await both(rendered, (root) => root.querySelector('input[type="search"]'), type('vergabe'))
    await both(rendered, byText('Filter zurücksetzen'), click)
    await both(rendered, byLabel('Priorität'), (target) => fireEvent.change(target, { target: { value: 'hoch' } }))
    await both(rendered, byText('Filter zurücksetzen'), click)
    await both(rendered, (root) => root.querySelector('[data-card-id="c"] .fa-kanban-card__check'), click)
  })

  it('Einstellungen: Spalte hinzufügen, umbenennen, verschieben, speichern', async () => {
    const rendered = await renderBoard()
    await both(rendered, byLabel('Board-Einstellungen'), click)
    await both(rendered, byText('Spalte hinzufügen'), click, true)
    await both(rendered, (root) => root.querySelectorAll('[data-column-editor] input.fa-field__input')[6], type('Nachprüfung'), true)
    await both(rendered, (root) => root.querySelectorAll('[aria-label="Nach oben"]')[3], click, true)
    await both(rendered, (root) => root.querySelector('[data-testid="kanban-settings-save"]'), click, true)
    expect(rendered.react.textContent).toContain('Nachprüfung')
  })

  it('Teilen: Person suchen, freigeben, Recht ändern, entfernen', async () => {
    const rendered = await renderBoard()
    await both(rendered, byLabel('Board teilen'), click)
    await both(rendered, (root) => root.querySelector('input[type="search"]'), type('Tobias'), true)
    await both(rendered, byText('Tobias Keller · tobias.keller@example.org'), click, true)
    await both(rendered, (root) => root.querySelector('[data-share="neu"] select'), (target) => fireEvent.change(target, { target: { value: 'edit' } }), true)
    expect(dialogOf('react')?.querySelector('[data-share="neu"]')).not.toBeNull()
    await both(rendered, byLabel('Freigabe für Lena Schmidt entfernen'), click, true)
    await both(rendered, byText('Freigabe wirklich entfernen?'), click, true)
    expect(dialogOf('react')?.querySelector('[data-share="leser"]')).toBeNull()
    await both(rendered, byLabel('Schließen'), click, true)
    expect(dialogOf('react')).toBeNull()
  })

  it('Boardliste: anlegen aus Vorlage, anheften, löschen', async () => {
    const props = { port: kanbanPort(), activeId: 'b1', now: NOW }
    const rendered = await renderBoth(KanbanBoardList, props, <FlowauditKanbanBoards {...props} port={kanbanPort()} />)
    await both(rendered, byText('Neues Board'), click)
    await both(rendered, (root) => root.querySelector('form input'), type('Jahreskontrollbericht'))
    await both(rendered, (root) => root.querySelectorAll('.fa-kanban-boards__template')[1], click)
    await both(rendered, (root) => root.querySelector('form'), (target) => fireEvent.submit(target))
    expect(rendered.react.textContent).toContain('Jahreskontrollbericht')
    await both(rendered, byLabel('Anheften'), click)
    await both(rendered, byLabel('Board Prüfung 2026 löschen'), click)
    await both(rendered, byText('Board „Prüfung 2026“ wirklich löschen?'), click)
  })
})
