import { afterAll, beforeAll, describe, expect, it } from 'vitest'
import {
  errorMessage,
  formatBytes,
  formatDate,
  formatDateTime,
  formatEur,
  formatNumber,
  isValidIban,
  isValidLei,
  parseDecimalResult,
  PARSE_FAILURE_HINTS,
  escapeCsvCell,
  toCsv,
  type CsvValue,
  type ParseMode,
} from '../src'
import { canonicalDecimal, decisions, loadContracts, normaliseCsv, tsCases, type Case, type Contract } from './contracts'

type Check = (entry: Case) => void

const MODES: Readonly<Record<string, ParseMode>> = { de: 'strict-de', en: 'strict-en', auto: 'auto' }
const HINTS: Readonly<Record<string, string>> = { empty: 'leer', ambiguous: 'mehrdeutig', invalid: 'ungültig', negative: 'negativ' }

function text(entry: Case, actual: string): void {
  expect(actual, entry.id).toBe(entry.expect.value)
}

const parseNumber: Check = (entry) => {
  const mode = MODES[String(entry.input.mode)]
  expect(mode, `${entry.id}: Modus`).toBeDefined()
  const result = parseDecimalResult(entry.input.text as string, { mode })
  if (entry.expect.invalid) {
    expect(result.ok, `${entry.id}: Ablehnung erwartet, erhalten ${JSON.stringify(result)}`).toBe(false)
    if (!result.ok && entry.expect.hint) expect(HINTS[result.reason], `${entry.id}: Hinweis`).toBe(entry.expect.hint)
    if (!result.ok) expect(PARSE_FAILURE_HINTS[result.reason]).toBeTruthy()
    return
  }
  expect(result.ok ? canonicalDecimal(result.value) : result, entry.id).toBe(canonicalDecimal(entry.expect.value))
}

/** Alle Anzeigeformatierer teilen den Ersatzwert (Vertrag empty-value). */
const DISPLAY_FORMATTERS: readonly ((value: unknown) => string)[] = [
  (value) => formatDate(value as never),
  (value) => formatDateTime(value as never),
  (value) => formatNumber(value as never),
  (value) => formatEur(value as never),
  (value) => formatBytes(value as never),
]

const CHECKS: Readonly<Record<string, Check>> = {
  'api-error-message': (entry) => {
    const actual = errorMessage(entry.input.error, String(entry.input.fallback))
    if ('value' in entry.expect) return text(entry, actual)
    for (const part of entry.expect.contains ?? []) expect(actual, entry.id).toContain(String(part))
    for (const part of entry.expect.not_contains ?? []) expect(actual, entry.id).not.toContain(part)
  },
  'csv-cell': (entry) => text(entry, escapeCsvCell(entry.input.value as CsvValue)),
  'csv-document': (entry) =>
    expect(normaliseCsv(toCsv(entry.input.rows as CsvValue[][])), entry.id).toBe(normaliseCsv(String(entry.expect.value))),
  'empty-value': (entry) => DISPLAY_FORMATTERS.forEach((format) => text(entry, format(entry.input.value))),
  'format-date': (entry) => text(entry, formatDate(entry.input.value as never)),
  'format-datetime': (entry) => text(entry, formatDateTime(entry.input.value as never)),
  'format-filesize': (entry) => text(entry, formatBytes(entry.input.bytes as never)),
  'format-money': (entry) => text(entry, formatEur(entry.input.value as never)),
  'iban-valid': (entry) => expect(isValidIban(String(entry.input.text)), entry.id).toBe(entry.expect.value),
  'lei-valid': (entry) => expect(isValidLei(String(entry.input.text)), entry.id).toBe(entry.expect.value),
  'parse-number': parseNumber,
}

const contracts: Contract[] = loadContracts()
const originalTz = process.env.TZ

beforeAll(() => {
  // Prüfzeitzone westlich von UTC (Festlegung probe_timezone): macht fehlendes timeZone sichtbar.
  process.env.TZ = String(decisions.probe_timezone)
})

afterAll(() => {
  process.env.TZ = originalTz
})

describe('Vertragsfälle contracts/common-cases', () => {
  it('die Prüfzeitzone ist aktiv', () => {
    expect(new Date('2026-01-31T12:00:00Z').getTimezoneOffset()).toBe(300)
  })

  it('jeder TypeScript-Vertrag hat eine Bindung', () => {
    const missing = contracts.filter((contract) => contract.languages.includes('ts') && !CHECKS[contract.contract])
    expect(missing.map((contract) => contract.contract)).toEqual([])
  })

  for (const contract of contracts) {
    const cases = tsCases(contract)
    if (cases.length === 0) continue
    describe(`${contract.contract} ${contract.version}`, () => {
      it.each(cases.map((entry) => [entry.id, entry] as const))('%s', (_id, entry) => {
        CHECKS[contract.contract]?.(entry)
      })
    })
  }
})
