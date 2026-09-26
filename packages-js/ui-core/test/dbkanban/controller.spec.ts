import { describe, expect, it, vi } from 'vitest'
import type { RecordPort } from '@auditcore/kanban-core'
import { createDbKanbanController, initialGroupBy } from '../../src/dbkanban/controller'
import { cellText, dbKanbanView } from '../../src/dbkanban/view'
import { recordPort, recordTable, t } from './fixtures'

function setup(port: RecordPort | null = recordPort(), editable = true) {
  const hooks = { onMoved: vi.fn(), onAdded: vi.fn(), onGroupBy: vi.fn(), onError: vi.fn() }
  const controller = createDbKanbanController({ port: () => port, t: () => t, editable: () => editable, lang: () => 'de', ...hooks })
  const view = () => dbKanbanView(controller.store.get(), t, 'de')
  return { controller, hooks, view }
}

describe('Datenbankansicht – Zustandsautomat', () => {
  it('gruppiert nach der ersten Auswahl-Eigenschaft wie group_by_value', async () => {
    const { controller, view } = setup()
    await controller.load()
    expect(controller.store.get().groupBy).toBe('status')
    expect(view().columns.map((column) => [column.label, column.cards.map((card) => card.id)])).toEqual([
      ['Ohne Wert', ['r3', 'r5']],
      ['offen', ['r1', 'r6']],
      ['in Prüfung', ['r4']],
      ['erledigt', ['r2']],
    ])
    const first = view().columns[1]?.cards[0]
    expect(first).toEqual({ id: 'r1', title: 'Vorhaben A', column: 'offen', fields: [{ id: 'fonds', label: 'Fonds', text: 'EFRE' }, { id: 'betrag', label: 'Betrag', text: '1.200' }] })
    expect(view().groupOptions).toEqual([{ value: 'status', label: 'Status' }, { value: 'fonds', label: 'Fonds' }])
  })

  it('übernimmt eine gewünschte Gruppierung und meldet Wechsel', async () => {
    const { controller, hooks, view } = setup()
    await controller.load('fonds')
    expect(view().columns.map((column) => column.value)).toEqual(['', 'EFRE', 'ESF+', 'JTF'])
    controller.setGroupBy('fonds')
    expect(hooks.onGroupBy).not.toHaveBeenCalled()
    controller.setGroupBy('status')
    expect(hooks.onGroupBy).toHaveBeenCalledWith('status')
    expect(initialGroupBy(recordTable, 'titel')).toBe('status')
    expect(initialGroupBy({ properties: [], rows: [] }, undefined)).toBe('')
  })

  it('verschiebt per Ablegen, setzt null für „ohne Wert“ und meldet es', async () => {
    const port = recordPort()
    const { controller, hooks, view } = setup(port)
    await controller.load()
    controller.startDrag('r1')
    expect(await controller.move('r1', 'erledigt')).toBe(true)
    expect(port.updateCell).toHaveBeenCalledWith('r1', 'status', 'erledigt')
    expect(hooks.onMoved).toHaveBeenCalledWith({ rowId: 'r1', propertyId: 'status', value: 'erledigt' })
    expect(controller.store.get()).toMatchObject({ dragging: null, notice: '„Vorhaben A“ nach „erledigt“ verschoben.' })
    expect(await controller.move('r2', '')).toBe(true)
    expect(port.updateCell).toHaveBeenLastCalledWith('r2', 'status', null)
    expect(view().columns[0]?.cards.map((card) => card.id)).toEqual(['r2', 'r3', 'r5'])
    expect(await controller.move('r2', '')).toBe(false)
  })

  it('nimmt die Verschiebung bei einem Fehler zurück', async () => {
    const port = recordPort({ updateCell: vi.fn(async () => Promise.reject(new TypeError('Failed to fetch'))) })
    const { controller, hooks } = setup(port)
    await controller.load()
    expect(await controller.move('r1', 'erledigt')).toBe(false)
    expect(controller.store.get().table?.rows[0]?.cells.status).toBe('offen')
    expect(controller.store.get().error?.message).toBe('Keine Verbindung zur Datenquelle (Failed to fetch).')
    expect(hooks.onError).toHaveBeenCalledOnce()
  })

  it('übernimmt einen gespeicherten Datensatz aus dem Port und akzeptiert void', async () => {
    const saved = { id: 'r1', cells: { titel: 'Vorhaben A (Server)', status: 'erledigt' } }
    const { controller, view } = setup(recordPort({ updateCell: vi.fn(async () => saved) }))
    await controller.load()
    await controller.move('r1', 'erledigt')
    expect(view().columns[3]?.cards.map((card) => card.title)).toEqual(['Vorhaben A (Server)', 'Vorhaben B'])
    const plain = setup(recordPort({ updateCell: vi.fn(async () => undefined) }))
    await plain.controller.load()
    expect(await plain.controller.move('r1', 'erledigt')).toBe(true)
  })

  it('verschiebt per Tastatur in die sichtbare Nachbarspalte', async () => {
    const { controller } = setup()
    await controller.load()
    expect(await controller.moveBy('r1', 1)).toBe(true)
    expect(controller.store.get().table?.rows[0]?.cells.status).toBe('in Prüfung')
    expect(await controller.moveBy('r3', -1)).toBe(false)
    expect(await controller.moveBy('fehlt', 1)).toBe(false)
  })

  it('legt Einträge mit dem Spaltenwert an', async () => {
    const port = recordPort()
    const { controller, hooks, view } = setup(port)
    await controller.load()
    const row = await controller.addCard('in Prüfung')
    expect(port.addRow).toHaveBeenCalledWith({ status: 'in Prüfung' })
    expect(hooks.onAdded).toHaveBeenCalledWith(row)
    expect(view().columns[2]?.cards.map((card) => card.title)).toEqual(['Vorhaben D', 'Ohne Titel'])
    expect(controller.store.get().notice).toBe('Eintrag in „in Prüfung“ angelegt.')
    const { addRow: _unused, ...withoutAdd } = recordPort()
    const limited = setup(withoutAdd)
    await limited.controller.load()
    expect(await limited.controller.addCard('offen')).toBeNull()
  })

  it('verändert im Nur-Lese-Modus nichts', async () => {
    const port = recordPort()
    const { controller } = setup(port, false)
    await controller.load()
    expect(await controller.move('r1', 'erledigt')).toBe(false)
    expect(await controller.addCard('offen')).toBeNull()
    expect(port.updateCell).not.toHaveBeenCalled()
  })

  it('filtert, meldet leere Treffer und Tabellen ohne Auswahl-Eigenschaft', async () => {
    const { controller, view } = setup()
    await controller.load()
    controller.setQuery('esf+')
    expect(view().columns.flatMap((column) => column.cards.map((card) => card.id))).toEqual(['r2'])
    controller.setQuery('gibt es nicht')
    expect(view().noMatches).toBe(true)
    const plain = setup(recordPort({}, { properties: [{ id: 'titel', name: 'Titel', type: 'text' }], rows: [] }))
    await plain.controller.load()
    expect(plain.view().notice).toBe('Die Tabelle hat keine Auswahl-Eigenschaft, nach der gruppiert werden kann.')
    const none = setup(null)
    await none.controller.load()
    expect(none.view()).toMatchObject({ columns: [], notice: null })
  })

  it('zeigt Zellwerte lesbar an', () => {
    expect(cellText(true, t, 'de')).toBe('Ja')
    expect(cellText(false, t, 'de')).toBe('Nein')
    expect(cellText(['a', 'b'], t, 'de')).toBe('a, b')
    expect(cellText(1234.5, t, 'en')).toBe('1,234.5')
    expect(cellText(null, t, 'de')).toBe('')
    expect(cellText(undefined, t, 'de')).toBe('')
  })
})
