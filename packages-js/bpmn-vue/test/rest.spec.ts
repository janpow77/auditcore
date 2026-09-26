import { describe, expect, it, vi } from 'vitest'
import { emptyCollection } from '@flowaudit/bpmn-flowaudit'
import { restPorts } from '@flowaudit/bpmn-flowaudit/ui'

type Call = { url: string; init: RequestInit }

function server(routes: Record<string, (init: RequestInit) => Response>) {
  const calls: Call[] = []
  const fetchMock = vi.fn(async (url: string, init: RequestInit) => {
    calls.push({ url, init })
    const key = `${init.method} ${url.replace('https://intranet.example/api/bpmn', '').split('?')[0]}`
    const route = routes[key]
    return route ? route(init) : new Response(JSON.stringify({ detail: `Keine Route ${key}` }), { status: 404 })
  })
  const ports = restPorts({ baseUrl: 'https://intranet.example/api/bpmn/', fetch: fetchMock as unknown as typeof fetch, headers: () => ({ Authorization: 'Bearer t' }) })
  return { ports, calls }
}

const json = (body: unknown, headers: Record<string, string> = {}) => new Response(JSON.stringify(body), { status: 200, headers: { 'Content-Type': 'application/json', ...headers } })

describe('REST ports', () => {
  it('reads and writes the collection in the snake_case model of auditcore_bpmn with ETag/If-Match', async () => {
    const wire = { schema: 'auditcore_bpmn.diagram-collection/1', id: 's', name: 'S', folders: [{ id: 'f', name: 'F', parent_id: 'p', position: 0 }], tags: [], diagrams: [] }
    const { ports, calls } = server({ 'GET /collection': () => json(wire, { ETag: '"v1"' }), 'PUT /collection': () => new Response(null, { status: 204, headers: { ETag: '"v2"' } }) })
    const data = await ports.storage.loadCollection()
    expect(data?.folders[0]).toEqual({ id: 'f', name: 'F', parentId: 'p', position: 0 })
    await ports.storage.saveCollection(data!)
    const put = calls[1]!
    expect((put.init.headers as Record<string, string>)['If-Match']).toBe('"v1"')
    expect((put.init.headers as Record<string, string>).Authorization).toBe('Bearer t')
    expect(JSON.parse(String(put.init.body)).folders[0]).toEqual({ id: 'f', name: 'F', parent_id: 'p', position: 0 })
  })

  it('treats 204 as no collection and reports conflicts', async () => {
    const { ports } = server({ 'GET /collection': () => new Response(null, { status: 204 }), 'PUT /collection': () => new Response(null, { status: 412 }) })
    expect(await ports.storage.loadCollection()).toBeNull()
    await expect(ports.storage.saveCollection(emptyCollection())).rejects.toThrow('zwischenzeitlich geändert')
  })

  it('transfers diagrams and approvals as XML', async () => {
    const { ports, calls } = server({
      'GET /diagrams/a%20b/xml': () => new Response('<x/>', { status: 200 }),
      'PUT /diagrams/a%20b/xml': () => new Response(null, { status: 204 }),
      'PUT /diagrams/a%20b/approvals/1.0': () => new Response(null, { status: 204 }),
      'DELETE /diagrams/a%20b': () => new Response(null, { status: 204 }),
    })
    expect(await ports.storage.loadDiagram('a b')).toBe('<x/>')
    await ports.storage.saveDiagram('a b', '<y/>')
    await ports.storage.saveApproval('a b', '1.0', '<y/>')
    await ports.storage.deleteDiagram('a b')
    expect((calls[1]!.init.headers as Record<string, string>)['Content-Type']).toContain('application/xml')
    expect(calls.map((call) => call.init.method)).toEqual(['GET', 'PUT', 'PUT', 'DELETE'])
  })

  it('maps comments, legal search hits, profiles and key requirements', async () => {
    const { ports, calls } = server({
      'GET /diagrams/d/comments': () => json([{ id: 'c1', element_id: 'T1', text: 'Hinweis', author: 'A', timestamp: '2026-09-25', resolved: false }]),
      'GET /legal-bases': () => json([{ act: 'Verordnung (EU) 2021/1060', article: '74', short_title: 'Verwaltungsprüfungen' }]),
      'GET /profiles': () => json([{ id: 'p', version: '1', title: 'Profil', programming_period: '2021-2027' }]),
      'GET /profiles/p/key-requirements': () => json([{ number: 1, title: 'KA 1', criteria: [] }]),
    })
    expect((await ports.storage.loadComments('d'))[0]!.elementId).toBe('T1')
    expect((await ports.legalSearch.search('Art. 74', { limit: 5, locale: 'de' }))[0]!.shortTitle).toBe('Verwaltungsprüfungen')
    expect(calls[1]!.url).toContain('q=Art.+74')
    expect((await ports.profiles.profiles())[0]!.programmingPeriod).toBe('2021-2027')
    expect((await ports.catalogue.keyRequirements('p', 'en'))[0]!.number).toBe(1)
  })

  it('validates on the server and returns ValidationIssues', async () => {
    const { ports, calls } = server({
      'POST /validation': () => json({ schema: 'auditcore_bpmn.validation-report/1', valid: false, issues: [{ rule_id: 'BPMN-S010', severity: 'fehler', message: 'Kein Start', params: { name: 'P' }, element_id: 'P' }] }),
    })
    const issues = await ports.validation.validate('<x/>', { profile: 'p', referenceDate: '2026-09-25' })
    expect(issues).toEqual([{ ruleId: 'BPMN-S010', severity: 'fehler', params: { name: 'P' }, elementId: 'P', message: 'Kein Start' }])
    expect(JSON.parse(String(calls[0]!.init.body))).toEqual({ xml: '<x/>', profile: 'p', reference_date: '2026-09-25' })
  })

  it('turns FastAPI error details into messages', async () => {
    const { ports } = server({ 'GET /diagrams/x/xml': () => new Response(JSON.stringify({ detail: [{ msg: 'unbekannt' }] }), { status: 422 }) })
    await expect(ports.storage.loadDiagram('x')).rejects.toThrow('unbekannt')
  })
})
