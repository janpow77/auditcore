import { effectScope, nextTick } from 'vue'
import { describe, expect, it } from 'vitest'
import { KanbanError, type BoardPort } from '@flowaudit/kanban-core'
import { useColumnEditor } from '../../src/kanban/useColumnEditor'
import { useKanbanActions } from '../../src/kanban/useKanbanActions'
import { useKanbanBoard } from '../../src/kanban/useKanbanBoard'
import { useKanbanFilter } from '../../src/kanban/useKanbanFilter'
import { board, flush, port } from './fixtures'

function setup(current: BoardPort, readOnly = false) {
  const scope = effectScope()
  const result = scope.run(() => {
    const filter = useKanbanFilter()
    const state = useKanbanBoard({ port: () => current, boardId: () => 'b1', criteria: () => filter.criteria.value, readOnly: () => readOnly, today: () => '2026-09-25' })
    return { filter, state, actions: useKanbanActions(state) }
  })
  if (!result) throw new Error('scope')
  return result
}

describe('useKanbanBoard', () => {
  it('lädt, gruppiert, filtert und kennt die Rechte', async () => {
    const { state, filter } = setup(port())
    await state.load()
    expect(state.columns.value.map((view) => view.cards.length)).toEqual([2, 1, 0])
    expect(state.can.value).toMatchObject({ move: true, configure: true, share: true })
    filter.state.query = 'vergabe'
    await nextTick()
    expect(state.columns.value[0]?.cards.map((entry) => entry.id)).toEqual(['b'])
    expect(state.columns.value[0]?.total).toBe(2)
  })

  it('wendet Änderungen optimistisch an und übernimmt den Port-Stand', async () => {
    const { state, actions } = setup(port())
    await state.load()
    const pending = actions.move('a', 'fertig', {})
    expect(state.columns.value[2]?.cards.map((entry) => entry.id)).toEqual(['a'])
    const result = await pending
    expect(result?.board.version).toBe(2)
    expect(state.board.value?.version).toBe(2)
  })

  it('rollt bei Ablehnung durch den Port zurück und meldet den Fehler', async () => {
    const failing = port()
    failing.moveCard = () => Promise.reject(new KanbanError('VERSION_CONFLICT', 'Board wurde inzwischen geändert'))
    const { state, actions } = setup(failing)
    await state.load()
    expect(await actions.move('a', 'fertig', {})).toBeNull()
    expect(state.columns.value[0]?.cards.map((entry) => entry.id)).toEqual(['a', 'b'])
    expect(state.error.value?.code).toBe('VERSION_CONFLICT')
  })

  it('lehnt lokal unzulässige Züge ohne Port-Aufruf ab (WIP-Limit)', async () => {
    const current = port()
    let calls = 0
    const original = current.moveCard.bind(current)
    current.moveCard = (...args) => {
      calls += 1
      return original(...args)
    }
    const { state, actions } = setup(current)
    await state.load()
    expect(await actions.move('a', 'arbeit', {})).toBeNull()
    expect(state.error.value?.code).toBe('WIP_LIMIT_REACHED')
    expect(calls).toBe(0)
  })

  it('sperrt im Nur-Lesen-Modus alle Schreibrechte, auch für Eigentümer', async () => {
    const { state } = setup(port(), true)
    await state.load()
    expect(state.can.value).toMatchObject({ read: true, move: false, edit: false, configure: false })
  })

  it('zeigt Unbeteiligten einen Fehler statt des Boards', async () => {
    const { state } = setup(port('fremd'))
    await state.load()
    expect(state.board.value).toBeNull()
    expect(state.error.value?.code).toBe('NOT_VISIBLE')
  })

  it('führt Änderungen nacheinander aus', async () => {
    const { state, actions } = setup(port())
    await state.load()
    await Promise.all([actions.toggle(state.board.value!.cards[0]!), actions.editCard('b', { title: 'Neu' }), actions.rename('Umbenannt')])
    await flush()
    expect(state.board.value?.version).toBe(4)
    expect(state.board.value?.title).toBe('Umbenannt')
  })
})

describe('useColumnEditor', () => {
  it('fügt hinzu, verschiebt, entfernt und prüft', () => {
    const editor = useColumnEditor(4)
    editor.reset(board().columns)
    editor.add('Neue Spalte')
    expect(editor.draft.value.map((column) => column.id)).toEqual(['offen', 'arbeit', 'fertig', 'neue_spalte'])
    expect(editor.canAdd.value).toBe(false)
    editor.move(3, -1)
    editor.remove(0)
    expect(editor.removed.value.map((column) => column.id)).toEqual(['offen'])
    editor.update(0, { done: true })
    editor.update(1, { done: true })
    expect(editor.draft.value.filter((column) => column.done).map((column) => column.id)).toEqual(['neue_spalte'])
    editor.update(0, { label: '  ' })
    expect(editor.validated()).toBeNull()
    expect(editor.problem.value).toBe('Spaltenlabel ist ungültig')
    expect(editor.dirty.value).toBe(true)
  })
})
