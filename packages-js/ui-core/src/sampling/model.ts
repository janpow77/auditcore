/**
 * Framework-freie Ansichtslogik des Stichprobenrechners: Eingaben prüfen,
 * Anfragen bilden, Vorschläge aus der Grundgesamtheit, Schichten zählen.
 * Kein Vue, kein DOM – direkt testbar.
 */
import { detectDecimal, parseNumber } from '@auditcore/common'
import type {
  AllocationMethod,
  MethodProfile,
  ParameterSpec,
  PopulationItem,
  SelectionRequest,
  SelectionVariant,
  SizeRequest,
} from './types'

export type FieldErrorCode = 'required' | 'invalid' | 'range'

export interface FieldError {
  code: FieldErrorCode
  min?: number
  max?: number
}

export type SizeValidation =
  | { ok: true; request: SizeRequest }
  | { ok: false; errors: Readonly<Record<string, FieldError>> }

/** Anteile werden in Prozent eingegeben und angezeigt. */
export function isPercent(spec: ParameterSpec): boolean {
  return spec.unit === 'Anteil' && spec.type !== 'choice'
}

/** Eingabetext (deutsch oder englisch notiert) → Zahl; leer → null, unlesbar → undefined. */
export function parseInput(text: string): number | null | undefined {
  return parseNumber(text, detectDecimal([text.trim()], ';'))
}

function lowerBound(spec: ParameterSpec): number | undefined {
  return spec.minimum ?? spec.exclusive_minimum
}

function upperBound(spec: ParameterSpec): number | undefined {
  return spec.maximum ?? spec.exclusive_maximum
}

function inRange(spec: ParameterSpec, value: number): boolean {
  if (spec.minimum !== undefined && value < spec.minimum) return false
  if (spec.exclusive_minimum !== undefined && value <= spec.exclusive_minimum) return false
  if (spec.maximum !== undefined && value > spec.maximum) return false
  return !(spec.exclusive_maximum !== undefined && value >= spec.exclusive_maximum)
}

/** Prüft ein Eingabefeld und liefert den Vertragswert (Prozent → Anteil). */
export function fieldValue(spec: ParameterSpec, text: string): { value: number } | { error: FieldError } {
  const parsed = parseInput(text)
  if (parsed === null) return { error: { code: 'required' } }
  if (parsed === undefined) return { error: { code: 'invalid' } }
  const value = isPercent(spec) ? parsed / 100 : parsed
  if (spec.type === 'integer' && !Number.isInteger(value)) return { error: { code: 'invalid' } }
  if (!inRange(spec, value)) {
    const scale = isPercent(spec) ? 100 : 1
    const min = lowerBound(spec)
    const max = upperBound(spec)
    return {
      error: {
        code: 'range',
        ...(min === undefined ? {} : { min: min * scale }),
        ...(max === undefined ? {} : { max: max * scale }),
      },
    }
  }
  return { value }
}

/** Anfrage für `POST /size`; jedes Feld ist Pflicht, nichts wird still ergänzt. */
export function buildSizeRequest(
  profile: MethodProfile,
  texts: Readonly<Record<string, string>>,
  confidence: number | null,
): SizeValidation {
  const errors: Record<string, FieldError> = {}
  const request: Record<string, number | string> = { method: profile.id }
  for (const spec of profile.parameters) {
    if (spec.type === 'choice') continue
    const result = fieldValue(spec, texts[spec.key] ?? '')
    if ('error' in result) errors[spec.key] = result.error
    else request[spec.key] = result.value
  }
  if (confidence === null) errors.confidence_level = { code: 'required' }
  else request.confidence_level = confidence
  if (Object.keys(errors).length > 0) return { ok: false, errors }
  return { ok: true, request: request as SizeRequest }
}

/** Vorschlagswerte aus der Grundgesamtheit (Summe positiver Werte bzw. Anzahl). */
export function populationSuggestions(items: readonly PopulationItem[]): Readonly<Record<string, number>> {
  const positive = items.reduce((sum, item) => (item.value !== null && item.value > 0 ? sum + item.value : sum), 0)
  return { population_value: Math.round(positive * 100) / 100, population_size: items.length }
}

/** Startwerte der Textfelder: vorgeschlagene Werte der Profile, sonst leer. */
export function initialTexts(profile: MethodProfile, formatter: (value: number) => string): Record<string, string> {
  const texts: Record<string, string> = {}
  for (const spec of profile.parameters) {
    if (spec.suggested === undefined) continue
    texts[spec.key] = formatter(isPercent(spec) ? spec.suggested * 100 : spec.suggested)
  }
  return texts
}

export interface StratumCount {
  stratum: string
  population: number
}

/** Schichten in Reihenfolge ihres ersten Auftretens; leer, wenn kein Element geschichtet ist. */
export function strataOf(items: readonly PopulationItem[]): StratumCount[] {
  const counts = new Map<string, number>()
  for (const item of items) {
    if (item.stratum === undefined || item.stratum === '') continue
    counts.set(item.stratum, (counts.get(item.stratum) ?? 0) + 1)
  }
  return [...counts].map(([stratum, population]) => ({ stratum, population }))
}

/** Teilweise geschichtete Grundgesamtheit (der Server lehnt sie ab). */
export function hasPartialStrata(items: readonly PopulationItem[]): boolean {
  const stratified = items.filter((item) => item.stratum !== undefined && item.stratum !== '').length
  return stratified > 0 && stratified < items.length
}

export interface SelectionInput {
  profile: MethodProfile
  items: readonly PopulationItem[]
  sampleSize: string
  seed: string
  variant: SelectionVariant | null
  allocation: AllocationMethod | null
}

export type SelectionValidation =
  | { ok: true; request: SelectionRequest }
  | { ok: false; error: 'noItems' | 'sampleSize' | 'seed' | 'variant' | 'allocation' | 'partialStrata' }

function optionalSeed(text: string): number | null | undefined {
  const trimmed = text.trim()
  if (trimmed === '') return null
  if (!/^\d{1,19}$/.test(trimmed)) return undefined
  const seed = Number(trimmed)
  return Number.isSafeInteger(seed) ? seed : undefined
}

type SelectionFailure = Extract<SelectionValidation, { ok: false }>['error']

function sampleSizeOf(text: string): number | null {
  const size = parseInput(text)
  return typeof size === 'number' && Number.isInteger(size) && size >= 0 ? size : null
}

function selectionProblem(input: SelectionInput): SelectionFailure | null {
  if (input.items.length === 0) return 'noItems'
  if (sampleSizeOf(input.sampleSize) === null) return 'sampleSize'
  if (optionalSeed(input.seed) === undefined) return 'seed'
  if (input.profile.kind === 'mus' && input.variant === null) return 'variant'
  if (hasPartialStrata(input.items)) return 'partialStrata'
  if (strataOf(input.items).length > 0 && input.allocation === null) return 'allocation'
  return null
}

/** Anfrage für `POST /selection`; ein leerer Seed überlässt dem Server die Erzeugung. */
export function buildSelectionRequest(input: SelectionInput): SelectionValidation {
  const problem = selectionProblem(input)
  if (problem !== null) return { ok: false, error: problem }
  const seed = optionalSeed(input.seed)
  const mus = input.profile.kind === 'mus'
  const stratified = strataOf(input.items).length > 0
  const request: SelectionRequest = {
    method: input.profile.kind,
    items: input.items,
    sample_size: sampleSizeOf(input.sampleSize) ?? 0,
    ...(mus && input.variant ? { variant: input.variant } : {}),
    ...(typeof seed === 'number' ? { seed } : {}),
    ...(stratified && input.allocation ? { allocation: input.allocation } : {}),
  }
  return { ok: true, request }
}

/** Übernommene Dateispalten → Elemente der Grundgesamtheit (Kennung sonst laufende Nummer). */
export function itemsFromImport(columns: {
  values: readonly (number | null)[]
  ids: readonly string[] | null
  strata: readonly string[] | null
}): PopulationItem[] {
  return columns.values.map((value, index) => {
    const item: PopulationItem = { id: columns.ids?.[index] || String(index + 1), value }
    const stratum = columns.strata?.[index]
    return stratum ? { ...item, stratum } : item
  })
}

/** Summe der positiven Werte (Auswahlbasis der Variante „portal“). */
export function positiveSum(items: readonly PopulationItem[]): number {
  return items.reduce((sum, item) => (item.value !== null && item.value > 0 ? sum + item.value : sum), 0)
}
