/**
 * Zufallsbelegungen der Blätter 05–07 (MUS-Standardansatz über mehrere Zeiträume): alle Eingaben
 * ausgefüllt, Auswahlfelder über alle Einträge. Die Fallsätze sind mit Python-Skripten entstanden;
 * die Ziehungsreihenfolge hier entspricht ihnen Zeile für Zeile (siehe `python-random.mjs`).
 * Die aktualisierte voraussichtliche Fehlerquote späterer Zeiträume ist nur in einem Teil der
 * Fälle belegt und steht deshalb am Ende der Eingaben.
 */
import { CHOICES, STRATA_COLUMNS, padded, randomCase, series } from '../core.mjs'
import { euro, pyRoundInt, pythonRandom } from '../python-random.mjs'

const MATERIALITY = [0.02, 0.02, 0.02, 0.015, 0.01]

/** Ist-Anzahl zu einer Prognose: Faktor in [min, max], mindestens `floor` Einheiten. */
const actualUnits = (r, forecast, min, max, floor) => Math.max(floor, pyRoundInt(forecast * r.uniform(min, max)))

/** Abgegrenzte systembedingte bzw. anomale Fehler: in zwei von drei Fällen 0. */
const separatedErrors = (r, max) => r.pick([0, 0, r.amount(0, max)])

function inputs05(r, index) {
  const bookValue1 = r.amount(2e6, 9e7)
  const forecastBookValue2 = r.amount(2e6, 9e7)
  const bookValue2 = euro(forecastBookValue2 * r.uniform(0.6, 1.5))
  const units1 = r.int(60, 900)
  const forecastUnits2 = r.int(60, 900)
  const units2 = actualUnits(r, forecastUnits2, 0.6, 1.5, 30)
  const cells = {
    C4: `Zufall ${index}`, C5: '2025/2026', C6: r.pick(CHOICES.samplingUnit),
    C7: bookValue1, C8: forecastBookValue2, C9: units1, C10: forecastUnits2,
    C12: r.pick(CHOICES.reliability), C13: r.pick(CHOICES.confidence), C14: r.pick(CHOICES.testType), C17: r.pick(MATERIALITY),
    C20: r.rate(0, 0.022), C23: r.rate(0.01, 0.6), C24: r.rate(0.01, 0.6), C26: r.pick(CHOICES.recalculation), C28: r.pick(CHOICES.category),
    C29: r.pick(CHOICES.yesNo), C30: r.pick(CHOICES.yesNo),
    C37: r.int(0, 12), C38: euro(bookValue1 * r.uniform(0, 0.3)), C43: r.pick([0, 0, 0, 1, 3]),
    C45: r.amount(0, 60000), C46: r.rate(0, 2), C47: r.rate(0, 0.4),
    C48: bookValue2, C49: units2, C50: r.rate(0.01, 0.6),
    C71: r.int(0, 12), C72: euro(bookValue2 * r.uniform(0, 0.3)), C77: r.pick([0, 0, 0, 2]),
    C80: r.amount(0, 60000), C81: r.rate(0, 2), C82: r.rate(0, 0.4),
    C87: separatedErrors(r, 90000), C88: separatedErrors(r, 20000),
  }
  if (r.chance(0.6)) cells.C51 = r.rate(0, 0.022)
  return cells
}

/** Schichtspalte Blatt 06: Zeitraum 1, Prognose und Ist für Zeitraum 2, Prüfergebnisse beider Zeiträume. */
function stratum06(r, column) {
  const bookValue1 = r.amount(5e5, 4e7)
  const forecastBookValue2 = r.amount(5e5, 4e7)
  const bookValue2 = euro(forecastBookValue2 * r.uniform(0.6, 1.5))
  const forecastUnits2 = r.int(20, 400)
  return {
    [`${column}8`]: bookValue1, [`${column}9`]: forecastBookValue2, [`${column}10`]: forecastUnits2,
    [`${column}24`]: r.rate(0.01, 0.6), [`${column}25`]: r.rate(0.01, 0.6),
    [`${column}41`]: r.int(0, 6), [`${column}42`]: euro(bookValue1 * r.uniform(0, 0.3)),
    [`${column}47`]: r.amount(0, 40000), [`${column}48`]: r.rate(0, 1.2), [`${column}49`]: r.rate(0, 0.4),
    [`${column}51`]: bookValue2, [`${column}52`]: actualUnits(r, forecastUnits2, 0.6, 1.5, 10), [`${column}53`]: r.rate(0.01, 0.6),
    [`${column}75`]: r.int(0, 6), [`${column}76`]: euro(bookValue2 * r.uniform(0, 0.3)),
    [`${column}81`]: r.amount(0, 40000), [`${column}82`]: r.rate(0, 1.2), [`${column}83`]: r.rate(0, 0.4),
  }
}

function case06(r, index) {
  const strata = r.pick([1, 2, 3, 3, 4, 5, 7, 7])
  const cells = {
    C4: `Zufall ${index}`, C5: '2025/2026', C6: r.pick(CHOICES.samplingUnit),
    C12: r.pick(CHOICES.reliability), C13: r.pick(CHOICES.confidence), C14: r.pick(CHOICES.testType), C17: r.pick(MATERIALITY),
    C20: r.rate(0, 0.022), C28: r.pick(CHOICES.recalculation), C30: r.pick(CHOICES.category),
    C31: r.pick(CHOICES.yesNo), C32: r.pick(CHOICES.yesNo),
    C91: separatedErrors(r, 90000), C92: separatedErrors(r, 20000),
  }
  if (r.chance(0.5)) cells.C54 = r.rate(0, 0.022)
  for (const column of STRATA_COLUMNS.slice(0, strata)) Object.assign(cells, stratum06(r, column))
  return randomCase(`Zufallsbelegung ${padded(index)} (${strata} Schichten)`, '06_MUS_2Z_S', cells)
}

/** Buchwerte und Anzahlen Blatt 07: Prognosen, aktualisierte Prognose für Zeitraum 3, Ist-Werte. */
function periods07(r) {
  const bookValue1 = r.amount(2e6, 6e7)
  const forecastBookValue2 = r.amount(2e6, 6e7)
  const forecastBookValue3 = r.amount(2e6, 6e7)
  const bookValue2 = euro(forecastBookValue2 * r.uniform(0.6, 1.5))
  const updatedBookValue3 = euro(forecastBookValue3 * r.uniform(0.7, 1.4))
  const bookValue3 = euro(updatedBookValue3 * r.uniform(0.6, 1.5))
  const forecastUnits2 = r.int(60, 700)
  const forecastUnits3 = r.int(60, 700)
  const units2 = actualUnits(r, forecastUnits2, 0.6, 1.5, 30)
  const updatedUnits3 = actualUnits(r, forecastUnits3, 0.7, 1.4, 30)
  const units3 = actualUnits(r, updatedUnits3, 0.6, 1.5, 30)
  return { bookValue1, forecastBookValue2, forecastBookValue3, bookValue2, updatedBookValue3, bookValue3, forecastUnits2, forecastUnits3, units2, updatedUnits3, units3 }
}

function inputs07(r, index) {
  const p = periods07(r)
  const deviation = () => r.rate(0.01, 0.6)
  const cells = {
    C4: `Zufall ${index}`, C5: '2025/2026', C6: r.pick(CHOICES.samplingUnit),
    C7: p.bookValue1, C8: p.forecastBookValue2, C9: p.forecastBookValue3, C10: p.forecastUnits2, C11: p.forecastUnits3,
    C13: r.pick(CHOICES.reliability), C14: r.pick(CHOICES.confidence), C15: r.pick(CHOICES.testType), C18: r.pick(MATERIALITY),
    C21: r.rate(0, 0.022), C24: deviation(), C25: deviation(), C26: deviation(),
    C28: r.pick(CHOICES.recalculation), C30: r.pick(CHOICES.category), C31: r.pick(CHOICES.yesNo), C32: r.pick(CHOICES.yesNo),
    C40: r.int(0, 10), C41: euro(p.bookValue1 * r.uniform(0, 0.3)), C46: r.pick([0, 0, 0, 1, 3]),
    C48: r.amount(0, 60000), C49: r.rate(0, 2), C50: r.rate(0, 0.4),
    C51: p.bookValue2, C52: p.units2, C53: p.updatedBookValue3, C54: p.updatedUnits3, C55: deviation(), C56: deviation(),
    C79: r.int(0, 10), C80: euro(p.bookValue2 * r.uniform(0, 0.3)), C85: r.pick([0, 0, 0, 2]),
    C87: r.amount(0, 60000), C88: r.rate(0, 2), C89: r.rate(0, 0.4),
    C90: p.bookValue3, C91: p.units3, C92: deviation(),
    C113: r.int(0, 10), C114: euro(p.bookValue3 * r.uniform(0, 0.3)), C119: r.pick([0, 0, 0, 2]),
    C121: r.amount(0, 60000), C122: r.rate(0, 2), C123: r.rate(0, 0.4),
    C130: separatedErrors(r, 90000), C131: separatedErrors(r, 20000),
  }
  if (r.chance(0.5)) cells.C57 = r.rate(0, 0.022)
  if (r.chance(0.5)) cells.C93 = r.rate(0, 0.022)
  return cells
}

/** Fälle mit dem Namen „Zufallsbelegung 001“ aus einer Belegungsfunktion. */
const plain = (sheet, inputs) => ({ start, count }) => {
  const r = pythonRandom(start)
  return series(count, (index) => randomCase(`Zufallsbelegung ${padded(index)}`, sheet, inputs(r, index)))
}

export const sheets = {
  '05_MUS_2Z': { start: 2026101305, count: 100, cases: plain('05_MUS_2Z', inputs05) },
  '06_MUS_2Z_S': {
    start: 2026101306,
    count: 100,
    cases: ({ start, count }) => {
      const r = pythonRandom(start)
      return series(count, (index) => case06(r, index))
    },
  },
  '07_MUS_3Z': { start: 2026101307, count: 100, cases: plain('07_MUS_3Z', inputs07) },
}
