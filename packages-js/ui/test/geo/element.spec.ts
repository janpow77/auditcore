import { flushPromises } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { defineFlowauditElements } from '../../src/elements'
import catalogue from '../fixtures/geo-catalogue.json'
import utm from '../fixtures/geo-utm.json'

afterEach(() => {
  document.body.innerHTML = ''
})

describe('Web Component flowaudit-geo-map', () => {
  it('läuft im Light DOM, nimmt Eigenschaften an und sendet reference-change', async () => {
    defineFlowauditElements({ only: ['flowaudit-geo-map'] })
    const element = document.createElement('flowaudit-geo-map') as HTMLElement & Record<string, unknown>
    element.port = { catalogue: vi.fn(async () => catalogue), utm: vi.fn(async () => utm) }
    element.points = [{ id: 'P-1', lat: 50.1, lon: 8.6 }]
    document.body.append(element)
    await flushPromises()
    expect(element.shadowRoot).toBeNull()
    expect(element.querySelector('[data-testid="geo-map"]')?.getAttribute('aria-label')).toContain('1 Punkten')
    const received: unknown[] = []
    element.addEventListener('reference-change', (event) => received.push((event as CustomEvent<unknown[]>).detail[0]))
    const lat = element.querySelector<HTMLInputElement>('[data-testid="geo-lat"]')
    const lon = element.querySelector<HTMLInputElement>('[data-testid="geo-lon"]')
    if (!lat || !lon) throw new Error('Eingabefelder fehlen')
    lat.value = '50,1'
    lat.dispatchEvent(new Event('input'))
    lon.value = '8,6'
    lon.dispatchEvent(new Event('input'))
    lat.closest('form')?.dispatchEvent(new Event('submit'))
    await flushPromises()
    expect(received).toEqual([{ lat: 50.1, lon: 8.6 }])
    expect(element.querySelector('[data-testid="geo-utm"]')?.textContent).toContain('Zone 32N')
  })
})
