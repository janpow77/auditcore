/** Typen des REST-Vertrags `docs/ui/benford-rest.md` (auditcore_statistics.web). */

export type BenfordTest = 'first' | 'first_two' | 'second'
export type ShortValues = 'exclude' | 'pad'

export interface ConformityProfile {
  id: string
  label: string
  source: string
  mad_bounds: Readonly<Record<BenfordTest, readonly [number, number, number]>>
  level_labels: readonly [string, string, string, string]
  z_critical: number
  continuity_correction: boolean
  significance_level: number
  note: string
}

export interface BenfordCatalogue {
  library: string
  method: string
  tests: readonly { id: BenfordTest; label: string; digits: 1 | 2 }[]
  short_values: readonly { id: ShortValues; label: string }[]
  profiles: readonly ConformityProfile[]
  limits: { max_values: number }
}

export interface AnalyseRequest {
  test: BenfordTest
  profile: string
  short_values?: ShortValues
  values: readonly (number | null)[]
}

export interface DistributionRow {
  digit: number
  observed_count: number
  observed_share: number
  expected_share: number
  deviation: number
}

export interface ConformityRow extends DistributionRow {
  z: number
  exceeds: boolean
}

export interface BenfordDistribution {
  method: string
  digits: 1 | 2
  short_values: ShortValues | null
  analysed: number
  excluded: { missing: number; zero: number; short: number }
  negative_absolute: number
  chi2_statistic: number
  degrees_of_freedom: number
  p_value: number
  rows: readonly DistributionRow[]
}

export interface Conformity {
  profile: string
  test: BenfordTest
  analysed: number
  mad: number
  mad_level: 0 | 1 | 2 | 3
  mad_label: string
  chi2_statistic: number
  degrees_of_freedom: number
  p_value: number
  significance_level: number
  chi2_exceeds: boolean
  z_critical: number
  exceeding_digits: readonly number[]
  rows: readonly ConformityRow[]
}

export interface BenfordAnalysis {
  library: string
  test: BenfordTest
  test_label: string
  distribution: BenfordDistribution
  conformity: Conformity
}

/** Schnittstelle der Komponente zur Fachlogik; Standardumsetzung: `createBenfordRestPort`. */
export interface BenfordPort {
  profiles(): Promise<BenfordCatalogue>
  analyse(request: AnalyseRequest): Promise<BenfordAnalysis>
}
