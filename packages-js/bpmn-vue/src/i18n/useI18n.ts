/**
 * Minimal i18n: German is the default, English is prepared. Components
 * call `t(key, params)`; applications may add or override messages. The
 * texts and the lookup live in the framework-free UI core.
 */

import { computed, inject, provide, ref, type InjectionKey, type Ref } from 'vue'
import { createTranslator, type Locale, type MessageTable } from '@auditcore/bpmn-flowaudit/ui'

export type { Locale, MessageTable } from '@auditcore/bpmn-flowaudit/ui'

export interface I18n {
  locale: Ref<Locale>
  t: (key: string, params?: Record<string, string | number>) => string
}

const KEY: InjectionKey<I18n> = Symbol('flowaudit-i18n')

export function createI18n(locale: Locale = 'de', overrides: Partial<Record<Locale, MessageTable>> = {}): I18n {
  const current = ref<Locale>(locale)
  const translate = computed(() => createTranslator(current.value, overrides))
  return { locale: current, t: (key, params) => translate.value(key, params) }
}

export function provideI18n(i18n: I18n): I18n {
  provide(KEY, i18n)
  return i18n
}

/** Injected i18n, or a German default when used standalone. */
export function useI18n(): I18n {
  return inject(KEY, null) ?? createI18n('de')
}
