import { describe, expect, it, vi } from 'vitest'
import { createDataProtectionRestPort } from '../../src/dataprotection/rest-port'
import { RestError } from '@auditcore/common'

function fakeFetch(status: number, body: unknown, headers: Record<string, string> = { 'Content-Type': 'application/json' }) {
  return vi.fn(async (_url: string, _init?: RequestInit) => new Response(typeof body === 'string' ? body : JSON.stringify(body), { status, headers }))
}

describe('REST-Port VVT/DSFA', () => {
  it('liest Profil und Verzeichnis per GET und speichert den Entwurf mit Revision', async () => {
    const fetch = fakeFetch(200, {})
    const port = createDataProtectionRestPort({ baseUrl: '/api/dataprotection/', headers: { 'X-CSRF': 't' }, fetch })
    await port.profile()
    await port.register()
    expect(fetch.mock.calls.map((call) => [call[0], call[1]?.method])).toEqual([
      ['/api/dataprotection/profile', 'GET'],
      ['/api/dataprotection/register', 'GET'],
    ])
    await port.saveDraft({ deckblatt: {}, referate: [], taetigkeiten: [] }, 3)
    const [url, init] = fetch.mock.calls[2]!
    expect(url).toBe('/api/dataprotection/register/draft')
    expect(init?.headers).toMatchObject({ 'Content-Type': 'application/json', 'X-CSRF': 't' })
    expect(JSON.parse(String(init?.body))).toEqual({ content: { deckblatt: {}, referate: [], taetigkeiten: [] }, expected_revision: 3 })
  })

  it('bildet die Aktionen einer Folgenabschätzung auf die Pfade des Vertrags ab', async () => {
    const fetch = fakeFetch(200, {})
    const port = createDataProtectionRestPort({ baseUrl: '/api', fetch })
    await port.decide('a 1', 4, { decision: 'freigabe', justification: '', conditions: [] })
    await port.requestDpo('a 1', 5, 'DSB', '2026-09-24')
    await port.releaseAssessment('a 1', 6)
    await port.calculate({}, [])
    await port.startAssessment('t1')
    await port.reassess('a 1')
    expect(fetch.mock.calls.map((call) => call[0])).toEqual([
      '/api/assessments/a%201/decide',
      '/api/assessments/a%201/dpo-request',
      '/api/assessments/a%201/release',
      '/api/calculate',
      '/api/assessments',
      '/api/assessments/a%201/reassess',
    ])
    expect(JSON.parse(String(fetch.mock.calls[1]![1]?.body))).toEqual({ expected_revision: 5, requested_from: 'DSB', requested_on: '2026-09-24' })
  })

  it('lädt Exporte als Datei mit dem Namen aus Content-Disposition', async () => {
    const fetch = fakeFetch(200, 'a;b', { 'Content-Type': 'text/csv', 'Content-Disposition': 'attachment; filename="verzeichnis.csv"' })
    const file = await createDataProtectionRestPort({ baseUrl: '/api', fetch }).exportRegister('csv', 'released')
    expect(file.filename).toBe('verzeichnis.csv')
    expect(JSON.parse(String(fetch.mock.calls[0]![1]?.body))).toEqual({ format: 'csv', source: 'released' })
  })

  it('meldet Vertragsfehler mit Code, Status und deutscher Meldung', async () => {
    const fetch = fakeFetch(403, { error: { code: 'vier_augen_verletzt', message: 'Vier-Augen-Prinzip verletzt.' } })
    const error = await createDataProtectionRestPort({ baseUrl: '/api', fetch }).releaseRegister(1).catch((caught: unknown) => caught)
    expect(error).toBeInstanceOf(RestError)
    expect(error).toMatchObject({ status: 403, code: 'vier_augen_verletzt', message: 'Vier-Augen-Prinzip verletzt.' })
  })
})
