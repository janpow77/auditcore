import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'
import ExtrapolationPanel from '../../src/extrapolation/ExtrapolationPanel.vue'
import { defineFlowauditElements } from '../../src/elements'
import { evaluationResult, fakeExtrapolationPort, fixtureStrata, fixtureUnits, residualResult, residualWithinResult } from '../../../ui-core/test/extrapolation/fake-port'

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
    expect(wrapper.get('[data-testid="extrapolation-rer"]').text()).toContain('über der Signifikanzschwelle')
    await wrapper.get('[data-testid="extrapolation-export-csv"]').trigger('click')
    await flushPromises()
    expect(port.calls.export[0]?.[1]).toBe('csv')
  })

  it('zeigt Begründung für „entfällt“ und Hinweise der RER, exportiert sie mit und verwirft sie bei neuer Hochrechnung', async () => {
    const port = fakeExtrapolationPort()
    port.residualAnswer = residualWithinResult
    const { wrapper } = await mounted(port)
    await wrapper.get('[data-testid="extrapolation-method"]').setValue('mus.standard')
    await wrapper.get('[data-testid="extrapolation-confidence"]').setValue('0.9')
    await wrapper.get('[data-testid="extrapolation-evaluate"]').trigger('click')
    await flushPromises()
    await wrapper.get('[data-testid="extrapolation-rer-corrections"]').setValue('20')
    await wrapper.get('[data-testid="extrapolation-residual"]').trigger('click')
    await flushPromises()
    expect(wrapper.get('[data-testid="extrapolation-rer"]').text()).toContain('höchstens Signifikanzschwelle')
    expect(wrapper.text()).toContain('Warum L und M entfallen')
    expect(wrapper.get('[data-testid="extrapolation-rer-not-applicable"]').text()).toBe('Entfällt: Restfehlerquote nicht über der Signifikanzschwelle von 2 %.')
    const notes = wrapper.findAll('[data-testid="extrapolation-rer-notes"] li').map((item) => item.text())
    expect(notes).toEqual([...residualWithinResult.residual_error_rate.notes])
    await wrapper.get('[data-testid="extrapolation-export-csv"]').trigger('click')
    await flushPromises()
    expect(port.calls.export[0]?.[0].residual).toEqual(port.calls.residual[0])
    await wrapper.get('[data-testid="extrapolation-evaluate"]').trigger('click')
    await flushPromises()
    expect(wrapper.find('[data-testid="extrapolation-rer"]').exists()).toBe(false)
    expect(wrapper.find('[data-testid="extrapolation-rer-not-applicable"]').exists()).toBe(false)
    expect(wrapper.find('[data-testid="extrapolation-rer-notes"]').exists()).toBe(false)
    await wrapper.get('[data-testid="extrapolation-export-json"]').trigger('click')
    await flushPromises()
    expect(port.calls.export[1]?.[0]).not.toHaveProperty('residual')
  })

  it('zeigt bei Überschreitung keine Begründung für „entfällt“, wohl aber die Hinweise (englisch)', async () => {
    const wrapper = mount(ExtrapolationPanel, { props: { port: fakeExtrapolationPort(), strata: fixtureStrata, units: fixtureUnits, locale: 'en' }, attachTo: document.body })
    await flushPromises()
    await wrapper.get('[data-testid="extrapolation-method"]').setValue('mus.standard')
    await wrapper.get('[data-testid="extrapolation-confidence"]').setValue('0.9')
    await wrapper.get('[data-testid="extrapolation-evaluate"]').trigger('click')
    await flushPromises()
    await wrapper.get('[data-testid="extrapolation-residual"]').trigger('click')
    await flushPromises()
    expect(wrapper.find('[data-testid="extrapolation-rer-not-applicable"]').exists()).toBe(false)
    expect(wrapper.text()).toContain('Notes on the residual error rate')
    expect(wrapper.findAll('[data-testid="extrapolation-rer-notes"] li')).toHaveLength(residualResult.residual_error_rate.notes.length)
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
