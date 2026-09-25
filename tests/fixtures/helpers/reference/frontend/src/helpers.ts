// Reference implementation of every shared helper contract (test fixture).
const EMPTY = '—'
const TIME_ZONE = 'Europe/Berlin'
const IBAN_LENGTHS: Record<string, number> = { AT: 20, BE: 16, CH: 21, DE: 22, ES: 24, FR: 27, GB: 22, IT: 27, LU: 20, NL: 18 }
const SEPARATORS: Record<string, [string, string]> = { de: ['.', ','], en: [',', '.'] }

const escape = (text: string): string => text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')

function autoMode(text: string): string | null {
  const dot = text.lastIndexOf('.')
  const comma = text.lastIndexOf(',')
  if (dot >= 0 && comma >= 0) return comma > dot ? 'de' : 'en'
  const sep = dot >= 0 ? '.' : comma >= 0 ? ',' : ''
  if (!sep) return 'de'
  const count = text.split(sep).length - 1
  if (count === 1 && text.length - text.indexOf(sep) - 1 === 3) return null
  if (count > 1) return sep === '.' ? 'de' : 'en'
  return sep === '.' ? 'en' : 'de'
}

export function parseNumber(text: unknown, mode = 'de'): number | null {
  if (typeof text !== 'string') return null
  let cleaned = text.replace(/€|\bEUR\b/gi, '').replace(/ /g, ' ').trim()
  cleaned = cleaned.replace(/(?<=\d) (?=\d{3}\b)/g, '')
  const chosen = mode === 'auto' ? autoMode(cleaned) : mode
  const separators = chosen ? SEPARATORS[chosen] : undefined
  if (!separators) return null
  const [group, decimal] = separators
  const pattern = new RegExp(`^-?(\\d{1,3}(${escape(group)}\\d{3})+|\\d+)(${escape(decimal)}\\d+)?$`)
  if (!pattern.test(cleaned)) return null
  return Number(cleaned.split(group).join('').replace(decimal, '.'))
}

const isEmpty = (value: unknown): boolean =>
  value === null || value === undefined || value === '' || (typeof value === 'number' && Number.isNaN(value))

export function formatMoney(value: unknown): string {
  if (isEmpty(value)) return EMPTY
  const amount = Number(value)
  if (!Number.isFinite(amount)) return EMPTY
  return new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' }).format(amount)
}

function moment(value: unknown): Date | null {
  if (value instanceof Date) return Number.isNaN(value.getTime()) ? null : value
  if (typeof value !== 'string' || !value) return null
  const dateOnly = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value)
  const parsed = dateOnly ? new Date(`${value}T12:00:00Z`) : new Date(value)
  return Number.isNaN(parsed.getTime()) ? null : parsed
}

export function formatDate(value: unknown): string {
  const parsed = moment(value)
  if (!parsed) return EMPTY
  return new Intl.DateTimeFormat('de-DE', { timeZone: TIME_ZONE, day: '2-digit', month: '2-digit', year: 'numeric' }).format(parsed)
}

export function formatDateTime(value: unknown): string {
  const parsed = typeof value === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(value) ? null : moment(value)
  if (!parsed) return EMPTY
  const options: Intl.DateTimeFormatOptions = {
    timeZone: TIME_ZONE, day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit',
  }
  return new Intl.DateTimeFormat('de-DE', options).format(parsed)
}

export function formatFilesize(size: unknown): string {
  if (typeof size !== 'number' || !Number.isInteger(size) || size < 0) return EMPTY
  if (size < 1024) return `${size} B`
  let value = size
  let unit = 'B'
  for (const next of ['KB', 'MB', 'GB', 'TB']) {
    value /= 1024
    unit = next
    if (value < 1024) break
  }
  return `${value.toFixed(1).replace('.', ',').replace(/,0$/, '')} ${unit}`
}

function mod97(text: string): number {
  let rest = 0
  for (const char of text) {
    for (const digit of String(parseInt(char, 36))) rest = (rest * 10 + Number(digit)) % 97
  }
  return rest
}

export function ibanValid(text: unknown): boolean {
  if (typeof text !== 'string') return false
  const iban = text.replace(/ /g, '').toUpperCase()
  if (!/^[A-Z]{2}\d{2}[A-Z0-9]+$/.test(iban)) return false
  if (IBAN_LENGTHS[iban.slice(0, 2)] !== iban.length) return false
  return mod97(iban.slice(4) + iban.slice(0, 4)) === 1
}

export function leiValid(text: unknown): boolean {
  if (typeof text !== 'string') return false
  const lei = text.toUpperCase()
  return /^[A-Z0-9]{18}\d{2}$/.test(lei) && mod97(lei) === 1
}

export function csvCell(value: unknown): string {
  if (value === null || value === undefined) return ''
  if (typeof value === 'number') return String(value).replace('.', ',')
  let text = String(value)
  if (/^[=+\-@\t\r]/.test(text)) text = `'${text}`
  if (/[;"\n\r]/.test(text)) text = `"${text.replace(/"/g, '""')}"`
  return text
}

export function csvDocument(rows: unknown[][]): string {
  return '﻿' + rows.map((row) => row.map(csvCell).join(';') + '\r\n').join('')
}

interface ValidationItem { loc?: unknown[]; msg?: string }

function fromData(data: unknown): string | null {
  if (!data || typeof data !== 'object') return null
  const record = data as { detail?: unknown; error?: { message?: unknown } }
  if (typeof record.detail === 'string') return record.detail
  if (Array.isArray(record.detail)) {
    return (record.detail as ValidationItem[])
      .map((item) => `${String(item.loc?.[item.loc.length - 1] ?? '')}: ${item.msg ?? ''}`)
      .join('; ')
  }
  return typeof record.error?.message === 'string' ? record.error.message : null
}

export function errorMessage(error: unknown, fallback: string): string {
  if (typeof error === 'string') return error
  const response = (error as { response?: { data?: unknown } } | null)?.response
  const text = fromData(response?.data)
  if (text) return text
  return error instanceof Error ? error.message : fallback
}
