/**
 * Übersetzungsdienst `translate` (Signatur wie in diagram-js):
 * `translate(template, replacements)` ersetzt die englische Vorlage durch
 * die deutsche Fassung und füllt `{platzhalter}`.
 */

import { translations } from './translations'

export type Translate = (template: string, replacements?: Record<string, unknown>) => string

function fill(text: string, replacements?: Record<string, unknown>): string {
  const values = replacements || {}
  return text.replace(/{([^}]+)}/g, (match, key: string) => {
    const value = values[key]
    return value === undefined || value === null ? match : String(value)
  })
}

export function createTranslate(locale: 'de' | 'en' = 'de', extra: Record<string, string> = {}): Translate {
  const table: Record<string, string> = locale === 'de' ? { ...translations, ...extra } : { ...extra }
  return (template, replacements) => fill(table[template] ?? template, replacements)
}

export function translateModule(locale: 'de' | 'en' = 'de') {
  return {
    translate: ['value', createTranslate(locale)],
  }
}
