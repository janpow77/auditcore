/**
 * Formular und Anzeige der Merkmalsstichprobe (reine Funktionen für Vue und
 * React): Prüfung der Eingaben, Aufbau der Anfrage, Kennzahlen und Herleitung.
 */
import { intlFormatNumber as formatNumber, intlFormatPercent as formatPercent, type TableColumn, type TableRow } from '@auditcore/common'
import type { BadgeTone } from '../base/types'
import type { Locale, Translate } from '../i18n'
import { parseInput } from '../sampling/model'
import type { AttributesMessageKey } from './messages'
import type { AttributeApproach, AttributesCatalogue, AttributesConclusion, AttributesRequest, AttributesResult } from './types'

export type AttributesTranslate = Translate<AttributesMessageKey>

export interface AttributesForm {
  approach: AttributeApproach
  deviations: string
  sampleSize: string
  confidence: number | null
  profileId: string | null
  /** Tolerierbare bzw. kritische Quote in Prozent. */
  rate: string
}

export type AttributesIssue = 'required' | 'invalid' | 'range'
export type AttributesIssues = Readonly<Record<string, AttributesIssue>>
export type AttributesValidation = { ok: true; request: AttributesRequest } | { ok: false; issues: AttributesIssues }

export const EMPTY_ATTRIBUTES_FORM: AttributesForm = { approach: 'normal', deviations: '', sampleSize: '', confidence: null, profileId: null, rate: '' }

const APPROACHES: readonly AttributeApproach[] = ['normal', 'discovery', 'stop_or_go']

export function attributesApproachChoices(t: AttributesTranslate): { id: AttributeApproach; label: string }[] {
  return APPROACHES.map((id) => ({ id, label: t(`approach${id}`) }))
}

function whole(text: string, minimum: number): number | AttributesIssue {
  const value = parseInput(text)
  if (value === null) return 'required'
  if (value === undefined || !Number.isInteger(value)) return 'invalid'
  return value < minimum ? 'range' : value
}

function percent(text: string): number | AttributesIssue {
  const value = parseInput(text)
  if (value === null) return 'required'
  if (value === undefined) return 'invalid'
  return value <= 0 || value >= 100 ? 'range' : value / 100
}

function selectionIssues(form: AttributesForm, issues: Record<string, AttributesIssue>): void {
  if (form.confidence === null) issues.confidence = 'required'
  if (form.approach === 'normal' && form.profileId === null) issues.profileId = 'required'
}

/** Anfrage für `POST /attributes`; bei Befunden die Feldschlüssel mit ihrem Fehler. */
export function buildAttributesRequest(form: AttributesForm): AttributesValidation {
  const issues: Record<string, AttributesIssue> = {}
  const take = (key: string, value: number | AttributesIssue): number => {
    if (typeof value === 'number') return value
    issues[key] = value
    return 0
  }
  const size = take('sampleSize', whole(form.sampleSize, 1))
  const deviations = take('deviations', whole(form.deviations, 0))
  if (!issues.sampleSize && !issues.deviations && deviations > size) issues.deviations = 'range'
  const rate = take('rate', percent(form.rate))
  selectionIssues(form, issues)
  if (Object.keys(issues).length || form.confidence === null) return { ok: false, issues }
  const request: AttributesRequest = { approach: form.approach, deviations, sample_size: size, confidence_level: form.confidence, tolerable_rate: rate }
  const profile = form.approach === 'normal' && form.profileId ? { factor_profile: form.profileId } : {}
  return { ok: true, request: { ...request, ...profile } }
}

export function attributesConfidenceChoices(catalogue: AttributesCatalogue | null): readonly number[] {
  return catalogue?.confidence_levels.z ?? []
}

export function attributesPercent(value: number, locale: Locale): string {
  return formatPercent(value, locale, 2)
}

export function attributesIssueKey(issue: AttributesIssue): AttributesMessageKey {
  return issue === 'required' ? 'issueRequired' : issue === 'invalid' ? 'issueInvalid' : 'issueRange'
}

const TONES: Readonly<Record<AttributesConclusion, BadgeTone>> = {
  supported: 'success', criterion_met: 'success', stop: 'success', not_supported: 'danger', deviation_found: 'danger', go: 'warning',
}

export function attributesConclusionTone(conclusion: AttributesConclusion): BadgeTone {
  return TONES[conclusion]
}

export interface AttributesMetric {
  id: string
  label: string
  value: string
}

export function attributesMetrics(result: AttributesResult, t: AttributesTranslate, locale: Locale): AttributesMetric[] {
  const outcome = result.attributes
  const metrics: AttributesMetric[] = [{ id: 'rate', label: t('rate'), value: attributesPercent(outcome.rate, locale) }]
  if (outcome.precision !== undefined) metrics.push({ id: 'precision', label: t('precision'), value: attributesPercent(outcome.precision, locale) })
  metrics.push({ id: 'upper', label: t('upperLimit'), value: attributesPercent(outcome.upper_limit, locale) })
  const threshold = outcome.tolerable_rate ?? outcome.threshold
  if (threshold !== undefined) metrics.push({ id: 'threshold', label: t('threshold'), value: attributesPercent(threshold, locale) })
  return metrics
}

export function attributesStepColumns(t: AttributesTranslate, locale: Locale): TableColumn[] {
  return [
    { key: 'label', label: t('colStep') },
    { key: 'formula', label: t('colFormula') },
    { key: 'value', label: t('colValue'), align: 'end', format: (value) => (typeof value === 'number' ? formatNumber(value, locale, { maximumFractionDigits: 6 }) : '') },
    { key: 'source', label: t('colSource') },
  ]
}

export function attributesStepRows(result: AttributesResult): TableRow[] {
  return result.attributes.steps.map((step, index) => ({ id: index + 1, ...step }))
}

export const ATTRIBUTE_FIELDS: readonly { key: 'deviations' | 'sampleSize' | 'rate'; numeric: true }[] = [
  { key: 'sampleSize', numeric: true },
  { key: 'deviations', numeric: true },
  { key: 'rate', numeric: true },
]

export function attributesFieldLabel(key: 'deviations' | 'sampleSize' | 'rate', approach: AttributeApproach, t: AttributesTranslate): string {
  if (key === 'rate') return t(approach === 'discovery' ? 'critical' : 'tolerable')
  return t(key)
}

export function attributesFormMessage(issues: AttributesIssues, t: AttributesTranslate): string {
  return Object.keys(issues).length ? t('formIncomplete') : ''
}
