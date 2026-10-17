/**
 * Begründete Abweichungen des Blatts X4 vom Verhalten der Vorlage bei leeren
 * Eingaben. Die Altvorlage rechnet mit jeder leeren Zelle als 0 weiter; fehlt
 * eine Pflichteingabe, zeigt die Webfassung „Angabe fehlt“ (`null`), nie einen
 * anderen Wert. Sind alle Pflichteingaben vorhanden, zeigt sie, was die Vorlage
 * zeigt – fragwürdige Ergebnisse mit Hinweis in Warnfarbe. Jede Zeile
 * nennt genau die Eingaben, deren Fehlen die Vorlage einen Wert zeigen lässt,
 * und ist durch einen Golden-Fall belegt (test/deviations.spec.ts).
 *
 * Die Standardabweichung der Stichprobe des ersten Zeitraums (C22) ist
 * Pflichteingabe, weil sie in die Neuberechnung des Umfangs (C31) eingeht.
 * Keine Abweichung, sondern wie in der Vorlage mit 0 gerechnet und ausgewiesen
 * (`zeroAssumed`): die Standardabweichung der Stichprobe des zweiten Zeitraums
 * (C35) und der Fehler der Stichprobe eines Zeitraums (C21 bzw. C34), wenn der
 * andere Zeitraum einen trägt. Fehlen beide Fehler, bleibt die Hochrechnung offen.
 */
import type { Deviation } from '../../model/types'
import { deviationRows } from '../shared/legacy'

const FIRST = ['C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C10', 'C12']
/** Eingaben, ohne die die Vorlage für den zweiten Zeitraum dennoch einen Wert zeigt. */
const SECOND = ['C3', 'C4', 'C6', 'C7', 'C8', 'C12', 'C22', 'C25', 'C27']
const BOOK_VALUE = 'Der Buchwert der Grundgesamtheit setzt die Buchwerte beider Zeiträume voraus.'
const RECALCULATION = 'Ohne die Angaben beider Zeiträume ist der neu berechnete Stichprobenumfang nicht bestimmt; alle Folgegrößen bleiben offen.'

export const deviations: readonly Deviation[] = [
  ...deviationRows(['C1', 'C15'], ['C3', 'C4'], 'Wert auf Grundlage nur eines Buchwerts bzw. 0 €', BOOK_VALUE),
  ...deviationRows(['C9'], ['C5', 'C6', 'C7', 'C8'], 'Wert ohne den Beitrag des Zeitraums mit fehlender Angabe', 'Das gewichtete Mittel der Varianzen setzt Umfang und Standardabweichung beider Zeiträume voraus.'),
  ...deviationRows(['C11'], ['C10'], 'FALSCH (keine Stufe des Konfidenzniveaus trifft zu; zählt in der Rechnung als 0)', 'Ohne Konfidenzniveau gibt es keinen Koeffizienten z.'),
  ...deviationRows(['C13'], ['C3', 'C4', 'C12'], '0 € bzw. Wert auf Grundlage nur eines Buchwerts', 'Der voraussichtliche Fehler setzt die Buchwerte beider Zeiträume und die erwartete Fehlerquote voraus.'),
  ...deviationRows(['C16', 'C17', 'C18'], FIRST, 'Umfang auf Grundlage der mit 0 gerechneten Angabe (z. B. 0)', 'Ohne die Angaben zur Planung des ersten Zeitraums ist der Stichprobenumfang nicht bestimmt.'),
  ...deviationRows(['C24', 'C30', 'C43'], ['C3', 'C25'], 'Wert auf Grundlage nur eines Buchwerts bzw. 0 €', BOOK_VALUE),
  ...deviationRows(['C28'], ['C3', 'C25', 'C27'], '0 € bzw. Wert auf Grundlage nur eines Buchwerts', 'Der voraussichtliche Fehler setzt die Buchwerte beider Zeiträume und die erwartete Fehlerquote voraus.'),
  ...deviationRows(['C31'], [...SECOND, 'C23', 'C26'], 'Umfang auf Grundlage der mit 0 gerechneten Angabe (z. B. 0)', RECALCULATION),
  ...deviationRows(['C39', 'C40'], SECOND, 'Genauigkeit auf Grundlage der mit 0 gerechneten Angabe', RECALCULATION),
  ...deviationRows(
    ['C36', 'C37', 'C38', 'C41', 'C42'],
    [...SECOND, 'C21', 'C34'],
    'Hochrechnung mit einem Stichprobenfehler von 0 € bzw. auf Grundlage der mit 0 gerechneten Angabe',
    'Die Hochrechnung setzt die Stichprobenumfänge und die Fehler der Stichproben beider Zeiträume voraus.',
  ),
]
