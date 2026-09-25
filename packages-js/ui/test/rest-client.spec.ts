import { describe, expect, it, vi } from 'vitest'
import { RestError, requestFile, requestJson } from '../src/rest'

describe('REST-Client', () => {
  it('sendet JSON an die Basis-URL und liefert die Antwort', async () => {
    const fetch = vi.fn(async () => new Response(JSON.stringify({ ok: 1 }), { status: 200 }))
    const result = await requestJson({ baseUrl: '/api/sampling/', fetch, headers: { 'X-CSRF': 't' } }, '/size', { method: 'x' })
    expect(result).toEqual({ ok: 1 })
    expect(fetch).toHaveBeenCalledWith('/api/sampling/size', expect.objectContaining({ method: 'POST', body: '{"method":"x"}' }))
    const init = (fetch.mock.calls[0] as unknown as [string, RequestInit])[1]
    expect(init.headers).toMatchObject({ 'X-CSRF': 't', 'Content-Type': 'application/json' })
  })

  it('wandelt Vertragsfehler in RestError um', async () => {
    const body = JSON.stringify({ error: { code: 'invalid_input', message: 'Pflichtfeld fehlt.' } })
    const fetch = vi.fn(async () => new Response(body, { status: 422 }))
    await expect(requestJson({ baseUrl: '', fetch }, '/size', {})).rejects.toEqual(new RestError('Pflichtfeld fehlt.', 422, 'invalid_input'))
    const broken = vi.fn(async () => new Response('<html>', { status: 502 }))
    await expect(requestJson({ baseUrl: '', fetch: broken }, '/x')).rejects.toMatchObject({ status: 502, code: 'http_error' })
  })

  it('liest den Dateinamen des Exports aus Content-Disposition', async () => {
    const fetch = vi.fn(async () => new Response('a;b', { status: 200, headers: { 'Content-Disposition': 'attachment; filename="stichprobe-srs-seed-7.csv"', 'Content-Type': 'text/csv' } }))
    const file = await requestFile({ baseUrl: '', fetch }, '/selection/export', {}, 'fallback.csv')
    expect(file.filename).toBe('stichprobe-srs-seed-7.csv')
    expect(file.mediaType).toBe('text/csv')
  })
})
