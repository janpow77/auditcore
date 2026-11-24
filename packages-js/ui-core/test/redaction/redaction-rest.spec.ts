import { describe, expect, it, vi } from 'vitest'
import {
  createRedactionRestPort,
  redactionSelectionPayload,
} from '../../src'
import { redactionCatalogue, redactionPlan } from './fake-port'

describe('Schwärzen: REST-Port', () => {
  function fetchStub(responses: Response[]) {
    const calls: Array<{ url: string; init: RequestInit }> = []
    const fetch = vi.fn(async (url: RequestInfo | URL, init?: RequestInit) => {
      calls.push({ url: String(url), init: init ?? {} })
      return responses.shift()!
    })
    return { fetch, calls }
  }

  it('sendet Datei und Felder als Formular und liest den Bericht aus den Köpfen', async () => {
    const pdf = new Blob(['%PDF'], { type: 'application/pdf' })
    const { fetch, calls } = fetchStub([
      Response.json(redactionCatalogue),
      Response.json(redactionPlan),
      new Response(new Blob(['png'], { type: 'image/png' })),
      new Response(pdf, {
        headers: {
          'Content-Disposition': "attachment; filename=\"vermerk_geschw_rzt.pdf\"; filename*=UTF-8''vermerk_geschw%C3%A4rzt.pdf",
          'X-Redactions': '4', 'X-Redaction-Areas': '1', 'X-Redaction-Hidden': '2', 'X-Redaction-Deselected': 'x', 'X-Redaction-Pages': '2',
          'X-Redaction-Sanitized': 'true', 'X-Redaction-Verified': 'true',
        },
      }),
      new Response(pdf),
    ])
    const port = createRedactionRestPort({ baseUrl: '/api/redaction/', fetch, headers: { 'X-Mandant': 'demo' } })
    expect(await port.catalogue()).toEqual(redactionCatalogue)
    expect(await port.plan(pdf, 'vermerk.pdf', redactionPlan.criteria)).toEqual(redactionPlan)
    expect(await (await port.preview(pdf, 'vermerk.pdf', 2)).text()).toBe('png')
    const selection = redactionSelectionPayload(redactionPlan, new Set(), [], true)
    const result = await port.apply(pdf, 'vermerk.pdf', selection)
    expect(result.filename).toBe('vermerk_geschwärzt.pdf')
    expect(result.report).toEqual({ redactions: 4, areas: 1, hidden: 2, deselected: 0, pages: 2, sanitized: true, verified: true })
    expect((await port.apply(pdf, 'vermerk.pdf', selection)).filename).toBe('geschwärzt.pdf')
    expect(calls.map((call) => [call.url, call.init.method])).toEqual([
      ['/api/redaction/catalogue', 'GET'], ['/api/redaction/plan', 'POST'], ['/api/redaction/preview', 'POST'], ['/api/redaction/apply', 'POST'], ['/api/redaction/apply', 'POST'],
    ])
    const form = calls[2]!.init.body as FormData
    expect(form.get('page')).toBe('2')
    expect(form.get('file')).toBeInstanceOf(Blob)
    expect(JSON.parse((calls[1]!.init.body as FormData).get('criteria') as string)).toEqual(redactionPlan.criteria)
    expect(calls[3]!.init.headers).toMatchObject({ Accept: 'application/pdf', 'X-Mandant': 'demo' })
  })

  it('wirft RestError mit Code und Meldung des Dienstes', async () => {
    const { fetch } = fetchStub([
      Response.json({ error: { code: 'stale_plan', message: 'Die Datei hat sich geändert.' } }, { status: 409 }),
      new Response('kaputt', { status: 502 }),
      new Response('kaputt', { status: 500 }),
    ])
    const port = createRedactionRestPort({ baseUrl: '/api', fetch })
    const pdf = new Blob(['%PDF'])
    await expect(port.apply(pdf, 'a.pdf', redactionSelectionPayload(redactionPlan, new Set(), [], true))).rejects.toMatchObject({ status: 409, code: 'stale_plan', message: 'Die Datei hat sich geändert.' })
    await expect(port.plan(pdf, 'a.pdf', redactionPlan.criteria)).rejects.toMatchObject({ status: 502, code: 'http_error' })
    await expect(port.catalogue()).rejects.toMatchObject({ status: 500 })
  })
})
