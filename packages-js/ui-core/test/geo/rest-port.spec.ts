import { describe, expect, it, vi } from 'vitest'
import { createGeoRestPort } from '../../src/geo/rest-port'
import type { FetchLike } from '@flowaudit/common'

function recorder(): { fetch: FetchLike; calls: [string, RequestInit | undefined][] } {
  const calls: [string, RequestInit | undefined][] = []
  const fetch: FetchLike = vi.fn(async (input: string, init?: RequestInit) => {
    calls.push([input, init])
    return new Response('{}', { status: 200, headers: { 'Content-Type': 'application/json' } })
  })
  return { fetch, calls }
}

describe('REST-Port Geo', () => {
  it('ruft die Endpunkte des Vertrags auf und lädt GeoPackage-Dateien roh hoch', async () => {
    const { fetch, calls } = recorder()
    const port = createGeoRestPort({ baseUrl: '/api/geo/', fetch })
    await port.catalogue()
    await port.radius({ zentrum: { lat: 1, lon: 2 }, punkte: [], radius_m: 5, erdmodell: 'x' })
    await port.locate({ punkt: { lat: 1, lon: 2 }, flaeche: { type: 'Polygon', coordinates: [] }, erdmodell: 'x', rand_gilt_als_innen: true })
    await port.utm({ punkt: { lat: 1, lon: 2 }, ellipsoid: 'GRS80' })
    await port.simplify({ flaeche: { type: 'Polygon', coordinates: [] }, toleranz: 1, einheit: 'meter' })
    await port.loadGeoPackage?.(new Blob(['x']), 'gebiete')
    await port.loadSource?.('Schutz gebiete')
    expect(calls.map(([url]) => url)).toEqual([
      '/api/geo/profile', '/api/geo/umkreis', '/api/geo/lage', '/api/geo/utm', '/api/geo/vereinfachung',
      '/api/geo/gpkg?tabelle=gebiete', '/api/geo/gpkg/quellen/Schutz%20gebiete',
    ])
    const upload = calls[5]?.[1]
    expect(upload?.method).toBe('POST')
    expect((upload?.headers as Record<string, string>)['Content-Type']).toBe('application/geopackage+sqlite3')
    expect(upload?.body).toBeInstanceOf(Blob)
  })

  it('bietet die Adresssuche nur auf ausdrücklichen Wunsch an', async () => {
    const { fetch, calls } = recorder()
    expect(createGeoRestPort({ baseUrl: '/geo', fetch }).geocode).toBeUndefined()
    const port = createGeoRestPort({ baseUrl: '/geo', fetch, geocoding: true })
    await port.geocode?.('Musterstraße 1')
    expect(calls[0]?.[0]).toBe('/geo/geocode')
    expect(JSON.parse(String(calls[0]?.[1]?.body))).toEqual({ anfrage: 'Musterstraße 1' })
  })

  it('meldet Fehler des Servers mit Code', async () => {
    const fetch: FetchLike = vi.fn(async () => new Response(JSON.stringify({ error: { code: 'zu_gross', message: 'GeoPackage zu groß.' } }), { status: 413 }))
    const port = createGeoRestPort({ baseUrl: '/geo', fetch })
    await expect(port.loadGeoPackage?.(new Blob(['x']))).rejects.toMatchObject({ status: 413, code: 'zu_gross', message: 'GeoPackage zu groß.' })
  })
})
