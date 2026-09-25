/**
 * Läufer für die gemeinsamen Vertragsfälle `contracts/common-cases/*.json`
 * (dieselben Dateien nutzt die Python-Referenz, `auditcore.tools.helpers`).
 * Sonderwerte und Vergleich wie in `src/auditcore/tools/helpers/compare.py`.
 */
import { readFileSync, readdirSync } from 'node:fs'
import { fileURLToPath } from 'node:url'

export const CASES_DIR = fileURLToPath(new URL('../../../contracts/common-cases/', import.meta.url))
const NON_CONTRACTS = new Set(['decisions.json', 'schema.json'])

export type Json = null | boolean | number | string | Json[] | { [key: string]: Json }

export interface Expect {
  value?: Json
  invalid?: true
  hint?: string
  contains?: Json[]
  not_contains?: string[]
}

export interface Case {
  id: string
  input: Record<string, unknown>
  expect: Expect
  tags?: string[]
  languages?: string[]
}

export interface Contract {
  contract: string
  version: string
  status: string
  languages: string[]
  params: string[]
  result: 'decimal' | 'text' | 'boolean' | 'text-contains' | 'csv'
  cases: Case[]
}

function readJson(name: string): unknown {
  return JSON.parse(readFileSync(`${CASES_DIR}${name}`, 'utf8'))
}

export const decisions = (readJson('decisions.json') as { decisions: Record<string, Json> }).decisions

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

/** Löst `$decision` auf und dekodiert `$undefined`, `$nan`, `$date`, `$error`. */
export function decode(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(decode)
  if (!isRecord(value)) return value
  const keys = Object.keys(value)
  if (keys.length === 1) {
    if ('$decision' in value) return decisions[String(value.$decision)]
    if ('$undefined' in value) return undefined
    if ('$nan' in value) return Number.NaN
    if ('$date' in value) return new Date(String(value.$date))
    if ('$error' in value) return new Error(String(value.$error))
  }
  return Object.fromEntries(Object.entries(value).map(([key, item]) => [key, decode(item)]))
}

export function loadContracts(): Contract[] {
  return readdirSync(CASES_DIR)
    .filter((name) => name.endsWith('.json') && !NON_CONTRACTS.has(name))
    .sort()
    .map((name) => readJson(name) as Contract)
}

/** Fälle für TypeScript (Vertrag und Fall), mit dekodierten Eingaben und Erwartungen. */
export function tsCases(contract: Contract): Case[] {
  if (!contract.languages.includes('ts')) return []
  return contract.cases
    .filter((entry) => !entry.languages || entry.languages.includes('ts'))
    .map((entry) => ({ ...entry, input: decode(entry.input) as Record<string, unknown>, expect: decode(entry.expect) as Expect }))
}

/** Dezimalwerte vergleichbar machen (`1.50` = `1.5`, `-0` = `0`). */
export function canonicalDecimal(value: unknown): string | null {
  const text = typeof value === 'number' ? String(value) : typeof value === 'string' ? value.trim() : null
  const match = text === null ? null : /^(-?)(\d+)(?:\.(\d*))?$/.exec(text)
  if (!match) return null
  const integer = (match[2] ?? '0').replace(/^0+(?=\d)/, '')
  const fraction = (match[3] ?? '').replace(/0+$/, '')
  const body = fraction ? `${integer}.${fraction}` : integer
  return body === '0' ? '0' : `${match[1]}${body}`
}

export function normaliseCsv(text: string): string {
  const unified = text.replace(/\r\n/g, '\n')
  return unified.endsWith('\n') ? unified.slice(0, -1) : unified
}
