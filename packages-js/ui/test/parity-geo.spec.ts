// Gemeinsame Paritätsfälle der Geo-Karte gegen die Vue-Fassung (Kartenansicht als Attrappe).
import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, it, vi } from 'vitest'
import { geoCases } from '../../ui-core/test/parity/cases-geo'
import { checkExpectation } from '../../ui-core/test/parity/expect'
import { FaGeoMap } from '../src'

vi.mock('@auditcore/ui-core', async (original) => ({
  ...(await original<typeof import('@auditcore/ui-core')>()),
  createLeafletView: vi.fn(async () => ({ update: vi.fn(), setTiles: vi.fn(), fit: vi.fn(), destroy: vi.fn() })),
}))

afterEach(() => {
  document.body.innerHTML = ''
})

describe('Paritätsfälle Geo-Karte (Vue)', () => {
  for (const entry of geoCases) {
    it(entry.name, async () => {
      const wrapper = mount(FaGeoMap, { props: { ...entry.props() }, attachTo: document.body })
      await flushPromises()
      checkExpectation(wrapper.element as HTMLElement, entry.expect)
      wrapper.unmount()
    })
  }
})
