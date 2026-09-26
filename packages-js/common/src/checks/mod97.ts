// Prüfziffern nach ISO 7064 MOD 97-10 (IBAN, LEI, Leitweg-ID). Buchstaben
// zählen als A=10 … Z=35. Die IBAN-Länderlängen entsprechen dem
// SWIFT-Register wie in `auditcore_identifiers.registry.IBAN_LENGTHS`.

/** Rest modulo 97 einer beliebig langen Ziffernfolge (stückweise, ohne BigInt). */
export function mod97(digits: string): number {
  if (!/^\d+$/.test(digits)) throw new RangeError('mod97 erwartet nur Ziffern')
  let rest = 0
  for (let index = 0; index < digits.length; index += 7) {
    rest = Number(`${rest}${digits.slice(index, index + 7)}`) % 97
  }
  return rest
}

/** Buchstaben in Zahlen (A=10 … Z=35); andere Zeichen bleiben. */
export function lettersToDigits(text: string): string {
  return text.replace(/[A-Z]/g, (char) => String(char.charCodeAt(0) - 55))
}

/** Zwei Prüfziffern nach ISO 7064 MOD 97-10 für einen Rumpf aus A–Z/0–9. */
export function iso7064CheckDigits(body: string): string {
  const value = 98 - mod97(lettersToDigits(body.toUpperCase()) + '00')
  return String(value).padStart(2, '0')
}

/** IBAN-Gesamtlänge je Land (SWIFT-Register, gleich `auditcore_identifiers`). */
export const IBAN_LENGTHS: Readonly<Record<string, number>> = Object.freeze({
  AD: 24, AE: 23, AL: 28, AT: 20, AZ: 28, BA: 20, BE: 16, BG: 22, BH: 22, BI: 27, BR: 29, BY: 28, CH: 21, CR: 22,
  CY: 28, CZ: 24, DE: 22, DJ: 27, DK: 18, DO: 28, EE: 20, EG: 29, ES: 24, FI: 18, FK: 18, FO: 18, FR: 27, GB: 22,
  GE: 22, GI: 23, GL: 18, GR: 27, GT: 28, HN: 28, HR: 21, HU: 28, IE: 22, IL: 23, IQ: 23, IS: 26, IT: 27, JO: 30,
  KW: 30, KZ: 20, LB: 28, LC: 32, LI: 21, LT: 20, LU: 20, LV: 21, LY: 25, MC: 27, MD: 24, ME: 22, MK: 19, MN: 20,
  MR: 27, MT: 31, MU: 30, NI: 28, NL: 18, NO: 15, OM: 23, PK: 24, PL: 28, PS: 29, PT: 25, QA: 29, RO: 24, RS: 22,
  RU: 33, SA: 24, SC: 31, SD: 18, SE: 24, SI: 19, SK: 24, SM: 27, SO: 23, ST: 25, SV: 28, TL: 23, TN: 24, TR: 26,
  UA: 29, VA: 22, VG: 24, XK: 20, YE: 30,
})

/** IBAN ohne Leerraum, in Großbuchstaben. */
export function normalizeIban(text: string): string {
  return text.replace(/\s+/g, '').toUpperCase()
}

/** IBAN in Vierergruppen (`DE89 3704 0044 …`). */
export function formatIban(text: string): string {
  return normalizeIban(text).replace(/(.{4})(?=.)/g, '$1 ')
}

/** Gültig nur mit bekanntem Land, passender Länge und Prüfziffer (Leerzeichen und Kleinbuchstaben erlaubt). */
export function isValidIban(text: string): boolean {
  const iban = normalizeIban(text)
  if (!/^[A-Z]{2}\d{2}[A-Z0-9]+$/.test(iban)) return false
  if (IBAN_LENGTHS[iban.slice(0, 2)] !== iban.length) return false
  return mod97(lettersToDigits(iban.slice(4) + iban.slice(0, 4))) === 1
}

/** LEI nach ISO 17442: 20 Zeichen A–Z/0–9, die letzten beiden sind Prüfziffern (MOD 97-10). */
export function isValidLei(text: string): boolean {
  const lei = text.trim().toUpperCase()
  return /^[A-Z0-9]{18}\d{2}$/.test(lei) && mod97(lettersToDigits(lei)) === 1
}

/** Prüfziffern einer Leitweg-ID (XRechnung) aus Grob- und Feinadressierung, z. B. `04011000-1234512345`. */
export function leitwegCheckDigits(idWithoutCheck: string): string {
  return iso7064CheckDigits(idWithoutCheck.replace(/-/g, ''))
}

/** Leitweg-ID `Grob[-Fein]-Prüfziffer` mit gültiger Prüfziffer. */
export function isValidLeitwegId(text: string): boolean {
  const id = text.trim().toUpperCase()
  const match = /^(\d{2,12}(?:-[A-Z0-9]{1,30})?)-(\d{2})$/.exec(id)
  return match !== null && leitwegCheckDigits(match[1] ?? '') === match[2]
}
