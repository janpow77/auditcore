/** Anzeige eines beliebigen Werts wie Vues `{{ }}` (toDisplayString): leer, Text oder JSON. */
export function displayValue(value: unknown): string {
  if (value === null || value === undefined) return ''
  if (typeof value === 'object') return JSON.stringify(value, null, 2)
  return String(value)
}
