import { afterEach, describe, expect, it, vi } from 'vitest'
import { createLeafletView, escapeHtml, type MapLayers } from '../../src/geo/mapView'

const AREA = { id: 'G-1', label: 'Gebiet A', geometry: { type: 'Polygon' as const, coordinates: [[[8.66, 50.1], [8.68, 50.1], [8.68, 50.11], [8.66, 50.11], [8.66, 50.1]]] } }
const LAYERS: MapLayers = {
  points: [{ id: 'P-1', lat: 50.105, lon: 8.67 }, { id: 'P-2', lat: 50.2, lon: 8.9 }],
  areas: [AREA],
  reference: { lat: 50.1, lon: 8.67 },
  radiusMetres: 1000,
  hits: new Set(['P-1']),
  selectedArea: 'G-1',
  simplified: AREA.geometry,
}

function container(): HTMLElement {
  const element = document.createElement('div')
  Object.defineProperty(element, 'clientWidth', { value: 600 })
  Object.defineProperty(element, 'clientHeight', { value: 400 })
  document.body.append(element)
  return element
}

afterEach(() => {
  document.body.innerHTML = ''
})

describe('Leaflet-Ansicht', () => {
  it('zeichnet Objekte mit Token-Klassen, ohne Kachelquelle ohne Kachelebene', async () => {
    const element = container()
    const view = await createLeafletView(element, { center: { lat: 50, lon: 8 }, zoom: 9, tiles: null, onPick: vi.fn(), label: (entry) => entry.id })
    view.update(LAYERS)
    expect(element.querySelector('.leaflet-tile-pane')?.children).toHaveLength(0)
    expect(element.querySelectorAll('path.fa-geo__point')).toHaveLength(2)
    expect(element.querySelectorAll('path.fa-geo__point--hit')).toHaveLength(1)
    expect(element.querySelector('path.fa-geo__area--selected')).not.toBeNull()
    expect(element.querySelector('path.fa-geo__simplified')).not.toBeNull()
    expect(element.querySelector('path.fa-geo__radius')).not.toBeNull()
    expect(element.querySelector('path.fa-geo__reference')).not.toBeNull()
    expect(element.querySelector('.leaflet-control-attribution')?.textContent).toContain('Leaflet')
    view.fit()
    view.destroy()
  })

  it('gibt Namensnennung und Beschriftungen nur als Text an Leaflet', async () => {
    expect(escapeHtml('<img src=x onerror="1">&')).toBe('&#60;img src=x onerror=&#34;1&#34;&#62;&#38;')
    const element = container()
    const view = await createLeafletView(element, { center: { lat: 50, lon: 8 }, zoom: 9, tiles: { url: '/k/{z}/{x}/{y}.png', attribution: '<b>fett</b>' }, onPick: vi.fn(), label: () => '<script>x</script>' })
    view.update(LAYERS)
    expect(element.querySelector('.leaflet-control-attribution b')).toBeNull()
    expect(element.querySelector('.leaflet-control-attribution')?.textContent).toContain('<b>fett</b>')
    view.destroy()
  })

  it('setzt eine Kachelquelle mit Namensnennung und meldet Klicks als Bezugspunkt', async () => {
    const element = container()
    const onPick = vi.fn()
    const view = await createLeafletView(element, { center: { lat: 50, lon: 8 }, zoom: 9, tiles: null, onPick, label: (entry) => entry.id })
    view.setTiles({ url: '/kacheln/{z}/{x}/{y}.png', attribution: 'Synthetische Kacheln' })
    expect(element.querySelector('.leaflet-control-attribution')?.textContent).toContain('Synthetische Kacheln')
    view.setTiles(null)
    expect(element.querySelector('.leaflet-control-attribution')?.textContent).not.toContain('Synthetische Kacheln')
    element.dispatchEvent(new MouseEvent('click', { clientX: 300, clientY: 200, bubbles: true }))
    expect(onPick).toHaveBeenCalledTimes(1)
    const point = onPick.mock.calls[0]?.[0] as { lat: number; lon: number }
    expect(point.lat).toBeGreaterThan(49)
    expect(point.lon).toBeGreaterThan(7)
    view.destroy()
  })
})
