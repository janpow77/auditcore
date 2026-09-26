import { describe, expect, it, vi } from 'vitest'
import {
  createDsfaController,
  createStore,
  createSynopsisController,
  createVvtController,
  dataprotectionMessages,
  dsfaDerived,
  selectSynopsis,
  synopsisMessages,
  translator,
  vvtView,
} from '../src'
import { fakePort, register } from './dataprotection/fake-port'
import { standard } from './synopsis/fixtures'

const dp = translator(dataprotectionMessages, 'de')
const syn = translator(synopsisMessages, 'de')

describe('createStore', () => {
  it('benachrichtigt nur bei Änderungen und liefert neue Stände', () => {
    const store = createStore({ a: 1, b: 'x' })
    const listener = vi.fn()
    const stop = store.subscribe(listener)
    const first = store.get()
    store.set({ a: 1 })
    expect(listener).not.toHaveBeenCalled()
    store.set((state) => ({ a: state.a + 1 }))
    expect(listener).toHaveBeenCalledTimes(1)
    expect(store.get()).not.toBe(first)
    stop()
    store.set({ b: 'y' })
    expect(listener).toHaveBeenCalledTimes(1)
  })
})

describe('createSynopsisController', () => {
  it('filtert, navigiert und verwirft lokale Änderungen', async () => {
    const controller = createSynopsisController(() => syn)
    const inputs = { comparison: standard }
    let selection = selectSynopsis(controller.store.get(), inputs, syn)
    expect(selection.rows).toHaveLength(8)
    expect(controller.go(selection, 1)).toBe(standard.result.rows[0]?.row_id)
    selection = selectSynopsis(controller.store.get(), inputs, syn)
    expect(selection.position).toBe('Änderung 1 von 8')
    await controller.updateRow(inputs, standard.result.rows[0]!.row_id, { selected: false })
    expect(selectSynopsis(controller.store.get(), inputs, syn).selectedText).toContain('7 von')
    controller.resetOverrides()
    controller.setQuery('gibt es nicht')
    selection = selectSynopsis(controller.store.get(), inputs, syn)
    expect(selection.rows).toHaveLength(0)
    expect(selection.activeId).toBeNull()
  })
})

describe('createVvtController', () => {
  it('lädt, wählt die erste Tätigkeit, bearbeitet und speichert mit Revision', async () => {
    const port = fakePort()
    const onSaved = vi.fn()
    const controller = createVvtController({ port: () => port, t: () => dp, onSaved, checkDelay: 0 })
    await controller.load(true)
    expect(controller.store.get().selected).toBe(0)
    controller.changeField('zweck', 'Neu')
    expect(vvtView(controller.store.get()).dirty).toBe(true)
    await controller.save()
    expect(port.saveDraft).toHaveBeenCalledWith(expect.anything(), register.draft!.revision)
    expect(controller.store.get().notice).toContain('gespeichert')
    expect(onSaved).toHaveBeenCalledTimes(1)
    expect(controller.exportAs('csv', 'de').filename).toBe('Verarbeitungsverzeichnis_Fassung_2.csv')
    controller.dispose()
  })
})

describe('createDsfaController', () => {
  it('öffnet eine Abschätzung, erkennt Änderungen und meldet Fehler', async () => {
    const onError = vi.fn()
    const port = fakePort({ decide: vi.fn(async () => Promise.reject(new Error('offline'))) })
    const controller = createDsfaController({ port: () => port, t: () => dp, onError, previewDelay: 0 })
    await controller.connect('')
    expect(controller.store.get().rows.length).toBeGreaterThan(0)
    const withDsfa = controller.store.get().rows.find((row) => row.dsfa)
    await controller.openActivity(withDsfa!.id)
    const survey = controller.store.get().survey!
    controller.edit({ ...survey, necessity: 'geändert' })
    expect(dsfaDerived(controller.store.get()).dirty).toBe(true)
    await controller.decide({ decision: 'freigabe', justification: '', conditions: [] })
    expect(onError).toHaveBeenCalledWith(expect.objectContaining({ code: 'network_error', message: 'Verbindung fehlgeschlagen: offline' }))
    controller.dispose()
  })
})
