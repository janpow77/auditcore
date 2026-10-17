/**
 * Gemeinsamer Kern der Zufallsfälle: Zufallsgenerator mit festem Startwert, Ziehungen in
 * fachlich möglichen Bereichen (Beträge, Anteile, Auswahlwerte), Hilfen für Schichtspalten
 * und die Ausgabe im Fallformat von `scripts/golden_recalc.py`. Alle Werte sind erfunden.
 */

/** Auswahllisten der Vorlage (Blatt 01_Parameter), soweit die Belegungen sie brauchen. */
export const CHOICES = {
  reliability: ['hoch', 'mittel', 'gering'],
  confidence: [0.6, 0.7, 0.8, 0.9, 0.95],
  testType: ['zweiseitig', 'einseitig'],
  yesNo: ['Ja', 'Nein'],
  category: [1, 2, 3, 4],
  recalculation: [
    'Standard (Art. 5 Abs. 6 Buchst. a)',
    'Global (Art. 5 Abs. 6 Buchst. b)',
    'Erhöhung bei begrenztem Umfang (Art. 5 Abs. 7 UAbs. 4 Buchst. a)',
    'keine Neuberechnung',
  ],
  samplingUnit: ['Vorhaben', 'Zahlungsantrag', 'Ausgabenerklärung'],
}

/** Schichtspalten der Blätter 2021–2027 (D bis J) und der Altvorlage X3 (E bis K). */
export const STRATA_COLUMNS = ['D', 'E', 'F', 'G', 'H', 'I', 'J']
export const LEGACY_STRATA_COLUMNS = ['E', 'F', 'G', 'H', 'I', 'J', 'K']

/** Mulberry32: kleiner, reproduzierbarer Zufallsgenerator; liefert Werte in [0, 1). */
export function mulberry32(seed) {
  let state = seed >>> 0
  return () => {
    state = (state + 0x6d2b79f5) >>> 0
    let value = state
    value = Math.imul(value ^ (value >>> 15), value | 1)
    value ^= value + Math.imul(value ^ (value >>> 7), value | 61)
    return ((value ^ (value >>> 14)) >>> 0) / 4294967296
  }
}

/** Startwert je Blatt aus einem gemeinsamen Startwert und dem Blattnamen. */
export function sheetSeed(start, sheet) {
  return [...sheet].reduce((hash, character) => (Math.imul(hash, 31) + character.charCodeAt(0)) >>> 0, start)
}

const round = (value, digits) => Number(value.toFixed(digits))

/** Ziehungen in fachlich möglichen Bereichen auf einem Generator für Werte in [0, 1). */
export function draws(random) {
  return {
    /** Ganze Zahl in [min, max]. */
    int: (min, max) => min + Math.floor(random() * (max - min + 1)),
    /** Betrag in Euro mit zwei Nachkommastellen. */
    amount: (min, max) => round(min + random() * (max - min), 2),
    /** Anteil bzw. Quote mit `digits` Nachkommastellen. */
    rate: (min, max, digits = 4) => round(min + random() * (max - min), digits),
    /** Ein Eintrag einer Auswahlliste. */
    pick: (values) => values[Math.floor(random() * values.length)],
    /** Wahr mit Wahrscheinlichkeit `share`. */
    chance: (share) => random() < share,
  }
}

/** Zellen einer Schichtspalte: `entries` ordnet Zeilen ihren Werten zu, in der Reihenfolge der Zeilen. */
export function stratumCells(column, entries) {
  return Object.fromEntries(entries.map(([row, value]) => [`${column}${row}`, value]))
}

/** Ein Fall im Format der Falldateien. */
export function randomCase(name, sheet, inputs) {
  return { name, blatt: sheet, eingaben: inputs }
}

/** `count` Fälle; `build` erhält die laufende Nummer ab 1. */
export function series(count, build) {
  return Array.from({ length: count }, (_, index) => build(index + 1))
}

/** Dreistellige laufende Nummer für Fallnamen. */
export const padded = (index) => String(index).padStart(3, '0')

/** Wert als JSON; Werte mit eigener Schreibweise (`jsonToken`) bestimmen ihren Text selbst. */
function token(value) {
  return typeof value?.jsonToken === 'function' ? value.jsonToken() : JSON.stringify(value)
}

/**
 * Falldatei als Text: dieselbe Gestalt wie `JSON.stringify(cases, null, 1)` mit Zeilenende,
 * nur dass einzelne Zahlen ihre Schreibweise mitbringen dürfen (siehe `python-random.mjs`).
 */
export function serialize(cases) {
  if (cases.length === 0) return '[]\n'
  const blocks = cases.map((entry) => {
    const cells = Object.entries(entry.eingaben).map(([cell, value]) => `   ${JSON.stringify(cell)}: ${token(value)}`)
    const inputs = cells.length > 0 ? `{\n${cells.join(',\n')}\n  }` : '{}'
    return ` {\n  "name": ${JSON.stringify(entry.name)},\n  "blatt": ${JSON.stringify(entry.blatt)},\n  "eingaben": ${inputs}\n }`
  })
  return `[\n${blocks.join(',\n')}\n]\n`
}
