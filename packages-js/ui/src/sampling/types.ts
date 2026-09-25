/** Typen des REST-Vertrags `docs/ui/sampling-rest.md` (auditcore_sampling.web). */
import type { DownloadFile } from '../rest'

export type MethodKind = 'mus' | 'srs'
export type MethodStatus = 'RECOMMENDED' | 'SUPERSEDED' | 'LEGACY_CHARACTERIZED'
export type SelectionVariant = 'portal' | 'flowstat'
export type AllocationMethod = 'proportional' | 'equal'

export interface ParameterSpec {
  key: string
  label: string
  unit: 'EUR' | 'Anteil' | 'Stück'
  type: 'number' | 'integer' | 'choice'
  minimum?: number
  maximum?: number
  exclusive_minimum?: number
  exclusive_maximum?: number
  suggested?: number
}

export interface ConfidenceLevel {
  level: number
  factor: number
}

export interface MethodProfile {
  id: string
  kind: MethodKind
  label: string
  status: MethodStatus
  recommended: boolean
  source: string
  note: string
  formula: string
  confidence_levels: readonly ConfidenceLevel[]
  parameters: readonly ParameterSpec[]
  default_variant: SelectionVariant | null
}

export interface NamedOption<I extends string> {
  id: I
  label: string
  description?: string
  formula?: string
}

export interface SamplingCatalogue {
  library: string
  recommended: { mus: string }
  decision: Readonly<Record<string, string>>
  methods: readonly MethodProfile[]
  selection_variants: readonly NamedOption<SelectionVariant>[]
  allocation_methods: readonly NamedOption<AllocationMethod>[]
}

export type SizeRequest = { method: string } & Readonly<Record<string, number | string>>

export interface DerivationStep {
  label: string
  formula: string
  value: number
}

export interface SizeResult {
  library: string
  method: string
  kind: MethodKind
  status: MethodStatus
  sample_size: number
  interval: number
  inputs: Readonly<Record<string, number>>
  warnings: readonly string[]
  derivation: readonly DerivationStep[]
}

export interface PopulationItem {
  id?: string | number
  value: number | null
  stratum?: string
}

export interface AllocationRequest {
  total_sample_size: number
  method: AllocationMethod
  strata: Readonly<Record<string, number>>
}

export interface AllocationResult {
  method: AllocationMethod
  total_sample_size: number
  allocated: number
  strata: readonly { stratum: string; population: number; sample_size: number }[]
}

export interface SelectionRequest {
  method: MethodKind
  variant?: SelectionVariant
  items: readonly PopulationItem[]
  sample_size: number
  seed?: number
  allocation?: AllocationMethod
}

export interface SelectionRow {
  order: number
  position: number
  id: string
  value: number | null
  stratum: string | null
  hits: number
}

export interface StratumResult {
  stratum: string | null
  population: number
  sample_size: number
  interval?: number
  start?: number
  excluded_negative?: readonly string[]
  excluded_zero_or_missing?: readonly string[]
}

export interface SelectionResult {
  library: string
  method: MethodKind
  variant: SelectionVariant | null
  seed: number
  seed_generated: boolean
  items_sha256: string
  population: number
  selected: number
  strata: readonly StratumResult[]
  rows: readonly SelectionRow[]
}

export type ExportFormat = 'csv' | 'json'

/** Schnittstelle der Komponente zur Fachlogik; Standardumsetzung: `createSamplingRestPort`. */
export interface SamplingPort {
  profiles(): Promise<SamplingCatalogue>
  size(request: SizeRequest): Promise<SizeResult>
  allocation(request: AllocationRequest): Promise<AllocationResult>
  selection(request: SelectionRequest): Promise<SelectionResult>
  exportSelection(request: SelectionRequest & { seed: number }, format: ExportFormat): Promise<DownloadFile>
}
