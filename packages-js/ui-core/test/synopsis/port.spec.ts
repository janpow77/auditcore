import { describe, expect, it } from 'vitest'
import { RestError, type FetchLike } from '@flowaudit/common'
import { createSynopsisRestClient } from '../../src/synopsis/port'
import { standard } from './fixtures'

interface Call {
  url: string
  init: RequestInit | undefined
}

function fakeRequest(responses: Response[]): { request: FetchLike; calls: Call[] } {
  const calls: Call[] = []
  const request: FetchLike = async (url, init) => {
    calls.push({ url, init })
    const next = responses.shift()
    if (!next) throw new Error('keine Antwort vorbereitet')
    return next
  }
  return { request, calls }
}

const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })

describe('REST-Client', () => {
  it('nutzt die Pfade des Vertrags und sendet Zeilenänderungen als JSON', async () => {
    const { request, calls } = fakeRequest([json(standard), json(standard), json({ items: [] }), json({ items: [{ id: 'p' }] }), new Response(null, { status: 204 })])
    const client = createSynopsisRestClient({ baseUrl: '/api/synopsis/', fetch: request, headers: { 'X-CSRF': 't' } })
    expect((await client.load('a b')).id).toBe(standard.id)
    await client.updateRows('a b', [{ row_id: 'r1', selected: false }])
    expect(await client.list()).toEqual([])
    expect((await client.profiles())[0]?.id).toBe('p')
    await client.remove('x')
    expect(calls.map((call) => [call.init?.method ?? 'GET', call.url])).toEqual([
      ['GET', '/api/synopsis/comparisons/a%20b'],
      ['PATCH', '/api/synopsis/comparisons/a%20b/rows'],
      ['GET', '/api/synopsis/comparisons'],
      ['GET', '/api/synopsis/profiles'],
      ['DELETE', '/api/synopsis/comparisons/x'],
    ])
    expect(calls[1]?.init?.headers).toEqual({ Accept: 'application/json', 'X-CSRF': 't', 'Content-Type': 'application/json' })
    expect(JSON.parse(String(calls[1]?.init?.body))).toEqual({ rows: [{ row_id: 'r1', selected: false }] })
    expect(client.exportUrl('x', 'docx')).toBe('/api/synopsis/comparisons/x/export?format=docx')
  })

  it('lädt zwei Dateien mit Formularfeldern hoch', async () => {
    const { request, calls } = fakeRequest([json(standard, 201)])
    const client = createSynopsisRestClient({ baseUrl: '/api', fetch: request })
    await client.create(new Blob(['a']), 'alt.docx', new Blob(['b']), 'neu.docx', {
      comparison_type: 'article_law',
      threshold: 90,
      include_editorial: false,
      output_sections: ['changed', 'added'],
    })
    const form = calls[0]?.init?.body as FormData
    expect(calls[0]?.init?.method).toBe('POST')
    expect((form.get('old_file') as File).name).toBe('alt.docx')
    expect(form.get('threshold')).toBe('90')
    expect(form.get('include_editorial')).toBe('false')
    expect(form.get('output_sections')).toBe('changed,added')
    expect(form.has('mode')).toBe(false)
  })

  it('meldet Fehler mit der deutschen Meldung des Servers', async () => {
    const { request } = fakeRequest([json({ detail: 'Vergleich nicht gefunden.' }, 404), new Response('kaputt', { status: 500 })])
    const client = createSynopsisRestClient({ baseUrl: '', fetch: request })
    await expect(client.load('x')).rejects.toEqual(new RestError('Vergleich nicht gefunden.', 404, 'http_error'))
    await expect(client.list()).rejects.toMatchObject({ status: 500, message: 'HTTP 500' })
  })

  it('importiert ein fertiges Ergebnis als JSON (POST /comparisons/import)', async () => {
    const { request, calls } = fakeRequest([json(standard, 201)])
    const client = createSynopsisRestClient({ baseUrl: '/api/synopsis', fetch: request })
    expect((await client.importResult({ title: 'Import', result: standard.result })).id).toBe(standard.id)
    expect(calls[0]?.url).toBe('/api/synopsis/comparisons/import')
    expect(calls[0]?.init?.method).toBe('POST')
    expect(JSON.parse(String(calls[0]?.init?.body))).toEqual({ title: 'Import', result: standard.result })
  })
})
