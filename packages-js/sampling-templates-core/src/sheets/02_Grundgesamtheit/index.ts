/** Blatt 02_Grundgesamtheit: Aufbereitung der Grundgesamtheit; liefert BV und N an die Methodenblätter. */
import { defineSheet } from '../../model/sheet'
import type { CellMap } from '../../model/types'
import { compute } from './compute'
import { definition } from './definition'
import { deviations } from './deviations'
import { en } from './texts.en'

/** Erfundene Beispielwerte; sie stammen aus keiner Prüfung und passen zu den Beispielwerten des Blatts 03. */
const sample: CellMap = {
  C9: '2021DE16RFPR000 (Beispiel)',
  C10: 'EFRE',
  C11: '2021–2027',
  C12: '01.07.2025–30.06.2026',
  C13: 'Zahlungsantrag des Begünstigten',
  C14: 'Beispielauszug, Stichtag 31.07.2026',
  C15: 49200000,
  C16: 49200000,
  C20: 700000,
  C21: 'Ja',
  C23: 432,
  C24: 420,
  C25: 48500000,
  C26: 12,
  C27: 0,
  C36: 'Ja',
  C40: 400000,
  C49: 'keine betroffenen Einheiten',
}

export const sheet = defineSheet({ id: '02_Grundgesamtheit', definition, compute, sample: { inputs: sample }, deviations, translations: { en } })
