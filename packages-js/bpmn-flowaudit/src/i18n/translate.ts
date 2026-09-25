/**
 * Translation service for diagram-js (`translate`) with the same behaviour
 * as `deutschTranslate` of the audit_designer: unknown strings stay
 * unchanged (a new core version yields at worst English, never empty
 * labels), placeholders `{name}` are filled afterwards.
 */

import type { Translate } from '../diagram/services'
import { LEGACY_TRANSLATIONS } from './legacyTranslations'
import { MESSAGES_DE } from './messagesDe'
import { MESSAGES_EN } from './messagesEn'

export type Messages = Record<string, string>

export const MESSAGES: Record<'de' | 'en', Messages> = { de: MESSAGES_DE, en: MESSAGES_EN }

export function fillPlaceholders(text: string, replacements: Record<string, string> = {}): string {
  return text.replace(/{([^}]+)}/g, (match, key: string) => (replacements[key] === undefined ? match : String(replacements[key])))
}

/**
 * Creates a translate function. Tables are merged in order: core table
 * (optional), legacy audit_designer table (German only), FlowAudit messages,
 * application overrides.
 */
export function createTranslator(locale: 'de' | 'en' = 'de', ...tables: Messages[]): Translate {
  const merged: Messages = Object.assign({}, locale === 'de' ? LEGACY_TRANSLATIONS : {}, MESSAGES[locale], ...tables)
  return (template, replacements) => fillPlaceholders(merged[template] ?? template, replacements)
}

/** Legacy API: German translation (`deutschTranslate`). */
export const germanTranslate: Translate = createTranslator('de')

/** diagram-js module replacing `translate` (legacy `deutschModul`). */
export function translateModule(locale: 'de' | 'en' = 'de', ...tables: Messages[]): Record<string, unknown> {
  return { translate: ['value', createTranslator(locale, ...tables)] }
}
