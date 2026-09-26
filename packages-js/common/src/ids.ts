function randomBytes(count: number): Uint8Array {
  const bytes = new Uint8Array(count)
  const crypto = globalThis.crypto
  if (crypto && typeof crypto.getRandomValues === 'function') return crypto.getRandomValues(bytes)
  for (let index = 0; index < count; index += 1) bytes[index] = Math.floor(Math.random() * 256)
  return bytes
}

/**
 * Neue UUID v4. Nutzt `crypto.randomUUID` und fällt ohne sicheren Kontext
 * (HTTP im Intranet) auf `crypto.getRandomValues` zurück, zuletzt auf
 * `Math.random` (nur für Anzeige-Kennungen, nicht für Geheimnisse).
 */
export function newId(): string {
  const crypto = globalThis.crypto
  if (crypto && typeof crypto.randomUUID === 'function') return crypto.randomUUID()
  const bytes = randomBytes(16)
  bytes[6] = ((bytes[6] ?? 0) & 0x0f) | 0x40
  bytes[8] = ((bytes[8] ?? 0) & 0x3f) | 0x80
  const hex = Array.from(bytes, (byte) => byte.toString(16).padStart(2, '0')).join('')
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`
}

/** Kurze Kennung mit Präfix für DOM-IDs und Schlüssel (`fa-3k9x2m`); nicht kryptografisch. */
export function shortId(prefix = 'fa'): string {
  const text = Array.from(randomBytes(6), (byte) => (byte % 36).toString(36)).join('')
  return `${prefix}-${text}`
}
