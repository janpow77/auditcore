/**
 * Anzeige der Bestandsprüfung für Vue und React (reine Funktionen): Zuordnung,
 * Regelübersicht, Befunde mit betroffenen Belegen, Kennzahlen. Texte nur aus
 * `batchchecksMessages`.
 */
import { intlFormatNumber as formatNumber, intlFormatPercent as formatPercent } from '@auditcore/common'
import type { Locale, Translate } from '../i18n'
import type { TableImportData } from '../tabular'
import type { BatchchecksData } from './controller'
import type { BatchchecksMessageKey } from './messages'
import type { BatchchecksAnswer, BatchchecksFinding, BatchchecksLevel, BatchchecksRuleResult } from './types'

export type BatchchecksTranslate = Translate<BatchchecksMessageKey>
export type BatchchecksTone = 'success' | 'warning' | 'danger' | 'neutral'

/** Höchstzahl aufgezählter Belege je Befund. */
export const BATCHCHECKS_LISTED_DOCUMENTS = 10

const LEVEL_TONES: Readonly<Record<BatchchecksLevel, BatchchecksTone>> = { info: 'neutral', warning: 'warning', blocker: 'danger' }

export function batchchecksLevelText(level: BatchchecksLevel | null, t: BatchchecksTranslate): string {
  return level ? t(`level${level}`) : ''
}

export function batchchecksLevelTone(level: BatchchecksLevel | null): BatchchecksTone {
  return level ? LEVEL_TONES[level] : 'success'
}

/** Eine Tabelle ist geladen (und keine JSON-Datei). */
export function batchchecksHasTable(state: BatchchecksData, table: TableImportData): boolean {
  return state.json === null && (table.table?.header.length ?? 0) > 0
}

/** Kurzbeschreibung der eingelesenen Datei. */
export function batchchecksSourceText(state: BatchchecksData, table: TableImportData, t: BatchchecksTranslate): string {
  if (state.json) return t('jsonSummary', { file: state.jsonName, count: state.json.length })
  return table.table ? t('tableSummary', { file: table.filename, rows: table.table.rows.length }) : ''
}

export interface BatchchecksColumnField {
  name: string
  label: string
  value: number | null
}

/** Auswahlfelder der Spaltenzuordnung in der Reihenfolge des Katalogs. */
export function batchchecksColumnFields(state: BatchchecksData): BatchchecksColumnField[] {
  return (state.catalogue?.fields ?? []).map((field) => ({ name: field.name, label: field.label, value: state.mapping[field.name] ?? null }))
}

export interface BatchchecksRuleRow {
  code: string
  title: string
  checks: string
  basis: string
  supplement: boolean
  status: string
  tone: BatchchecksTone
  note: string
}

function ruleStatus(rule: BatchchecksRuleResult, t: BatchchecksTranslate): string {
  if (rule.status === 'findings') return t('statusfindings', { count: rule.findings, documents: rule.documents })
  return t(`status${rule.status}`)
}

function ruleTone(rule: BatchchecksRuleResult): BatchchecksTone {
  if (rule.status === 'findings') return batchchecksLevelTone(rule.level)
  return rule.status === 'passed' ? 'success' : 'neutral'
}

/** Regelübersicht: alle Regeln mit Status, auch ohne Befund und nicht geprüfte. */
export function batchchecksRuleRows(answer: BatchchecksAnswer, t: BatchchecksTranslate): BatchchecksRuleRow[] {
  return answer.rules.map((rule) => ({
    code: rule.code,
    title: rule.title,
    checks: rule.checks,
    basis: rule.legal_basis,
    supplement: rule.code.startsWith('ERG-'),
    status: ruleStatus(rule, t),
    tone: ruleTone(rule),
    note: rule.note ?? '',
  }))
}

/** Regeln mit Befunden für die Filterauswahl. */
export function batchchecksFilterOptions(answer: BatchchecksAnswer): { code: string; label: string }[] {
  return answer.rules.filter((rule) => rule.findings > 0).map((rule) => ({ code: rule.code, label: `${rule.code} ${rule.title} (${rule.findings})` }))
}

/** Betroffene Belege als Kennungen (höchstens zehn, dann „… und n weitere“); ohne Belege „Gesamtbestand“. */
export function batchchecksAffectedText(finding: BatchchecksFinding, answer: BatchchecksAnswer, t: BatchchecksTranslate): string {
  if (!finding.documents.length) return t('inventoryWide')
  const refs = finding.documents.slice(0, BATCHCHECKS_LISTED_DOCUMENTS).map((index) => answer.documents[index]?.ref ?? String(index + 1))
  const rest = finding.documents.length - refs.length
  return rest > 0 ? `${refs.join(', ')} ${t('more', { count: rest })}` : refs.join(', ')
}

export interface BatchchecksFindingRow {
  id: string
  rule: string
  level: string
  tone: BatchchecksTone
  message: string
  affected: string
  basis: string
}

/** Befunde (wahlweise einer Regel) mit Begründung und betroffenen Belegen. */
export function batchchecksFindingRows(answer: BatchchecksAnswer, ruleFilter: string | null, t: BatchchecksTranslate): BatchchecksFindingRow[] {
  return answer.findings
    .filter((finding) => ruleFilter === null || finding.rule === ruleFilter)
    .map((finding) => ({
      id: finding.id,
      rule: finding.rule,
      level: batchchecksLevelText(finding.level, t),
      tone: batchchecksLevelTone(finding.level),
      message: finding.message,
      affected: batchchecksAffectedText(finding, answer, t),
      basis: finding.rule_reference,
    }))
}

export function batchchecksSummaryText(answer: BatchchecksAnswer, t: BatchchecksTranslate): string {
  const { documents, findings, documents_with_findings: affected } = answer.summary
  return t('summary', { documents, findings, affected })
}

const percent = (value: number | null, locale: Locale, t: BatchchecksTranslate): string => (value === null ? t('noValue') : formatPercent(value, locale, 1))

/** Kennzahlen der Extraktionsqualität (C-12). */
export function batchchecksMetricRows(answer: BatchchecksAnswer, t: BatchchecksTranslate, locale: Locale): { label: string; value: string }[] {
  const m = answer.metrics
  return [
    { label: t('metricMandatory'), value: percent(m.mandatory_fields_success_rate, locale, t) },
    { label: t('metricFormal'), value: percent(m.formal_correctness_rate, locale, t) },
    { label: t('metricErrors'), value: `${formatNumber(m.documents_with_errors, locale)} (${percent(m.documents_with_errors_rate, locale, t)})` },
    { label: t('metricOcrAvg'), value: percent(m.avg_ocr_confidence, locale, t) },
    { label: t('metricOcrMin'), value: percent(m.min_ocr_confidence, locale, t) },
  ]
}
