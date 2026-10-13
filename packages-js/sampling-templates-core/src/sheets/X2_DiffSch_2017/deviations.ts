/**
 * Begründete Abweichungen des Blatts X2 vom Verhalten der Vorlage bei leeren
 * Eingaben. Die Altvorlage rechnet mit jeder leeren Zelle als 0 weiter; die
 * Webfassung zeigt „Angabe fehlt“ (`null`), nie einen anderen Wert. Jede Zeile
 * nennt genau die Eingaben, deren Fehlen die Vorlage einen Wert zeigen lässt,
 * und ist durch einen Golden-Fall belegt (test/deviations.spec.ts). Fehlt der
 * Buchwert (C1), zeigt auch die Vorlage ab C11 keinen Wert (Division durch
 * null). Die Standardabweichung der Stichprobe (C15) ist keine Abweichung: Sie
 * wird wie in der Vorlage mit 0 gerechnet und ausgewiesen (`zeroAssumed`).
 */
import type { Deviation } from '../../model/types'
import { deviationRows } from '../shared/legacy'

const SIZE_INPUTS = ['C3', 'C4', 'C5', 'C7']
const SIZE = 'Ohne Umfang der Grundgesamtheit, Standardabweichung, Konfidenzniveau und erwartete Fehlerquote ist der Stichprobenumfang nicht bestimmt; alle Folgegrößen bleiben offen.'

export const deviations: readonly Deviation[] = [
  ...deviationRows(['C6'], ['C5'], '0 (keine Stufe des Konfidenzniveaus trifft zu; Excel zeigt FALSCH)', 'Ohne Konfidenzniveau gibt es keinen Koeffizienten z.'),
  ...deviationRows(['C8'], ['C1', 'C7'], '0 € (leere Zelle zählt als 0)', 'Der voraussichtliche Fehler setzt Buchwert und erwartete Fehlerquote voraus.'),
  ...deviationRows(['C10', 'C23'], ['C1'], '0 € (leere Zelle zählt als 0)', 'Der zulässige Fehler setzt den Buchwert voraus.'),
  ...deviationRows(['C11', 'C19', 'C20'], SIZE_INPUTS, 'Wert auf Grundlage des mit 0 berechneten Umfangs (Mindestumfang 30)', SIZE),
  ...deviationRows(
    ['C14', 'C16', 'C17', 'C18', 'C21', 'C22'],
    [...SIZE_INPUTS, 'C13'],
    'Hochrechnung mit einem Stichprobenfehler von 0 € bzw. auf Grundlage des mit 0 berechneten Umfangs',
    'Die Hochrechnung setzt den Stichprobenumfang und den Fehler der Stichprobe voraus.',
  ),
]
