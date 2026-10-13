/**
 * Zufallsbelegungen der Blätter 08–12 (einfaches Zufallsstichprobenverfahren): alle Eingaben
 * ausgefüllt, in den geschichteten Blättern alle sieben Schichtspalten, Auswahlfelder über alle
 * Einträge (auch die vier Ansätze der Neuberechnung). Der Generator jedes Blatts startet mit
 * einem Wert, der aus dem gemeinsamen Startwert und dem Blattnamen gebildet wird.
 */
import { CHOICES, STRATA_COLUMNS, draws, mulberry32, padded, randomCase, series, sheetSeed } from '../core.mjs'

const START = 20231067
const COUNT = 100
const MATERIALITY = [0.02, 0.02, 0.02, 0.015, 0.03]
/** „Nein“ doppelt so häufig wie „Ja“. */
const MOSTLY_NO = ['Ja', 'Nein', 'Nein']
const money = (value) => Number(value.toFixed(2))

/** Abgegrenzte systembedingte und anomale Fehler: in 60 % der Fälle 0. */
const separated = (r, max) => (r.chance(0.6) ? 0 : r.amount(0, max))

function inputs08(r) {
  const units = r.int(120, 2500)
  const bookValue = r.amount(5e6, 2e8)
  const exhaustiveUnits = r.int(0, 12)
  const mean = bookValue / units
  return {
    C4: 'Zufallsfall', C5: '2025/2026', C6: 'Vorhaben',
    C7: bookValue, C8: units,
    C9: exhaustiveUnits === 0 ? 0 : money(r.rate(0.02, 0.3) * bookValue),
    C10: exhaustiveUnits, C11: r.int(0, exhaustiveUnits),
    C14: r.pick(CHOICES.reliability), C15: r.pick(CHOICES.confidence), C16: r.pick(CHOICES.testType),
    C19: r.pick(MATERIALITY), C22: r.rate(0, 0.024),
    C25: r.amount(0.02 * mean, 0.6 * mean),
    C27: r.pick(CHOICES.category), C28: r.pick(MOSTLY_NO), C29: r.pick(MOSTLY_NO),
    C36: r.amount(20 * mean, 120 * mean), C37: r.amount(0, 2.5 * mean),
    C38: r.amount(0.01 * mean, 0.4 * mean), C39: r.amount(0.01 * mean, 0.4 * mean),
    C40: r.chance(0.5) ? 0 : r.amount(0, 0.5 * mean),
    C45: separated(r, 2 * mean), C46: separated(r, mean),
  }
}

/** Blatt 02 mit festen Werten, damit der Abgleich mit der angepassten Grundgesamtheit einen Wert hat. */
const POPULATION = {
  '02_Grundgesamtheit!C15': 49200000, '02_Grundgesamtheit!C16': 49200000, '02_Grundgesamtheit!C20': 700000, '02_Grundgesamtheit!C21': 'Ja',
  '02_Grundgesamtheit!C23': 432, '02_Grundgesamtheit!C24': 420, '02_Grundgesamtheit!C25': 48500000, '02_Grundgesamtheit!C26': 12, '02_Grundgesamtheit!C27': 0,
  '02_Grundgesamtheit!C36': 'Ja', '02_Grundgesamtheit!C40': 400000, '02_Grundgesamtheit!C49': 'keine betroffenen Einheiten',
}

function inputs09(r) {
  const exhaustiveUnits = r.int(0, 12)
  const cells = {
    C4: 'Zufallsfall', C5: '2025/2026', C6: 'Vorhaben', C7: 'Fonds',
    C8: exhaustiveUnits === 0 ? 0 : r.amount(2e5, 2e7), C9: exhaustiveUnits, C10: r.int(0, exhaustiveUnits),
    C16: r.pick(CHOICES.reliability), C17: r.pick(CHOICES.confidence), C18: r.pick(CHOICES.testType),
    C21: r.pick(MATERIALITY), C24: r.rate(0, 0.024),
    C32: r.pick(CHOICES.category), C33: r.pick(MOSTLY_NO), C34: r.pick(MOSTLY_NO),
    C43: r.chance(0.5) ? 0 : r.amount(0, 40000),
    C54: separated(r, 150000), C55: separated(r, 60000),
  }
  for (const column of STRATA_COLUMNS) {
    const units = r.int(8, 600)
    const mean = r.amount(15000, 250000)
    cells[`${column}12`] = units
    cells[`${column}13`] = money(units * mean)
    cells[`${column}28`] = r.amount(0.02 * mean, 0.6 * mean)
    cells[`${column}45`] = r.amount(3 * mean, 40 * mean)
    cells[`${column}46`] = r.chance(0.2) ? 0 : r.amount(0, 1.2 * mean)
    cells[`${column}47`] = r.amount(0.01 * mean, 0.4 * mean)
  }
  return { ...cells, ...POPULATION }
}

/** Umfassende Schicht eines Zeitraums Blatt 10: Buchwert, Einheiten, davon hochwertige. */
function exhaustive10(r, bookValue) {
  const units = r.int(0, 10)
  return [units === 0 ? 0 : money(r.rate(0.02, 0.3) * bookValue), units, r.int(0, units)]
}

/** Prüfergebnisse eines Zeitraums Blatt 10: Σ BV_i, Σ E_i, s_e, s_q, ΣE_e. */
function findings10(r, mean) {
  return [r.amount(10 * mean, 60 * mean), r.amount(0, 0.6 * mean), r.amount(0.01 * mean, 0.3 * mean), r.amount(0.01 * mean, 0.4 * mean), r.chance(0.5) ? 0 : r.amount(0, 0.5 * mean)]
}

function inputs10(r) {
  const units1 = r.int(120, 1500)
  const bookValue1 = r.amount(5e6, 1e8)
  const forecastUnits2 = r.int(100, 1500)
  const forecastBookValue2 = r.amount(5e6, 1e8)
  const [exhaustiveBookValue1, exhaustiveUnits1, highValueUnits1] = exhaustive10(r, bookValue1)
  const mean = (bookValue1 + forecastBookValue2) / (units1 + forecastUnits2)
  const bookValue2 = money(forecastBookValue2 * r.rate(0.7, 1.4))
  const units2 = Math.round(forecastUnits2 * r.rate(0.7, 1.4))
  const [exhaustiveBookValue2, exhaustiveUnits2, highValueUnits2] = exhaustive10(r, bookValue2)
  const [sampleBookValue1, errors1, errorDeviation1, ratioDeviation1, exhaustiveErrors1] = findings10(r, mean)
  const [sampleBookValue2, errors2, errorDeviation2, ratioDeviation2, exhaustiveErrors2] = findings10(r, mean)
  return {
    C4: 'Zufallsfall', C5: '2025/2026', C6: 'Vorhaben',
    C7: bookValue1, C8: units1, C9: exhaustiveBookValue1, C10: exhaustiveUnits1, C11: highValueUnits1,
    C14: forecastBookValue2, C15: forecastUnits2,
    C18: r.pick(CHOICES.reliability), C19: r.pick(CHOICES.confidence), C20: r.pick(CHOICES.testType),
    C23: r.pick(MATERIALITY), C26: r.rate(0, 0.024),
    C29: r.amount(0.02 * mean, 0.6 * mean), C30: r.amount(0.02 * mean, 0.6 * mean),
    C32: r.pick(CHOICES.recalculation),
    C34: r.pick(CHOICES.category), C35: r.pick(MOSTLY_NO), C36: r.pick(MOSTLY_NO),
    C44: sampleBookValue1, C45: errors1, C46: errorDeviation1, C47: ratioDeviation1, C48: exhaustiveErrors1,
    C49: bookValue2, C50: units2, C51: exhaustiveBookValue2, C52: exhaustiveUnits2, C53: highValueUnits2,
    C56: r.amount(0.02 * mean, 0.6 * mean), C57: r.rate(0, 0.024),
    C77: sampleBookValue2, C78: errors2, C79: errorDeviation2, C80: ratioDeviation2, C81: exhaustiveErrors2,
    C86: separated(r, 2 * mean), C87: separated(r, mean),
  }
}

/** Umfassende Schicht eines Zeitraums Blatt 11: Buchwert, Einheiten, davon hochwertig, Fehlersumme. */
function exhaustive11(r) {
  const units = r.int(0, 8)
  return [units === 0 ? 0 : r.amount(2e5, 2e7), units, r.int(0, units), r.chance(0.5) ? 0 : r.amount(0, 40000)]
}

/** Schichtzeilen einer Spalte Blatt 11: Zeitraum 1, Prognose und Ist für Zeitraum 2, Prüfergebnisse. */
function stratum11(r, column, cells) {
  const mean = r.amount(15000, 250000)
  const [units1, units2] = [r.int(8, 600), r.int(8, 600)]
  const actual2 = Math.max(4, Math.round(units2 * r.rate(0.7, 1.4)))
  Object.assign(cells, {
    [`${column}11`]: units1, [`${column}12`]: money(units1 * mean),
    [`${column}13`]: units2, [`${column}14`]: money(units2 * mean * r.rate(0.8, 1.2)),
    [`${column}29`]: r.amount(0.02 * mean, 0.6 * mean), [`${column}30`]: r.amount(0.02 * mean, 0.6 * mean),
    [`${column}49`]: r.amount(3 * mean, 40 * mean), [`${column}50`]: r.chance(0.2) ? 0 : r.amount(0, 1.2 * mean),
    [`${column}51`]: r.amount(0.02 * mean, 0.6 * mean), [`${column}52`]: r.amount(0.01 * mean, 0.4 * mean),
    [`${column}57`]: actual2, [`${column}58`]: money(actual2 * mean * r.rate(0.8, 1.2)),
    [`${column}59`]: r.amount(0.02 * mean, 0.6 * mean),
    [`${column}84`]: r.amount(3 * mean, 40 * mean), [`${column}85`]: r.chance(0.2) ? 0 : r.amount(0, 1.2 * mean),
    [`${column}86`]: r.amount(0.02 * mean, 0.6 * mean), [`${column}87`]: r.amount(0.01 * mean, 0.4 * mean),
  })
}

function inputs11(r) {
  const [bookValue1, units1, highValue1, errors1] = exhaustive11(r)
  const [bookValue2, units2, highValue2, errors2] = exhaustive11(r)
  const cells = {
    C4: 'Zufallsfall', C5: '2025/2026', C6: 'Vorhaben',
    C7: bookValue1, C8: units1, C9: highValue1,
    C17: r.pick(CHOICES.reliability), C18: r.pick(CHOICES.confidence), C19: r.pick(CHOICES.testType),
    C22: r.pick(MATERIALITY), C25: r.rate(0, 0.024),
    C33: r.pick(CHOICES.recalculation),
    C35: r.pick(CHOICES.category), C36: r.pick(MOSTLY_NO), C37: r.pick(MOSTLY_NO),
    C47: errors1,
    C53: bookValue2, C54: units2, C55: highValue2, C60: r.rate(0, 0.024),
    C82: errors2,
    C94: separated(r, 150000), C95: separated(r, 60000),
  }
  for (const column of STRATA_COLUMNS) stratum11(r, column, cells)
  return cells
}

/** Ist-Werte eines Zeitraums Blatt 12: Buchwert, Anzahl, umfassende Schicht mit hochwertigen Einheiten. */
function period12(r) {
  const units = r.int(60, 900)
  const bookValue = r.amount(3e6, 8e7)
  const exhaustiveUnits = r.int(0, 8)
  return {
    units, bookValue, exhaustiveUnits, mean: bookValue / units,
    exhaustiveBookValue: exhaustiveUnits === 0 ? 0 : money(r.rate(0.02, 0.25) * bookValue),
    highValueUnits: r.int(0, exhaustiveUnits),
  }
}

/** Prüfergebnisse eines Zeitraums Blatt 12: Σ BV_i, Σ E_i, s_e, s_q, ΣE_e. */
function findings12(r, mean) {
  return [r.amount(8 * mean, 70 * mean), r.amount(0, 1.5 * mean), r.amount(0.01 * mean, 0.2 * mean), r.amount(0.01 * mean, 0.2 * mean), r.chance(0.5) ? 0 : r.amount(0, 0.5 * mean)]
}

/** Prognose zu einem Ist-Wert: 80 % bis 125 %. */
const forecast = (r, value, digits) => Number((value * r.rate(0.8, 1.25)).toFixed(digits))

function inputs12(r) {
  const [p1, p2, p3] = [period12(r), period12(r), period12(r)]
  const [f1, f2, f3] = [findings12(r, p1.mean), findings12(r, p2.mean), findings12(r, p3.mean)]
  const deviation = (p) => r.amount(0.01 * p.mean, 0.15 * p.mean)
  return {
    C4: 'Zufallsfall', C5: '2025/2026', C6: 'Vorhaben',
    C7: p1.bookValue, C8: p1.units, C9: p1.exhaustiveBookValue, C10: p1.exhaustiveUnits, C11: p1.highValueUnits,
    C14: forecast(r, p2.bookValue, 2), C15: forecast(r, p2.units - p2.exhaustiveUnits, 0), C16: forecast(r, p3.bookValue, 2), C17: forecast(r, p3.units - p3.exhaustiveUnits, 0),
    C20: r.pick(CHOICES.reliability), C21: r.pick(CHOICES.confidence), C22: r.pick(CHOICES.testType),
    C25: r.pick(MATERIALITY), C28: r.rate(0, 0.021),
    C31: deviation(p1), C32: deviation(p2), C33: deviation(p3), C35: r.pick(CHOICES.recalculation),
    C37: r.pick(CHOICES.category), C38: r.pick(MOSTLY_NO), C39: r.pick(MOSTLY_NO),
    C48: f1[0], C49: f1[1], C50: f1[2], C51: f1[3], C52: f1[4],
    C53: p2.bookValue, C54: p2.units, C55: p2.exhaustiveBookValue, C56: p2.exhaustiveUnits, C57: p2.highValueUnits,
    C60: forecast(r, p3.bookValue, 2), C61: forecast(r, p3.units - p3.exhaustiveUnits, 0), C62: deviation(p2), C63: deviation(p3), C64: r.rate(0, 0.02),
    C87: f2[0], C88: f2[1], C89: f2[2], C90: f2[3], C91: f2[4],
    C92: p3.bookValue, C93: p3.units, C94: p3.exhaustiveBookValue, C95: p3.exhaustiveUnits, C96: p3.highValueUnits,
    C99: deviation(p3), C100: r.rate(0, 0.02),
    C121: f3[0], C122: f3[1], C123: f3[2], C124: f3[3], C125: f3[4],
    C130: separated(r, 2 * p1.mean), C131: separated(r, p1.mean),
  }
}

/** Beschreibung eines Blatts: Generator aus Startwert und Blattname, Fallname „Zufall 001“. */
function sheet(sheetName, inputs) {
  return {
    start: START,
    count: COUNT,
    cases: ({ start, count }) => {
      const r = draws(mulberry32(sheetSeed(start, sheetName)))
      return series(count, (index) => randomCase(`Zufall ${padded(index)}`, sheetName, inputs(r)))
    },
  }
}

export const sheets = {
  '08_SRS_1Z': sheet('08_SRS_1Z', inputs08),
  '09_SRS_1Z_S': sheet('09_SRS_1Z_S', inputs09),
  '10_SRS_2Z': sheet('10_SRS_2Z', inputs10),
  '11_SRS_2Z_S': sheet('11_SRS_2Z_S', inputs11),
  '12_SRS_3Z': sheet('12_SRS_3Z', inputs12),
}
