import { fireEvent as domEvent } from '@testing-library/dom'
import { fireEvent } from '@testing-library/react'
import { flushPromises } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import BatchChecks from '../../../ui/src/batchchecks/BatchChecks.vue'
import { batchCsv, fakeBatchchecksPort, textFile } from '../../../ui-core/test/batchchecks/fake-port'
import { batchchecksCases } from '../../../ui-core/test/parity/cases-batchchecks'
import { formState, normalizeDom } from '../../../ui-core/test/parity/dom'
import { FlowauditBatchChecks } from '../../src/batchchecks/FlowauditBatchChecks'
import { both, byTestId } from './interact'
import { expectParity, renderBoth, tick, type Rendered } from './setup'

describe('Parität BatchChecks Vue ↔ React', () => {
  for (const entry of batchchecksCases) {
    it(entry.name, async () => {
      const rendered = await renderBoth(BatchChecks, { ...entry.props() }, <FlowauditBatchChecks {...entry.props()} />)
      expectParity(rendered, entry.expect)
    })
  }
})

async function upload(rendered: Rendered, file: File): Promise<void> {
  for (const [root, events] of [[rendered.vue, domEvent], [rendered.react, fireEvent]] as const) {
    const input = root.querySelector('[data-testid="batchchecks-file"]') as HTMLInputElement
    Object.defineProperty(input, 'files', { value: [file], configurable: true })
    events.change(input)
    for (let i = 0; i < 3; i += 1) {
      await flushPromises()
      await tick()
    }
  }
  expect(normalizeDom(rendered.react)).toBe(normalizeDom(rendered.vue))
  expect(formState(rendered.react)).toEqual(formState(rendered.vue))
}

describe('Parität BatchChecks nach Interaktion', () => {
  it('CSV einlesen, zuordnen, Gesamtvolumen, prüfen, nach Regel filtern', async () => {
    const vuePort = fakeBatchchecksPort()
    const reactPort = fakeBatchchecksPort()
    const rendered = await renderBoth(BatchChecks, { port: vuePort }, <FlowauditBatchChecks port={reactPort} />)
    await both(rendered, byTestId('batchchecks-run'), { kind: 'submit' })
    expect(rendered.react.querySelector('[role="alert"]')?.textContent).toBe('Bitte zuerst eine Datei einlesen.')
    await upload(rendered, textFile(batchCsv, 'bestand.csv'))
    expect(rendered.react.querySelector('[data-testid="batchchecks-source"]')?.textContent).toBe('bestand.csv: 10 Zeile(n)')
    expect((rendered.react.querySelector('[data-testid="batchchecks-col-invoice_number"]') as HTMLSelectElement).value).toBe('1')
    await both(rendered, byTestId('batchchecks-col-description'), { kind: 'change', value: '' })
    await both(rendered, byTestId('batchchecks-total'), { kind: 'input', value: 'viel' })
    await both(rendered, byTestId('batchchecks-run'), { kind: 'submit' })
    expect(rendered.react.querySelector('[role="alert"]')?.textContent).toBe('Das Gesamtvolumen ist keine lesbare Zahl.')
    await both(rendered, byTestId('batchchecks-total'), { kind: 'input', value: '48.500,00' })
    await both(rendered, byTestId('batchchecks-run'), { kind: 'submit' })
    expect(rendered.react.querySelector('[data-testid="batchchecks-level"]')?.textContent).toBe('Blockade')
    expect(rendered.react.querySelectorAll('[data-testid="batchchecks-export-csv"]')).toHaveLength(1)
    await both(rendered, byTestId('batchchecks-filter'), { kind: 'change', value: 'C-09' })
    expect(rendered.react.querySelectorAll('[data-testid="batchchecks-findings"] tbody tr')).toHaveLength(1)
    await both(rendered, byTestId('batchchecks-export-csv'), { kind: 'click' })
    expect(reactPort.calls).toEqual(vuePort.calls)
    expect(reactPort.calls.map(([kind]) => kind)).toEqual(['catalogue', 'run', 'export'])
    expect(reactPort.calls[1]?.[1]?.documents[0]).not.toHaveProperty('description')
  })

  it('JSON-Datei statt Tabelle, Ergänzungsprüfungen abschalten', async () => {
    const vuePort = fakeBatchchecksPort()
    const reactPort = fakeBatchchecksPort()
    const rendered = await renderBoth(BatchChecks, { port: vuePort }, <FlowauditBatchChecks port={reactPort} />)
    await upload(rendered, textFile('[{"invoice_number": "A-1"}, {"invoice_number": "A-2"}]', 'bestand.json'))
    expect(rendered.react.querySelector('[data-testid="batchchecks-source"]')?.textContent).toBe('bestand.json: 2 Beleg(e) aus JSON')
    expect(rendered.react.querySelectorAll('fieldset')).toHaveLength(0)
    await both(rendered, byTestId('batchchecks-supplementary'), { kind: 'click' })
    await both(rendered, byTestId('batchchecks-run'), { kind: 'submit' })
    expect(reactPort.calls[1]?.[1]).toEqual({ documents: [{ invoice_number: 'A-1' }, { invoice_number: 'A-2' }], options: { supplementary: false } })
    expect(reactPort.calls).toEqual(vuePort.calls)
  })
})
