/**
 * Message lookup of the editor UI: German is the default, English is
 * prepared. `t(key, params)` fills `{name}` placeholders and falls back to
 * the key; applications may add or override messages per language.
 */

import { MESSAGES_DE } from './messages.de'
import { MESSAGES_EN } from './messages.en'

export type Locale = 'de' | 'en'
export type MessageTable = Record<string, string>
export type Translate = (key: string, params?: Record<string, string | number>) => string

const TABLES: Record<Locale, MessageTable> = { de: MESSAGES_DE, en: MESSAGES_EN }

export function messageTable(locale: Locale, overrides: Partial<Record<Locale, MessageTable>> = {}): MessageTable {
  return { ...MESSAGES_DE, ...TABLES[locale], ...(overrides[locale] ?? {}) }
}

export function createTranslator(locale: Locale = 'de', overrides: Partial<Record<Locale, MessageTable>> = {}): Translate {
  const table = messageTable(locale, overrides)
  return (key, params = {}) => (table[key] ?? key).replace(/\{(\w+)\}/g, (match, name: string) => (params[name] === undefined ? match : String(params[name])))
}
