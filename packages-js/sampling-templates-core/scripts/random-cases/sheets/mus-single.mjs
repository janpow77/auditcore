/**
 * Zufallsbelegungen der Blätter 03 und 04 (MUS-Standardansatz, ein Stichprobenzeitraum): alle
 * Eingaben ausgefüllt, Auswahlfelder über alle Einträge. Blatt 04 belegt eine bis sieben
 * Schichtspalten ohne Lücken. Für diese beiden Blätter gab es bisher keinen Fallsatz
 * `<Blatt>.zufall.json`; die Startwerte sind hier erstmals festgelegt.
 */
import { CHOICES, STRATA_COLUMNS, draws, mulberry32, padded, randomCase, series, stratumCells } from '../core.mjs'

const COUNT = 100
const MATERIALITY = [0.02, 0.02, 0.02, 0.015, 0.01]

/** Abgegrenzte systembedingte bzw. anomale Fehler: in 60 % der Fälle 0. */
const separated = (r, max) => (r.chance(0.6) ? 0 : r.amount(0, max))

/** Hochwertige Einheiten: Anzahl, ihr Buchwert (bis 30 % der Grundgesamtheit bzw. Schicht), ihre Fehlersumme. */
function highValue(r, bookValue, maxUnits) {
  const units = r.int(0, maxUnits)
  return { units, bookValue: units === 0 ? 0 : r.amount(0, 0.3 * bookValue), errors: units === 0 || r.chance(0.3) ? 0 : r.amount(0, 60000) }
}

function inputs03(r, index) {
  const bookValue = r.amount(2e6, 3e8)
  const high = highValue(r, bookValue, 12)
  return {
    C4: `Zufall ${index}`, C5: '2025/2026', C6: r.pick(CHOICES.samplingUnit),
    C7: bookValue, C8: r.int(60, 3000),
    C9: r.pick(CHOICES.reliability), C10: r.pick(CHOICES.confidence), C11: r.pick(CHOICES.testType),
    C14: r.pick(MATERIALITY), C17: r.rate(0, 0.022), C20: r.rate(0.01, 0.6),
    C22: r.pick(CHOICES.category), C23: r.pick(CHOICES.yesNo), C24: r.pick(CHOICES.yesNo),
    C29: high.units, C30: high.bookValue, C35: r.pick([0, 0, 0, 1, 3]),
    C37: high.errors, C38: r.rate(0, 2), C39: r.rate(0, 0.4),
    C44: separated(r, 90000), C45: separated(r, 20000),
  }
}

/** Schichtspalte Blatt 04: Grundgesamtheit, Planung, hochwertige Einheiten und Prüfergebnisse. */
function stratum04(r, column) {
  const bookValue = r.amount(5e5, 4e7)
  const high = highValue(r, bookValue, 6)
  return stratumCells(column, [
    [9, bookValue], [10, r.int(20, 400)], [24, r.rate(0.01, 0.6)],
    [37, high.units], [38, high.bookValue], [43, r.pick([0, 0, 0, 1, 2])],
    [45, high.errors], [46, r.rate(0, 1.2)], [47, r.rate(0, 0.4)],
  ])
}

function case04(r, index) {
  const strata = r.pick([1, 2, 3, 3, 4, 5, 7, 7])
  const cells = {
    C4: `Zufall ${index}`, C5: '2025/2026', C6: r.pick(CHOICES.samplingUnit), C7: r.pick(['Programm', 'Fonds', 'zwischengeschaltete Stelle', 'Risiko']),
    C12: r.pick(CHOICES.reliability), C13: r.pick(CHOICES.confidence), C14: r.pick(CHOICES.testType),
    C17: r.pick(MATERIALITY), C20: r.rate(0, 0.022),
    C28: r.pick(CHOICES.category), C29: r.pick(CHOICES.yesNo), C30: r.pick(CHOICES.yesNo),
    C55: separated(r, 90000), C56: separated(r, 20000),
  }
  for (const column of STRATA_COLUMNS.slice(0, strata)) Object.assign(cells, stratum04(r, column))
  return randomCase(`Zufallsbelegung ${padded(index)} (${strata} Schichten)`, '04_MUS_1Z_S', cells)
}

export const sheets = {
  '03_MUS_1Z': {
    start: 2026101303,
    count: COUNT,
    cases: ({ start, count }) => {
      const r = draws(mulberry32(start))
      return series(count, (index) => randomCase(`Zufallsbelegung ${padded(index)}`, '03_MUS_1Z', inputs03(r, index)))
    },
  },
  '04_MUS_1Z_S': {
    start: 2026101304,
    count: COUNT,
    cases: ({ start, count }) => {
      const r = draws(mulberry32(start))
      return series(count, (index) => case04(r, index))
    },
  },
}
