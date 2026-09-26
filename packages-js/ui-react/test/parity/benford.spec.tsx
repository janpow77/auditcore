import { describe, expect, it } from 'vitest'
import BenfordPanel from '../../../ui/src/benford/BenfordPanel.vue'
import { fakeBenfordPort } from '../../../ui-core/test/sampling/fake-port'
import { benfordCases, flowinvoiceMetrics } from '../../../ui-core/test/parity/cases-benford'
import { FlowauditBenford } from '../../src/benford/FlowauditBenford'
import { byTestId, both } from './interact'
import { expectParity, renderBoth } from './setup'

describe('Parität Benford Vue ↔ React', () => {
  for (const entry of benfordCases) {
    it(entry.name, async () => {
      const rendered = await renderBoth(BenfordPanel, { ...entry.props() }, <FlowauditBenford {...entry.props()} />)
      expectParity(rendered, entry.expect)
    })
  }
})

describe('Parität Benford nach Interaktion', () => {
  it('analysieren, Test wechseln, kurze Werte verlangen und wählen, Profil abwählen', async () => {
    const vuePort = fakeBenfordPort()
    const reactPort = fakeBenfordPort()
    const values = [123, 45.6, null, 0]
    const rendered = await renderBoth(BenfordPanel, { port: vuePort, values }, <FlowauditBenford port={reactPort} values={values} />)
    await both(rendered, byTestId('benford-analyse'), { kind: 'submit' })
    expect(rendered.react.querySelectorAll('.fa-benford__bar--exceeds')).toHaveLength(1)
    await both(rendered, (root) => root.querySelector('[data-testid="benford-table"] .fa-table__sort'), { kind: 'click' })
    await both(rendered, byTestId('benford-test'), { kind: 'change', value: 'second' })
    await both(rendered, byTestId('benford-analyse'), { kind: 'submit' })
    await both(rendered, byTestId('benford-short-exclude'), { kind: 'click' })
    await both(rendered, byTestId('benford-analyse'), { kind: 'submit' })
    expect(reactPort.calls).toEqual(vuePort.calls)
    expect(reactPort.calls).toHaveLength(2)
    await both(rendered, byTestId('benford-profile'), { kind: 'change', value: '' })
    await both(rendered, byTestId('benford-analyse'), { kind: 'submit' })
    expect(rendered.react.querySelector('.fa-benford__error')?.textContent).toBe('Bewertungsprofil wählen.')
  })
})

describe('Parität Benford: Kennzahlen abwählen', () => {
  it('auffällige Ziffern abgewählt, nur der Chi²-Test wird angefordert', async () => {
    const vuePort = fakeBenfordPort()
    const reactPort = fakeBenfordPort()
    const values = [123, 45.6]
    const rendered = await renderBoth(BenfordPanel, { port: vuePort, values, metrics: flowinvoiceMetrics }, <FlowauditBenford port={reactPort} values={values} metrics={flowinvoiceMetrics} />)
    await both(rendered, byTestId('benford-metric-digit_z'), { kind: 'click' })
    await both(rendered, byTestId('benford-analyse'), { kind: 'submit' })
    expect(reactPort.calls).toEqual(vuePort.calls)
    expect(reactPort.calls[0]).toMatchObject({ metrics: { chi_square: { significance_level: 0.05 } } })
    expect((reactPort.calls[0] as { metrics: object }).metrics).not.toHaveProperty('digit_z')
  })
})
