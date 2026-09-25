import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'
import BenfordPanel from '../../src/benford/BenfordPanel.vue'
import type { BenfordAnalysis, BenfordCatalogue, BenfordPort } from '../../src/benford/types'
import analysis from '../fixtures/benford-analysis.json'
import profiles from '../fixtures/benford-profiles.json'

function fakePort(): BenfordPort {
  return {
    profiles: vi.fn(async () => profiles as unknown as BenfordCatalogue),
    analyse: vi.fn(async () => analysis as unknown as BenfordAnalysis),
  }
}

afterEach(() => {
  document.body.innerHTML = ''
})

describe('BenfordPanel', () => {
  it('analysiert übergebene Werte, zeigt Kennzahlen, Stufe und hebt Ziffern hervor', async () => {
    const port = fakePort()
    const wrapper = mount(BenfordPanel, { props: { port, values: [123, 45.6, null, 0] } })
    await flushPromises()
    expect(wrapper.get('[data-testid="benford-count"]').text()).toBe('4 Werte übernommen')
    await wrapper.get('form').trigger('submit')
    await flushPromises()
    expect(port.analyse).toHaveBeenCalledWith({ test: 'first', profile: 'nigrini.2012', values: [123, 45.6, null, 0] })
    expect(wrapper.get('[data-testid="benford-level"]').text()).toBe(analysis.conformity.mad_label)
    expect(wrapper.get('[data-testid="benford-exceeding"]').text()).toBe(analysis.conformity.exceeding_digits.join(', '))
    const flagged = wrapper.findAll('.fa-benford__bar--exceeds').map((bar) => Number(bar.attributes('data-digit')))
    expect(flagged).toEqual(analysis.conformity.exceeding_digits)
    expect(wrapper.get('[data-testid="benford-chart"]').attributes('role')).toBe('img')
    expect(wrapper.text()).toContain('keine Feststellungen')
    expect(wrapper.emitted('analysis-completed')?.[0]).toEqual([analysis])
  })

  it('verlangt bei zweistelligen Tests die Regel für kurze Werte', async () => {
    const port = fakePort()
    const wrapper = mount(BenfordPanel, { props: { port, values: [12, 34] } })
    await flushPromises()
    await wrapper.get('[data-testid="benford-test"]').setValue('second')
    await wrapper.get('form').trigger('submit')
    expect(wrapper.get('[role="alert"]').text()).toContain('Regel für Werte')
    expect(port.analyse).not.toHaveBeenCalled()
    await wrapper.get('[data-testid="benford-short-exclude"]').setValue(true)
    await wrapper.get('form').trigger('submit')
    await flushPromises()
    expect(port.analyse).toHaveBeenCalledWith({ test: 'second', profile: 'nigrini.2012', short_values: 'exclude', values: [12, 34] })
  })

  it('liest eine CSV-Datei mit Dezimalkomma und meldet unlesbare Zeilen', async () => {
    const wrapper = mount(BenfordPanel, { props: { port: fakePort() } })
    await flushPromises()
    const input = wrapper.get('input[type="file"]')
    const file = new File(['Beleg;Betrag\nA;1.234,50\nB;x\nC;17,00\n'], 'belege.csv', { type: 'text/csv' })
    Object.defineProperty(input.element, 'files', { value: [file] })
    await input.trigger('change')
    await flushPromises()
    expect(wrapper.text()).toContain('belege.csv: 3 Zeilen')
    expect(wrapper.text()).toContain('1 Zeilen nicht lesbar (Zeilen 2)')
    await wrapper.get('[data-testid="import-apply"]').trigger('click')
    expect(wrapper.get('[data-testid="benford-count"]').text()).toBe('2 Werte übernommen')
  })
})
