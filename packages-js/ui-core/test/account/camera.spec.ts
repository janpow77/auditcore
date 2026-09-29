import { describe, expect, it, vi } from 'vitest'
import { createAccountCamera, cropAccountImage } from '../../src'

describe('Kamera-Lebenszyklus', () => {
  it('schließt Tracks auch bei spät erteilter Berechtigung nach Abbruch', async () => {
    const stop = vi.fn()
    let resolve: ((stream: MediaStream) => void) | undefined
    const stream = { getTracks: () => [{ stop }] } as unknown as MediaStream
    vi.stubGlobal('navigator', { mediaDevices: { getUserMedia: () => new Promise<MediaStream>((done) => { resolve = done }) } })
    const camera = createAccountCamera()
    const pending = camera.start(document.createElement('video'))
    camera.stop()
    resolve?.(stream)
    await pending
    expect(stop).toHaveBeenCalledOnce()
    vi.unstubAllGlobals()
  })
  it('lehnt ungültige Zuschnittparameter vor dem Dekodieren ab', async () => {
    await expect(cropAccountImage(new Blob(), Number.NaN, 0, 0)).rejects.toThrow('Ungültiger')
  })
})
