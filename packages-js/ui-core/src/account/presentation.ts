import type { AccountDocument, AccountPort } from './types'
/** Keine beliebigen CSS-Werte aus editierbaren Feldern einsetzen. */
export function accountPreviewStyle(values: Readonly<Record<string, string>>) {
  const color = (value: string | undefined, fallback: string) => /^#[0-9a-f]{6}$/i.test(value ?? '') ? value : fallback
  const fonts: Record<string, string> = { system: 'system-ui, sans-serif', sans: "'DejaVu Sans', sans-serif", serif: "'DejaVu Serif', serif" }
  return { backgroundColor: color(values.primary, '#164e63'), color: color(values.text_on_primary, '#ffffff'),
    fontFamily: fonts[values.body_font ?? ''] ?? fonts.system }
}
export function accountImageUrl(port: AccountPort | null | undefined, id: string): string {
  const url = id ? port?.imageUrl?.(id) ?? '' : ''
  return /^(https?:\/\/|blob:|\/(?!\/))/.test(url) ? url : ''
}
export function accountWelcomePreview(document: AccountDocument, values: Readonly<Record<string, string>>): string {
  if (document.kind !== 'welcome') return ''
  return `${values.heading ?? ''}\n\n${values.body ?? ''}`
    .replace(/{{\s*display_name\s*}}/g, 'Alex Beispiel')
    .replace(/{{\s*tenant_name\s*}}/g, 'Beispielorganisation')
    .replace(/{{\s*contact_name\s*}}/g, 'Organisationskontakt')
}
