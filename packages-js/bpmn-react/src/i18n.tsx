/**
 * i18n of the React editor: German is the default, English is prepared. The
 * texts and the lookup come from the framework-free UI core (same tables as
 * the Vue editor); applications may add or override messages.
 */

import { createContext, useContext, useMemo, type ReactNode } from 'react'
import { createTranslator, type Locale, type MessageTable, type Translate } from '@auditcore/bpmn-flowaudit/ui'

export interface I18n {
  locale: Locale
  t: Translate
}

const DEFAULT: I18n = { locale: 'de', t: createTranslator('de') }
const I18nContext = createContext<I18n | null>(null)

export function createI18n(locale: Locale = 'de', overrides: Partial<Record<Locale, MessageTable>> = {}): I18n {
  return { locale, t: createTranslator(locale, overrides) }
}

export function I18nProvider({ locale = 'de', overrides, children }: { locale?: Locale; overrides?: Partial<Record<Locale, MessageTable>>; children?: ReactNode }) {
  const value = useMemo(() => createI18n(locale, overrides), [locale, overrides])
  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>
}

/** Provided i18n, or German when used standalone. */
export function useI18n(): I18n {
  return useContext(I18nContext) ?? DEFAULT
}
