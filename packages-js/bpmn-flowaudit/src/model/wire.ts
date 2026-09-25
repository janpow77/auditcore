/**
 * JSON of `auditcore_bpmn` ↔ TypeScript objects.
 *
 * The Python data classes use the same English field names in snake_case
 * (`valid_from`, `key_requirement`); this module converts keys recursively.
 */

type Json = unknown

export function camelToSnake(key: string): string {
  return key.replace(/[A-Z]/g, (letter) => `_${letter.toLowerCase()}`)
}

export function snakeToCamel(key: string): string {
  return key.replace(/_([a-z0-9])/g, (_match, letter: string) => letter.toUpperCase())
}

function convertKeys(value: Json, convert: (key: string) => string): Json {
  if (Array.isArray(value)) return value.map((item) => convertKeys(item, convert))
  if (value && typeof value === 'object') {
    return Object.fromEntries(Object.entries(value).map(([key, item]) => [convert(key), convertKeys(item, convert)]))
  }
  return value
}

/** TypeScript object → JSON for `auditcore_bpmn` (snake_case keys). */
export function toWire<T = Record<string, unknown>>(value: object): T {
  return convertKeys(value, camelToSnake) as T
}

/** JSON of `auditcore_bpmn` → TypeScript object (camelCase keys). */
export function fromWire<T = Record<string, unknown>>(value: Json): T {
  return convertKeys(value, snakeToCamel) as T
}
