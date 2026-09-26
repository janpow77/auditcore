/**
 * Port der Risiko-Komponenten zu `auditcore_risk.web` (docs/ui/risk-rest.md).
 * Komponenten erhalten den Port als Prop und rufen nie selbst `fetch` auf;
 * `createRiskRestPort` ist die mitgelieferte REST-Umsetzung.
 */
import { requestJson, type RestOptions } from '@auditcore/common'
import type { Evaluation, JsonObject, ProfileDetail, ProfileReference } from './types'

export interface EvaluateRequest {
  profile: { id: string; version: string }
  records: readonly JsonObject[]
  columns?: readonly string[]
  reference_date?: string
  record_key?: string
  flatten?: boolean
  points?: Readonly<Record<string, number>>
}

export interface ProfileSummary extends ProfileReference {
  kind: string
  legal_status: string
  rule_count: number
  field_count: number
  open_decision_count: number
}

export interface ColumnCheck {
  profile: ProfileReference
  columns: string[]
  complete: boolean
  aborts: boolean
  rules: Array<{ code: string; label: string; missing: string[]; when_missing_columns: string }>
}

export interface RiskPort {
  profiles(): Promise<ProfileSummary[]>
  profile(id: string, version: string): Promise<ProfileDetail>
  checkColumns(id: string, version: string, columns: readonly string[]): Promise<ColumnCheck>
  evaluate(request: EvaluateRequest): Promise<Evaluation>
}

function profilePath(id: string, version: string): string {
  return `/profiles/${encodeURIComponent(id)}/${encodeURIComponent(version)}`
}

/** REST-Umsetzung des Ports, z. B. `createRiskRestPort({ baseUrl: '/api/risk' })`. */
export function createRiskRestPort(options: RestOptions): RiskPort {
  return {
    profiles: async () => (await requestJson<{ profiles: ProfileSummary[] }>(options, '/profiles')).profiles,
    profile: (id, version) => requestJson<ProfileDetail>(options, profilePath(id, version)),
    checkColumns: (id, version, columns) =>
      requestJson<ColumnCheck>(options, `${profilePath(id, version)}/check-columns`, { columns }),
    evaluate: (request) => requestJson<Evaluation>(options, '/evaluate', request),
  }
}
