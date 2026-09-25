import { describe, expect, it, vi } from 'vitest'
import { createBenfordRestPort } from '../../src/benford/rest-port'
import { createSamplingRestPort } from '../../src/sampling/rest-port'

describe('REST-Ports Stichprobe und Benford', () => {
  it('sendet Seed und Format beim Export der Auswahl', async () => {
    const fetch = vi.fn(async () => new Response('a;b', { status: 200, headers: { 'Content-Type': 'text/csv' } }))
    const port = createSamplingRestPort({ baseUrl: '/api/sampling', fetch })
    const file = await port.exportSelection({ method: 'srs', items: [], sample_size: 1, seed: 7 }, 'csv')
    const [url, init] = fetch.mock.calls[0] as unknown as [string, RequestInit]
    expect(url).toBe('/api/sampling/selection/export')
    expect(JSON.parse(String(init.body))).toMatchObject({ seed: 7, format: 'csv' })
    expect(file.filename).toBe('stichprobe-seed-7.csv')
  })

  it('ruft die Benford-Analyse unter /analyze auf', async () => {
    const fetch = vi.fn(async () => new Response('{"ok":true}', { status: 200, headers: { 'Content-Type': 'application/json' } }))
    const port = createBenfordRestPort({ baseUrl: '/api/benford', fetch })
    await port.profiles()
    expect((fetch.mock.calls[0] as unknown as [string])[0]).toBe('/api/benford/profiles')
  })
})
