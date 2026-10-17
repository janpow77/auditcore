/**
 * Blatt 01 der Vorlage als Daten: z-Werte nach Anhang I Nr. 3 DelVO (EU) 2023/67
 * und die Auswahllisten. Das Blatt hat keine Eingaben und keine Formeln.
 */
import { FormulaError, eq, isNumber, sameText } from '../../excel/index'
import type { TranslationLocale } from '../../model/texts'
import type { Parameters } from '../../model/types'
import { en } from './texts.en'

/** Arbeitsübersetzungen zu Blatt 01 (Listeneinträge, Merksätze); sie gelten für alle Blätter. */
export const SHARED_TEXTS: Readonly<Record<TranslationLocale, Readonly<Record<string, string>>>> = { en }

export const PARAMETERS: Parameters = {
  zTable: [
    { confidence: 0.6, twoSided: 0.842, oneSided: 0.253, source: 'Anh. I Nr. 3', inAnnex: true },
    { confidence: 0.7, twoSided: 1.036, oneSided: 0.524, source: 'Anh. I Nr. 3', inAnnex: true },
    { confidence: 0.8, twoSided: 1.282, oneSided: 0.842, source: 'Anh. I Nr. 3', inAnnex: true },
    { confidence: 0.9, twoSided: 1.645, oneSided: 1.282, source: 'Anh. I Nr. 3', inAnnex: true },
    {
      confidence: 0.95,
      twoSided: 1.96,
      oneSided: 1.645,
      source: 'Nicht in Anh. I enthalten; Werte der Standardnormalverteilung, nur bei fachlich begründet höherem Konfidenzniveau',
      inAnnex: false,
    },
  ],
  notes: {
    materiality: 'Wesentlichkeitsschwelle: höchstens 2 % (Anh. I Nr. 1 i. V. m. Anh. XX Nr. 5.9 VO (EU) 2021/1060).',
    minimumSize: 'Mindeststichprobenumfang: 30 Einheiten, mindestens 3 je Zufallsschicht eines Stichprobenzeitraums (Art. 5 Abs. 5).',
    limitedSize: 'Begrenzter Stichprobenumfang: 50 Einheiten für Programme der Kategorie 1 oder 2 ohne Art. 83 (Art. 5 Abs. 7); 30 Einheiten bei Art. 83.',
  },
  lists: {
    reliability: ['hoch', 'mittel', 'gering'],
    testType: ['zweiseitig', 'einseitig'],
    yesNo: ['Ja', 'Nein'],
    category: [1, 2, 3, 4],
    recalculation: [
      'Standard (Art. 5 Abs. 6 Buchst. a)',
      'Global (Art. 5 Abs. 6 Buchst. b)',
      'Erhöhung bei begrenztem Umfang (Art. 5 Abs. 7 UAbs. 4 Buchst. a)',
      'keine Neuberechnung',
    ],
    article80: ['keine betroffenen Einheiten', 'Ausschluss (Art. 3 Abs. 6 Buchst. b)', 'Ersetzung (Anh. III)'],
    negativePopulation: ['Prüfung im Rahmen der Prüfung der Rechnungslegung', 'gesondertes Stichprobenverfahren'],
    methodSheets: [
      '03_MUS_1Z',
      '04_MUS_1Z_S',
      '05_MUS_2Z',
      '06_MUS_2Z_S',
      '07_MUS_3Z',
      '08_SRS_1Z',
      '09_SRS_1Z_S',
      '10_SRS_2Z',
      '11_SRS_2Z_S',
      '12_SRS_3Z',
      '13_NS_GW',
      '14_NS_GW_S',
      '15_NS_PPS',
      '16_NS_PPS_S',
    ],
  },
}

/**
 * Koeffizient z bzw. z' zum Konfidenzniveau; entspricht
 * `INDEX(01_Parameter!C5:D9;VERGLEICH(niveau;01_Parameter!B5:B9;0);WENN(testart="einseitig";2;1))`.
 * Ein Konfidenzniveau außerhalb der Tabelle ergibt einen Fehlerwert.
 */
export function zValue(parameters: Parameters, confidence: unknown, testType: unknown): number {
  const row = isNumber(confidence) ? parameters.zTable.find((entry) => eq(entry.confidence, confidence)) : undefined
  if (!row) throw new FormulaError('#NV')
  return sameText(testType, 'einseitig') ? row.oneSided : row.twoSided
}
