import { FaGeoMap } from '@auditcore/ui'
import { fireEvent as domEvent } from '@testing-library/dom'
import { fireEvent } from '@testing-library/react'
import { flushPromises } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'
import type { LatLon, MapViewOptions } from '@auditcore/ui-core'
import { fakeGeoPort, GEO_AREA, GEO_POINTS, geoCases } from '../../../ui-core/test/parity/cases-geo'
import { formState, normalizeDom } from '../../../ui-core/test/parity/dom'
import { FlowauditGeoMap } from '../../src/geo/FlowauditGeoMap'
import { expectParity, renderBoth, tick, type Rendered } from './setup'

// Leaflet braucht echtes Layout; beide Fassungen bekommen dieselbe Attrappe der Kartenansicht.
const views = vi.hoisted(() => [] as MapViewOptions[])
vi.mock('@auditcore/ui-core', async (original) => ({
  ...(await original<typeof import('@auditcore/ui-core')>()),
  createLeafletView: vi.fn(async (_element: HTMLElement, options: MapViewOptions) => {
    views.push(options)
    return { update: vi.fn(), setTiles: vi.fn(), fit: vi.fn(), destroy: vi.fn() }
  }),
}))

describe('Parität Geo-Karte Vue ↔ React', () => {
  for (const entry of geoCases) {
    it(entry.name, async () => {
      expectParity(await renderBoth(FaGeoMap, { ...entry.props() }, <FlowauditGeoMap {...entry.props()} />), entry.expect)
    })
  }
})

async function same(rendered: Rendered): Promise<void> {
  await flushPromises()
  await tick()
  expect(normalizeDom(rendered.react)).toBe(normalizeDom(rendered.vue))
  expect(formState(rendered.react)).toEqual(formState(rendered.vue))
}

async function both(rendered: Rendered, selector: string, action: (element: HTMLElement, react: boolean) => void): Promise<void> {
  for (const [root, react] of [[rendered.vue, false], [rendered.react, true]] as const) {
    const element = root.querySelector<HTMLElement>(selector)
    expect(element, selector).toBeTruthy()
    action(element as HTMLElement, react)
    await flushPromises()
    await tick()
  }
  await same(rendered)
}

const submit = (element: HTMLElement, react: boolean) => (react ? fireEvent : domEvent).submit(element.closest('form') as HTMLFormElement)
const select = (value: string) => (element: HTMLElement, react: boolean) => (react ? fireEvent : domEvent).change(element, { target: { value } })
const click = (element: HTMLElement, react: boolean) => (react ? fireEvent : domEvent).click(element)

describe('Parität Geo-Karte nach Interaktion', () => {
  it('Hinweis, Bezugspunkt, Umkreis, Punkt in Fläche, Vereinfachung, GeoPackage', async () => {
    views.length = 0
    const props = { points: GEO_POINTS, areas: [GEO_AREA] }
    const rendered = await renderBoth(FaGeoMap, { port: fakeGeoPort(), ...props }, <FlowauditGeoMap port={fakeGeoPort()} {...props} />)
    await both(rendered, '[data-testid="geo-radius-run"]', submit)
    await both(rendered, '[data-testid="geo-point-select"]', select('V-1'))
    await both(rendered, '[data-testid="geo-point-take"]', click)
    await both(rendered, '[data-testid="geo-radius-run"]', submit)
    for (const view of views) view.onPick({ lat: 50.1, lon: 8.67 } satisfies LatLon)
    await same(rendered)
    await both(rendered, '[data-testid="geo-locate-area"]', select('G-1'))
    await both(rendered, '[data-testid="geo-locate-run"]', submit)
    await both(rendered, '[data-testid="geo-simplify-run"]', submit)
    await both(rendered, '[data-testid="geo-unit-grad"]', click)
    const file = new File([new Uint8Array([1, 2, 3])], 'gebiete.gpkg')
    await both(rendered, '[data-testid="geo-gpkg-file"]', (element, react) => {
      Object.defineProperty(element, 'files', { value: [file], configurable: true })
      ;(react ? fireEvent : domEvent).change(element)
    })
    expect(rendered.react.querySelector('[data-testid="geo-gpkg-result"]')?.textContent).toContain('1 Flächen aus Tabelle')
  })
})

const type = (value: string) => (element: HTMLElement, react: boolean) =>
  react ? fireEvent.change(element, { target: { value } }) : domEvent.input(element, { target: { value } })

describe('Parität Geo-Karte: UTM-Eingabe', () => {
  it('Fehler je Feld, Halbkugel, Rückrechnung setzt den Bezugspunkt und füllt die Felder', async () => {
    views.length = 0
    const ports = [fakeGeoPort(), fakeGeoPort()]
    const rendered = await renderBoth(FaGeoMap, { port: ports[0], points: GEO_POINTS }, <FlowauditGeoMap port={ports[1]} points={GEO_POINTS} />)
    await both(rendered, '[data-testid="geo-utm-zone"]', type('61'))
    await both(rendered, '[data-testid="geo-utm-apply"]', submit)
    expect(rendered.react.querySelector('.fa-geo__utm [role="alert"]')?.textContent).toBe('Zone muss eine ganze Zahl von 1 bis 60 sein.')
    await both(rendered, '[data-testid="geo-utm-zone"]', type('32'))
    await both(rendered, '[data-testid="geo-utm-east"]', type('476398,98'))
    await both(rendered, '[data-testid="geo-utm-north"]', type('5549801,4'))
    await both(rendered, '[data-testid="geo-utm-hemisphere"]', select('S'))
    await both(rendered, '[data-testid="geo-utm-hemisphere"]', select('N'))
    await both(rendered, '[data-testid="geo-utm-apply"]', submit)
    for (const port of ports) {
      expect(port.fromUtm).toHaveBeenCalledWith({ zone: 32, ost: 476398.98, nord: 5549801.4, nordhalbkugel: true, ellipsoid: 'GRS80' })
    }
    expect(rendered.react.querySelector('[data-testid="geo-reference"]')?.textContent).toContain('50,100000')
    expect((rendered.react.querySelector('[data-testid="geo-utm-east"]') as HTMLInputElement).value).toBe('476398.98')
  })
})
