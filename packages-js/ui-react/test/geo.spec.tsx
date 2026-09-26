import { act, cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { MapLayers, MapViewOptions, SimplifyResult } from '@flowaudit/ui-core'
import { fakeGeoPort, GEO_AREA, GEO_POINTS, GEO_RESULTS } from '../../ui-core/test/parity/cases-geo'
import { FlowauditGeoMap, type FlowauditGeoMapProps } from '../src'

const view = vi.hoisted(() => ({ options: null as MapViewOptions | null, layers: [] as MapLayers[], fit: 0, tiles: [] as unknown[] }))
vi.mock('@flowaudit/ui-core', async (original) => ({
  ...(await original<typeof import('@flowaudit/ui-core')>()),
  createLeafletView: vi.fn(async (_element: HTMLElement, options: MapViewOptions) => {
    view.options = options
    return { update: (layers: MapLayers) => view.layers.push(layers), setTiles: (tiles: unknown) => view.tiles.push(tiles), fit: () => (view.fit += 1), destroy: vi.fn() }
  }),
}))

const flush = () => act(() => new Promise<void>((resolve) => setTimeout(resolve, 0)))
const byTestId = (id: string) => screen.getByTestId(id)
const submit = (id: string) => fireEvent.submit(byTestId(id).closest('form') as HTMLFormElement)

async function renderMap(props: Partial<FlowauditGeoMapProps> = {}) {
  const port = fakeGeoPort()
  const result = render(<FlowauditGeoMap port={port} points={GEO_POINTS} areas={[GEO_AREA]} {...props} />)
  await flush()
  await flush()
  return { port, ...result }
}

beforeEach(() => {
  view.options = null
  view.layers = []
  view.fit = 0
  view.tiles = []
})
afterEach(cleanup)

describe('FlowauditGeoMap (nativ)', () => {
  it('zeichnet Punkte und Flächen ohne Fremdserver und wechselt die Kachelquelle', async () => {
    const { rerender, port } = await renderMap()
    expect(view.options?.tiles).toBeNull()
    expect(byTestId('geo-no-tiles').textContent).toContain('Keine Kachelquelle')
    expect(view.layers.at(-1)?.points).toHaveLength(3)
    expect(view.fit).toBeGreaterThanOrEqual(1)
    expect(byTestId('geo-map').getAttribute('aria-label')).toContain('3 Punkten und 1 Flächen')
    const tiles = { url: '/kacheln/{z}/{x}/{y}.png', attribution: 'Synthetische Kacheln' }
    rerender(<FlowauditGeoMap port={port} points={GEO_POINTS} areas={[GEO_AREA]} tiles={tiles} />)
    await flush()
    expect(view.tiles.at(-1)).toEqual(tiles)
    expect(byTestId('geo-attribution').textContent).toBe('Kartendaten: Synthetische Kacheln')
  })

  it('übernimmt einen Kartenklick als Bezugspunkt, zeigt UTM und sucht im Umkreis', async () => {
    const onReferenceChange = vi.fn()
    const onRadiusCompleted = vi.fn()
    const { port } = await renderMap({ onReferenceChange, onRadiusCompleted })
    submit('geo-radius-run')
    await flush()
    expect(byTestId('geo-hint').textContent).toBe('Zuerst einen Bezugspunkt setzen.')
    act(() => view.options?.onPick({ lat: 50.105, lon: 8.67 }))
    await flush()
    expect(port.utm).toHaveBeenCalledWith({ punkt: { lat: 50.105, lon: 8.67 }, ellipsoid: 'GRS80' })
    expect(byTestId('geo-utm').textContent).toContain('EPSG:25832')
    expect(onReferenceChange).toHaveBeenCalledWith({ lat: 50.105, lon: 8.67 })
    submit('geo-radius-run')
    await flush()
    expect(port.radius).toHaveBeenCalledWith(expect.objectContaining({ radius_m: 5000, erdmodell: 'kugel.r1_6371008_8m' }))
    expect(byTestId('geo-radius-result').textContent).toContain('2 von 3 Punkten im Umkreis von 5,00 km')
    expect([...(view.layers.at(-1)?.hits ?? [])]).toEqual(['V-1', 'V-2'])
    expect(onRadiusCompleted).toHaveBeenCalledWith(GEO_RESULTS.radius)
  })

  it('prüft Punkt in Fläche, vereinfacht beim Loslassen des Reglers und meldet Portfehler', async () => {
    const onError = vi.fn()
    const { port } = await renderMap({ onError })
    act(() => view.options?.onPick({ lat: 50.1, lon: 8.67 }))
    await flush()
    fireEvent.change(byTestId('geo-locate-area'), { target: { value: 'G-1' } })
    submit('geo-locate-run')
    await flush()
    expect(byTestId('geo-position').textContent).toBe('auf dem Rand')
    expect(byTestId('geo-boundary-case').textContent).toContain('nach der gewählten Randregel zählt er als innen')
    const slider = byTestId('geo-simplify-tolerance') as HTMLInputElement
    expect(slider.getAttribute('aria-valuetext')).toBe('10 m')
    fireEvent.input(slider, { target: { value: '6' } })
    slider.dispatchEvent(new Event('change'))
    await flush()
    expect(port.simplify).toHaveBeenCalledWith({ flaeche: GEO_AREA.geometry, toleranz: 50, einheit: 'meter' })
    expect(view.layers.at(-1)?.simplified).toEqual((GEO_RESULTS.simplify as unknown as SimplifyResult).geometrie)
    vi.mocked(port.utm).mockRejectedValueOnce(new Error('Dienst aus'))
    act(() => view.options?.onPick({ lat: 1, lon: 2 }))
    await flush()
    expect(document.querySelector('.fa-geo__failure')?.textContent).toBe('Anfrage abgelehnt: Dienst aus')
    expect(onError).toHaveBeenCalledWith('Dienst aus')
  })

  it('setzt den Bezugspunkt aus UTM-Koordinaten und prüft die Zone', async () => {
    const onReferenceChange = vi.fn()
    const { port } = await renderMap({ onReferenceChange })
    fireEvent.change(byTestId('geo-utm-zone'), { target: { value: '0' } })
    submit('geo-utm-apply')
    await flush()
    expect(byTestId('geo-utm-zone').getAttribute('aria-invalid')).toBe('true')
    expect(port.fromUtm).not.toHaveBeenCalled()
    fireEvent.change(byTestId('geo-utm-zone'), { target: { value: '32' } })
    fireEvent.change(byTestId('geo-utm-east'), { target: { value: '476398.98' } })
    fireEvent.change(byTestId('geo-utm-north'), { target: { value: '5549801.4' } })
    submit('geo-utm-apply')
    await flush()
    await flush()
    expect(port.fromUtm).toHaveBeenCalledWith({ zone: 32, ost: 476398.98, nord: 5549801.4, nordhalbkugel: true, ellipsoid: 'GRS80' })
    expect(onReferenceChange).toHaveBeenCalledWith(GEO_RESULTS.utmPoint.punkt)
  })
})
