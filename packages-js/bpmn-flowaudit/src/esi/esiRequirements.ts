/**
 * ESI requirements per BPMN element, ported from `useEsiRequirements.ts` of
 * the audit_designer: accepts several plausible response shapes (array,
 * map by element, `{ requirements }`, `{ elements }`) and derives the status
 * (fulfilled / unclear / missing) if the server sends none.
 */

export type EsiStatus = 'fulfilled' | 'unclear' | 'missing'

export interface EsiRequirementResult {
  elementId: string
  elementName: string
  requirementId: string
  description: string
  status: EsiStatus
  expected: string | null
  actual: string | null
}

type Raw = Record<string, unknown>

function asString(value: unknown, fallback = ''): string {
  if (typeof value === 'string') return value
  return typeof value === 'number' || typeof value === 'boolean' ? String(value) : fallback
}

function asNullable(value: unknown): string | null {
  if (value === null || value === undefined || value === '') return null
  return asString(value) || null
}

const STATUS_WORDS: Record<EsiStatus, string[]> = {
  fulfilled: ['fulfilled', 'ok', 'erfüllt', 'erfuellt'],
  missing: ['missing', 'fehlend', 'failed', 'error'],
  unclear: ['unclear', 'unknown', 'unklar', 'warning'],
}

export function deriveStatus(raw: unknown, expected: string | null, actual: string | null): EsiStatus {
  if (typeof raw === 'string') {
    const normalized = raw.toLowerCase()
    const found = (Object.keys(STATUS_WORDS) as EsiStatus[]).find((status) => STATUS_WORDS[status].includes(normalized))
    if (found) return found
  }
  if (expected === null) return 'unclear'
  if (actual === null) return 'missing'
  return actual.trim() === expected.trim() ? 'fulfilled' : 'unclear'
}

function first(raw: Raw, names: string[]): unknown {
  return names.map((name) => raw[name]).find((value) => value !== undefined && value !== null)
}

export function normalizeRequirement(raw: Raw, fallbackId: string, fallbackName: string, index: number): EsiRequirementResult {
  const elementId = asString(first(raw, ['element_id', 'elementId', 'element']) ?? fallbackId, fallbackId)
  const elementName = asString(first(raw, ['element_name', 'elementName']) ?? fallbackName, fallbackName || elementId)
  const requirementId = asString(first(raw, ['requirement_id', 'requirementId', 'id']), `${elementId}-${index}`)
  const expected = asNullable(first(raw, ['expected', 'expected_value']))
  const actual = asNullable(first(raw, ['actual', 'actual_value']))
  return {
    elementId,
    elementName,
    requirementId,
    description: asString(first(raw, ['description', 'text']), requirementId),
    status: deriveStatus(raw.status, expected, actual),
    expected,
    actual,
  }
}

function fromBlock(block: Raw, key: string): EsiRequirementResult[] {
  const id = asString(first(block, ['element_id', 'elementId', 'id']) ?? key, key)
  const name = asString(first(block, ['element_name', 'elementName', 'name']), id)
  const list = first(block, ['requirements', 'esi_requirements', 'items'])
  return Array.isArray(list) ? list.map((item, index) => normalizeRequirement(item as Raw, id, name, index)) : []
}

function isBlock(value: unknown): value is Raw {
  return Boolean(value && typeof value === 'object' && ['requirements', 'esi_requirements', 'items'].some((key) => key in (value as Raw)))
}

/** Flat list from any of the supported response shapes. */
export function normalizeEsiResponse(response: unknown): EsiRequirementResult[] {
  if (Array.isArray(response)) {
    return response.flatMap((item, index) => (isBlock(item) ? fromBlock(item, String(index)) : [normalizeRequirement(item as Raw, '', '', index)]))
  }
  if (!response || typeof response !== 'object') return []
  const raw = response as Raw
  for (const key of ['requirements', 'elements']) if (Array.isArray(raw[key])) return normalizeEsiResponse(raw[key])
  return Object.entries(raw).flatMap(([key, value]) => (isBlock(value) ? fromBlock(value, key) : []))
}

export interface EsiElementGroup {
  elementId: string
  elementName: string
  requirements: EsiRequirementResult[]
  fulfilledCount: number
  totalCount: number
}

export function groupByElement(list: EsiRequirementResult[]): EsiElementGroup[] {
  const groups = new Map<string, EsiElementGroup>()
  for (const item of list) {
    const group = groups.get(item.elementId) ?? { elementId: item.elementId, elementName: item.elementName, requirements: [], fulfilledCount: 0, totalCount: 0 }
    group.requirements.push(item)
    group.totalCount += 1
    if (item.status === 'fulfilled') group.fulfilledCount += 1
    groups.set(item.elementId, group)
  }
  return [...groups.values()]
}

export function summarize(list: EsiRequirementResult[]): { total: number; fulfilled: number; unclear: number; missing: number } {
  return {
    total: list.length,
    fulfilled: list.filter((item) => item.status === 'fulfilled').length,
    unclear: list.filter((item) => item.status === 'unclear').length,
    missing: list.filter((item) => item.status === 'missing').length,
  }
}
