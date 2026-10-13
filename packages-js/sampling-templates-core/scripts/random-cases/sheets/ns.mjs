/**
 * Zufallsbelegungen der Blätter 13–16 (nichtstatistische Stichproben): alle Eingaben ausgefüllt,
 * Anzahl der Einheiten um die Schwellen des Art. 79 Abs. 2 VO (EU) 2021/1060 gestreut (299, 300,
 * darüber), Stichprobenumfang um die Mindesterfassung von 10 % herum. Die Fallsätze sind mit
 * Python-Skripten entstanden; die Ziehungsreihenfolge hier entspricht ihnen (siehe
 * `python-random.mjs`). Der Generator jedes Blatts startet mit Startwert + Blattnummer.
 */
import { STRATA_COLUMNS, padded, randomCase, series, stratumCells } from '../core.mjs'
import { ceilDiv, euro, pyRound, pyRoundInt, pySum, pythonRandom } from '../python-random.mjs'

const START = 20261013
const COUNT = 120
const TEXT = { C4: 'Beispiel – EFRE-Programm', C5: '2025/2026', C6: 'Vorhaben' }
const MATERIALITY = [0.02, 0.02, 0.02, 0.015, 0.01]
/** Größen, bei denen 0,1 · N im Gleitkomma knapp neben der ganzen Zahl liegt. */
const AWKWARD_SIZES = [30, 70, 110, 170, 230, 290]

/** Anzahl der Einheiten: unter, auf und über der Schwelle von 300. */
const populationUnits = (r) => r.pick([r.int(20, 299), r.int(20, 299), r.int(300, 650), 299, 300, r.pick(AWKWARD_SIZES)])
const stratifiedUnits = (r) => r.pick([r.int(20, 299), r.int(20, 299), r.int(300, 650), 299, 300])

/** Fehlersumme einer Stichprobe: 0, bis 5 %, bis 2 % oder leicht negativ bis 3 % ihres Buchwerts. */
const sampleErrors = (r, bookValue) =>
  r.pick([0, euro(bookValue * r.uniform(0, 0.05)), euro(bookValue * r.uniform(0, 0.02)), euro(bookValue * r.uniform(-0.005, 0.03))])

/** Abgegrenzte systembedingte bzw. anomale Fehler: in zwei von drei Fällen 0. */
const separatedErrors = (r, bookValue, share) => r.pick([0, 0, euro(bookValue * r.uniform(0, share))])

/** Summe der Fehlerquoten: 0 oder ein Wert bis `wide`, bis `narrow` oder leicht negativ bis `mixed`. */
const errorRates = (r, wide, narrow, mixed) =>
  r.pick([0, pyRound(r.uniform(0, wide), 4), pyRound(r.uniform(0, narrow), 6), pyRound(r.uniform(-0.02, mixed), 4)])

/** Belegte Schichtspalten: die ersten drei Fälle mit 1, 3 und 7 Schichten, in 30 % der Fälle mit Lücken. */
function strataColumns(r, index) {
  const count = index <= 3 ? [1, 3, 7][index - 1] : r.int(1, 7)
  return r.chance(0.3) ? r.sample(STRATA_COLUMNS, count).sort() : STRATA_COLUMNS.slice(0, count)
}

/** Einheiten je Schicht: `total` nach zufälligen Gewichten verteilt, je Schicht mindestens eine. */
function strataUnits(r, count, total) {
  const weights = Array.from({ length: count }, () => r.uniform(0.2, 1))
  const sum = pySum(weights)
  return weights.map((weight) => Math.max(1, pyRoundInt((total * weight) / sum)))
}

const total = (values) => values.reduce((sum, value) => sum + value, 0)
const name = (index, start) => `Zufall ${padded(index)} (Startwert ${start})`

function inputs13(r) {
  const bookValue = r.amount(2e5, 4e7)
  const units = populationUnits(r)
  const exhaustive = r.chance(0.6)
  const share = exhaustive ? r.uniform(0.02, 0.4) : 0
  const exhaustiveUnits = exhaustive ? r.int(1, 8) : 0
  const sampleSize = Math.max(1, ceilDiv(units, 10) + r.pick([-2, -1, 0, 0, 1, 3, 10]) - exhaustiveUnits)
  const sampleBookValue = euro(bookValue * (1 - share) * r.uniform(0.05, 0.5))
  const errors = sampleErrors(r, sampleBookValue)
  return {
    ...TEXT, C7: bookValue, C8: units, C10: euro(bookValue * share), C11: exhaustiveUnits, C13: sampleSize,
    C17: sampleBookValue, C18: errors, C19: r.pick([0, euro(bookValue * share * r.uniform(0, 0.03))]),
    C23: separatedErrors(r, bookValue, 0.01), C24: separatedErrors(r, bookValue, 0.004), C27: r.pick(MATERIALITY),
  }
}

function inputs14(r, index) {
  const columns = strataColumns(r, index)
  const totalUnits = stratifiedUnits(r)
  const exhaustive = r.chance(0.5)
  const exhaustiveUnits = exhaustive ? r.int(1, 8) : 0
  const units = strataUnits(r, columns.length, totalUnits - exhaustiveUnits)
  const bookValues = units.map((count) => euro(count * r.uniform(8000, 60000)))
  const sampleBookValues = bookValues.map((bookValue) => euro(bookValue * r.uniform(0.05, 0.5)))
  const errors = sampleBookValues.map((bookValue) => sampleErrors(r, bookValue))
  const sampleSize = Math.max(1, ceilDiv(total(units) + exhaustiveUnits, 10) + r.pick([-3, -1, 0, 0, 1, 3, 10]) - exhaustiveUnits)
  const bookValue = pySum(bookValues)
  const exhaustiveBookValue = exhaustive ? euro(bookValue * r.uniform(0.02, 0.3)) : 0
  const strata = columns.map((column, position) =>
    stratumCells(column, [[11, units[position]], [12, bookValues[position]], [24, sampleBookValues[position]], [25, errors[position]]]),
  )
  return {
    ...TEXT, ...Object.assign({}, ...strata), C8: exhaustiveBookValue, C9: exhaustiveUnits, C16: sampleSize,
    C22: r.pick([0, euro(exhaustiveBookValue * r.uniform(0, 0.03))]),
    C30: separatedErrors(r, bookValue, 0.01), C31: separatedErrors(r, bookValue, 0.004), C34: r.pick(MATERIALITY),
  }
}

function inputs15(r) {
  const bookValue = r.amount(2e5, 4e7)
  const units = populationUnits(r)
  const sampleSize = Math.max(3, ceilDiv(units, 10) + r.pick([-2, -1, 0, 0, 1, 3, 10]))
  const drawn = r.pick([0, 0, r.int(1, 4), r.int(1, 4), Math.max(0, sampleSize - r.int(0, 3))])
  const highValueUnits = Math.min(drawn, sampleSize + 1)
  const share = highValueUnits ? r.uniform(0.05, 0.5) : 0
  return {
    ...TEXT, C7: bookValue, C8: units, C10: sampleSize, C14: highValueUnits, C15: euro(bookValue * share),
    C20: r.pick([0, 0, 0, 1, 3]), C22: highValueUnits ? r.pick([0, euro(bookValue * share * r.uniform(0, 0.03))]) : 0,
    C23: errorRates(r, 0.8, 0.3, 0.2),
    C27: separatedErrors(r, bookValue, 0.01), C28: separatedErrors(r, bookValue, 0.004), C31: r.pick(MATERIALITY),
  }
}

/** Hochwertige Einheiten je Schicht Blatt 16: Anzahl, Buchwert, Fehlersumme. */
function highValue16(r, bookValues, sampleSize) {
  const bookValue = pySum(bookValues)
  const allocated = bookValues.map((value) => Math.max(1, ceilDiv(Math.trunc((value / bookValue) * sampleSize * 1000), 1000)))
  const units = allocated.map((size) => r.pick([0, 0, r.int(0, Math.max(0, size - 1)), r.chance(0.1) ? size : 0]))
  const values = units.map((count, position) => (count ? euro(bookValues[position] * r.uniform(0.05, 0.5)) : 0))
  const errors = values.map((value) => r.pick([0, euro(value * r.uniform(0, 0.03))]))
  return { units, values, errors }
}

function inputs16(r, index) {
  const columns = strataColumns(r, index)
  const units = strataUnits(r, columns.length, stratifiedUnits(r))
  const bookValues = units.map((count) => euro(count * r.uniform(8000, 60000)))
  const sampleSize = Math.max(1, ceilDiv(total(units), 10) + r.pick([-3, -1, 0, 0, 1, 3, 10]))
  const highValue = highValue16(r, bookValues, sampleSize)
  const rates = units.map(() => errorRates(r, 0.5, 0.2, 0.1))
  const rows = [[9, bookValues], [10, units], [19, highValue.units], [20, highValue.values], [25, highValue.errors], [26, rates]]
  const strata = rows.map(([row, values]) => Object.fromEntries(columns.map((column, position) => [`${column}${row}`, values[position]])))
  const bookValue = pySum(bookValues)
  return {
    ...TEXT, ...Object.assign({}, ...strata), C13: sampleSize,
    C31: separatedErrors(r, bookValue, 0.01), C32: separatedErrors(r, bookValue, 0.004), C35: r.pick(MATERIALITY),
  }
}

/** Beschreibung eines Blatts: Generator mit Startwert + Blattnummer, Name mit dem Startwert. */
function sheet(sheetName, number, inputs) {
  return {
    start: START,
    count: COUNT,
    cases: ({ start, count }) => {
      const r = pythonRandom(start + number)
      return series(count, (index) => randomCase(name(index, start), sheetName, inputs(r, index)))
    },
  }
}

export const sheets = {
  '13_NS_GW': sheet('13_NS_GW', 13, inputs13),
  '14_NS_GW_S': sheet('14_NS_GW_S', 14, inputs14),
  '15_NS_PPS': sheet('15_NS_PPS', 15, inputs15),
  '16_NS_PPS_S': sheet('16_NS_PPS_S', 16, inputs16),
}
