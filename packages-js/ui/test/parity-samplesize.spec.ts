// Gemeinsame Paritätsfälle (ui-core/test/parity/cases-samplesize.ts) gegen
// die Vue-Fassung; die React-Fassung prüft dieselben Fälle und vergleicht
// zusätzlich das DOM.
import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, expect, it } from 'vitest'
import { conservativeRequest, fakeSamplesizePort, samplesizeCases } from '../../ui-core/test/parity/cases-samplesize'
import { checkExpectation } from '../../ui-core/test/parity/expect'
import SampleSizePlanner from '../src/samplesize/SampleSizePlanner.vue'

afterEach(() => {
  document.body.innerHTML = ''
})

describe('Paritätsfälle SampleSizePlanner (Vue)', () => {
  for (const entry of samplesizeCases) {
    it(entry.name, async () => {
      const wrapper = mount(SampleSizePlanner, { props: { ...entry.props() }, attachTo: document.body })
      await flushPromises()
      checkExpectation(wrapper.element as HTMLElement, entry.expect)
      wrapper.unmount()
    })
  }

  it('meldet das Ergebnis als Ereignis', async () => {
    const wrapper = mount(SampleSizePlanner, { props: { port: fakeSamplesizePort(), request: conservativeRequest }, attachTo: document.body })
    await flushPromises()
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    const events = wrapper.emitted('plan-calculated') as [{ sample_size: number }][] | undefined
    expect(events?.[0]?.[0].sample_size).toBe(136)
    wrapper.unmount()
  })
})
