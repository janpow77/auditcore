/** Framework-freie Anfrage- und Anzeigelogik von „Kennung prüfen“ (Vue und React). */
import { recordsToCsv, type ParsedTable } from '@flowaudit/common'
import type { Translate } from '../i18n'
import type { IdentifierMessageKey } from './messages'
import type {
  IdentifierBatchAnswer,
  IdentifierBatchItem,
  IdentifierBatchRequest,
  IdentifierBatchRow,
  IdentifierCheckRequest,
  IdentifierDetailValue,
  IdentifierCatalogue,
  IdentifierKindInfo,
  IdentifierProfileInfo,
  IdentifierResult,
  IdentifierStatus,
} from './types'

export type IdentifierTranslate = Translate<IdentifierMessageKey>
export type IdentifierError = 'kind' | 'profile' | 'noTable' | 'noRows' | 'tooMany' | 'kindColumn'
export type IdentifierValidation<R> = { ok: true; request: R } | { ok: false; error: IdentifierError }

export function findIdentifierProfile(catalogue: IdentifierCatalogue | null, id: string | null): IdentifierProfileInfo | null {
  return catalogue?.profiles.find((entry) => entry.id === id) ?? null
}

/** Kennungsarten, die das gewählte Profil prüft (ohne Profil: keine). */
export function identifierProfileKinds(catalogue: IdentifierCatalogue | null, profileId: string | null): IdentifierKindInfo[] {
  const profile = findIdentifierProfile(catalogue, profileId)
  return profile && catalogue ? catalogue.kinds.filter((kind) => profile.kinds.includes(kind.id)) : []
}

/** Anzeige eines Profils in der Auswahl: Empfehlung und Altverhalten sichtbar. */
export function identifierProfileLabel(catalogue: IdentifierCatalogue, profile: IdentifierProfileInfo, t: IdentifierTranslate): string {
  if (profile.id === catalogue.recommended_profile) return t('recommended', { label: profile.title })
  return profile.legacy ? t('legacy', { label: profile.title }) : profile.title
}

export function kindNeedsCountry(catalogue: IdentifierCatalogue | null, kind: string | null): boolean {
  return catalogue?.kinds.find((entry) => entry.id === kind)?.country === true
}

function country(text: string | null | undefined): string | null {
  const trimmed = (text ?? '').trim().toUpperCase()
  return trimmed === '' ? null : trimmed
}

export interface IdentifierCheckInput {
  catalogue: IdentifierCatalogue
  profile: string | null
  kind: string | null
  value: string
  country: string
}

/** Anfrage für `POST /check`; Profil und Kennungsart sind Pflicht, ein leerer Wert ergibt „fehlt“. */
export function buildIdentifierCheck(input: IdentifierCheckInput): IdentifierValidation<IdentifierCheckRequest> {
  if (!findIdentifierProfile(input.catalogue, input.profile)) return { ok: false, error: 'profile' }
  if (!input.kind || !identifierProfileKinds(input.catalogue, input.profile).some((kind) => kind.id === input.kind)) return { ok: false, error: 'kind' }
  const request: IdentifierCheckRequest = { kind: input.kind, value: input.value.trim() === '' ? null : input.value, profile: input.profile as string }
  const land = kindNeedsCountry(input.catalogue, input.kind) ? country(input.country) : null
  return { ok: true, request: land ? { ...request, country: land } : request }
}

/** Kennungsart aus einer Tabellenzelle: Kennung oder Bezeichnung des Katalogs, sonst unverändert (Server meldet sie). */
export function resolveIdentifierKind(catalogue: IdentifierCatalogue, cell: string): string {
  const text = cell.trim().toLowerCase()
  const found = catalogue.kinds.find((kind) => kind.id === text || kind.label.toLowerCase() === text)
  return found ? found.id : cell.trim()
}

export interface IdentifierBatchMapping {
  table: ParsedTable | null
  hasHeader: boolean
  valueColumn: number
  refColumn: number | null
  /** Kennungsart für alle Zeilen; `null` = aus `kindColumn`. */
  kind: string | null
  kindColumn: number | null
  countryColumn: number | null
}

function batchItem(catalogue: IdentifierCatalogue, mapping: IdentifierBatchMapping, row: readonly string[], index: number): IdentifierBatchItem {
  const cell = (column: number | null): string => (column === null ? '' : (row[column] ?? ''))
  const value = cell(mapping.valueColumn)
  const line = index + (mapping.hasHeader ? 2 : 1)
  const kind = mapping.kind ?? resolveIdentifierKind(catalogue, cell(mapping.kindColumn))
  const item: IdentifierBatchItem = { ref: mapping.refColumn === null ? String(line) : cell(mapping.refColumn), kind, value: value.trim() === '' ? null : value }
  const land = mapping.countryColumn === null ? null : country(cell(mapping.countryColumn))
  return land ? { ...item, country: land } : item
}

/** Anfrage für `POST /check/batch` aus der geladenen Tabelle und der Spaltenzuordnung. */
export function buildIdentifierBatch(catalogue: IdentifierCatalogue, profile: string | null, mapping: IdentifierBatchMapping): IdentifierValidation<IdentifierBatchRequest> {
  if (!findIdentifierProfile(catalogue, profile)) return { ok: false, error: 'profile' }
  if (!mapping.table) return { ok: false, error: 'noTable' }
  if (mapping.table.rows.length === 0) return { ok: false, error: 'noRows' }
  if (mapping.table.rows.length > catalogue.limits.max_items) return { ok: false, error: 'tooMany' }
  if (mapping.kind === null && mapping.kindColumn === null) return { ok: false, error: 'kindColumn' }
  const items = mapping.table.rows.map((row, index) => batchItem(catalogue, mapping, row, index))
  return { ok: true, request: { profile: profile as string, items } }
}

export function identifierErrorKey(error: IdentifierError): IdentifierMessageKey {
  return `error${error}`
}

export type IdentifierTone = 'success' | 'danger' | 'warning' | 'neutral'

const TONES: Readonly<Record<IdentifierStatus, IdentifierTone>> = { VALID: 'success', INVALID: 'danger', MISSING: 'warning' }

export function identifierStatusTone(status: IdentifierStatus | null): IdentifierTone {
  return status ? TONES[status] : 'neutral'
}

export function identifierStatusText(status: IdentifierStatus | null, t: IdentifierTranslate): string {
  return status ? t(`status${status}`) : t('notChecked')
}

/** Begründung eines Ergebnisses: Meldung der Bibliothek, bei „gültig“ der Satz zum Profil. */
export function identifierReasonText(result: IdentifierResult, profileTitle: string, t: IdentifierTranslate): string {
  if (result.message) return result.message
  return result.status === 'VALID' ? t('validText', { profile: profileTitle }) : (result.reason_label ?? '')
}

function detailValue(catalogue: IdentifierCatalogue, value: IdentifierDetailValue, t: IdentifierTranslate): string {
  if (value === null) return '—'
  if (typeof value === 'boolean') return t(value ? 'yes' : 'no')
  return catalogue.value_labels[String(value)] ?? String(value)
}

/** Einzelheiten (`details`) mit deutschen Bezeichnungen aus dem Katalog. */
export function identifierFacts(catalogue: IdentifierCatalogue, result: IdentifierResult, t: IdentifierTranslate): { key: string; label: string; value: string }[] {
  return Object.entries(result.details).map(([key, value]) => ({
    key,
    label: catalogue.detail_labels[key] ?? key,
    value: detailValue(catalogue, value, t),
  }))
}

/** Status einer Stapelzeile; `null` = nicht prüfbar. */
export function identifierRowStatus(row: IdentifierBatchRow): IdentifierStatus | null {
  return row.error === null ? row.status : null
}

/** Begründung einer Stapelzeile; gültige Zeilen nur mit eigener Meldung der Bibliothek (Tabelle bleibt knapp). */
export function identifierRowReason(row: IdentifierBatchRow): string {
  if (row.error !== null) return row.error.message
  return row.message || (row.status === 'VALID' ? '' : (row.reason_label ?? ''))
}

export function identifierRowKind(catalogue: IdentifierCatalogue, row: IdentifierBatchRow, request: IdentifierBatchRequest | null): string {
  if (row.error === null) return row.kind_label
  const kind = request?.items[row.index]?.kind ?? ''
  return catalogue.kinds.find((entry) => entry.id === kind)?.label ?? kind
}

export function identifierRowValue(row: IdentifierBatchRow, request: IdentifierBatchRequest | null): string {
  return row.error === null ? (row.raw ?? '') : (request?.items[row.index]?.value ?? '')
}

/** Zeilen der Ergebnistabelle; wahlweise nur ungültige, fehlende und nicht prüfbare. */
export function visibleIdentifierRows(answer: IdentifierBatchAnswer, onlyIssues: boolean): readonly IdentifierBatchRow[] {
  return onlyIssues ? answer.results.filter((row) => identifierRowStatus(row) !== 'VALID') : answer.results
}

export function identifierBatchSummary(answer: IdentifierBatchAnswer, t: IdentifierTranslate): string {
  const { total, valid, invalid, missing, not_checked: notChecked } = answer.summary
  return t('summary', { total, valid, invalid, missing, notChecked })
}

/** Anzeigezeile der Stapelprüfung (Tabelle und CSV). */
export interface IdentifierBatchLine {
  key: number
  ref: string
  kind: string
  value: string
  status: string
  tone: IdentifierTone
  reason: string
  normalized: string
}

export function identifierBatchLines(
  catalogue: IdentifierCatalogue,
  answer: IdentifierBatchAnswer,
  request: IdentifierBatchRequest | null,
  onlyIssues: boolean,
  t: IdentifierTranslate,
): IdentifierBatchLine[] {
  return visibleIdentifierRows(answer, onlyIssues).map((row) => ({
    key: row.index,
    ref: row.ref,
    kind: identifierRowKind(catalogue, row, request),
    value: identifierRowValue(row, request),
    status: identifierStatusText(identifierRowStatus(row), t),
    tone: identifierStatusTone(identifierRowStatus(row)),
    reason: identifierRowReason(row),
    normalized: row.error === null ? (row.normalized ?? '') : '',
  }))
}

/** CSV (Excel-DE) der Stapelprüfung mit denselben Spalten wie die Tabelle (alle Zeilen). */
export function identifierBatchCsv(catalogue: IdentifierCatalogue, answer: IdentifierBatchAnswer, request: IdentifierBatchRequest | null, t: IdentifierTranslate): string {
  return recordsToCsv(identifierBatchLines(catalogue, answer, request, false, t), [
    { label: t('colRef'), value: 'ref' },
    { label: t('colKind'), value: 'kind' },
    { label: t('colValue'), value: 'value' },
    { label: t('colStatus'), value: 'status' },
    { label: t('colReason'), value: 'reason' },
    { label: t('colNormalized'), value: 'normalized' },
  ])
}

export type IdentifierColumn = 'value' | 'kind' | 'ref' | 'country'

export interface IdentifierColumnField {
  id: IdentifierColumn
  label: IdentifierMessageKey
  value: number | null
  /** Text der leeren Auswahl: „keine“ bei optionalen Spalten, „Bitte wählen“ bei der Spalte mit Kennungsart. */
  placeholder: IdentifierMessageKey | null
}

/** Spaltenauswahl der Stapelprüfung; die Spalte mit Kennungsart nur ohne feste Art. */
export function identifierColumnFields(mapping: IdentifierBatchMapping): IdentifierColumnField[] {
  const field = (id: IdentifierColumn, label: IdentifierMessageKey, value: number | null, placeholder: IdentifierMessageKey | null): IdentifierColumnField => ({
    id, label, value, placeholder,
  })
  return [
    field('value', 'valueColumn', mapping.valueColumn, null),
    ...(mapping.kind === null ? [field('kind', 'kindColumn', mapping.kindColumn, 'choose')] : []),
    field('ref', 'refColumn', mapping.refColumn, 'none'),
    field('country', 'countryColumn', mapping.countryColumn, 'none'),
  ]
}
