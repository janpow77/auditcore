import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'
import ExtrapolationPanel from '../../src/extrapolation/ExtrapolationPanel.vue'
import { defineFlowauditElements } from '../../src/elements'
import { evaluationResult, fakeExtrapolationPort, fixtureStrata, fixtureUnits, residualResult } from '../../../ui-core/test/extrapolation/fake-port'

vi.mock('../../src/rest/download', () => ({ saveFile: vi.fn() }))

afterEach(() => {
  document.body.innerHTML = ''
})

async function mounted(port = fakeExtrapolationPort()) {
  const wrapper = mount(ExtrapolationPanel, { props: { port, strata: fixtureStrata, units: fixtureUnits }, attachTo: document.body })
  await flushPromises()
  return { wrapper, port }
}

describe('ExtrapolationPanel', () => {
  it('rechnet hoch, zeigt TER, Obergrenze, Erläuterung und Herleitung und sendet das Ereignis', async () => {
    const { wrapper, port } = await mounted()
    await wrapper.get('[data-testid="extrapolation-method"]').setValue('mus.standard')
    await wrapper.get('[data-testid="extrapolation-confidence"]').setValue('0.9')
    await wrapper.get('[data-testid="extrapolation-evaluate"]').trigger('click')
    await flushPromises()
    expect(port.calls.evaluate[0]).toMatchObject({ method: 'mus.standard', confidence_level: 0.9, factor_profile: 'kom_2017_tables', materiality_rate: 0.02 })
    expect(wrapper.emitted('evaluation-completed')?.[0]).toEqual([evaluationResult])
    const metrics = wrapper.get('[data-testid="extrapolation-metrics"]').text()
    expect(metrics).toContain('Gesamtfehlerquote (TER)')
    expect(metrics).toContain('Fehlerobergrenze (ULE)')
    expect(wrapper.text()).toContain('Korrigierte anomale Fehler sind nicht Teil der Gesamtfehlerquote.')
    expect(wrapper.findAll('[data-testid="extrapolation-steps"] tbody tr').length).toBeGreaterThan(5)
    expect(wrapper.text()).toContain('Restfehlerquote (RER) nach Finanzkorrekturen')
  })

  it('berechnet die RER getrennt und exportiert die Auswertung', async () => {
    const { wrapper, port } = await mounted()
    await wrapper.get('[data-testid="extrapolation-method"]').setValue('mus.standard')
    await wrapper.get('[data-testid="extrapolation-confidence"]').setValue('0.9')
    await wrapper.get('[data-testid="extrapolation-evaluate"]').trigger('click')
    await flushPromises()
    expect((wrapper.get('[data-testid="extrapolation-rer-terRate"]').element as HTMLInputElement).value).toBe('1,6')
    await wrapper.get('[data-testid="extrapolation-rer-corrections"]').setValue('2,1')
    await wrapper.get('[data-testid="extrapolation-residual"]').trigger('click')
    await flushPromises()
    expect(port.calls.residual[0]).toMatchObject({ audit_population: 1_000_000, total_error_rate: 0.016, financial_corrections: 2.1 })
    expect(wrapper.emitted('residual-computed')?.[0]).toEqual([residualResult])
    expect(wrapper.get('[data-testid="extrapolation-rer"]').text()).toContain('über der Wesentlichkeitsschwelle')
    await wrapper.get('[data-testid="extrapolation-export-csv"]').trigger('click')
    await flushPromises()
    expect(port.calls.export[0]?.[1]).toBe('csv')
  })

  it('meldet abgelehnte Anfragen und markiert Feldbefunde', async () => {
    const { wrapper } = await mounted(fakeExtrapolationPort('evaluate'))
    await wrapper.get('[data-testid="extrapolation-method"]').setValue('mus.standard')
    await wrapper.get('[data-testid="extrapolation-confidence"]').setValue('0.9')
    await wrapper.get('[aria-label="Buchwert, Zeile 1"]').setValue('')
    await wrapper.get('[data-testid="extrapolation-evaluate"]').trigger('click')
    expect(wrapper.get('[data-testid="extrapolation-form-error"]').text()).toBe('Bitte die markierten Felder prüfen.')
    expect(wrapper.get('[aria-label="Buchwert, Zeile 1"]').attributes('aria-invalid')).toBe('true')
    await wrapper.get('[aria-label="Buchwert, Zeile 1"]').setValue('20000')
    await wrapper.get('[data-testid="extrapolation-evaluate"]').trigger('click')
    await flushPromises()
    expect(wrapper.get('[role="alert"]').text()).toContain('Tabelle 3')
    expect(wrapper.emitted('error')).toHaveLength(1)
  })

  it('Web Component im Light DOM', async () => {
    defineFlowauditElements({ only: ['flowaudit-extrapolation'] })
    const element = document.createElement('flowaudit-extrapolation') as HTMLElement & Record<string, unknown>
    element.port = fakeExtrapolationPort()
    element.units = fixtureUnits
    element.strata = fixtureStrata
    document.body.append(element)
    await flushPromises()
    expect(element.shadowRoot).toBeNull()
    expect(element.querySelectorAll('[data-testid="extrapolation-units"] tbody tr')).toHaveLength(5)
  })
})
