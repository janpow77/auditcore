/** Vorbelegte Felder (BV und N aus Blatt 02) mit nicht lesbarer Eingabe: kein stiller Rückfall auf die Vorbelegung. */
import { mount, type VueWrapper } from '@vue/test-utils'
import { afterEach, describe, expect, it } from 'vitest'
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

describe('Vorbelegte Felder', () => {
  it('ungültige Eingabe in einem vorbelegten Feld fällt nicht still auf Blatt 02 zurück', async () => {
    const wrapper = mountCalculator()
    await wrapper.get('[data-sheet="03_MUS_1Z"]').trigger('click')
    await menu(wrapper, 'sample')
    expect(value(wrapper, 'C27')).toBe('92')
    await input(wrapper, 'C7').setValue('abc')
    await input(wrapper, 'C7').trigger('blur')
    expect(input(wrapper, 'C7').attributes('aria-invalid')).toBe('true')
    // Ergebnisspalte und Kennzahlenleiste: „Eingabe ungültig“ statt des mit BV aus Blatt 02 gerechneten Umfangs; Folgegrößen „—“.
    expect([value(wrapper, 'C16'), value(wrapper, 'C21'), value(wrapper, 'C27')]).toEqual(['Eingabe ungültig', '—', '—'])
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
})
