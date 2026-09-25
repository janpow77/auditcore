import { mount } from '@vue/test-utils'
import { defineComponent, h, ref } from 'vue'
import { describe, expect, it } from 'vitest'
import {
  createFlowauditUi,
  defineMessages,
  formatDate,
  formatPercent,
  interpolate,
  isLocale,
  setDefaultLocale,
  translate,
  useI18n,
  type Locale,
} from '../src'

const catalogs = defineMessages({
  de: { greeting: 'Hallo {name}', onlyGerman: 'Prüfung' },
  en: { greeting: 'Hello {name}' },
})

describe('i18n', () => {
  it('interpoliert Platzhalter und lässt unbekannte stehen', () => {
    expect(interpolate('{a} und {b}', { a: 1 })).toBe('1 und {b}')
  })

  it('fällt auf Deutsch zurück, wenn die englische Übersetzung fehlt', () => {
    expect(translate(catalogs, 'en', 'greeting', { name: 'Ada' })).toBe('Hello Ada')
    expect(translate(catalogs, 'en', 'onlyGerman')).toBe('Prüfung')
  })

  it('erkennt unterstützte Sprachen', () => {
    expect(isLocale('de')).toBe(true)
    expect(isLocale('fr')).toBe(false)
  })

  it('nutzt die per Plugin bereitgestellte Sprache und die Prop-Übersteuerung', async () => {
    const locale = ref<Locale>('de')
    const Probe = defineComponent({
      props: { locale: { type: String as () => Locale, default: undefined } },
      setup(props) {
        const { t } = useI18n(catalogs, () => props.locale)
        return () => h('span', t('greeting', { name: 'Jan' }))
      },
    })
    const wrapper = mount(Probe, { global: { plugins: [createFlowauditUi({ locale })] } })
    expect(wrapper.text()).toBe('Hallo Jan')
    locale.value = 'en'
    await wrapper.vm.$nextTick()
    expect(wrapper.text()).toBe('Hello Jan')
    await wrapper.setProps({ locale: 'de' })
    expect(wrapper.text()).toBe('Hallo Jan')
  })

  it('verwendet ohne Provider die Standardsprache', () => {
    setDefaultLocale('en')
    const Probe = defineComponent({ setup: () => () => h('span', useI18n(catalogs).t('greeting', { name: 'X' })) })
    expect(mount(Probe).text()).toBe('Hello X')
    setDefaultLocale('de')
  })

  it('formatiert Datum und Prozent sprachabhängig', () => {
    expect(formatDate('2026-09-25', 'de')).toBe('25.09.2026')
    expect(formatDate('kein Datum', 'de')).toBe('')
    expect(formatPercent(0.5, 'de')).toMatch(/50\s?%/)
  })
})
