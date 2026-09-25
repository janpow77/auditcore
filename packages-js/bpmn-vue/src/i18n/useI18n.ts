/**
 * Minimal i18n: German is the default, English is prepared. Components
 * call `t(key, params)`; applications may add or override messages.
 */

import { computed, inject, provide, ref, type InjectionKey, type Ref } from 'vue'
import { MESSAGES_DE } from './messages.de'
import { MESSAGES_EN } from './messages.en'

export type Locale = 'de' | 'en'
export type MessageTable = Record<string, string>

export interface I18n {
  locale: Ref<Locale>
  t: (key: string, params?: Record<string, string | number>) => string
}

const TABLES: Record<Locale, MessageTable> = { de: MESSAGES_DE, en: MESSAGES_EN }
const KEY: InjectionKey<I18n> = Symbol('flowaudit-i18n')

export function createI18n(locale: Locale = 'de', overrides: Partial<Record<Locale, MessageTable>> = {}): I18n {
  const current = ref<Locale>(locale)
  const tables = computed(() => ({ ...MESSAGES_DE, ...TABLES[current.value], ...(overrides[current.value] ?? {}) }))
  return {
    locale: current,
    t: (key, params = {}) =>
      (tables.value[key] ?? key).replace(/\{(\w+)\}/g, (match, name: string) => (params[name] === undefined ? match : String(params[name]))),
  }
}

export function provideI18n(i18n: I18n): I18n {
  provide(KEY, i18n)
  return i18n
}

/** Injected i18n, or a German default when used standalone. */
export function useI18n(): I18n {
  return inject(KEY, null) ?? createI18n('de')
}
