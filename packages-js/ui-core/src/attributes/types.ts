/** Typen des REST-Endpunkts `POST /attributes` (Vertrag `auditcore_extrapolation.evaluation/1`, Leitfaden 7.9). */

export type AttributeApproach = 'normal' | 'discovery' | 'stop_or_go'

export interface AttributesCatalogue {
  contract: string
  library: string
  factor_profiles: readonly { id: string; label: string }[]
  recommended_profile: string
  confidence_levels: { z: readonly number[] }
  attribute_approaches?: readonly { id: AttributeApproach; label: string; source: string }[]
}

export interface AttributesRequest {
  approach: AttributeApproach
  deviations: number
  sample_size: number
  confidence_level: number
  /** Nur Normalapproximation (z-Wert). */
  factor_profile?: string
  /** Tolerierbare bzw. kritische Abweichungsquote als Anteil. */
  tolerable_rate: number
}

export interface AttributesStep {
  label: string
  formula: string
  value: number
  source: string
}

export type AttributesConclusion = 'supported' | 'not_supported' | 'criterion_met' | 'deviation_found' | 'stop' | 'go'

export interface AttributesOutcome {
  approach: AttributeApproach
  deviations: number
  sample_size: number
  confidence_level: number
  rate: number
  upper_limit: number
  conclusion: AttributesConclusion
  steps: readonly AttributesStep[]
  precision?: number
  tolerable_rate?: number
  threshold?: number
}

export interface AttributesResult {
  contract: string
  library: string
  fingerprint: string
  attributes: AttributesOutcome
}

/** Fachlogik hinter der Oberfläche; Standardumsetzung: `createAttributesRestPort`. */
export interface AttributesPort {
  profiles: () => Promise<AttributesCatalogue>
  evaluate: (request: AttributesRequest) => Promise<AttributesResult>
}
