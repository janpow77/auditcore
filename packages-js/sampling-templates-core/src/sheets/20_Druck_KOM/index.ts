/** Blatt 20_Druck_KOM: Druckfassung für die Kommission; liest Blatt 02, das aktive Verfahren und Blatt 18. */
import { defineSheet, templateNumber, type Adaptation } from '../../model/sheet'
import type { CellMap, CellValue } from '../../model/types'
import { compute, headLead } from './compute'
import { CASE_ROWS, definition } from './definition'
import { deviations } from './deviations'
import { webHints } from './hints'
import { en } from './texts.en'

/** Beginn des Teils der Kopfzeile, den die Webfassung unverändert aus der Vorlage übernimmt. */
const HEAD_TAIL_START = 'CCI '

/** Erfundene Beispielwerte; sie stammen aus keiner Prüfung, Programm und Prüfbehörde gibt es nicht. */
const sample: CellMap = {
  W4: 'Beispielprogramm EFRE Musterland 2021–2027',
  W5: 'Prüfbehörde Musterland (Beispiel)',
  W6: 'Referat Beispiel',
  W7: 'Musterstadt',
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

/**
 * Kopfzeile A6: Die Vorlage beginnt sie mit einem festen Programmnamen. Die
 * Webfassung setzt die Bezeichnung des Programms ein, die die Prüfbehörde angibt
 * (W4); der Rest der Zeile – ab „CCI“ – ist wie in der Vorlage.
 */
const adapted: readonly Adaptation[] = [
  {
    cell: 'A6',
    reason: 'Die Vorlage nennt in der Kopfzeile fest ein bestimmtes Programm; die Webfassung nennt das Programm der Prüfbehörde, die den Bericht erstellt.',
    fromTemplate: (shown, results) => (typeof shown === 'string' && shown.includes(HEAD_TAIL_START) ? `${headLead(results.W4)}${shown.slice(shown.indexOf(HEAD_TAIL_START))}` : templateNumber(shown)),
  },
  // Fehlerquote eines Falls mit Buchwert 0: Die Formel der Vorlage hat kein WENNFEHLER und zeigt #DIV/0!; die Webfassung zeigt keinen Wert und den Hinweis „case-book-value-zero“.
  ...CASE_ROWS.map((row) => ({
    cell: `E${row}`,
    reason: 'Bei Buchwert 0 zeigt die Vorlage den Fehlerwert #DIV/0! (die Formel fängt ihn nicht ab). Die Webfassung zeigt keinen Wert und weist den Fall als nicht bestimmbar aus.',
    fromTemplate: (shown: CellValue | boolean) => (shown === '#DIV/0!' ? null : templateNumber(shown)),
  })),
]

export const sheet = defineSheet({ id: '20_Druck_KOM', definition, compute, sample: { inputs: sample }, deviations, webHints, adapted, translations: { en } })
