/**
 * Embedding a diagram in a Jupyter Book (MyST Markdown), ported from
 * `mystExport.ts` of the audit_designer (`baueMystSchnipsel` →
 * `buildMystSnippet`, `diagrammKennung` → `diagramLabel`, `base64Utf8`,
 * `inZwischenablage` → `copyToClipboard`). The XML travels base64 encoded
 * in a `{bpmn}` directive so the book builds without a side file.
 */

/** Base64 with correct handling of umlauts (`btoa` only knows Latin-1). */
export function base64Utf8(text: string): string {
  const bytes = new TextEncoder().encode(text)
  let binary = ''
  const block = 0x8000
  for (let i = 0; i < bytes.length; i += block) binary += String.fromCharCode(...bytes.subarray(i, i + block))
  return btoa(binary)
}

/** Label for the book: lower case, without blanks and special characters. */
export function diagramLabel(name: string, id: number | string | null): string {
  const base =
    (name || 'diagramm')
      .toLowerCase()
      .replace(/ä/g, 'ae')
      .replace(/ö/g, 'oe')
      .replace(/ü/g, 'ue')
      .replace(/ß/g, 'ss')
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '')
      .slice(0, 60) || 'diagramm'
  return id === null ? base : `${base}-${id}`
}

export interface MystOptions {
  title: string
  name: string
  id: number | string | null
  xml: string
}

export function buildMystSnippet(options: MystOptions): string {
  const caption = (options.title || options.name || 'BPMN-Diagramm').replace(/\r?\n/g, ' ').trim()
  return ['```{bpmn}', '---', `caption: ${caption}`, `name: ${diagramLabel(options.name, options.id)}`, 'format: base64', '---', base64Utf8(options.xml), '```', ''].join('\n')
}

/**
 * Puts text on the clipboard. The fallback through a hidden text field is
 * needed because the Clipboard API is only available in secure contexts.
 */
export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text)
      return true
    }
  } catch {
    // continue with the fallback
  }
  try {
    const field = document.createElement('textarea')
    field.value = text
    field.setAttribute('readonly', '')
    field.style.position = 'fixed'
    field.style.opacity = '0'
    document.body.appendChild(field)
    field.select()
    const success = document.execCommand('copy')
    document.body.removeChild(field)
    return success
  } catch {
    return false
  }
}
