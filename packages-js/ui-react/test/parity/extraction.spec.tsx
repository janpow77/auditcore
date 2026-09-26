import { fireEvent as domEvent } from '@testing-library/dom'
import { fireEvent } from '@testing-library/react'
import { flushPromises } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import FaExtraction from '../../../ui/src/extraction/FaExtraction.vue'
import { fakeExtractionPort, syntheticFile } from '../../../ui-core/test/extraction/fake-port'
import { extractionCases } from '../../../ui-core/test/parity/cases-extraction'
import { formState, normalizeDom } from '../../../ui-core/test/parity/dom'
import { FlowauditExtraction } from '../../src/extraction/FlowauditExtraction'
import { both, byTestId } from './interact'
import { expectParity, renderBoth, tick, type Rendered } from './setup'

describe('Parität Belegerkennung Vue ↔ React', () => {
  for (const entry of extractionCases) {
    it(entry.name, async () => {
      const rendered = await renderBoth(FaExtraction, { ...entry.props() }, <FlowauditExtraction {...entry.props()} />)
      expectParity(rendered, entry.expect)
    })
  }
})

/** Datei in beiden Fassungen wählen (Dateiauswahl lässt sich nur als Eigenschaft setzen). */
async function chooseBoth(rendered: Rendered): Promise<void> {
  for (const [root, events] of [[rendered.vue, domEvent], [rendered.react, fireEvent]] as const) {
    const input = root.querySelector('[data-testid="extraction-file"]') as HTMLInputElement
    events.change(input, { target: { files: [syntheticFile()] } })
    await flushPromises()
    await tick()
  }
  expect(normalizeDom(rendered.react)).toBe(normalizeDom(rendered.vue))
}

describe('Parität Belegerkennung nach Interaktion', () => {
  it('ohne Datei senden, Datei wählen, Donut-Profil wählen, erkennen', async () => {
    const vuePort = fakeExtractionPort()
    const reactPort = fakeExtractionPort()
    const rendered = await renderBoth(FaExtraction, { port: vuePort }, <FlowauditExtraction port={reactPort} />)
    await both(rendered, byTestId('extraction-run'), { kind: 'submit' })
    expect(rendered.react.querySelector('.fa-extraction__error')?.textContent).toBe('Bitte eine Datei auswählen.')
    await chooseBoth(rendered)
    await both(rendered, byTestId('extraction-profile'), { kind: 'change', value: 'auditcore.pipeline.donut' })
    expect(rendered.react.querySelector('[data-testid="extraction-experimental"]')).not.toBeNull()
    await both(rendered, byTestId('extraction-run'), { kind: 'submit' })
    expect(reactPort.calls).toEqual(vuePort.calls)
    expect(reactPort.calls).toEqual([['beleg.png', 'auditcore.pipeline.donut', 64]])
    expect(rendered.react.querySelector('[data-testid="extraction-status"]')?.textContent).toBe('Prüfung erforderlich')
    await both(rendered, (root) => root.querySelector('.fa-extraction__passed summary'), { kind: 'click' })
    expect(formState(rendered.react)).toEqual(formState(rendered.vue))
  })
})
