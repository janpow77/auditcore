import { describe, expect, it } from 'vitest'
import AttributeSampling from '../../../ui/src/attributes/AttributeSampling.vue'
import { fakeAttributesPort } from '../../../ui-core/test/attributes/fake-port'
import { attributesCases } from '../../../ui-core/test/parity/cases-attributes'
import { FlowauditAttributeSampling } from '../../src/attributes/FlowauditAttributeSampling'
import { both, byTestId } from './interact'
import { expectParity, renderBoth } from './setup'

describe('Parität AttributeSampling Vue ↔ React', () => {
  for (const entry of attributesCases) {
    it(entry.name, async () => {
      const rendered = await renderBoth(AttributeSampling, { ...entry.props() }, <FlowauditAttributeSampling {...entry.props()} />)
      expectParity(rendered, entry.expect)
    })
  }
})

describe('Parität AttributeSampling nach Interaktion', () => {
  it('Befunde, Merkmalsstichprobe auswerten, Discovery wählen', async () => {
    const vuePort = fakeAttributesPort()
    const reactPort = fakeAttributesPort()
    const rendered = await renderBoth(AttributeSampling, { port: vuePort }, <FlowauditAttributeSampling port={reactPort} />)
    await both(rendered, byTestId('attributes-evaluate'), { kind: 'click' })
    expect(rendered.react.querySelectorAll('[aria-invalid="true"]')).toHaveLength(4)
    await both(rendered, byTestId('attributes-sampleSize'), { kind: 'input', value: '150' })
    await both(rendered, byTestId('attributes-deviations'), { kind: 'input', value: '3' })
    await both(rendered, byTestId('attributes-rate'), { kind: 'input', value: '5' })
    await both(rendered, byTestId('attributes-confidence'), { kind: 'change', value: '0.95' })
    await both(rendered, byTestId('attributes-evaluate'), { kind: 'click' })
    expect(reactPort.calls).toEqual(vuePort.calls)
    expect(rendered.react.querySelectorAll('[data-testid="attributes-metrics"] [data-metric]')).toHaveLength(4)
    await both(rendered, byTestId('attributes-approach'), { kind: 'change', value: 'discovery' })
    expect(rendered.vue.querySelector('[data-testid="attributes-profile"]')).toBeNull()
    await both(rendered, byTestId('attributes-evaluate'), { kind: 'click' })
    expect(reactPort.calls[1]).toMatchObject({ approach: 'discovery', tolerable_rate: 0.05 })
    expect(rendered.react.querySelector('[data-testid="attributes-conclusion"]')?.textContent).toBe('Keine Abweichung: Quote unter der kritischen Schwelle')
  })
})
