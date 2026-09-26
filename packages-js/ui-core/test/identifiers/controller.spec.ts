import { describe, expect, it, vi } from 'vitest'
import { createIdentifierController, type IdentifiersPort } from '../../src'
import { BATCH_CSV, fakeIdentifiersPort } from './fake-port'

function controllerWith(port: IdentifiersPort | null) {
  const callbacks = { checked: vi.fn(), batchChecked: vi.fn(), failed: vi.fn() }
  return { controller: createIdentifierController({ port: () => port, callbacks: () => callbacks }), callbacks }
}

describe('createIdentifierController', () => {
  it('lädt den Katalog und wählt das empfohlene Profil sichtbar vor', async () => {
    const { controller } = controllerWith(fakeIdentifiersPort())
    await controller.load()
    expect(controller.store.get()).toMatchObject({ profileId: 'strict', kind: 'iban', batchKind: 'iban' })
  })

  it('passt die Kennungsart beim Profilwechsel an und prüft über den Port', async () => {
    const port = fakeIdentifiersPort()
    const { controller, callbacks } = controllerWith(port)
    await controller.load()
    controller.setProfile('flowworkshop.legacy')
    expect(controller.store.get().kind).toBe('lei')
    controller.setProfile('strict')
    controller.setKind('vat_id')
    controller.setField('value', '136695976')
    controller.setField('country', 'de')
    await controller.check()
    expect(port.calls.check).toEqual([{ kind: 'vat_id', value: '136695976', profile: 'strict', country: 'DE' }])
    expect(controller.store.get().result?.status).toBe('VALID')
    expect(callbacks.checked).toHaveBeenCalledOnce()
  })

  it('prüft eine geladene Tabelle als Stapel und meldet fehlende Zuordnung', async () => {
    const port = fakeIdentifiersPort()
    const { controller, callbacks } = controllerWith(port)
    await controller.load()
    await controller.checkBatch()
    expect(controller.store.get().batchValidation).toBe('noTable')
    await controller.readFile(new File([BATCH_CSV], 'kennungen.csv'))
    controller.table.setValueColumn(2)
    controller.table.setIdColumn(0)
    controller.setBatchKind(null)
    await controller.checkBatch()
    expect(controller.store.get().batchValidation).toBe('kindColumn')
    controller.setField('kindColumn', 1)
    await controller.checkBatch()
    expect(port.calls.batch).toHaveLength(1)
    expect(controller.store.get().batch?.summary.total).toBe(5)
    expect(callbacks.batchChecked).toHaveBeenCalledOnce()
  })

  it('meldet Fehler des Ports und tut ohne Port nichts', async () => {
    const { controller, callbacks } = controllerWith(fakeIdentifiersPort('catalogue'))
    await controller.load()
    expect(controller.store.get().error).toBe('Dienst nicht erreichbar')
    expect(callbacks.failed).toHaveBeenCalledWith('Dienst nicht erreichbar')
    const idle = controllerWith(null).controller
    await idle.load()
    await idle.check()
    expect(idle.store.get().catalogue).toBeNull()
  })
})
