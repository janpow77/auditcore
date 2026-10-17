/**
 * Zufallsgenerator, Rundung, Summe und Zahlenschreibweise wie in Python 3.12. Die Fallsätze der
 * Blätter 05–07 und 13–16 sind ursprünglich mit Python-Skripten (`random.Random(startwert)`)
 * entstanden; damit dieselben Startwerte dieselben Dateien liefern, bildet dieses Modul nach:
 *
 * - den Mersenne-Twister MT19937 samt Startwertbildung (`init_by_array`),
 * - `random`, `uniform`, `randint`, `choice`, `sample` in der Ziehungsreihenfolge von CPython,
 * - `round(x, n)` (kaufmännisch nur scheinbar: exakte Mitten gehen zur geraden Ziffer),
 * - `sum` über Gleitkommazahlen (Ausgleichssummation nach Neumaier, seit Python 3.12),
 * - die Schreibweise von Gleitkommazahlen (`26083489.0`, `0.0`, `2.3e-05`).
 */

const N = 624
const M = 397
const UPPER = 0x80000000
const LOWER = 0x7fffffff

/** Zustand des MT19937 aus einem Schlüssel aus 32-Bit-Wörtern (`init_by_array`). */
function initialState(key) {
  const mt = new Uint32Array(N)
  mt[0] = 19650218
  for (let i = 1; i < N; i += 1) mt[i] = Math.imul(1812433253, mt[i - 1] ^ (mt[i - 1] >>> 30)) + i
  let i = 1
  let j = 0
  const advance = () => {
    i += 1
    if (i >= N) {
      mt[0] = mt[N - 1]
      i = 1
    }
  }
  for (let k = Math.max(N, key.length); k > 0; k -= 1) {
    mt[i] = (mt[i] ^ Math.imul(mt[i - 1] ^ (mt[i - 1] >>> 30), 1664525)) + key[j] + j
    advance()
    j = (j + 1) % key.length
  }
  for (let k = N - 1; k > 0; k -= 1) {
    mt[i] = (mt[i] ^ Math.imul(mt[i - 1] ^ (mt[i - 1] >>> 30), 1566083941)) - i
    advance()
  }
  mt[0] = UPPER
  return mt
}

/** Nächster Block von 624 Zustandswörtern. */
function twist(mt) {
  for (let k = 0; k < N; k += 1) {
    const y = (mt[k] & UPPER) | (mt[(k + 1) % N] & LOWER)
    mt[k] = mt[(k + M) % N] ^ (y >>> 1) ^ (y & 1 ? 0x9908b0df : 0)
  }
}

/** MT19937 mit ganzzahligem Startwert (bis 2^53) wie `random.Random(startwert)`; liefert 32-Bit-Zahlen. */
export function mersenneTwister(seed) {
  const high = Math.floor(seed / 4294967296)
  const mt = initialState(high > 0 ? [seed >>> 0, high] : [seed >>> 0])
  let position = N
  return () => {
    if (position >= N) {
      twist(mt)
      position = 0
    }
    let y = mt[position]
    position += 1
    y ^= y >>> 11
    y ^= (y << 7) & 0x9d2c5680
    y ^= (y << 15) & 0xefc60000
    return (y ^ (y >>> 18)) >>> 0
  }
}

/** Gleitkommazahl mit der Schreibweise von Python; rechnet in Ausdrücken wie eine Zahl. */
export class PyFloat {
  constructor(value) {
    this.value = value
  }

  valueOf() {
    return this.value
  }

  jsonToken() {
    return floatRepr(this.value)
  }
}

/** `repr(float)`: ganzzahlige Werte mit `.0`, sehr kleine in Exponentialschreibweise mit zwei Stellen. */
export function floatRepr(value) {
  if (Object.is(value, -0)) return '-0.0'
  if (Number.isInteger(value) && Math.abs(value) < 1e16) return `${value}.0`
  if (Math.abs(value) < 1e-4) {
    const [mantissa, exponent] = value.toExponential().split('e')
    const digits = String(Math.abs(Number(exponent))).padStart(2, '0')
    return `${mantissa}e${Number(exponent) < 0 ? '-' : '+'}${digits}`
  }
  return String(value)
}

/** `round(x, digits)`: richtig gerundet, exakte Mitten zur geraden Ziffer. */
export function pyRound(x, digits) {
  const scaled = Number(x) * 2 ** (digits + 1)
  if (Number.isInteger(scaled) && scaled % 2 !== 0) {
    const doubled = scaled * 5 ** digits
    const lower = (doubled - 1) / 2
    return new PyFloat((lower % 2 === 0 ? lower : lower + 1) / 10 ** digits)
  }
  return new PyFloat(Number(Number(x).toFixed(digits)))
}

/** `round(x)`: ganze Zahl, exakte Mitten zur geraden Zahl. */
export function pyRoundInt(x) {
  const floor = Math.floor(x)
  const rest = x - floor
  if (rest < 0.5) return floor
  if (rest > 0.5) return floor + 1
  return floor % 2 === 0 ? floor : floor + 1
}

/** `sum(values)` über Gleitkommazahlen mit Ausgleichssummation (Neumaier). */
export function pySum(values) {
  const [first = 0, ...rest] = values.map(Number)
  let total = first
  let compensation = 0
  for (const x of rest) {
    const next = total + x
    compensation += Math.abs(total) >= Math.abs(x) ? total - next + x : x - next + total
    total = next
  }
  return compensation !== 0 && Number.isFinite(compensation) ? total + compensation : total
}

/** Aufrundende Ganzzahldivision `-(-a // b)`. */
export function ceilDiv(a, b) {
  const quotient = Math.floor(a / b)
  return quotient * b === a ? quotient : quotient + 1
}

/**
 * Ziehungen wie `random.Random(seed)`. Neben den Python-Namen (`random`, `uniform`, `sample`)
 * stehen dieselben Hilfen wie in `core.mjs` (`int`, `amount`, `rate`, `pick`, `chance`);
 * `amount` und `rate` liefern `PyFloat`, damit die Schreibweise in der Falldatei stimmt.
 */
export function pythonRandom(seed) {
  const next = mersenneTwister(seed)
  const random = () => ((next() >>> 5) * 67108864 + (next() >>> 6)) / 9007199254740992
  const below = (n) => {
    const shift = Math.clz32(n)
    let value = next() >>> shift
    while (value >= n) value = next() >>> shift
    return value
  }
  const uniform = (min, max) => min + (max - min) * random()
  /** `sample(population, count)` für kleine Grundgesamtheiten (Auswahl aus einer Kopie). */
  const sample = (population, count) => {
    const pool = [...population]
    return Array.from({ length: count }, (_, index) => {
      const position = below(pool.length - index)
      const chosen = pool[position]
      pool[position] = pool[pool.length - index - 1]
      return chosen
    })
  }
  return {
    random,
    uniform,
    sample,
    int: (min, max) => min + below(max - min + 1),
    amount: (min, max) => pyRound(uniform(min, max), 2),
    rate: (min, max, digits = 4) => pyRound(uniform(min, max), digits),
    pick: (values) => values[below(values.length)],
    chance: (share) => random() < share,
  }
}

/** Betrag in Euro: `round(value, 2)`. */
export const euro = (value) => pyRound(value, 2)
