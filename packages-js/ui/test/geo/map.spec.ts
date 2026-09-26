import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import FaGeoMap from '../../src/geo/FaGeoMap.vue'
import type { MapLayers, MapViewOptions } from '../../src/geo/mapView'
import type { GeoCatalogue, GeoPackageResult, GeoPort, LocateResult, RadiusResult, SimplifyResult, UtmResult } from '../../src/geo/types'
import catalogue from '../fixtures/geo-catalogue.json'
import gpkg from '../fixtures/geo-gpkg.json'
import locate from '../fixtures/geo-locate-rand.json'
import radius from '../fixtures/geo-radius.json'
import simplify from '../fixtures/geo-simplify.json'
import utm from '../fixtures/geo-utm.json'

const view = vi.hoisted(() => ({ options: null as MapViewOptions | null, layers: [] as MapLayers[], fit: 0, tiles: [] as unknown[] }))

vi.mock('../../src/geo/mapView', () => ({
  createLeafletView: vi.fn(async (_element: HTMLElement, options: MapViewOptions) => {
    view.options = options
    return {
      update: (layers: MapLayers) => view.layers.push(layers),
      setTiles: (tiles: unknown) => view.tiles.push(tiles),
      fit: () => (view.fit += 1),
      destroy: vi.fn(),
    }
  }),
}))

const POINTS = [
  { id: 'V-1', label: 'Vorhaben Nord', lat: 50.105, lon: 8.67 },
  { id: 'V-2', label: 'Vorhaben Ost', lat: 50.14, lon: 8.68 },
  { id: 'V-3', label: 'Vorhaben Berlin', lat: 52.52, lon: 13.405 },
]
const AREA = { id: 'G-1', label: 'Gebiet A', geometry: { type: 'Polygon' as const, coordinates: [[[8.66, 50.1], [8.68, 50.1], [8.68, 50.11], [8.66, 50.11], [8.66, 50.1]]] } }

function fakePort(extra: Partial<GeoPort> = {}): GeoPort & Record<string, ReturnType<typeof vi.fn>> {
  return {
    catalogue: vi.fn(async () => catalogue as unknown as GeoCatalogue),
    radius: vi.fn(async () => radius as unknown as RadiusResult),
    locate: vi.fn(async () => locate as unknown as LocateResult),
    utm: vi.fn(async () => utm as unknown as UtmResult),
    simplify: vi.fn(async () => simplify as unknown as SimplifyResult),
    loadGeoPackage: vi.fn(async () => gpkg as unknown as GeoPackageResult),
    ...extra,
  } as GeoPort & Record<string, ReturnType<typeof vi.fn>>
}

async function mountMap(port: GeoPort | null = fakePort(), props: Record<string, unknown> = {}) {
  const wrapper = mount(FaGeoMap, { props: { port, points: POINTS, areas: [AREA], ...props }, attachTo: document.body })
  await flushPromises()
  return wrapper
}

beforeEach(() => {
  view.options = null
  view.layers = []
  view.fit = 0
  view.tiles = []
})

afterEach(() => {
  document.body.innerHTML = ''
})

describe('FaGeoMap', () => {
  it('zeichnet Punkte und Flächen, zeigt ohne Kachelquelle keinen Fremdserver', async () => {
    const wrapper = await mountMap()
    expect(view.options?.tiles).toBeNull()
    expect(wrapper.get('[data-testid="geo-no-tiles"]').text()).toContain('Keine Kachelquelle')
    const last = view.layers.at(-1)
    expect(last?.points).toHaveLength(3)
    expect(last?.areas.map((area) => area.id)).toEqual(['G-1'])
    expect(view.fit).toBe(1)
    const map = wrapper.get('[data-testid="geo-map"]')
    expect(map.attributes('role')).toBe('application')
    expect(map.attributes('aria-label')).toContain('3 Punkten und 1 Flächen')
  })

  it('zeigt die Namensnennung einer übergebenen Kachelquelle', async () => {
    const tiles = { url: '/kacheln/{z}/{x}/{y}.png', attribution: 'Synthetische Kacheln' }
    const wrapper = await mountMap(fakePort(), { tiles })
    expect(view.options?.tiles).toEqual(tiles)
    expect(wrapper.get('[data-testid="geo-attribution"]').text()).toBe('Kartendaten: Synthetische Kacheln')
    await wrapper.setProps({ tiles: null })
    expect(view.tiles).toEqual([null])
  })

  it('übernimmt einen Kartenklick als Bezugspunkt und zeigt UTM', async () => {
    const port = fakePort()
    const wrapper = await mountMap(port)
    view.options?.onPick({ lat: 50.1, lon: 8.67 })
    await flushPromises()
    expect(port.utm).toHaveBeenCalledWith({ punkt: { lat: 50.1, lon: 8.67 }, ellipsoid: 'GRS80' })
    expect(wrapper.get('[data-testid="geo-utm"]').text()).toMatch(/Zone 32N, E 4\d{5},\d{2} m, N 55\d{5},\d{2} m/)
    expect(wrapper.get('[data-testid="geo-utm"]').text()).toContain('EPSG:25832')
    expect((wrapper.get('[data-testid="geo-lat"]').element as HTMLInputElement).value).toBe('50.1')
    expect(wrapper.emitted('reference-change')?.[0]).toEqual([{ lat: 50.1, lon: 8.67 }])
    expect(view.layers.at(-1)?.reference).toEqual({ lat: 50.1, lon: 8.67 })
  })

  it('setzt den Bezugspunkt per Tastatur und meldet ungültige Eingaben', async () => {
    const wrapper = await mountMap()
    await wrapper.get('[data-testid="geo-lat"]').setValue('95')
    await wrapper.get('[data-testid="geo-lon"]').setValue('8,67')
    await wrapper.get('[data-testid="geo-apply"]').trigger('submit')
    expect(wrapper.get('[role="alert"]').text()).toContain('Breite muss')
    expect(wrapper.get('[data-testid="geo-lat"]').attributes('aria-invalid')).toBe('true')
    await wrapper.get('[data-testid="geo-lat"]').setValue('50,1')
    await wrapper.get('[data-testid="geo-lat"]').element.closest('form')?.dispatchEvent(new Event('submit'))
    await flushPromises()
    expect(wrapper.get('[data-testid="geo-reference"]').text()).toContain('50,100000, 8,670000')
  })

  it('sucht im Umkreis mit ausdrücklichem Erdmodell und listet Entfernungen', async () => {
    const port = fakePort()
    const wrapper = await mountMap(port)
    await wrapper.get('[data-testid="geo-radius-run"]').element.closest('form')?.dispatchEvent(new Event('submit'))
    expect(wrapper.get('[data-testid="geo-hint"]').text()).toBe('Zuerst einen Bezugspunkt setzen.')
    expect(port.radius).not.toHaveBeenCalled()
    await wrapper.get('[data-testid="geo-point-select"]').setValue('V-1')
    await wrapper.get('[data-testid="geo-point-take"]').trigger('click')
    await flushPromises()
    await wrapper.get('[data-testid="geo-radius-run"]').element.closest('form')?.dispatchEvent(new Event('submit'))
    await flushPromises()
    expect(port.radius).toHaveBeenCalledWith({
      zentrum: { lat: 50.105, lon: 8.67 },
      punkte: POINTS.map(({ id, lat, lon }) => ({ id, lat, lon })),
      radius_m: 5000,
      erdmodell: 'kugel.r1_6371008_8m',
    })
    const result = wrapper.get('[data-testid="geo-radius-result"]')
    expect(result.text()).toContain('2 von 3 Punkten im Umkreis von 5,00 km')
    expect(result.findAll('tbody tr').map((row) => row.text())).toEqual(['Vorhaben Nord556 m', 'Vorhaben Ost4,50 km'])
    expect(result.attributes('aria-live')).toBe('polite')
    expect([...(view.layers.at(-1)?.hits ?? [])]).toEqual(['V-1', 'V-2'])
    expect(view.layers.at(-1)?.radiusMetres).toBe(5000)
    expect(wrapper.emitted('radius-completed')?.[0]).toEqual([radius])
  })

  it('prüft Punkt in Fläche und zeigt den Randfall mit Randregel', async () => {
    const port = fakePort()
    const wrapper = await mountMap(port)
    view.options?.onPick({ lat: 50.1, lon: 8.67 })
    await flushPromises()
    await wrapper.get('[data-testid="geo-locate-area"]').setValue('G-1')
    expect(view.layers.at(-1)?.selectedArea).toBe('G-1')
    await wrapper.get('[data-testid="geo-locate-run"]').element.closest('form')?.dispatchEvent(new Event('submit'))
    await flushPromises()
    expect(port.locate).toHaveBeenCalledWith(expect.objectContaining({ rand_gilt_als_innen: true, rand_toleranz_m: 0, flaeche: AREA.geometry }))
    expect(wrapper.get('[data-testid="geo-position"]').text()).toBe('auf dem Rand')
    expect(wrapper.get('[data-testid="geo-boundary-case"]').text()).toBe('Randfall: Der Punkt liegt exakt auf dem Rand; nach der gewählten Randregel zählt er als innen.')
    expect(wrapper.get('[data-testid="geo-locate-result"]').text()).toContain('Ergebnis: in der Fläche')
  })

  it('vereinfacht mit Toleranzregler und blendet das Ergebnis ein', async () => {
    const port = fakePort()
    const wrapper = await mountMap(port)
    await wrapper.get('[data-testid="geo-simplify-area"]').setValue('G-1')
    expect(wrapper.text()).toContain('Stützpunkte der Fläche: 5')
    const slider = wrapper.get('[data-testid="geo-simplify-tolerance"]')
    expect(slider.attributes('aria-valuetext')).toBe('10 m')
    await slider.setValue('6')
    await slider.trigger('change')
    await flushPromises()
    expect(port.simplify).toHaveBeenCalledWith({ flaeche: AREA.geometry, toleranz: 50, einheit: 'meter' })
    expect(wrapper.get('[data-testid="geo-simplify-result"]').text()).toContain('41 → ')
    expect(view.layers.at(-1)?.simplified).toEqual((simplify as unknown as SimplifyResult).geometrie)
    await wrapper.get('[data-testid="geo-unit-grad"]').setValue(true)
    expect(wrapper.find('[data-testid="geo-simplify-result"]').exists()).toBe(false)
  })

  it('lädt ein GeoPackage, übernimmt die Flächen und meldet unlesbare Geometrien', async () => {
    const port = fakePort()
    const wrapper = await mountMap(port)
    const input = wrapper.get('[data-testid="geo-gpkg-file"]')
    const file = new File([new Uint8Array([1, 2, 3])], 'gebiete.gpkg')
    Object.defineProperty(input.element, 'files', { value: [file], configurable: true })
    await input.trigger('change')
    await flushPromises()
    expect(port.loadGeoPackage).toHaveBeenCalledWith(file)
    const result = wrapper.get('[data-testid="geo-gpkg-result"]')
    expect(result.text()).toContain('1 Flächen aus Tabelle „gebiete“ (srs_id 4326)')
    expect(result.text()).toContain('1 Geometrie(n) nicht lesbar')
    expect(view.layers.at(-1)?.areas.map((area) => area.id)).toEqual(['G-1', 'datei:1'])
    expect(wrapper.emitted('areas-loaded')?.[0]?.[0]).toHaveLength(1)
  })

  it('bietet Adresssuche nur mit Geocode-Port und aktivem Server-Geocoder an', async () => {
    const without = await mountMap(fakePort())
    expect(without.find('[data-testid="geo-address"]').exists()).toBe(false)
    const geocode = vi.fn(async () => ({ treffer: [{ rang: 1, lat: 50.11, lon: 8.68, anzeigename: 'Musterstraße 1' }], namensnennung: '© OSM' }))
    const serverOff = await mountMap(fakePort({ geocode }))
    expect(serverOff.find('[data-testid="geo-address"]').exists()).toBe(false)
    const active = { ...catalogue, geocoder: { aktiv: true, namensnennung: '© OSM' } }
    const wrapper = await mountMap(fakePort({ geocode, catalogue: vi.fn(async () => active as unknown as GeoCatalogue) }))
    await wrapper.get('[data-testid="geo-address"]').setValue('Musterstraße 1')
    await wrapper.get('[data-testid="geo-address"]').element.closest('form')?.dispatchEvent(new Event('submit'))
    await flushPromises()
    expect(geocode).toHaveBeenCalledWith('Musterstraße 1')
    await wrapper.get('.fa-geo__link').trigger('click')
    await flushPromises()
    expect(wrapper.emitted('reference-change')?.at(-1)).toEqual([{ lat: 50.11, lon: 8.68 }])
  })

  it('meldet Portfehler, arbeitet ohne Port nur mit Hinweis und spricht Englisch', async () => {
    const failing = fakePort({ utm: vi.fn(async () => { throw new Error('Dienst aus') }) })
    const wrapper = await mountMap(failing)
    view.options?.onPick({ lat: 1, lon: 2 })
    await flushPromises()
    expect(wrapper.get('.fa-geo__failure').text()).toBe('Anfrage abgelehnt: Dienst aus')
    expect(wrapper.emitted('error')?.[0]).toEqual(['Dienst aus'])
    const empty = await mountMap(null)
    expect(empty.text()).toContain('Kein Port übergeben')
    const english = await mountMap(fakePort(), { locale: 'en' })
    expect(english.text()).toContain('Radius search')
  })
})
