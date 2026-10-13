/** Blatt 20_Druck_KOM: Druckfassung für die Kommission; liest Blatt 02, das aktive Verfahren und Blatt 18. */
import { defineSheet } from '../../model/sheet'
import type { CellMap } from '../../model/types'
import { compute } from './compute'
import { definition } from './definition'
import { deviations } from './deviations'
import { webHints } from './hints'
import { en } from './texts.en'

/** Erfundene Beispielwerte; sie stammen aus keiner Prüfung. */
const sample: CellMap = {
  J4: '13.10.2026',
  J5: 'vorläufig',
  J6: 5300000,
  J7: 0,
  J8: 120000,
  A20: 'Beispiel-VP 1',
  B20: 'Beispiel A',
  C20: 250000,
  D20: 4200,
  F20: 'nicht förderfähige Ausgaben (Beispiel)',
  G20: 'vorläufig',
  A21: 'Beispiel-VP 2',
  B21: 'Beispiel B',
  C21: 480000,
  D21: 1150,
  F21: 'Vergabe (Beispiel)',
  G21: 'endgültig',
}

export const sheet = defineSheet({ id: '20_Druck_KOM', definition, compute, sample: { inputs: sample }, deviations, webHints, translations: { en } })
