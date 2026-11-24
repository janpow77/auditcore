import { describe, expect, it, vi } from 'vitest'
import { createRedactionController } from '../../src'
import { fakeRedactionPort, fakeUrls, redactionPlan, syntheticPdf } from './fake-port'

async function setup(port = fakeRedactionPort(), urls = fakeUrls()) {
  const planned = vi.fn()
  const completed = vi.fn()
  const controller = createRedactionController({ port: () => port, urls, callbacks: () => ({ planned, completed }) })
  await controller.load()
  controller.selectFile(syntheticPdf())
  controller.setPattern('email', true)
  controller.setTerms('Prüfvermerk\n\n Prüfvermerk \n')
  await controller.plan()
  return { controller, port, urls, planned, completed }
}

describe('Schwärzen: Nebenläufigkeit', () => {
  it('hält die Auswahl während des Schwärzens fest und verwirft Antworten nach dem Entfernen', async () => {
    let finish: (blob: Blob) => void = () => undefined
    const quick = fakeRedactionPort()
    const slow = { ...quick, apply: (...args: Parameters<typeof quick.apply>) => new Promise<Awaited<ReturnType<typeof quick.apply>>>((done) => { finish = (blob) => void quick.apply(...args).then((result) => done({ ...result, blob })) }) }
    const { controller, completed } = await setup(slow)
    controller.addDefaultArea()
    const before = controller.store.get()
    const running = controller.apply()
    expect(controller.store.get().busy).toBe('apply')
    controller.toggle(redactionPlan.candidates[0]!.id)
    controller.setOption('sanitize', false)
    controller.removeArea(before.areas[0]!.id)
    controller.nudgeArea(before.areas[0]!.id, 'ArrowDown', 'move', false)
    controller.pointerDown([0.1, 0.1])
    expect(controller.addDefaultArea()).toBe(false)
    const locked = controller.store.get()
    expect([locked.selected, locked.sanitize, locked.areas, locked.gesture]).toEqual([before.selected, before.sanitize, before.areas, null])
    controller.dispose()
    finish(new Blob(['%PDF']))
    await running
    expect(completed).not.toHaveBeenCalled()
    expect(controller.store.get().result).toBeNull()
  })

  it('teilt gleichzeitige Anfragen desselben Seitenbilds', async () => {
    let release: () => void = () => undefined
    const quick = fakeRedactionPort()
    const gate = new Promise<void>((done) => (release = done))
    const gated = { ...quick, preview: async (file: Blob, name: string, page: number) => { if (page === 2) await gate; return quick.preview(file, name, page) } }
    const { controller, urls } = await setup(gated)
    const first = controller.showPage(2)
    const second = controller.showPage(2)
    release()
    await Promise.all([first, second])
    expect(quick.calls.filter((call) => call[0] === 'preview' && call[2] === 2)).toHaveLength(1)
    expect(controller.store.get()).toMatchObject({ page: 2, preview: 'blob:fa-test/image/png/7', previewError: null })
    controller.dispose()
    expect(urls.live.size).toBe(0)
  })
})
