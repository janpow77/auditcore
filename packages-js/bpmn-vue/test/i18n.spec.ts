import { describe, expect, it } from 'vitest'
import { createI18n } from '../src/i18n/useI18n'
import { MESSAGES_DE } from '../src/i18n/messages.de'
import { MESSAGES_EN } from '../src/i18n/messages.en'

const placeholders = (text: string) => [...text.matchAll(/\{(\w+)\}/g)].map((m) => m[1]).sort()

describe('i18n', () => {
  it('fills parameters and falls back to the key', () => {
    const { t } = createI18n('de')
    expect(t('collection.version', { version: '1.2' })).toBe('Version 1.2')
    expect(t('unbekannt.schluessel')).toBe('unbekannt.schluessel')
  })

  it('switches the locale and accepts application overrides', () => {
    const i18n = createI18n('de', { en: { 'common.save': 'Store' } })
    i18n.locale.value = 'en'
    expect(i18n.t('common.save')).toBe('Store')
    expect(i18n.t('common.cancel')).toBe('Cancel')
  })

  it('has the same keys and placeholders in German and English', () => {
    expect(Object.keys(MESSAGES_EN).sort()).toEqual(Object.keys(MESSAGES_DE).sort())
    for (const [key, text] of Object.entries(MESSAGES_DE)) expect(placeholders(MESSAGES_EN[key] ?? ''), key).toEqual(placeholders(text))
  })

  it('uses real umlauts and no ASCII substitutes in German texts', () => {
    const substitutes = /pruef|fuer|aender|koenn|ueber|schluess|gemaess|naechst|loesch|waehl|hinzufueg|oeffn|zurueck|moeglich|gueltig|foerder|behoerde/i
    expect(Object.values(MESSAGES_DE).filter((text) => substitutes.test(text))).toEqual([])
  })
})
