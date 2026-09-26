/**
 * Anzeige der Belegerkennung für Vue und React (reine Funktionen): Profile,
 * Feld- und Befundzeilen, Konfidenzen, Status. Texte nur aus `extractionMessages`.
 */
import { intlFormatNumber as formatNumber, intlFormatPercent as formatPercent } from '@auditcore/common'
import type { Locale, Translate } from '../i18n'
import { extractionMessages, type ExtractionMessageKey } from './messages'
import type { ExtractedField, ExtractionCatalogue, ExtractionProfile, ExtractionRun, ExtractionJson, ExtractionFinding } from './types'

export type ExtractionTranslate = Translate<ExtractionMessageKey>
export type ExtractionTone = 'success' | 'warning' | 'danger' | 'neutral'

const KNOWN = new Set<string>(Object.keys(extractionMessages.de))

function known(key: string): ExtractionMessageKey | null {
  return KNOWN.has(key) ? (key as ExtractionMessageKey) : null
}

/** Dateigröße in MiB (bzw. KiB unter 1 MiB). */
export function extractionSizeText(bytes: number, locale: Locale): string {
  if (bytes < 1024 * 1024) return `${formatNumber(Math.ceil(bytes / 1024), locale)} KiB`
  return `${formatNumber(bytes / (1024 * 1024), locale, { maximumFractionDigits: 1 })} MiB`
}

export function extractionProfileText(profile: ExtractionProfile, t: ExtractionTranslate): string {
  if (!profile.available) return t('unavailable', { label: profile.label })
  return profile.recommended ? t('recommended', { label: profile.label }) : profile.label
}

export function extractionFieldLabel(name: string, t: ExtractionTranslate): string {
  const key = known(`field_${name}`)
  return key ? t(key) : name
}

export function extractionRuleLabel(finding: ExtractionFinding, t: ExtractionTranslate): string {
  const key = known(`rule_${finding.rule_id}`)
  return key ? t(key) : finding.rule_name || finding.rule_id
}

/** Wert eines Feldes als Text (Zahlen sprachabhängig, Listen mit Komma). */
export function extractionValueText(value: ExtractionJson, locale: Locale): string {
  if (value === null || value === '') return ''
  if (typeof value === 'number') return formatNumber(value, locale, { maximumFractionDigits: 2 })
  if (typeof value === 'string' || typeof value === 'boolean') return String(value)
  return JSON.stringify(value)
}

export function extractionConfidenceText(value: number | null, locale: Locale): string {
  return value === null ? '' : formatPercent(value, locale, 0)
}

/** Ton einer Feldkonfidenz gegen den Schwellwert des Profils. */
export function extractionConfidenceTone(value: number | null, threshold: number | null): ExtractionTone {
  if (value === null) return 'neutral'
  return threshold === null || value >= threshold ? 'success' : 'warning'
}

export function extractionDecisionText(field: ExtractedField, t: ExtractionTranslate): string {
  if (!field.decision) return ''
  const key = known(`decision${field.decision}`)
  return key ? t(key) : field.decision
}

export function extractionDecisionTone(field: ExtractedField): ExtractionTone {
  if (field.decision === 'accepted') return 'success'
  if (field.decision === 'rejected' || field.decision === 'disagreement') return 'danger'
  return field.decision ? 'warning' : 'neutral'
}

export function extractionStatusText(result: ExtractionRun, t: ExtractionTranslate): string {
  const key = known(`status${result.run.status}`)
  return key ? t(key) : t('statusOther', { status: result.run.status })
}

export function extractionStatusTone(result: ExtractionRun): ExtractionTone {
  const status = result.run.status
  if (status === 'ok') return 'success'
  return status === 'review_needed' ? 'warning' : 'danger'
}

export function extractionDocumentText(result: ExtractionRun, t: ExtractionTranslate): string {
  const { filename, mime_type, page_count } = result.document
  const pages = page_count === null ? t('noValue') : t('pages', { count: page_count })
  return t('documentValue', { file: filename || t('noValue'), type: mime_type ?? t('noValue'), pages })
}

export function extractionOcrText(result: ExtractionRun, t: ExtractionTranslate, locale: Locale): string {
  const ocr = result.ocr
  if (!ocr) return t('noValue')
  const avg = formatPercent(ocr.avg_confidence, locale, 0)
  return `${t('ocrValue', { engine: ocr.engine, avg, min: formatPercent(ocr.min_confidence, locale, 0) })} – ${t(`quality${ocr.quality}`)}`
}

const OUTCOME_ORDER: Readonly<Record<string, number>> = { FAIL: 0, REVIEW: 1, PASS: 2 }
const SEVERITY_ORDER: Readonly<Record<string, number>> = { CRITICAL: 0, WARN: 1, INFO: 2 }

/** Auffällige Befunde (nicht bestanden, prüfen) zuerst nach Gewicht; bestandene getrennt. */
export function splitExtractionFindings(findings: readonly ExtractionFinding[]): { open: ExtractionFinding[]; passed: ExtractionFinding[] } {
  const rank = (entry: ExtractionFinding): number => (OUTCOME_ORDER[entry.outcome] ?? 3) * 10 + (SEVERITY_ORDER[entry.severity] ?? 3)
  const sorted = [...findings].sort((a, b) => rank(a) - rank(b))
  return { open: sorted.filter((entry) => entry.outcome !== 'PASS'), passed: sorted.filter((entry) => entry.outcome === 'PASS') }
}

export function extractionOutcomeTone(finding: ExtractionFinding): ExtractionTone {
  if (finding.outcome === 'PASS') return 'success'
  return finding.outcome === 'FAIL' && finding.severity === 'CRITICAL' ? 'danger' : 'warning'
}

/** Schwellwert der Feldkonfidenz des gelaufenen Profils (nur Donut). */
export function extractionFieldThreshold(catalogue: ExtractionCatalogue | null, result: ExtractionRun): number | null {
  return catalogue?.profiles.find((entry) => entry.id === result.profile.id)?.min_field_confidence ?? null
}

/** Dateiauswahl der Oberfläche (`accept`) aus den zulässigen Typen. */
export function extractionAccept(catalogue: ExtractionCatalogue | null): string {
  const types = catalogue?.accepted_types ?? []
  return [...types, ...(types.includes('application/pdf') ? ['.pdf'] : [])].join(',')
}

/** Donut-Vorschlag, wenn er nicht übernommen wurde (sonst leer). */
export function extractionProposalText(field: ExtractedField, t: ExtractionTranslate, locale: Locale): string {
  if (!field.decision || field.decision === 'accepted' || field.proposal === null) return ''
  const text = extractionValueText(field.proposal, locale)
  return text ? t('proposal', { value: text }) : ''
}

/** Meldung zur Prüfung vor dem Senden. */
export function extractionValidationText(validation: 'needFile' | 'tooLarge' | 'profile', catalogue: ExtractionCatalogue | null, t: ExtractionTranslate, locale: Locale): string {
  if (validation !== 'tooLarge') return t(`error${validation}`)
  return t('errortooLarge', { size: extractionSizeText(catalogue?.limits.max_upload_bytes ?? 0, locale) })
}
