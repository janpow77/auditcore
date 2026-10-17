/** Blatt 07_MUS_3Z: MUS-Standardansatz, drei Stichprobenzeiträume, nicht geschichtet. */
import { gt, isBlank, isNumber, le, sameNumber } from '../../excel/index'
import { defineSheet, type ZeroAssumption } from '../../model/sheet'
import type { CellMap, WebHint } from '../../model/types'
import { approachOf, errorDependents, limitWithoutSize, partialErrorSums } from '../shared/mus'
import { compute } from './compute'
import { definition } from './definition'
import { deviations } from './deviations'
import { en } from './texts.en'

/** Erfundene Beispielwerte; sie stammen aus keiner Prüfung. */
const sample: CellMap = {
  C4: 'Beispiel – EFRE-Programm',
  C5: '2025/2026',
  C6: 'Zahlungsantrag des Begünstigten',
  C7: 18000000, C8: 16000000, C9: 14500000, C10: 150, C11: 140,
  C13: 'mittel', C14: 0.7, C15: 'zweiseitig', C18: 0.02, C21: 0.007, C24: 0.12, C25: 0.12, C26: 0.12,
  C28: 'Standard (Art. 5 Abs. 6 Buchst. a)', C30: 2, C31: 'Nein', C32: 'Nein',
  C40: 2, C41: 1500000, C46: 0, C48: 4000, C49: 0.2, C50: 0.05,
  C51: 17000000, C52: 160, C53: 15000000, C54: 145, C55: 0.11, C56: 0.12,
  C79: 2, C80: 1300000, C85: 0, C87: 0, C88: 0.18, C89: 0.045,
  C90: 15500000, C91: 150, C92: 0.1,
  C113: 1, C114: 900000, C119: 0, C121: 2500, C122: 0.15, C123: 0.04,
  C130: 0, C131: 0,
}

/** Hinweis: Stichprobenumfang eines Zeitraums übersteigt die Anzahl seiner Einheiten. */
function exceeds(results: CellMap, size: string, units: string, period: number): WebHint[] {
  const [n, total] = [results[size], results[units]]
  if (!isNumber(n) || !isNumber(total) || !gt(n, total)) return []
  return [{ id: `size-exceeds-population-${period}`, tone: 'warning', text: `Stichprobenumfang für Zeitraum ${period} übersteigt die Anzahl der Einheiten des Zeitraums` }]
}

/** Hinweis: Nenner der Standardneuberechnung nicht positiv (nur beim Standardansatz von Belang). */
function negativeDenominator(results: CellMap, cell: string, id: string, periods: string): WebHint[] {
  const value = results[cell]
  if (approachOf(results.C28) !== 'standard' || !isNumber(value) || !le(value, 0)) return []
  return [{ id, tone: 'warning', text: `Nenner der Standardneuberechnung ist nicht positiv: Der Standardansatz liefert keinen Umfang für ${periods}. Sind alle Pflichteingaben vorhanden, zeigt die Webfassung wie die Vorlage nur die Untergrenze 3 bzw. die Auffüllung auf 30 und rechnet damit weiter; das Ergebnis ist nicht belastbar. Empfohlen: globale Neuberechnung` }]
}

/** Hinweise der Webfassung zu Blatt 07; sie verändern kein Rechenergebnis. Die Vorlage führt für Zeitraum 1 keine Anzahl der Einheiten. */
function webHints(inputs: CellMap, results: CellMap): WebHint[] {
  const hints: WebHint[] = [
    ...limitWithoutSize(results, 'C34', 'C29', 'C35'),
    ...exceeds(results, 'C108', 'C52', 2),
    ...exceeds(results, 'C109', 'C91', 3),
    ...negativeDenominator(results, 'C64', 'negative-denominator-2', 'Zeitraum 2'),
    ...negativeDenominator(results, 'C98', 'negative-denominator-3', 'Zeitraum 3'),
  ]
  if (sameNumber(results.C14, 0.95)) hints.push({ id: 'confidence-outside-annex', tone: 'warning', text: 'Konfidenzniveau 95 % liegt außerhalb der Tabelle in Anhang I' })
  return hints
}

/** Zellen, die von der Genauigkeit abhängen: SE, Fehlergrenzen, relative Genauigkeit, obere Grenze in %, Würdigung. */
const PRECISION_CELLS = ['C129', 'C132', 'C133', 'C134', 'C137', 'C138']

/** Zellen, die von der Summe der Fehlerquoten eines Zeitraums abhängen: EE_s, EE, Fehlergrenzen, Quoten, Würdigung, N5 und N11. */
const ERROR_CELLS = ['C127', ...errorDependents(128)]

/**
 * Fehlt die Standardabweichung der Stichprobe eines Zeitraums (C50, C89, C123),
 * rechnet die Vorlage dessen Beitrag zur Genauigkeit mit 0. Fehlt die Summe der
 * Fehlerquoten eines Zeitraums (C49, C88, C122), während die eines anderen
 * eingetragen ist, rechnet sie dessen Beitrag zur Hochrechnung mit 0.
 */
function zeroAssumed(results: CellMap): ZeroAssumption[] {
  const sums = partialErrorSums(results, 'C128', [['C49', ERROR_CELLS], ['C88', ERROR_CELLS], ['C122', ERROR_CELLS]])
  if (!isNumber(results.C129)) return sums
  return [...['C50', 'C89', 'C123'].filter((input) => isBlank(results[input])).map((input) => ({ input, cells: PRECISION_CELLS })), ...sums]
}

export const sheet = defineSheet({ id: '07_MUS_3Z', definition, compute, sample: { inputs: sample }, deviations, webHints, zeroAssumed, translations: { en } })
