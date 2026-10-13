/**
 * Wegweiser der Verfahrensauswahl: regelbasierte Hinweise aus Blatt 02 und
 * Blatt 01, wörtlich aus der Vorlage. Der Wegweiser empfiehlt kein Verfahren.
 */
import { formatEur, formatInt } from '@auditcore/common'
import { isBlank, isNumber, toneOf } from '../excel/index'
import type { Translate } from '../i18n/messages'
import { findField } from '../model/definition'
import type { AvailableSheet } from '../model/sheet'
import { translateValue } from '../model/texts'
import type { CellMap, Parameters, Tone } from '../model/types'

/** Blatt, aus dem der Wegweiser liest. */
export const POPULATION_SHEET = '02_Grundgesamtheit'

export interface GuideItem {
  id: string
  text: string
  tone: Tone
}

export interface GuideView {
  /** Kurzfassung der angepassten Grundgesamtheit oder Hinweis, dass Blatt 02 noch leer ist. */
  lead: string
  items: readonly GuideItem[]
}

/**
 * Hinweise aus der angepassten Grundgesamtheit: Zulässigkeit eines
 * nichtstatistischen Verfahrens (02!C53), Mindestumfang von 10 % (02!C54) und
 * der Merksatz zum begrenzten Stichprobenumfang aus Blatt 01.
 */
export function buildGuide(population: AvailableSheet | undefined, results: CellMap | undefined, parameters: Parameters, t: Translate): GuideView {
  const limited: GuideItem = { id: 'limited-size', text: translateValue(population?.texts, parameters.notes.limitedSize), tone: 'neutral' }
  const units = results?.C52
  if (!population || !results || !isNumber(units) || units === 0) return { lead: t('guideEmpty'), items: [limited] }
  return { lead: t('guideUnits', { units: formatInt(units), bookValue: formatEur(results.C51) }), items: [...populationItems(population, results), limited] }
}

/** Hinweise, die Blatt 02 selbst ausgibt: Prüfhinweis C53 und Mindestumfang C54 mit Bezeichnung und Fundstelle. */
function populationItems(population: AvailableSheet, results: CellMap): GuideItem[] {
  const items: GuideItem[] = []
  if (!isBlank(results.C53)) items.push({ id: 'C53', text: translateValue(population.texts, String(results.C53)), tone: toneOf(results.C53) })
  const minimum = findField(population.definition, 'C54')
  if (minimum && isNumber(results.C54)) items.push({ id: 'C54', text: `${minimum.label}: ${formatInt(results.C54)} (${minimum.hint ?? ''})`, tone: 'neutral' })
  return items
}
