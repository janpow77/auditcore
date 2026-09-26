function copyWithTextarea(text: string): boolean {
  const area = document.createElement('textarea')
  area.value = text
  area.setAttribute('readonly', '')
  area.style.position = 'fixed'
  area.style.opacity = '0'
  document.body.append(area)
  area.select()
  try {
    // execCommand ist veraltet, aber der einzige Weg ohne sicheren Kontext (HTTP im Intranet).
    return document.execCommand('copy')
  } catch {
    return false
  } finally {
    area.remove()
  }
}

/** Kopiert Text in die Zwischenablage (Clipboard-API, sonst Textfeld-Rückfall); `true` bei Erfolg. */
export async function copyText(text: string): Promise<boolean> {
  const clipboard = globalThis.navigator?.clipboard
  if (clipboard && globalThis.isSecureContext !== false) {
    try {
      await clipboard.writeText(text)
      return true
    } catch {
      // Rechte verweigert oder Fokus fehlt: Rückfall unten.
    }
  }
  return typeof document === 'undefined' ? false : copyWithTextarea(text)
}
