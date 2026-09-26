/**
 * Form logic of the declarative field and list editors: committing one
 * field (trim, tokens, dropping empty values), display text, select options
 * that keep unknown values visible, list updates.
 */

import type { FieldDescriptor } from './descriptors'

export interface Option {
  value: string
  label: string
}

type Row = Record<string, unknown>

const isEmpty = (value: unknown) => value === '' || value === false || value === undefined || (Array.isArray(value) && !value.length)

/** New object with one field set; empty values remove the key. */
export function withField(row: Row, key: string, raw: unknown): Row {
  const next: Row = { ...row }
  const value = typeof raw === 'string' ? raw.trim() : raw
  if (isEmpty(value)) delete next[key]
  else next[key] = value
  return next
}

/** Parsed input of a text-like field (tokens are split at blanks and commas). */
export function parseFieldInput(field: FieldDescriptor, raw: string): unknown {
  return field.kind === 'tokens' ? raw.split(/[\s,]+/).filter(Boolean) : raw
}

export function fieldText(row: Row, field: FieldDescriptor): string {
  const value = row[field.key]
  return Array.isArray(value) ? value.join(' ') : value === undefined ? '' : String(value)
}

export function inputType(field: FieldDescriptor): string {
  return field.kind === 'date' ? 'date' : field.kind === 'number' ? 'number' : 'text'
}

export const isWide = (field: FieldDescriptor): boolean => Boolean(field.wide || field.kind === 'textarea')

/** Unknown current value of a select (not among the options) or `null`. */
export function unknownOption(options: Option[], current: string): string | null {
  return current && !options.some((option) => option.value === current) ? current : null
}

export const replaceAt = <T>(items: readonly T[], index: number, value: T): T[] => items.map((item, i) => (i === index ? value : item))
export const removeAt = <T>(items: readonly T[], index: number): T[] => items.filter((_, i) => i !== index)
export const toggleIndex = (open: number | null, index: number): number | null => (open === index ? null : index)
