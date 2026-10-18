/** Einbindung in eine Anwendung: Texte, Sprache, Hinweis des Fachrahmens und Datenmarke (ohne Dateiaktionen). */
import { mount, type VueWrapper } from '@vue/test-utils'
import { afterEach, describe, expect, it } from 'vitest'
import { SamplingCalculator } from '../src/index'
import { FOUNDATION_SHEETS } from './sheets'

const mounted: VueWrapper[] = []

function mountCalculator(props: Record<string, unknown> = {}): VueWrapper {
  const wrapper = mount(SamplingCalculator, { attachTo: document.body, props: { sheets: FOUNDATION_SHEETS, localDraft: false, ...props } })
  mounted.push(wrapper)
  return wrapper
}

afterEach(() => {
  for (const wrapper of mounted.splice(0)) wrapper.unmount()
  document.body.innerHTML = ''
})

describe('Texte', () => {
  it('eine Anwendung kann Texte überschreiben und Englisch liefern', () => {
    const wrapper = mountCalculator({ locale: 'en', messages: { en: { exportResult: 'Export result', pickerQuestion: 'Which sampling method do you apply?' } } })
    expect(wrapper.get('[data-action="export"]').text()).toBe('Export result')
    expect(wrapper.get('.fa-st__question').text()).toBe('Which sampling method do you apply?')
    expect(wrapper.get('.fa-st__menu-wrap > button').text()).toBe('Working file')
    expect(wrapper.get('[data-translation-note]').text()).toContain('Working translation')
  })
})

describe('Einbindung in eine Anwendung', () => {
  it('zeigt den Hinweis des Fachrahmens und den Stand der Vorlage', () => {
    const wrapper = mountCalculator()
    expect(wrapper.get('[data-disclaimer]').text()).toBe('Die Berechnung bildet die Stichprobenvorlagen 2021–2027 nach. Sie ersetzt nicht die fachliche Würdigung der Prüfbehörde und ist kein Dokument der Europäischen Kommission.')
    expect(wrapper.get('[data-template-status]').text()).toContain('Fassung 4, Stand Oktober 2026')
    expect(wrapper.get('[data-template-status]').text()).toContain('keine amtliche Fassung')
    expect(wrapper.find('[data-mark]').exists()).toBe(false)
  })

  it('nimmt die Datenmarke der Anwendung als Text oder als Slot', () => {
    expect(mountCalculator({ dataMark: 'Daten bleiben im Browser' }).get('[data-mark]').text()).toBe('Daten bleiben im Browser')
    const wrapper = mount(SamplingCalculator, { props: { sheets: FOUNDATION_SHEETS }, slots: { mark: '<span class="eco-datamark">Browser</span>' } })
    mounted.push(wrapper)
    expect(wrapper.get('[data-mark] .eco-datamark').text()).toBe('Browser')
  })
})
