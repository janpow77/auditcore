import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { nextTick } from 'vue'
import { SamplingCalculator } from '../src/index'
import { todayText } from '../src/composables/useSamplingSession'

/** Hinweise der Abnahme vom 14.10.2026: Stand des Beispielberichts, eigenes Menü der Anwendung, Kennzahlenleiste. */
const mounted: VueWrapper[] = []

function mountCalculator(props: Record<string, unknown> = {}): VueWrapper {
  const wrapper = mount(SamplingCalculator, { attachTo: document.body, props: { draft: 'off', guardUnload: false, ...props } })
  mounted.push(wrapper)
  return wrapper
}

async function settle(): Promise<void> {
  for (let round = 0; round < 4; round += 1) {
    await flushPromises()
    await vi.dynamicImportSettled()
    await new Promise((resolve) => setTimeout(resolve, 0))
  }
  await nextTick()
}

interface Exposed {
  loadSample: (method?: string) => void
  runAction: (action: string) => void
  isDirty: () => boolean
}
const api = (wrapper: VueWrapper): Exposed => wrapper.vm as unknown as Exposed

afterEach(() => {
  for (const wrapper of mounted.splice(0)) wrapper.unmount()
  document.body.innerHTML = ''
})

describe('Hinweise der Abnahme', () => {
  it('todayText schreibt TT.MM.JJJJ mit führenden Nullen', () => {
    expect(todayText(new Date(2026, 0, 5))).toBe('05.01.2026')
    expect(todayText(new Date(2026, 9, 14))).toBe('14.10.2026')
  })

  it('der Bericht der Beispielwerte trägt das heutige Datum als Stand', async () => {
    const wrapper = mountCalculator()
    api(wrapper).loadSample('03_MUS_1Z')
    await settle()
    await wrapper.get('[data-step="report"]').trigger('click')
    await settle()
    expect(wrapper.get('[data-report-as-of]').text()).toBe(`Stand ${todayText()}`)
    expect(api(wrapper).isDirty()).toBe(false)
  })

  it('workspaceMenu=false blendet das eigene Menü aus; runAction lädt die Beispielwerte', async () => {
    const wrapper = mountCalculator({ workspaceMenu: false })
    expect(wrapper.find('.fa-st__menu-wrap').exists()).toBe(false)
    api(wrapper).runAction('sample')
    await settle()
    expect(wrapper.get('[data-status]').text()).toContain('Beispielwerte')
  })

  it('die kompakte Kennzahlenleiste nennt Hauptgröße, Kennzahlen und Ampel', async () => {
    const wrapper = mountCalculator()
    api(wrapper).loadSample('03_MUS_1Z')
    await settle()
    const strip = wrapper.get('[data-kpi-strip]')
    expect(strip.attributes('aria-hidden')).toBe('true')
    expect(strip.text()).toContain('Wesentlichkeitsschwelle')
    expect(strip.findAll('.fa-st__strip-item').length).toBeGreaterThan(1)
  })
})
