// Gemeinsame Paritätsfälle (ui-core/test/parity/cases-batchchecks.ts) gegen
// die Vue-Fassung; die React-Fassung prüft dieselben Fälle und vergleicht
// zusätzlich das DOM.
import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, expect, it } from 'vitest'
import { batchCsv, fakeBatchchecksPort, textFile } from '../../ui-core/test/batchchecks/fake-port'
import { batchchecksCases } from '../../ui-core/test/parity/cases-batchchecks'
import { checkExpectation } from '../../ui-core/test/parity/expect'
import BatchChecks from '../src/batchchecks/BatchChecks.vue'

afterEach(() => {
  document.body.innerHTML = ''
})

describe('Paritätsfälle BatchChecks (Vue)', () => {
  for (const entry of batchchecksCases) {
    it(entry.name, async () => {
      const wrapper = mount(BatchChecks, { props: { ...entry.props() }, attachTo: document.body })
      await flushPromises()
      checkExpectation(wrapper.element as HTMLElement, entry.expect)
      wrapper.unmount()
    })
  }
})

describe('BatchChecks (Vue): Ereignisse', () => {
  it('meldet checks-completed nach dem Prüflauf und error bei Ablehnung', async () => {
    const wrapper = mount(BatchChecks, { props: { port: fakeBatchchecksPort() }, attachTo: document.body })
    await flushPromises()
    const input = wrapper.find('[data-testid="batchchecks-file"]').element as HTMLInputElement
    Object.defineProperty(input, 'files', { value: [textFile(batchCsv, 'bestand.csv')], configurable: true })
    await wrapper.find('[data-testid="batchchecks-file"]').trigger('change')
    await flushPromises()
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    expect(wrapper.emitted('checks-completed')).toHaveLength(1)
    await wrapper.setProps({ port: fakeBatchchecksPort({ failing: 'catalogue' }) })
    await flushPromises()
    expect(wrapper.emitted('error')?.[0]).toEqual(['Dienst nicht erreichbar'])
    wrapper.unmount()
  })
})
