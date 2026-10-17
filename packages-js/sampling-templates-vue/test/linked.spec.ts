/** Felder mit nicht lesbarer Eingabe: kein stiller Rückfall auf die Vorbelegung (BV und N aus Blatt 02) und nicht auf „leer = 0“. */
import { mount, type VueWrapper } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { nextTick } from 'vue'
import { SamplingCalculator } from '../src/index'
import { FOUNDATION_SHEETS } from './sheets'

const nbsp = (text: string): string => text.replaceAll(String.fromCharCode(160), ' ')
const mounted: VueWrapper[] = []

function mountCalculator(): VueWrapper {
  const wrapper = mount(SamplingCalculator, { attachTo: document.body, props: { sheets: FOUNDATION_SHEETS, localDraft: false } })
  mounted.push(wrapper)
  return wrapper
}

async function menu(wrapper: VueWrapper, action: string): Promise<void> {
  await wrapper.get('.fa-st__menu-wrap > button').trigger('click')
  await wrapper.get(`[data-action="${action}"]`).trigger('click')
}

const cell = (wrapper: VueWrapper, address: string) => wrapper.get(`[data-cell="${address}"]`)
const input = (wrapper: VueWrapper, address: string) => cell(wrapper, address).get<HTMLInputElement>('input, select')
const value = (wrapper: VueWrapper, address: string): string => nbsp(cell(wrapper, address).get('.fa-st__value').text())

afterEach(() => {
  for (const wrapper of mounted.splice(0)) wrapper.unmount()
  document.body.innerHTML = ''
})

describe('Ungültige Eingaben', () => {
  it('ungültige Eingabe in einem vorbelegten Feld fällt nicht still auf Blatt 02 zurück', async () => {
    const wrapper = mountCalculator()
    await wrapper.get('[data-sheet="03_MUS_1Z"]').trigger('click')
    await menu(wrapper, 'sample')
    expect(value(wrapper, 'C27')).toBe('92')
    await input(wrapper, 'C7').setValue('abc')
    await input(wrapper, 'C7').trigger('blur')
    expect(input(wrapper, 'C7').attributes('aria-invalid')).toBe('true')
    // Ergebnisspalte und Kennzahlenleiste: „Eingabe ungültig“ statt des mit BV aus Blatt 02 gerechneten Umfangs, auch in jeder Folgegröße.
    expect([value(wrapper, 'C16'), value(wrapper, 'C21'), value(wrapper, 'C27')]).toEqual(['Eingabe ungültig', 'Eingabe ungültig', 'Eingabe ungültig'])
    expect(wrapper.get('[data-result="primary"]').text()).toBe('Eingabe ungültig. Ungültige Eingabe: Buchwert der angepassten zu prüfenden Grundgesamtheit (positive Einheiten) (BV) (C7)')
    expect(wrapper.get('[data-kpi-strip]').text()).toContain('Anzuwendender Stichprobenumfang Eingabe ungültig')
    expect(wrapper.get('[data-kpi-strip]').text()).not.toContain('92 Einheiten')
    // Erst das geleerte Feld übernimmt wieder die Vorbelegung.
    await input(wrapper, 'C7').setValue('')
    await input(wrapper, 'C7').trigger('blur')
    await nextTick()
    expect(cell(wrapper, 'C7').get('[data-link]').text()).toBe('aus Blatt 02_Grundgesamtheit vorbelegt')
    expect(value(wrapper, 'C27')).toBe('92')
    // N geht in den MUS-Umfang der Vorlage nicht ein: Ungültig ist nur das Feld selbst, der Umfang bleibt.
    await input(wrapper, 'C8').setValue('abc')
    await input(wrapper, 'C8').trigger('blur')
    expect([input(wrapper, 'C8').attributes('aria-invalid'), value(wrapper, 'C27')]).toEqual(['true', '92'])
  })

  it('ungültige Eingabe in einem Feld, das leer mit 0 rechnet (s_r): „Eingabe ungültig“ statt still 0, keine grüne Würdigung; erst leer „mit 0 berechnet“', async () => {
    const wrapper = mountCalculator()
    await wrapper.get('[data-sheet="03_MUS_1Z"]').trigger('click')
    await menu(wrapper, 'sample')
    for (const text of ['abc', '1.5', '0,6752123456789']) {
      await input(wrapper, 'C39').setValue(text)
      await input(wrapper, 'C39').trigger('blur')
      if (input(wrapper, 'C39').attributes('aria-invalid') !== 'true') continue
      expect(value(wrapper, 'C43'), text).toBe('Eingabe ungültig')
      expect(cell(wrapper, 'C52').text(), text).toContain('Eingabe ungültig')
      expect(wrapper.get('[data-kpi-strip]').text(), text).not.toContain('unter der Signifikanzschwelle')
      // Ergebnisspalte, Kennzahlenleiste und Ansage nennen den Grund; die Gesamtfehlerquote bleibt sichtbar.
      expect(wrapper.get('[data-kpis]').text(), text).toContain('Eingabe ungültig')
      expect(wrapper.get('[data-invalid-note]').text(), text).toMatch(/^Eingabe ungültig\. Ungültige Eingabe: .*\(C39\)$/)
      expect(wrapper.get('[data-kpi-strip]').text(), text).toContain('Obere Fehlergrenze Eingabe ungültig')
      expect(wrapper.get('[data-kpi-strip]').text(), text).toContain('(C39)')
      expect(wrapper.get('[data-kpi-strip]').text(), text).toMatch(/Gesamtfehlerquote \d/)
    }
    await input(wrapper, 'C39').setValue('')
    await input(wrapper, 'C39').trigger('blur')
    expect(value(wrapper, 'C43')).not.toBe('Eingabe ungültig')
    expect(cell(wrapper, 'C43').text()).toContain('Keine Angabe, daher mit 0 berechnet')
    expect(wrapper.find('[data-invalid-note]').exists()).toBe(false)
  })

  it('die Ansage (aria-live) nennt den Grund einer ungültigen Eingabe', async () => {
    vi.useFakeTimers()
    try {
      const wrapper = mountCalculator()
      await wrapper.get('[data-sheet="03_MUS_1Z"]').trigger('click')
      await menu(wrapper, 'sample')
      vi.advanceTimersByTime(1600)
      await nextTick()
      await input(wrapper, 'C39').setValue('abc')
      await input(wrapper, 'C39').trigger('blur')
      vi.advanceTimersByTime(1600)
      await nextTick()
      const live = nbsp(wrapper.get('[data-live]').text())
      expect(live).toContain('Obere Fehlergrenze Eingabe ungültig')
      expect(live).toMatch(/Eingabe ungültig\. Ungültige Eingabe: .*\(C39\)$/)
    } finally {
      vi.useRealTimers()
    }
  })
})

