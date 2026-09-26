// Kaufmännische Rundung (half-up, vom Nullpunkt weg) auf Dezimalzeichenketten,
// damit 0,125 → 0,13 und 1,005 → 1,01 werden (Binärgleitkomma und
// `Intl.NumberFormat` allein runden 1,005 auf 1,00).

const PLAIN = /^(-?)(\d+)(?:\.(\d+))?$/

/** Dezimalzeichenkette ohne Exponent (`1e-7` → `0.0000001`); `null` bei nicht endlichen Zahlen. */
export function toPlainDecimal(value: number | string): string | null {
  if (typeof value === 'string') {
    const text = value.trim().replace(/^\+/, '')
    return PLAIN.test(text) ? text : null
  }
  if (!Number.isFinite(value)) return null
  const text = String(value)
  if (!/e/i.test(text)) return text
  return Math.abs(value) < 1 ? value.toFixed(20).replace(/0+$/, '').replace(/\.$/, '') : BigInt(Math.round(value)).toString()
}

function incrementDigits(digits: string): string {
  const chars = digits.split('')
  for (let index = chars.length - 1; index >= 0; index -= 1) {
    if (chars[index] !== '9') {
      chars[index] = String(Number(chars[index]) + 1)
      return chars.join('')
    }
    chars[index] = '0'
  }
  return `1${chars.join('')}`
}

/** Rundet eine Dezimalzeichenkette half-up auf `digits` Nachkommastellen (Ergebnis wieder als Zeichenkette). */
export function roundHalfUp(decimal: string, digits: number): string {
  const match = PLAIN.exec(decimal)
  if (!match) throw new RangeError(`Keine Dezimalzahl: ${decimal}`)
  const [, sign = '', integer = '0', fraction = ''] = match
  const padded = fraction.padEnd(digits + 1, '0')
  let kept = integer + padded.slice(0, digits)
  if (Number(padded[digits]) >= 5) kept = incrementDigits(kept)
  const whole = kept.slice(0, kept.length - digits) || '0'
  const rest = kept.slice(kept.length - digits)
  const text = digits > 0 ? `${whole}.${rest}` : whole
  return /^[0.]+$/.test(text) ? text : `${sign}${text}`
}
