/** Typen des REST-Vertrags `auditcore_extrapolation.evaluation/1` (docs/ui/extrapolation-rest.md). */
import type { DownloadFile } from '@auditcore/common'

export interface ExtrapolationMethod {
  id: string
  label: string
  statistical: boolean
  selection: 'equal_probability' | 'pps'
  stratification: boolean
  source: string
  formula: string
  needs_population_size: boolean
  needs_sample_size: boolean
}

export interface FactorProfileInfo {
  id: string
  label: string
  source: string
  note: string
}

export interface ExtrapolationCatalogue {
  contract: string
  library: string
  sources: Readonly<Record<string, string>>
  methods: readonly ExtrapolationMethod[]
  factor_profiles: readonly FactorProfileInfo[]
  recommended_profile: string
  confidence_levels: { z: readonly number[]; 'mus.conservative': readonly number[] }
  materiality: { default: number; maximum: number }
  error_classes: readonly { id: string; label: string; description: string }[]
  conclusions: readonly { id: Conclusion; label: string }[]
  limits: { max_units: number; max_strata: number }
}

export interface StratumInput {
  name: string
  book_value: number
  population_size?: number
  systemic_error?: number
}

export interface UnitInput {
  id: string
  stratum: string
  book_value: number
  random_error?: number
  systemic_error?: number
  anomalous_error?: number
  anomalous_reason?: string
  anomalous_corrected?: boolean
  exhaustive?: boolean
}

export interface EvaluationRequest {
  method: string
  confidence_level?: number
  factor_profile?: string
  sample_size?: number
  materiality_rate: number
  strata: readonly StratumInput[]
  units: readonly UnitInput[]
}

export interface ExtrapolationStep {
  label: string
  formula: string
  value: number
  source: string
}

export interface StratumProjection {
  name: string
  projected_error: number
  exhaustive_error: number
  sample_size: number
  sampling_book_value: number
  figures: Readonly<Record<string, number>>
}

export interface Projection {
  method: string
  projected_random_error: number
  precision: number | null
  confidence_level: number | null
  factor_profile: string | null
  coefficient: number | null
  strata: readonly StratumProjection[]
  sample_errors: { random: number; systemic: number; anomalous_uncorrected: number; anomalous_corrected: number }
  systemic_population: number
  steps: readonly ExtrapolationStep[]
  warnings: readonly string[]
  extra: Readonly<Record<string, unknown>>
}

export type Conclusion = 'material' | 'not_material' | 'inconclusive'

export interface TotalErrorRate {
  book_value: number
  materiality_rate: number
  tolerable_error: number
  projected_random_error: number
  systemic_errors: number
  anomalous_uncorrected: number
  anomalous_corrected_excluded: number
  total_error: number
  rate: number
  precision: number | null
  upper_limit: number | null
  upper_limit_rate: number | null
  conclusion: Conclusion
  explanation: readonly string[]
  steps: readonly ExtrapolationStep[]
  difference: { corrected_book_value: number; lower_limit: number; book_value_less_tolerable: number } | null
}

export interface EvaluationResult {
  contract: string
  library: string
  fingerprint: string
  method: ExtrapolationMethod
  projection: Projection
  total_error_rate: TotalErrorRate
}

export interface ResidualRequest {
  audit_population: number
  total_error_rate: number
  ongoing_assessment: number
  other_negative_amounts: number
  financial_corrections: number
  materiality_rate: number
}

export interface ResidualRow {
  row: string
  label: string
  value: number | null
  exact: string | null
}

export interface ResidualErrorRate {
  source: string
  rate: number | null
  rate_rounded: number | null
  exceeds_materiality: boolean
  materiality_rate: number
  extrapolated_correction: number | null
  rate_after_correction: number | null
  rows: readonly ResidualRow[]
  not_applicable: string | null
  notes: readonly string[]
}

export interface ResidualResult {
  contract: string
  library: string
  fingerprint: string
  residual_error_rate: ResidualErrorRate
}

export type ExtrapolationExportFormat = 'csv' | 'json'

/** Schnittstelle der Komponente zur Fachlogik; Standardumsetzung: `createExtrapolationRestPort`. */
export interface ExtrapolationPort {
  profiles(): Promise<ExtrapolationCatalogue>
  evaluate(request: EvaluationRequest): Promise<EvaluationResult>
  residual(request: ResidualRequest): Promise<ResidualResult>
  exportEvaluation(request: EvaluationRequest, format: ExtrapolationExportFormat): Promise<DownloadFile>
}
