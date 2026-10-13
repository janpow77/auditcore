/**
 * Zufallsbelegungen der Altvorlagen X1–X4 (Stand 2017): alle Eingaben ausgefüllt, das
 * Konfidenzniveau über alle Stufen, die erwartete Fehlerquote in einem kleinen Teil der Fälle
 * an oder über der Wesentlichkeitsschwelle. Blatt X3 belegt eine bis sieben Schichten, in
 * einem Fünftel der Fälle mit Lücken zwischen den Spalten.
 */
import { CHOICES, LEGACY_STRATA_COLUMNS, draws, mulberry32, randomCase, series } from '../core.mjs'

const COUNT = 100
/** Eingabezeilen je Schicht in X3: Buchwert, Umfang, σ der Planung, Ausgaben, Fehler und s der Stichprobe. */
const STRATUM_ROWS = [6, 7, 8, 18, 19, 21]

/** Erwartete Fehlerquote: meist unter, in 10 % der Fälle an oder über der Wesentlichkeitsschwelle. */
const anticipatedErrorRate = (d) => (d.chance(0.1) ? d.rate(0.02, 0.03) : d.rate(0, 0.018))

function inputsX1(d) {
  const bookValue = d.amount(100000, 500000000)
  return {
    C1: bookValue,
    C2: d.pick(CHOICES.samplingUnit),
    C3: d.int(50, 5000),
    C4: d.pick(CHOICES.confidence),
    C7: d.chance(0.15) ? d.rate(0.012, 0.03) : d.rate(0, 0.012),
    C13: d.amount(0, bookValue * 0.004),
    C14: d.rate(0, 3),
    C16: d.amount(0, bookValue * 0.006),
  }
}

function inputsX2(d) {
  const bookValue = d.amount(1000000, 500000000)
  const units = d.int(300, 6000)
  const average = bookValue / units
  const sample = d.amount(bookValue * 0.05, bookValue * 0.3)
  return {
    C1: bookValue,
    C2: d.pick(CHOICES.samplingUnit),
    C3: units,
    C4: d.amount(average * 0.01, average * 0.08),
    C5: d.pick(CHOICES.confidence),
    C7: anticipatedErrorRate(d),
    C12: sample,
    C13: d.amount(0, sample * 0.02),
    C15: d.amount(average * 0.005, average * 0.08),
  }
}

/** Werte einer Schicht in X3 in der Reihenfolge von `STRATUM_ROWS`. */
function stratumX3(d) {
  const bookValue = d.amount(500000, 100000000)
  const units = d.int(20, 2000)
  const average = bookValue / units
  const sample = d.amount(bookValue * 0.05, bookValue * 0.3)
  return [bookValue, units, d.amount(average * 0.01, average * 0.08), sample, d.amount(0, sample * 0.02), d.amount(average * 0.005, average * 0.08)]
}

function caseX3(d, index) {
  const count = d.int(1, 7)
  const columns = d.chance(0.2) ? LEGACY_STRATA_COLUMNS.filter(() => d.chance(0.6)) : LEGACY_STRATA_COLUMNS.slice(0, count)
  const used = columns.length > 0 ? columns : ['E']
  const inputs = { D2: d.pick(CHOICES.samplingUnit), D9: d.pick(CHOICES.confidence), D11: anticipatedErrorRate(d) }
  for (const column of used) {
    const values = stratumX3(d)
    STRATUM_ROWS.forEach((row, position) => (inputs[`${column}${row}`] = values[position]))
  }
  return randomCase(`Zufallsbelegung ${index} (${used.join(', ')})`, 'X3_DiffSch_S_2017', inputs)
}

function inputsX4(d) {
  const first = d.amount(500000, 250000000)
  const second = d.amount(500000, 250000000)
  const unitsFirst = d.int(100, 3000)
  const unitsSecond = d.int(100, 3000)
  const averageFirst = first / unitsFirst
  const actualSecond = d.amount(second * 0.8, second * 1.2)
  const actualUnits = Math.max(1, Math.round(unitsSecond * (0.8 + 0.4 * d.rate(0, 1))))
  const averageSecond = actualSecond / actualUnits
  const sampleFirst = d.amount(first * 0.05, first * 0.3)
  const sampleSecond = d.amount(actualSecond * 0.05, actualSecond * 0.3)
  return {
    C2: d.pick(CHOICES.samplingUnit),
    C3: first,
    C4: second,
    C5: unitsFirst,
    C6: unitsSecond,
    C7: d.amount(averageFirst * 0.01, averageFirst * 0.08),
    C8: d.amount((second / unitsSecond) * 0.01, (second / unitsSecond) * 0.08),
    C10: d.pick(CHOICES.confidence),
    C12: anticipatedErrorRate(d),
    C20: sampleFirst,
    C21: d.amount(0, sampleFirst * 0.02),
    C22: d.amount(averageFirst * 0.005, averageFirst * 0.08),
    C23: d.amount(averageSecond * 0.01, averageSecond * 0.08),
    C25: actualSecond,
    C26: actualUnits,
    C27: anticipatedErrorRate(d),
    C33: sampleSecond,
    C34: d.amount(0, sampleSecond * 0.02),
    C35: d.amount(averageSecond * 0.005, averageSecond * 0.08),
  }
}

/** Beschreibung eines Blatts mit dem Fallnamen „Zufallsbelegung 1“. */
function sheet(sheetName, start, inputs) {
  return {
    start,
    count: COUNT,
    cases: ({ start: seed, count }) => {
      const d = draws(mulberry32(seed))
      return series(count, (index) => randomCase(`Zufallsbelegung ${index}`, sheetName, inputs(d)))
    },
  }
}

export const sheets = {
  X1_KonsMUS_2017: sheet('X1_KonsMUS_2017', 20170630, inputsX1),
  X2_DiffSch_2017: sheet('X2_DiffSch_2017', 20170631, inputsX2),
  X3_DiffSch_S_2017: {
    start: 20170632,
    count: COUNT,
    cases: ({ start, count }) => {
      const d = draws(mulberry32(start))
      return series(count, (index) => caseX3(d, index))
    },
  },
  X4_DiffSch_2Z_2017: sheet('X4_DiffSch_2Z_2017', 20170633, inputsX4),
}
