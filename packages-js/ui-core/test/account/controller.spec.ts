import { describe, expect, it } from 'vitest'
import { createAccountController, createAccountMemoryPort, accountIsEmpty, accountRows, accountSelection, type AccountPort } from '../../src'

const items = [{ id: 'a', label: 'Eintrag A' }, { id: 'b', label: 'Eintrag B' }]

function controller(port: AccountPort | null = createAccountMemoryPort(items)) {
  const events: string[] = []
  const created = createAccountController({ port: () => port, callbacks: () => ({ selected: (item) => events.push(item.id), failed: (message) => events.push(message) }) })
  return { created, events }
}

describe('createAccountController', () => {
  it('lädt die Einträge und wählt aus', async () => {
    const { created, events } = controller()
    await created.load()
    await created.select('b')
    const state = created.store.get()
    expect(accountRows(state).map((row) => row.selected)).toEqual([false, true])
    expect(accountSelection(state)?.label).toBe('Eintrag B')
    expect(events).toEqual(['b'])
  })

  it('meldet Fehler des Ports', async () => {
    const { created, events } = controller({ ...createAccountMemoryPort([]), list: async () => { throw new Error('Dienst nicht erreichbar') } })
    await created.load()
    expect(created.store.get().error).toBe('Dienst nicht erreichbar')
    expect(events).toEqual(['Dienst nicht erreichbar'])
  })

  it('ohne Port: leer, keine Auswahl unbekannter Einträge', async () => {
    const { created, events } = controller(null)
    await created.load()
    created.select('x')
    expect(accountIsEmpty(created.store.get())).toBe(true)
    expect(events).toEqual([])
  })
})

const profile = {
  id: 'profile', title: 'Persönliche Angaben', description: '', kind: 'profile' as const,
  revision: 1, fields: [{ id: 'display_name', label: 'Anzeigename' }, { id: 'function', label: 'Funktion', readonly: true }],
  values: { display_name: 'Alex', function: 'Prüfung' }, editable: true,
}
const profiles = [{ id: 'profile', label: 'Profil' }, { id: 'other', label: 'Anderer Bereich' }]

it('schützt Entwurf vor Navigation und übermittelt nur bearbeitbare Felder', async () => {
  const port = createAccountMemoryPort(profiles, [profile])
  const { created } = controller(port)
  await created.load(); await created.select('profile')
  created.edit('display_name', 'Geändert'); created.edit('function', 'Chef')
  await created.select('other')
  expect(created.store.get().selectedId).toBe('profile')
  await created.save()
  expect((await port.read('profile')).values).toEqual({ display_name: 'Geändert', function: 'Prüfung' })
  expect(created.store.get().dirty).toBe(false)
})

it('behält den Entwurf bei Versionskonflikt', async () => {
  const port = createAccountMemoryPort(profiles, [profile])
  const { created } = controller(port)
  await created.load(); await created.select('profile')
  created.edit('display_name', 'Mein Entwurf')
  await port.save('profile', 1, { display_name: 'Andere Sitzung' })
  await created.save()
  expect(created.store.get().error).toContain('inzwischen')
  expect(created.store.get().draft.display_name).toBe('Mein Entwurf')
  expect(created.store.get().dirty).toBe(true)
})

it('ignoriert Antworten des vorherigen Anschlusses', async () => {
  let resolve: ((items: typeof profiles) => void) | undefined
  let port: AccountPort = { ...createAccountMemoryPort([]), list: () => new Promise((done) => { resolve = done }) }
  const created = createAccountController({ port: () => port })
  const pending = created.load()
  port = createAccountMemoryPort([{ id: 'new', label: 'Neu' }])
  await created.load()
  resolve?.(profiles); await pending
  expect(created.store.get().items[0]?.id).toBe('new')
})

it('verwirft beim Schließen Passwortentwürfe', async () => {
  const created = createAccountController({ port: () => createAccountMemoryPort([]) })
  created.store.set({ draft: { password: 'secret' }, dirty: true })
  created.dispose()
  expect(created.store.get().draft).toEqual({})
})
