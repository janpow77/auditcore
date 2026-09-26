import { describe, expect, it, vi } from 'vitest'
import { RestError, bodyMessage, contentDispositionFilename, detailMessage, errorMessage, httpStatus, requestFile, requestJson } from '../src'

describe('errorMessage', () => {
  it('liest Axios-, fetch- und FastAPI-Formen', () => {
    const list = { detail: [{ loc: ['body', 'betrag'], msg: 'Pflichtfeld' }, { loc: ['query'], msg: 'zu groß' }, 'frei', {}] }
    expect(errorMessage({ response: { data: list } }, 'x')).toBe('betrag: Pflichtfeld; zu groß; frei')
    expect(errorMessage(list, 'x')).toBe('betrag: Pflichtfeld; zu groß; frei')
    expect(errorMessage({ data: { detail: 'Kein Zugriff' } }, 'x')).toBe('Kein Zugriff')
    expect(errorMessage({ response: { data: '<html>' }, message: 'Request failed' }, 'x')).toBe('<html>')
    expect(errorMessage({ response: { data: {} }, message: 'Request failed' }, 'x')).toBe('Request failed')
    expect(errorMessage(new RestError('Betrag fehlt', 400, 'invalid'), 'x')).toBe('Betrag fehlt')
    expect(errorMessage('  ', 'Ersatz')).toBe('Ersatz')
    expect(errorMessage(42, 'Ersatz')).toBe('Ersatz')
    expect(errorMessage({ error: 'kaputt' }, 'x')).toBe('kaputt')
  })

  it('liest Detailformen und Status', () => {
    expect(detailMessage({ message: 'M' })).toBe('M')
    expect(detailMessage([])).toBeNull()
    expect(bodyMessage({ message: 'nur message' })).toBe('nur message')
    expect(httpStatus({ response: { status: 422 } })).toBe(422)
    expect(httpStatus(new RestError('x', 404, 'c'))).toBe(404)
    expect(httpStatus('x')).toBeNull()
  })
})

describe('REST-Client', () => {
  it('meldet FastAPI-detail ohne auditcore-Hülle', async () => {
    const body = JSON.stringify({ detail: [{ loc: ['body', 'datum'], msg: 'Field required' }] })
    const fetch = vi.fn(async () => new Response(body, { status: 422 }))
    await expect(requestJson({ baseUrl: '', fetch }, '/x', {})).rejects.toEqual(new RestError('datum: Field required', 422, 'http_error'))
  })

  it('liest Dateinamen mit Umlauten', async () => {
    const header = `attachment; filename="pruefbericht.pdf"; filename*=UTF-8''Pr%C3%BCfbericht.pdf`
    const fetch = vi.fn(async () => new Response('x', { status: 200, headers: { 'Content-Disposition': header } }))
    const file = await requestFile({ baseUrl: '/api/', fetch }, '/export', {}, 'fallback.pdf')
    expect(file.filename).toBe('Prüfbericht.pdf')
    expect(file.mediaType).toBe('text/plain;charset=UTF-8')
    expect(contentDispositionFilename('attachment; filename=bericht.csv')).toBe('bericht.csv')
    expect(contentDispositionFilename("attachment; filename*=UTF-8''%E0%A4%A")).toBeNull()
    expect(contentDispositionFilename(null)).toBeNull()
  })

  it('nutzt ohne injiziertes fetch das globale', async () => {
    const spy = vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response('{"a":1}', { status: 200 }))
    await expect(requestJson({ baseUrl: '/api' }, '/a')).resolves.toEqual({ a: 1 })
    expect(spy).toHaveBeenCalledWith('/api/a', expect.objectContaining({ method: 'GET' }))
    spy.mockRestore()
  })
})
