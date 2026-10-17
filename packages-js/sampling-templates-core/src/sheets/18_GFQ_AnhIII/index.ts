/** Blatt 18_GFQ_AnhIII: Gesamtfehlerquote mit technischer Hilfe und Anpassung nach Anhang III; liest das aktive Verfahren und Blatt 02. */
import { defineSheet } from '../../model/sheet'
import type { CellMap } from '../../model/types'
import { compute } from './compute'
import { definition } from './definition'
import { deviations } from './deviations'
import { webHints } from './hints'
import { en } from './texts.en'

/** Erfundene Beispielwerte; sie stammen aus keiner Prüfung. Die übrigen Größen kommen aus Blatt 02 und dem gewählten Verfahren. */
const sample: CellMap = { C20: 'Nein', C29: 0.02 }

export const sheet = defineSheet({ id: '18_GFQ_AnhIII', definition, compute, sample: { inputs: sample }, deviations, webHints, translations: { en } })
