// Gemeinsame Paritätsfälle von „PDF schwärzen“ (ui-core/test/parity/cases-redaction.ts)
// gegen die Vue-Fassung; die React-Fassung prüft dieselben Fälle, vergleicht das DOM
// und führt die Interaktionen in beiden Fassungen aus.
import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, expect, it } from 'vitest'
import { fakeRedactionPort, fakeUrls } from '../../ui-core/test/redaction/fake-port'
import { redactionCases } from '../../ui-core/test/parity/cases-redaction'
import { checkExpectation } from '../../ui-core/test/parity/expect'
import PdfRedaction from '../src/redaction/PdfRedaction.vue'

afterEach(() => {
  document.body.innerHTML = ''
})

describe('Paritätsfälle PDF schwärzen (Vue)', () => {
  for (const entry of redactionCases) {
    it(entry.name, async () => {
      const wrapper = mount(PdfRedaction, { props: { ...entry.props() }, attachTo: document.body })
      await flushPromises()
      checkExpectation(wrapper.element as HTMLElement, entry.expect)
      wrapper.unmount()
    })
  }

  it('gibt Objekt-URLs beim Entfernen frei', async () => {
    const urls = fakeUrls()
    const wrapper = mount(PdfRedaction, { props: { port: fakeRedactionPort(), urls }, attachTo: document.body })
    await flushPromises()
    wrapper.unmount()
    expect(urls.live.size).toBe(0)
  })
})
