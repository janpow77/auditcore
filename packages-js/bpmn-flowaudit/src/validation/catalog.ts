/**
 * Catalogue of validation rules: stable ids, severity and messages (de/en).
 *
 * Identical to the rule catalogue of `auditcore_bpmn` (same ids, same
 * texts), so issues from the UI and from the server read alike. The rows
 * are generated (`scripts/generate_rule_catalog.py`); a test compares the
 * ids with the Python package when it is present.
 */

import { ROWS } from './catalogRows'

export type Severity = 'fehler' | 'warnung' | 'hinweis'
export type RuleGroup = 'structure' | 'content' | 'audit_authority' | 'segregation' | 'collection'

export interface Rule {
  id: string
  severity: Severity
  group: RuleGroup
  de: string
  en: string
}

export const SEVERITY_LABELS: Record<Severity, { de: string; en: string }> = {
  fehler: { de: 'Fehler', en: 'Error' },
  warnung: { de: 'Warnung', en: 'Warning' },
  hinweis: { de: 'Hinweis', en: 'Note' },
}

export const RULES: Record<string, Rule> = Object.fromEntries(
  ROWS.map(([id, severity, group, de, en]) => [id, { id, severity, group, de, en } as Rule]),
)

/** Message of a rule; parameters `name_de`/`name_en` override `name`. */
export function ruleText(rule: Rule, locale: 'de' | 'en', params: Record<string, unknown>): string {
  const template = locale === 'en' ? rule.en : rule.de
  const suffix = locale === 'en' ? '_en' : '_de'
  const values: Record<string, unknown> = { ...params }
  for (const [key, value] of Object.entries(params)) {
    if (key.endsWith(suffix)) values[key.slice(0, -suffix.length)] = value
  }
  return template.replace(/\{(\w+)\}/g, (match, key: string) => (values[key] === undefined ? match : String(values[key])))
}
