import { act } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import SamplingPanel from '../../../ui/src/sampling/SamplingPanel.vue'
import { fakeSamplingPort, populationItems } from '../../../ui-core/test/sampling/fake-port'
import { samplingCases } from '../../../ui-core/test/parity/cases-sampling'
import { FlowauditSampling } from '../../src/sampling/FlowauditSampling'
import { byTestId, both } from './interact'
import { expectParity, renderBoth } from './setup'

describe('Parität Stichprobe Vue ↔ React', () => {
  for (const entry of samplingCases) {
    it(entry.name, async () => {
      const rendered = await renderBoth(SamplingPanel, { ...entry.props() }, <FlowauditSampling {...entry.props()} />)
      expectParity(rendered, entry.expect)
    })
  }
})

describe('Parität Stichprobe nach Interaktion', () => {
  it('Pflichtangaben, Umfang berechnen, Aufteilung wählen, ziehen, neu ziehen', async () => {
    const vuePort = fakeSamplingPort()
    const reactPort = fakeSamplingPort()
    const rendered = await renderBoth(SamplingPanel, { port: vuePort, items: populationItems }, <FlowauditSampling port={reactPort} items={populationItems} />)
    await both(rendered, byTestId('sampling-calculate'), { kind: 'submit' })
    expect(rendered.react.querySelectorAll('[role="alert"]').length).toBeGreaterThanOrEqual(3)
    await both(rendered, byTestId('sampling-population_value'), { kind: 'input', value: '475.478,94' })
    await both(rendered, byTestId('sampling-materiality'), { kind: 'input', value: '50.000' })
    await both(rendered, byTestId('sampling-expected_error_rate'), { kind: 'input', value: '0,5' })
    await both(rendered, byTestId('sampling-confidence'), { kind: 'change', value: '0.95' })
    await both(rendered, byTestId('sampling-calculate'), { kind: 'submit' })
    expect(reactPort.calls.size).toEqual(vuePort.calls.size)
    expect(rendered.react.querySelector('[data-testid="sampling-size"]')?.textContent).toBe('n = 30')
    await both(rendered, byTestId('sampling-draw'), { kind: 'submit' })
    expect(rendered.react.textContent).toContain('Aufteilung auf Schichten wählen.')
    await both(rendered, byTestId('sampling-allocation'), { kind: 'change', value: 'proportional' })
    await both(rendered, byTestId('sampling-seed'), { kind: 'input', value: '42' })
    await both(rendered, byTestId('sampling-draw'), { kind: 'submit' })
    expect(reactPort.calls.selection).toEqual(vuePort.calls.selection)
    expect(reactPort.calls.selection).toHaveLength(1)
    expect(rendered.react.querySelectorAll('[data-testid="sampling-rows"] tbody tr')).toHaveLength(6)
    await both(rendered, (root) => root.querySelector('[data-testid="sampling-rows"] .fa-table__sort'), { kind: 'click' })
    await both(rendered, byTestId('sampling-redraw'), { kind: 'click' })
    await act(async () => undefined)
  })

  it('Methode wechseln (SRS) und Vorschläge aus der Grundgesamtheit übernehmen', async () => {
    const rendered = await renderBoth(SamplingPanel, { port: fakeSamplingPort(), items: populationItems }, <FlowauditSampling port={fakeSamplingPort()} items={populationItems} />)
    await both(rendered, byTestId('sampling-method'), { kind: 'change', value: 'portal.srs_normal' })
    const suggest = (root: HTMLElement) => Array.from(root.querySelectorAll('button')).find((node) => node.textContent?.trim() === 'Aus Grundgesamtheit übernehmen')
    await both(rendered, suggest, { kind: 'click' })
    await both(rendered, byTestId('sampling-margin_of_error'), { kind: 'input', value: '150' })
    await both(rendered, byTestId('sampling-calculate'), { kind: 'submit' })
    expect((rendered.react.querySelector('[data-testid="sampling-population_size"]') as HTMLInputElement).value).toBe('30')
  })
})
