import { describe, expect, it, vi } from 'vitest'
import { RestError } from '@auditcore/common'
import { createScreeningRestPort } from '../../src'

function fakeFetch(status: number, body: unknown) {
  return vi.fn(async (_url: string, _init?: RequestInit) =>
    new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } }),
  )
}

describe('REST-Port Screening-Trefferprüfung', () => {
  it('sendet Entscheidungen als JSON mit den Kopfzeilen der Anwendung', async () => {
    const fetch = fakeFetch(200, { hit_id: 'h1' })
    const port = createScreeningRestPort({ baseUrl: '/api/screening/', headers: { 'X-CSRF': 't' }, fetch })
    await port.decide('run 1', 'h1', { outcome: 'dismissed', reason: 'Kein Bezug.', four_eyes: false })
    const [url, init] = fetch.mock.calls[0]!
    expect(url).toBe('/api/screening/runs/run%201/hits/h1/decision')
    expect(init?.method).toBe('POST')
    expect(init?.headers).toMatchObject({ 'Content-Type': 'application/json', 'X-CSRF': 't' })
    expect(JSON.parse(String(init?.body))).toMatchObject({ outcome: 'dismissed' })
  })

  it('baut Filterabfragen ohne leere Werte und ruft die Zweitprüfung auf', async () => {
    const fetch = fakeFetch(200, {})
    const port = createScreeningRestPort({ baseUrl: '/api', fetch })
    await port.run('r', { status: 'open', list: '', min_score: '80' })
    expect(fetch.mock.calls[0]![0]).toBe('/api/runs/r?status=open&min_score=80')
    await port.secondReview('r', 'h', { approve: true, reason: 'Ja.' })
    expect(fetch.mock.calls[1]![0]).toBe('/api/runs/r/hits/h/second-review')
    await port.log('r')
    expect(fetch.mock.calls[2]![0]).toBe('/api/runs/r/log')
    expect(fetch.mock.calls[2]![1]?.method).toBe('GET')
  })

  it('meldet Vertragsfehler mit Code, Status und deutscher Meldung', async () => {
    const fetch = fakeFetch(409, { error: { code: 'same_person', message: 'Andere Person nötig.', details: {} } })
    const error = await createScreeningRestPort({ baseUrl: '/api', fetch }).settings().catch((caught: unknown) => caught)
    expect(error).toBeInstanceOf(RestError)
    expect(error).toMatchObject({ status: 409, code: 'same_person', message: 'Andere Person nötig.' })
  })

  it('meldet Fehler außerhalb des Vertrags allgemein', async () => {
    const fetch = vi.fn(async () => new Response('kaputt', { status: 502 }))
    await expect(createScreeningRestPort({ baseUrl: '/api', fetch }).sources()).rejects.toMatchObject({ status: 502, code: 'http_error' })
  })
})
