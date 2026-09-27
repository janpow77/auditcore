import { describe, expect, it } from 'vitest'
import SampleSizePlanner from '../../../ui/src/samplesize/SampleSizePlanner.vue'
import { conservativeRequest, fakeSamplesizePort, samplesizeCases, stratifiedRequest } from '../../../ui-core/test/parity/cases-samplesize'
import { FlowauditSampleSizePlanner } from '../../src/samplesize/FlowauditSampleSizePlanner'
import { both, byTestId } from './interact'
import { expectParity, renderBoth } from './setup'

describe('Parität SampleSizePlanner Vue ↔ React', () => {
  for (const entry of samplesizeCases) {
    it(entry.name, async () => {
      const rendered = await renderBoth(SampleSizePlanner, { ...entry.props() }, <FlowauditSampleSizePlanner {...entry.props()} />)
      expectParity(rendered, entry.expect)
    })
  }
})

describe('Parität SampleSizePlanner nach Interaktion', () => {
  it('Umfang berechnen zeigt Ergebnis, Herleitung und Status', async () => {
    const port = fakeSamplesizePort()
    const rendered = await renderBoth(SampleSizePlanner, { port, request: conservativeRequest }, <FlowauditSampleSizePlanner port={port} request={conservativeRequest} />)
    await both(rendered, byTestId('samplesize-calculate'), { kind: 'submit' })
    expect(rendered.react.textContent).toContain('136')
    expect(rendered.react.querySelectorAll('[data-testid="samplesize-derivation"] tbody tr')).toHaveLength(6)
    expect(rendered.react.textContent).toContain('nach Leitfaden')
    expect(port.calls).toEqual([conservativeRequest, conservativeRequest])
  })

  it('Aufteilung der Schichten und Pflichtfelder nach Methodenwechsel', async () => {
    const port = fakeSamplesizePort()
    const rendered = await renderBoth(SampleSizePlanner, { port, request: stratifiedRequest }, <FlowauditSampleSizePlanner port={port} request={stratifiedRequest} />)
    await both(rendered, byTestId('samplesize-calculate'), { kind: 'submit' })
    expect(rendered.vue.querySelectorAll('[data-testid="samplesize-allocation"] tbody tr')).toHaveLength(3)
    await both(rendered, byTestId('samplesize-method'), { kind: 'change', value: 'guidance.srs' })
    await both(rendered, byTestId('samplesize-calculate'), { kind: 'submit' })
    expect(rendered.react.querySelectorAll('[aria-invalid="true"]').length).toBeGreaterThan(2)
    await both(rendered, byTestId('samplesize-population_size'), { kind: 'input', value: '3852' })
  })
})
