import { act } from 'react'
import { createRoot, type Root } from 'react-dom/client'
import { afterEach, beforeAll, describe, expect, it, vi } from 'vitest'
import { FlowauditGeoMap, defineFlowauditElements } from '../src/elements'
import catalogue from '../../ui/test/fixtures/geo-catalogue.json'
import radius from '../../ui/test/fixtures/geo-radius.json'
import utm from '../../ui/test/fixtures/geo-utm.json'

;(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true

let root: Root | null = null
let host: HTMLElement

beforeAll(() => {
  defineFlowauditElements()
})

afterEach(() => {
  act(() => root?.unmount())
  root = null
  document.body.innerHTML = ''
})

const flush = () => new Promise((resolve) => setTimeout(resolve, 0))

describe('React-Hülle Geo-Karte', () => {
  it('übergibt Port, Punkte und Kachelquelle und reicht radius-completed weiter', async () => {
    const port = { catalogue: vi.fn(async () => catalogue), utm: vi.fn(async () => utm), radius: vi.fn(async () => radius), locate: vi.fn(), simplify: vi.fn() }
    const onRadiusCompleted = vi.fn()
    const onReferenceChange = vi.fn()
    host = document.createElement('div')
    document.body.append(host)
    root = createRoot(host)
    act(() =>
      root?.render(
        <FlowauditGeoMap
          port={port as never}
          points={[{ id: 'V-1', lat: 50.105, lon: 8.67 }]}
          tiles={{ url: '/kacheln/{z}/{x}/{y}.png', attribution: 'Synthetische Kacheln' }}
          onRadiusCompleted={onRadiusCompleted}
          onReferenceChange={onReferenceChange}
        />,
      ),
    )
    await act(flush)
    await act(flush)
    expect(port.catalogue).toHaveBeenCalled()
    expect(host.querySelector('[data-testid="geo-attribution"]')?.textContent).toContain('Synthetische Kacheln')
    const select = host.querySelector<HTMLSelectElement>('[data-testid="geo-point-select"]')
    if (!select) throw new Error('Auswahl fehlt')
    select.value = 'V-1'
    select.dispatchEvent(new Event('change'))
    await act(flush)
    host.querySelector<HTMLButtonElement>('[data-testid="geo-point-take"]')?.click()
    await act(flush)
    expect(onReferenceChange.mock.calls[0]?.[0]).toEqual({ lat: 50.105, lon: 8.67 })
    host.querySelector('[data-testid="geo-radius-run"]')?.closest('form')?.dispatchEvent(new Event('submit'))
    await act(flush)
    await act(flush)
    expect(port.radius).toHaveBeenCalled()
    expect(onRadiusCompleted.mock.calls[0]?.[0]).toEqual(radius)
  })
})
