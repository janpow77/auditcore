// Verhalten der nativen React-Fassung, entsprechend ui/test/kanban/board.spec.ts (Vue).
import { act, cleanup, fireEvent, render, screen } from '@testing-library/react'
import { createRef } from 'react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { board, card, port } from '../../ui/test/kanban/fixtures'
import { FlowauditKanbanBoard, FlowauditKanbanBoards, KanbanCard, LocaleProvider, type FlowauditKanbanBoardHandle, type FlowauditKanbanBoardProps } from '../src'

afterEach(() => {
  cleanup()
  document.body.innerHTML = ''
})

const flush = () => act(() => new Promise<void>((resolve) => setTimeout(resolve, 0)))

async function mountBoard(props: FlowauditKanbanBoardProps) {
  const view = render(<FlowauditKanbanBoard today="2026-09-25" {...props} />)
  await flush()
  await flush()
  return view.container
}

const ids = (root: HTMLElement, column: string) => Array.from(root.querySelectorAll<HTMLElement>(`[data-column-id="${column}"] [data-card-id]`)).map((node) => node.dataset.cardId)
const live = (): string => document.querySelector('[role="status"]')?.textContent ?? ''
const cardEl = (root: HTMLElement, id: string) => root.querySelector(`[data-card-id="${id}"]`) as HTMLElement

describe('FlowauditKanbanBoard (React, nativ)', () => {
  it('rendert Spalten, Zähler mit WIP-Limit und zugängliche Karten', async () => {
    const root = await mountBoard({ port: port(), boardId: 'b1' })
    expect(root.querySelectorAll('[data-column-id]')).toHaveLength(3)
    expect(ids(root, 'offen')).toEqual(['a', 'b'])
    expect(root.querySelector('[data-column-id="arbeit"] .fa-kanban-column__count')?.textContent).toBe('1/1')
    const first = cardEl(root, 'a')
    expect(first.getAttribute('role')).toBe('listitem')
    expect(first.getAttribute('aria-roledescription')).toBe('Karte')
    expect(first.getAttribute('aria-label')).toContain('Belegliste anfordern')
    expect(root.querySelector('[role="progressbar"]')?.getAttribute('aria-valuenow')).toBe('0')
  })

  it('verschiebt per Tastatur mit Ansage und respektiert das WIP-Limit', async () => {
    const onBoardChange = vi.fn()
    const root = await mountBoard({ port: port(), boardId: 'b1', onBoardChange })
    fireEvent.keyDown(cardEl(root, 'a'), { key: ' ' })
    await flush()
    expect(live()).toContain('aufgenommen')
    fireEvent.keyDown(cardEl(root, 'a'), { key: 'ArrowRight' })
    await flush()
    // „In Arbeit“ ist voll (WIP 1/1, Modus block): die Vorschau überspringt die Spalte.
    expect(live()).toContain('Spalte Erledigt')
    fireEvent.keyDown(cardEl(root, 'a'), { key: 'Enter' })
    await flush()
    await flush()
    expect(ids(root, 'fertig')).toEqual(['a'])
    expect(live()).toContain('abgelegt in Erledigt')
    expect(document.activeElement).toBe(cardEl(root, 'a'))
    fireEvent.keyDown(cardEl(root, 'b'), { key: 'ArrowRight', ctrlKey: true })
    await flush()
    await flush()
    expect(ids(root, 'fertig')).toEqual(['b', 'a'])
    expect(onBoardChange).toHaveBeenCalled()
  })

  it('bricht das Verschieben mit Escape ab', async () => {
    const root = await mountBoard({ port: port(), boardId: 'b1' })
    fireEvent.keyDown(cardEl(root, 'a'), { key: ' ' })
    await flush()
    expect(cardEl(root, 'a').getAttribute('aria-pressed')).toBe('true')
    fireEvent.keyDown(cardEl(root, 'a'), { key: 'Escape' })
    await flush()
    expect(live()).toContain('abgebrochen')
    expect(cardEl(root, 'a').getAttribute('aria-pressed')).toBeNull()
  })

  it('markiert Karten als erledigt und öffnet sie wieder', async () => {
    const root = await mountBoard({ port: port(), boardId: 'b1' })
    fireEvent.click(root.querySelector('[data-card-id="b"] .fa-kanban-card__check')!)
    await flush()
    expect(ids(root, 'fertig')).toEqual(['b'])
    fireEvent.click(root.querySelector('[data-card-id="b"] .fa-kanban-card__check')!)
    await flush()
    expect(ids(root, 'offen')).toEqual(['b', 'a'])
  })

  it('legt Karten an, öffnet die Details und speichert Änderungen', async () => {
    const onCardOpen = vi.fn()
    const root = await mountBoard({ port: port(), boardId: 'b1', onCardOpen, renderCardExtra: (entry) => <p data-testid="extra">Extra {entry.id}</p> })
    fireEvent.click(root.querySelector('[data-column-id="fertig"] .fa-kanban-column__add')!)
    await flush()
    await flush()
    expect(ids(root, 'fertig')).toHaveLength(1)
    const dialog = screen.getByRole('dialog')
    expect(dialog.textContent).toContain('Neue Aufgabe')
    expect(screen.getByTestId('extra').textContent).toMatch(/^Extra /)
    const title = screen.getByLabelText('Titel')
    fireEvent.change(title, { target: { value: 'Prüfvermerk schreiben' } })
    fireEvent.blur(title)
    await flush()
    await flush()
    expect(root.querySelector('[data-column-id="fertig"]')?.textContent).toContain('Prüfvermerk schreiben')
    fireEvent.keyDown(dialog, { key: 'Escape' })
    await flush()
    expect(screen.queryByRole('dialog')).toBeNull()
    fireEvent.click(cardEl(root, 'a'))
    expect(onCardOpen).toHaveBeenCalledWith(expect.objectContaining({ id: 'a' }))
  })

  it('zeigt Leserinnen ein Nur-Lesen-Banner ohne Bearbeitungselemente', async () => {
    const root = await mountBoard({ port: port('leser'), boardId: 'b1' })
    expect(root.querySelector('.fa-kanban__banner')?.textContent).toContain('Nur Lesezugriff')
    expect(root.querySelectorAll('.fa-kanban-column__add')).toHaveLength(0)
    expect(root.querySelectorAll('.fa-kanban-card__check')).toHaveLength(0)
    fireEvent.keyDown(cardEl(root, 'a'), { key: ' ' })
    await flush()
    expect(cardEl(root, 'a').getAttribute('aria-pressed')).toBeNull()
  })

  it('bearbeitet ohne Port ein übergebenes Board lokal und meldet die Änderung', async () => {
    const onBoardChange = vi.fn()
    const root = await mountBoard({ board: board(), userId: 'owner', onBoardChange })
    fireEvent.keyDown(cardEl(root, 'a'), { key: 'ArrowDown', ctrlKey: true })
    await flush()
    await flush()
    expect(ids(root, 'offen')).toEqual(['b', 'a'])
    expect(onBoardChange.mock.calls.at(-1)?.[0].version).toBe(2)
  })

  it('filtert über die Werkzeugleiste und setzt den Filter zurück', async () => {
    const root = await mountBoard({ port: port(), boardId: 'b1' })
    fireEvent.change(root.querySelector('input[type="search"]')!, { target: { value: 'efre' } })
    expect(ids(root, 'offen')).toEqual(['a'])
    fireEvent.click(screen.getByRole('button', { name: 'Filter zurücksetzen' }))
    expect(ids(root, 'offen')).toEqual(['a', 'b'])
  })

  it('Tastenkürzel: / fokussiert die Suche, F meldet Vollbild, N legt eine Karte an', async () => {
    const onFullscreen = vi.fn()
    const root = await mountBoard({ port: port(), boardId: 'b1', onFullscreen })
    fireEvent.keyDown(document.body, { key: '/' })
    expect(document.activeElement).toBe(root.querySelector('input[type="search"]'))
    ;(document.activeElement as HTMLElement).blur()
    fireEvent.keyDown(document.body, { key: 'f' })
    expect(onFullscreen).toHaveBeenCalledTimes(1)
    fireEvent.keyDown(document.body, { key: 'n' })
    await flush()
    await flush()
    expect(ids(root, 'offen')).toHaveLength(3)
  })

  it('benennt das Board um und speichert Spalten über den Einstellungsdialog', async () => {
    const onBoardChange = vi.fn()
    const root = await mountBoard({ port: port(), boardId: 'b1', onBoardChange })
    fireEvent.click(screen.getByRole('button', { name: 'Prüfung 2026' }))
    const input = screen.getByLabelText('Board-Titel')
    fireEvent.change(input, { target: { value: 'Prüfung 2027' } })
    fireEvent.keyDown(input, { key: 'Enter' })
    await flush()
    expect(root.querySelector('h1')?.textContent).toBe('Prüfung 2027')
    fireEvent.click(screen.getByRole('button', { name: 'Board-Einstellungen' }))
    fireEvent.click(screen.getByRole('button', { name: 'Spalte hinzufügen' }))
    fireEvent.click(screen.getByTestId('kanban-settings-save'))
    await flush()
    await flush()
    expect(screen.queryByRole('dialog')).toBeNull()
    expect(root.querySelectorAll('[data-column-id]')).toHaveLength(4)
  })

  it('meldet Fehler und lädt über die Handle-Methode neu', async () => {
    const onError = vi.fn()
    const ref = createRef<FlowauditKanbanBoardHandle>()
    render(<FlowauditKanbanBoard ref={ref} port={port('fremd')} boardId="b1" onError={onError} />)
    await flush()
    expect(onError.mock.calls[0]?.[0].code).toBe('NOT_VISIBLE')
    expect(screen.getByRole('alert').textContent).toContain('Fehler:')
    expect(ref.current?.board).toBeNull()
    await act(async () => ref.current?.reload())
    expect(onError).toHaveBeenCalledTimes(2)
  })

  it('übernimmt die Sprache aus dem LocaleProvider', async () => {
    render(<LocaleProvider locale="en"><FlowauditKanbanBoard port={port()} boardId="b1" /></LocaleProvider>)
    await flush()
    expect(screen.getByRole('button', { name: 'Share board' })).toBeTruthy()
  })
})

describe('KanbanCard (React)', () => {
  it('zeigt Frist, Checkliste und Kennung und meldet Öffnen', () => {
    const onOpen = vi.fn()
    const { container } = render(<KanbanCard today="2026-09-25" now={Date.parse('2026-09-25T12:00:00Z')} onOpen={onOpen} card={card('x', 'offen', 'V', { badge: 'VP-19', due: '2026-09-24', checklist: [{ text: 'a', done: true }, { text: 'b', done: false }], tags: ['a', 'b', 'c', 'd'] })} />)
    const article = container.querySelector('article') as HTMLElement
    expect(container.querySelector('.fa-kanban-card__due')?.className).toContain('is-overdue')
    expect(article.textContent).toContain('1/2')
    expect(article.textContent).toContain('+1')
    expect(container.querySelector('.fa-kanban-card__badge')?.getAttribute('style')).toContain('background')
    fireEvent.click(article)
    expect(onOpen).toHaveBeenCalledTimes(1)
  })
})

describe('FlowauditKanbanBoards (React)', () => {
  it('listet eigene Boards und legt neue aus Vorlagen an', async () => {
    const onBoardSelect = vi.fn()
    const onCreated = vi.fn()
    const { container } = render(<FlowauditKanbanBoards port={port()} onBoardSelect={onBoardSelect} onCreated={onCreated} />)
    await flush()
    expect(container.textContent).toContain('Prüfung 2026')
    fireEvent.click(container.querySelector('.fa-kanban-boards .fa-button')!)
    fireEvent.change(container.querySelector('input')!, { target: { value: 'Systemprüfung S03' } })
    fireEvent.click(container.querySelectorAll('.fa-kanban-boards__template')[4]!)
    fireEvent.submit(container.querySelector('form')!)
    await flush()
    await flush()
    expect(onBoardSelect).toHaveBeenCalled()
    expect(onCreated.mock.calls[0]?.[0].title).toBe('Systemprüfung S03')
    expect(container.textContent).toContain('Systemprüfung S03')
  })
})
