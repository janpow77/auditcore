/**
 * Vertrag `auditcore_sampling.guidance/1` (Python `auditcore_sampling.web`,
 * docs/ui/samplesize-rest.md): Stichprobenumfang nach dem KOM-Leitfaden
 * EGESIF_16-0014-01.
 */

/** Tabelle, aus der die Konfidenzniveaus einer Methode stammen. */
export type SampleSizeConfidenceTable = 'z' | 'reliability' | null

export interface SampleSizeMethod {
  id: string
  label: string
  section: string
  formula: string
  fields: readonly string[]
  source: string
  confidence_table: SampleSizeConfidenceTable
}

export interface SampleSizeLevel {
  level: number
  value: number
}

export interface SampleSizeChoice {
  id: string
  label: string
}

export interface SampleSizeCatalogue {
  contract: string
  library: string
  status: string
  status_label: string
  guidance: string
  materiality_rate: number
  methods: readonly SampleSizeMethod[]
  factor_profiles: readonly (SampleSizeChoice & { source: string; note: string })[]
  tables: { z: readonly SampleSizeLevel[]; reliability: readonly SampleSizeLevel[]; expansion: readonly SampleSizeLevel[] }
  nonstatistical_rules: readonly (SampleSizeChoice & { source: string })[]
  assurance_levels: readonly SampleSizeChoice[]
}

export interface SampleSizeStratumRequest {
  name: string
  population_size?: number
  book_value?: number
  sd?: number
  exhaustive: boolean
}

/** Anfrage an `POST /guidance/size`; Anteile als Werte zwischen 0 und 1. */
export interface SampleSizeRequest {
  method: string
  [field: string]: string | number | boolean | readonly SampleSizeStratumRequest[]
}

export interface SampleSizeStep {
  label: string
  formula: string
  value: number
  source: string
}

export interface SampleSizeAllocation {
  name: string
  sample_size: number
  exhaustive: boolean
  population_size: number | null
  book_value: number | null
  share: number | null
  cut_off: number | null
}

export interface SampleSizePlan {
  contract: string
  library: string
  status: string
  status_label: string
  method: string
  sample_size: number
  raw_size: number
  interval: number | null
  inputs: Readonly<Record<string, unknown>>
  strata: readonly SampleSizeAllocation[]
  derivation: readonly SampleSizeStep[]
  warnings: readonly string[]
}

/** Fachlogik hinter der Oberfläche; Vue und React rufen nur diesen Port auf. */
export interface SamplesizePort {
  profiles: () => Promise<SampleSizeCatalogue>
  plan: (request: SampleSizeRequest) => Promise<SampleSizePlan>
}
