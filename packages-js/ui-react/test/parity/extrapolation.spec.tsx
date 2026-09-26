import { describe, expect, it } from 'vitest'
import ExtrapolationPanel from '../../../ui/src/extrapolation/ExtrapolationPanel.vue'
import { fakeExtrapolationPort, fixtureStrata, fixtureUnits } from '../../../ui-core/test/extrapolation/fake-port'
import { extrapolationCases } from '../../../ui-core/test/parity/cases-extrapolation'
import { FlowauditExtrapolation } from '../../src/extrapolation/FlowauditExtrapolation'
import { byTestId, both } from './interact'
import { expectParity, renderBoth } from './setup'

describe('Parität Hochrechnung Vue ↔ React', () => {
  for (const entry of extrapolationCases) {
    it(entry.name, async () => {
      const rendered = await renderBoth(ExtrapolationPanel, { ...entry.props() }, <FlowauditExtrapolation {...entry.props()} />)
      expectParity(rendered, entry.expect)
    })
  }
})

const cell = (label: string) => (root: HTMLElement) => root.querySelector(`[aria-label="${label}"]`)

describe('Parität Hochrechnung nach Interaktion', () => {
  it('Methode fehlt, MUS wählen, Konfidenz, hochrechnen, RER berechnen', async () => {
    const vuePort = fakeExtrapolationPort()
    const reactPort = fakeExtrapolationPort()
    const props = { strata: fixtureStrata, units: fixtureUnits }
    const rendered = await renderBoth(ExtrapolationPanel, { port: vuePort, ...props }, <FlowauditExtrapolation port={reactPort} {...props} />)
    await both(rendered, byTestId('extrapolation-evaluate'), { kind: 'click' })
    expect(rendered.react.querySelector('[data-testid="extrapolation-form-error"]')?.textContent).toBe('Hochrechnungsmethode wählen.')
    await both(rendered, byTestId('extrapolation-method'), { kind: 'change', value: 'mus.standard' })
    await both(rendered, byTestId('extrapolation-confidence'), { kind: 'change', value: '0.9' })
    await both(rendered, byTestId('extrapolation-evaluate'), { kind: 'click' })
    expect(reactPort.calls.evaluate).toEqual(vuePort.calls.evaluate)
    expect(reactPort.calls.evaluate).toHaveLength(1)
    expect(rendered.react.querySelector('[data-testid="extrapolation-conclusion"]')?.textContent).toBe('Nicht schlüssig – weitere Prüfungshandlungen')
    await both(rendered, byTestId('extrapolation-rer-corrections'), { kind: 'input', value: '2,1' })
    await both(rendered, byTestId('extrapolation-residual'), { kind: 'click' })
    expect(reactPort.calls.residual).toEqual(vuePort.calls.residual)
    expect(rendered.react.querySelectorAll('[data-testid="extrapolation-rer-rows"] tbody tr')).toHaveLength(12)
  })

  it('Zeilen bearbeiten: Feldbefunde, Einheit hinzufügen, Kennzeichen setzen, Schicht hinzufügen', async () => {
    const props = { strata: fixtureStrata, units: fixtureUnits }
    const rendered = await renderBoth(ExtrapolationPanel, { port: fakeExtrapolationPort(), ...props }, <FlowauditExtrapolation port={fakeExtrapolationPort()} {...props} />)
    await both(rendered, byTestId('extrapolation-method'), { kind: 'change', value: 'nonstatistical.pps' })
    await both(rendered, cell('Buchwert, Zeile 2'), { kind: 'input', value: 'abc' })
    await both(rendered, byTestId('extrapolation-evaluate'), { kind: 'click' })
    expect(rendered.react.querySelectorAll('[aria-invalid="true"]')).toHaveLength(2)
    await both(rendered, byTestId('extrapolation-add-unit'), { kind: 'click' })
    await both(rendered, cell('Vollerhebung, Zeile 6'), { kind: 'click' })
    await both(rendered, byTestId('extrapolation-add-stratum'), { kind: 'click' })
    await both(rendered, cell('Schicht, Zeile 2'), { kind: 'input', value: 'Hochwert' })
    expect(rendered.react.querySelectorAll('[data-testid="extrapolation-strata"] tbody tr')).toHaveLength(2)
  })
})
