const HTML_ESCAPES: Readonly<Record<string, string>> = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }

/** Maskiert die fünf HTML-Sonderzeichen `& < > " '` (für Text in HTML und Attributen). */
export function escapeHtml(value: unknown): string {
  return String(value ?? '').replace(/[&<>"']/g, (char) => HTML_ESCAPES[char] ?? char)
}

/** Kürzt auf höchstens `max` Zeichen (Codepunkte) inklusive Auslassungszeichen. */
export function truncate(text: string, max: number, ellipsis = '…'): string {
  const chars = Array.from(text)
  if (chars.length <= max) return text
  const room = Math.max(0, max - Array.from(ellipsis).length)
  return `${chars.slice(0, room).join('').trimEnd()}${ellipsis}`
}

/** Initialen aus einem Namen (`Jan Riener` → `JR`, `riener, jan` → `RJ`), höchstens `max` Zeichen. */
export function initials(name: string, max = 2): string {
  const words = name.split(/[\s,.\-_]+/).filter((word) => word !== '')
  const letters = words.map((word) => Array.from(word)[0] ?? '').join('')
  return Array.from(letters).slice(0, max).join('').toLocaleUpperCase('de-DE')
}

const TRANSLITERATION: Readonly<Record<string, string>> = { ä: 'ae', ö: 'oe', ü: 'ue', ß: 'ss', Ä: 'ae', Ö: 'oe', Ü: 'ue' }

/** URL-/Dateinamen-Kennung: Kleinbuchstaben, Ziffern und `-`; deutsche Sonderzeichen werden umschrieben. */
export function slugify(text: string, max = 80): string {
  const plain = text
    .replace(/[äöüßÄÖÜ]/g, (char) => TRANSLITERATION[char] ?? char)
    .normalize('NFKD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
  return plain.slice(0, max).replace(/-+$/, '')
}
