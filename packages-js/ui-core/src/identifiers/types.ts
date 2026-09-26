/** Typen des REST-Vertrags `identifiers_ui/1` (`docs/ui/identifiers-rest.md`, auditcore_identifiers.web). */

export type IdentifierStatus = 'VALID' | 'INVALID' | 'MISSING'

export interface IdentifierKindInfo {
  id: string
  label: string
  description: string
  /** Land als Zusatzangabe sinnvoll (USt-IdNr. ohne Präfix). */
  country: boolean
}

export interface IdentifierProfileInfo {
  id: string
  title: string
  rationale: string
  origin: string
  legacy: boolean
  /** Kennungsarten, die das Profil prüft. */
  kinds: readonly string[]
}

export interface IdentifierCatalogue {
  contract: string
  library: string
  recommended_profile: string
  kinds: readonly IdentifierKindInfo[]
  profiles: readonly IdentifierProfileInfo[]
  reasons: readonly { id: string; label: string }[]
  detail_labels: Readonly<Record<string, string>>
  value_labels: Readonly<Record<string, string>>
  limits: { max_items: number; max_value_length: number; max_body_bytes: number }
}

export type IdentifierDetailValue = string | number | boolean | null

export interface IdentifierResult {
  kind: string
  kind_label: string
  status: IdentifierStatus
  raw: string | null
  normalized: string | null
  reason: string | null
  reason_label: string | null
  message: string
  country: string | null
  profile: string
  details: Readonly<Record<string, IdentifierDetailValue>>
}

export interface IdentifierCheckRequest {
  kind: string
  value: string | null
  profile: string
  country?: string | null
}

export interface IdentifierCheckAnswer {
  contract: string
  result: IdentifierResult
}

export interface IdentifierBatchItem {
  ref?: string
  kind: string
  value: string | null
  country?: string | null
}

export interface IdentifierBatchRequest {
  profile: string
  items: readonly IdentifierBatchItem[]
}

/** Zeile der Stapelprüfung: Ergebnisfelder oder `error` (Art unbekannt bzw. vom Profil nicht geprüft). */
export type IdentifierBatchRow = { index: number; ref: string } & (
  | ({ error: null } & IdentifierResult)
  | { error: { code: string; message: string } }
)

export interface IdentifierBatchSummary {
  total: number
  valid: number
  invalid: number
  missing: number
  not_checked: number
}

export interface IdentifierBatchAnswer {
  contract: string
  profile: string
  results: readonly IdentifierBatchRow[]
  summary: IdentifierBatchSummary
}

/** Schnittstelle zur Fachlogik; Standardumsetzung `createIdentifiersRestPort`. */
export interface IdentifiersPort {
  catalogue(): Promise<IdentifierCatalogue>
  check(request: IdentifierCheckRequest): Promise<IdentifierCheckAnswer>
  checkBatch(request: IdentifierBatchRequest): Promise<IdentifierBatchAnswer>
}
