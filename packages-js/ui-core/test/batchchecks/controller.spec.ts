import { describe, expect, it } from 'vitest'
import { createBatchchecksController, createBatchchecksMemoryPort, batchchecksIsEmpty, batchchecksRows, batchchecksSelection, type BatchchecksPort } from '../../src'

const items = [{ id: 'a', label: 'Eintrag A' }, { id: 'b', label: 'Eintrag B' }]

function controller(port: BatchchecksPort | null = createBatchchecksMemoryPort(items)) {
  const events: string[] = []
  const created = createBatchchecksController({ port: () => port, callbacks: () => ({ selected: (item) => events.push(item.id), failed: (message) => events.push(message) }) })
  return { created, events }
}

describe('createBatchchecksController', () => {
  it('lädt die Einträge und wählt aus', async () => {
    const { created, events } = controller()
    await created.load()
    created.select('b')
    const state = created.store.get()
    expect(batchchecksRows(state).map((row) => row.selected)).toEqual([false, true])
    expect(batchchecksSelection(state)?.label).toBe('Eintrag B')
    expect(events).toEqual(['b'])
  })

  it('meldet Fehler des Ports', async () => {
    const { created, events } = controller({ list: async () => { throw new Error('Dienst nicht erreichbar') } })
    await created.load()
    expect(created.store.get().error).toBe('Dienst nicht erreichbar')
    expect(events).toEqual(['Dienst nicht erreichbar'])
  })

  it('ohne Port: leer, keine Auswahl unbekannter Einträge', async () => {
    const { created, events } = controller(null)
    await created.load()
    created.select('x')
    expect(batchchecksIsEmpty(created.store.get())).toBe(true)
    expect(events).toEqual([])
  })
})
