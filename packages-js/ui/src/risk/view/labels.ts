/** Zuordnung fachlicher Zustände zu Textschlüsseln (framework-frei). */
import type { RiskMessageKey } from '../messages'
import type { FlagState, StateFilter } from './state'

export const STATE_KEYS: Readonly<Record<FlagState, RiskMessageKey>> = {
  hit: 'stateHit',
  undetermined: 'stateUndetermined',
  clear: 'stateClear',
  skipped: 'stateSkipped',
  absent: 'stateAbsent',
}

export const STATE_FILTER_KEYS: Readonly<Record<StateFilter, RiskMessageKey>> = {
  affected: 'filterAffected',
  hit: 'stateHit',
  undetermined: 'stateUndetermined',
  clear: 'stateClear',
  all: 'filterAll',
}

const STATUS_KEYS: Readonly<Record<string, RiskMessageKey>> = {
  APPROVED: 'statusApproved',
  LEGACY_CHARACTERIZED: 'statusLegacy',
  CANDIDATE_HUMAN_DECISION_REQUIRED: 'statusCandidate',
}

const STATUS_HINTS: Readonly<Record<string, RiskMessageKey>> = {
  LEGACY_CHARACTERIZED: 'statusHintLegacy',
  CANDIDATE_HUMAN_DECISION_REQUIRED: 'statusHintCandidate',
}

export function statusKey(status: string): RiskMessageKey | null {
  return STATUS_KEYS[status] ?? null
}

/** Hinweis für nicht freigegebene Profile, sonst `null`. */
export function statusHintKey(status: string): RiskMessageKey | null {
  return STATUS_HINTS[status] ?? null
}

const REQUIREMENT_KEYS: Readonly<Record<string, RiskMessageKey>> = {
  required: 'required',
  value_required: 'valueRequired',
  optional: 'optional',
}

export function requirementKey(requirement: string): RiskMessageKey {
  return REQUIREMENT_KEYS[requirement] ?? 'optional'
}

const WHEN_MISSING_KEYS: Readonly<Record<string, RiskMessageKey>> = {
  error: 'missingError',
  skip: 'missingSkip',
  all_false: 'missingAllFalse',
  undetermined: 'missingUndetermined',
}

export function whenMissingKey(mode: string): RiskMessageKey {
  return WHEN_MISSING_KEYS[mode] ?? 'missingError'
}
